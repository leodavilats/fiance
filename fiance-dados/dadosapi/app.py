from __future__ import annotations

import secrets
import threading
import time
from collections.abc import Callable
from contextlib import asynccontextmanager
from datetime import date, timedelta
from pathlib import Path
from typing import Literal

import httpx
from fastapi import Depends, FastAPI, Header, HTTPException, Query, Request, Response
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel, Field

from dadosapi import acesso, banco, cobranca, consultas, fumaca
from dadosapi.config import Configuracao, carregar

FONTES = (
    "B3 (COTAHIST, proventos e eventos); CVM, dados abertos sob ODbL (demonstrações, cadastro, "
    "informe de FII); BCB SGS; Tesouro Transparente. Organizado por fiance."
)
LIMITE_PADRAO = 500
LIMITE_MAXIMO = 5000
MAXIMO_DE_RETRATOS = 50
CHAVES_NOVAS_POR_DIA = 10
CADASTROS_POR_HORA = 5
CONFERENCIA_A_CADA = 6 * 3600
PRIMEIRA_CONFERENCIA = 60
EXEMPLO_DA_VITRINE = "HAPV3"
INICIO_DA_BASE = date(2000, 1, 1)

DESCRICAO = """
Dados de mercado da B3 organizados: cotação diária desde 2005 (com quem saiu da bolsa), série
ajustada por evento conferido pelo preço, proventos com data de pagamento, demonstrações com a data
em que foram entregues à CVM, informe mensal de FII, Tesouro Direto e séries do Banco Central.

**Autenticação:** `Authorization: Bearer <chave>`. Toda resposta traz `X-Limite-Dia` e
`X-Restante-Dia`.

**O dado é do fechamento**: a base é atualizada uma vez por dia útil, à noite. Não há cotação ao
longo do pregão.

**Lacunas conhecidas:** proventos de ETF e BDR só a partir de out/2025, e data de pagamento de
companhia, ETF e BDR também; rendimento de FII só a partir de nov/2016, pelo aviso do administrador
no FundosNet (`origem` `fundosnet`), e o mês sem aviso é estimado pelo informe da CVM e só vem com
`incluir_estimados=true`; cisão e redução de capital não ajustam a série.
"""


class NovaConta(BaseModel):
    email: str = Field(min_length=3, max_length=200)
    nome: str = Field(min_length=1, max_length=200)
    plano: str = "convidado"
    observacao: str | None = Field(default=None, max_length=500)
    pago_ate: date | None = None


class AlteracaoDeConta(BaseModel):
    plano: str | None = None
    ativa: bool | None = None
    pago_ate: date | None = None
    nome: str | None = Field(default=None, min_length=1, max_length=200)
    observacao: str | None = Field(default=None, max_length=500)


class NovaAssinatura(BaseModel):
    plano: Literal["essencial", "pro"]
    ciclo: Literal["mensal", "anual"] = "mensal"
    nome: str | None = Field(default=None, min_length=2, max_length=200)
    cpf_cnpj: str | None = Field(default=None, max_length=18)
    cep: str | None = Field(default=None, max_length=9)
    numero: str | None = Field(default=None, max_length=10)
    telefone: str | None = Field(default=None, max_length=20)

    def pagador(self) -> cobranca.Pagador | None:
        return cobranca.pagador(self.nome, self.cpf_cnpj, self.cep, self.numero, self.telefone)


class NovoAssinante(NovaAssinatura):
    nome: str = Field(min_length=2, max_length=200)
    cpf_cnpj: str = Field(max_length=18)
    cep: str = Field(max_length=9)
    numero: str = Field(max_length=10)
    email: str = Field(max_length=200, pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class NovaChave(BaseModel):
    nome: str = Field(default="principal", min_length=1, max_length=60)


_PAGINAS = Path(__file__).parent / "paginas"


def _pagina(nome: str) -> str:
    return (_PAGINAS / nome).read_text(encoding="utf-8")


def _origem(request: Request, proxies_confiaveis: int) -> str:
    conexao = request.client.host if request.client else "?"
    cadeia = [p.strip() for p in request.headers.get("x-forwarded-for", "").split(",") if p.strip()]
    if proxies_confiaveis <= 0 or len(cadeia) < proxies_confiaveis:
        return conexao
    return cadeia[-proxies_confiaveis]


def _conferir_sempre(conferir: Callable[[], dict], parar: threading.Event) -> None:
    espera = PRIMEIRA_CONFERENCIA
    while not parar.wait(espera):
        conferir()
        espera = CONFERENCIA_A_CADA


def _cliente_local(request: Request) -> httpx.Client:
    porta = request.scope["server"][1]
    return httpx.Client(base_url=f"http://127.0.0.1:{porta}", timeout=30)


def _corte(a: acesso.Acesso) -> date:
    if a.plano.historico_dias is None:
        return INICIO_DA_BASE
    return acesso.hoje() - timedelta(days=a.plano.historico_dias)


def _janela(a: acesso.Acesso, de: date | None, ate: date | None) -> tuple[date, date]:
    return max(de or INICIO_DA_BASE, _corte(a)), ate or acesso.hoje()


def _resposta(dados, proximo: str | None = None, **extra) -> dict:
    corpo = {"dados": dados, **extra}
    if proximo is not None or isinstance(dados, list):
        corpo["proximo"] = proximo
    return corpo


def criar(
    config: Configuracao | None = None,
    bancos: banco.Bancos | None = None,
    asaas: cobranca.Asaas | None = None,
    cliente_da_fumaca: Callable[[Request], httpx.Client] | None = None,
) -> FastAPI:
    config = config or carregar()
    bancos = bancos or banco.criar(config.database_url)
    por_minuto = acesso.LimitePorMinuto()
    tentativas = acesso.Tentativas()
    cadastros = acesso.Tentativas(maximo=CADASTROS_POR_HORA, janela=3600.0)
    if asaas is None and config.cobranca_ativa:
        asaas = cobranca.Asaas.criar(
            config.asaas_url, config.asaas_chave, config.asaas_token_webhook
        )
    cliente_da_fumaca = cliente_da_fumaca or _cliente_local
    fumaca_rodando = threading.Lock()
    vitrine_guardada: dict = {"quando": 0.0, "dados": None}
    conferencia: dict = {"ultima": None}

    def conferir_cobranca() -> dict:
        try:
            relatorio = cobranca.conferir(bancos.acesso, asaas)
        except Exception as erro:
            relatorio = {"em": None, "aplicados": [], "falhas": [f"a conferência caiu: {erro}"]}
        conferencia["ultima"] = relatorio
        return relatorio

    @asynccontextmanager
    async def ciclo_de_vida(_app: FastAPI):
        parar = threading.Event()
        if asaas is not None:
            threading.Thread(
                target=_conferir_sempre, args=(conferir_cobranca, parar), daemon=True
            ).start()
        yield
        parar.set()

    app = FastAPI(
        title="fiance dados",
        version="1.0.0",
        description=DESCRICAO,
        lifespan=ciclo_de_vida,
        openapi_tags=[
            {"name": "ativos", "description": "Ações, FIIs, ETFs e BDRs negociados na B3"},
            {"name": "empresas", "description": "Companhias abertas e demonstrações"},
            {"name": "macro", "description": "Banco Central e Tesouro Direto"},
            {"name": "conta", "description": "A sua conta e as suas chaves"},
        ],
    )

    @app.exception_handler(acesso.SemAcesso)
    async def _sem_acesso(_request: Request, erro: acesso.SemAcesso) -> JSONResponse:
        cabecalhos = {"Retry-After": str(erro.tentar_em)} if erro.tentar_em else {}
        return JSONResponse({"erro": erro.mensagem}, status_code=erro.status, headers=cabecalhos)

    @app.exception_handler(HTTPException)
    async def _erro(_request: Request, erro: HTTPException) -> JSONResponse:
        return JSONResponse({"erro": erro.detail}, status_code=erro.status_code)

    @app.exception_handler(consultas.CursorInvalido)
    async def _cursor(_request: Request, _erro: consultas.CursorInvalido) -> JSONResponse:
        return JSONResponse(
            {"erro": "Cursor inválido: use o `proximo` da página anterior."}, status_code=422
        )

    @app.middleware("http")
    async def _cabecalhos(request: Request, seguir):
        resposta = await seguir(request)
        resposta.headers["X-Fontes"] = "B3; CVM (ODbL); BCB SGS; Tesouro Transparente"
        resposta.headers["X-Content-Type-Options"] = "nosniff"
        resposta.headers["Content-Security-Policy"] = "frame-ancestors 'none'"
        resposta.headers["Referrer-Policy"] = "no-referrer"
        resposta.headers["Strict-Transport-Security"] = "max-age=31536000"
        uso: acesso.Acesso | None = getattr(request.state, "acesso", None)
        if uso is not None:
            resposta.headers["X-Limite-Dia"] = str(uso.plano.limite_por_dia)
            resposta.headers["X-Restante-Dia"] = str(uso.restantes_hoje)
        return resposta

    def autenticado(request: Request, authorization: str | None = Header(default=None)):
        texto = (authorization or "").removeprefix("Bearer ").strip() or request.headers.get(
            "x-api-key"
        )
        uso = acesso.autenticar(bancos.acesso, texto, por_minuto)
        request.state.acesso = uso
        return uso

    def na_conta(request: Request, authorization: str | None = Header(default=None)) -> int:
        texto = (authorization or "").removeprefix("Bearer ").strip() or request.headers.get(
            "x-api-key"
        )
        return acesso.entrar(bancos.acesso, texto)

    def administrador(request: Request, x_admin_token: str | None = Header(default=None)) -> None:
        origem = _origem(request, config.proxies_confiaveis)
        if tentativas.bloqueado(origem):
            raise HTTPException(429, "Tentativas demais. Espere 15 minutos.")
        if not x_admin_token or not secrets.compare_digest(
            x_admin_token.encode(), config.admin_token.encode()
        ):
            tentativas.registrar(origem)
            raise HTTPException(401, "Rota de administração.")

    def _papel(conn, codigo: str) -> consultas.Papel:
        p = consultas.papel(conn, codigo)
        if p is None:
            raise HTTPException(404, f"Ativo {codigo.upper()} não encontrado na base.")
        return p

    @app.get("/", include_in_schema=False)
    def portal() -> HTMLResponse:
        return HTMLResponse(_pagina("portal.html"))

    @app.get("/console", include_in_schema=False)
    def console() -> HTMLResponse:
        return HTMLResponse(_pagina("console.html"))

    @app.get("/saude", include_in_schema=False)
    def saude() -> dict:
        return {"ok": True}

    @app.get("/v1/planos", tags=["conta"], summary="Os planos, o que cada um libera, e o preço")
    def ver_planos() -> dict:
        return {
            "dados": acesso.planos_publicos(bancos.acesso),
            "cobranca_aberta": config.cobranca_ativa,
            "contato": config.contato or None,
            "whatsapp": config.whatsapp or None,
        }

    @app.get("/v1/vitrine", include_in_schema=False)
    def ver_vitrine() -> dict:
        if (
            vitrine_guardada["dados"] is None
            or time.monotonic() - vitrine_guardada["quando"] > 6 * 3600
        ):
            with bancos.leitura.connect() as conn:
                vitrine_guardada["dados"] = consultas.vitrine(conn, EXEMPLO_DA_VITRINE)
            vitrine_guardada["quando"] = time.monotonic()
        return vitrine_guardada["dados"]

    @app.post(
        "/v1/conta/assinatura",
        tags=["conta"],
        status_code=201,
        summary="Assinar um plano: devolve o link de pagamento",
    )
    def assinar(corpo: NovaAssinatura, conta_id: int = Depends(na_conta)) -> dict:
        if asaas is None:
            raise HTTPException(503, "A cobrança ainda não abriu. Fale com o contato do portal.")
        return _resposta(
            cobranca.criar_assinatura(
                bancos.acesso, asaas, conta_id, corpo.plano, corpo.ciclo, corpo.pagador()
            )
        )

    @app.post(
        "/v1/assinatura",
        tags=["conta"],
        status_code=201,
        summary="Criar a conta e assinar: devolve a chave e o link de pagamento",
        description=(
            "Sem chave. A conta nasce com a chave, que aparece só nesta resposta e responde 402 "
            "até o Asaas confirmar o pagamento."
        ),
    )
    def assinar_sem_conta(corpo: NovoAssinante, request: Request) -> dict:
        if asaas is None:
            raise HTTPException(503, "A cobrança ainda não abriu. Fale com o contato do portal.")
        quem_paga = corpo.pagador()
        origem = _origem(request, config.proxies_confiaveis)
        if cadastros.bloqueado(origem):
            raise HTTPException(429, "Cadastros demais deste endereço. Tente de novo em uma hora.")
        cadastros.registrar(origem)
        conta_id = acesso.conta_do_cadastro(
            bancos.acesso, corpo.email.strip(), corpo.nome.strip(), corpo.plano
        )
        chave = acesso.emitir_chave(bancos.acesso, conta_id, "principal", CHAVES_NOVAS_POR_DIA)
        assinatura = cobranca.criar_assinatura(
            bancos.acesso, asaas, conta_id, corpo.plano, corpo.ciclo, quem_paga
        )
        return _resposta(
            {**assinatura, "chave": chave["chave"], "prefixo": chave["prefixo"]},
            aviso="A chave só aparece agora, e passa a valer quando o pagamento for confirmado.",
        )

    @app.post("/cobranca/asaas", include_in_schema=False)
    async def webhook_do_asaas(
        request: Request, asaas_access_token: str | None = Header(default=None)
    ) -> dict:
        if asaas is None:
            raise HTTPException(503, "Cobrança desligada.")
        if not asaas.webhook_autentico(asaas_access_token):
            raise HTTPException(401, "Webhook sem o token combinado.")
        return {"resultado": cobranca.processar_evento(bancos.acesso, asaas, await request.json())}

    @app.get("/v1", tags=["conta"], summary="O que a API oferece, e de onde vem o dado")
    def indice() -> dict:
        return {
            "versao": "1",
            "fontes": FONTES,
            "documentacao": "/docs",
            "indicadores": {k: d for k, (_, d) in consultas.INDICADORES.items()},
        }

    @app.get("/v1/atualidade", tags=["conta"], summary="Até quando vai cada dado")
    def atualidade(_: acesso.Acesso = Depends(autenticado)) -> dict:
        with bancos.leitura.connect() as conn:
            return _resposta(consultas.atualidade(conn))

    @app.get("/v1/ativos", tags=["ativos"], summary="Ativos negociados nos últimos 30 dias")
    def listar_ativos(
        tipo: Literal["stock", "fii", "etf", "bdr"] | None = None,
        busca: str | None = Query(default=None, min_length=2),
        cursor: str | None = None,
        limite: int = Query(default=LIMITE_PADRAO, ge=1, le=LIMITE_MAXIMO),
        _: acesso.Acesso = Depends(autenticado),
    ) -> dict:
        with bancos.leitura.connect() as conn:
            dados, proximo = consultas.ativos(conn, tipo, busca, cursor, limite)
        return _resposta(dados, proximo)

    @app.get(
        "/v1/retratos",
        tags=["ativos"],
        summary="O retrato completo de vários ativos numa chamada",
        description=(
            "Até 50 tickers separados por vírgula. Para cada um: o retrato do último pregão, os "
            "outros papéis da mesma companhia (para o valor de mercado) e todas as versões das "
            "demonstrações, com a data de entrega. Ticker que a base não tem fica de fora."
        ),
    )
    def ver_retratos(
        codigos: str = Query(min_length=1, max_length=600),
        a: acesso.Acesso = Depends(autenticado),
    ) -> dict:
        lista = list(dict.fromkeys(c.strip().upper() for c in codigos.split(",") if c.strip()))
        if len(lista) > MAXIMO_DE_RETRATOS:
            raise HTTPException(422, f"No máximo {MAXIMO_DE_RETRATOS} tickers por chamada.")
        with bancos.leitura.connect() as conn:
            return _resposta(
                consultas.retratos(conn, lista, _corte(a), "ponto_no_tempo" in a.plano.recursos)
            )

    @app.get("/v1/ativos/{codigo}", tags=["ativos"], summary="O retrato do ativo no último pregão")
    def ver_ativo(codigo: str, _: acesso.Acesso = Depends(autenticado)) -> dict:
        with bancos.leitura.connect() as conn:
            dados = consultas.ativo(conn, codigo)
        if dados is None:
            raise HTTPException(404, f"Ativo {codigo.upper()} não encontrado na base.")
        return _resposta(dados)

    @app.get(
        "/v1/ativos/{codigo}/cotacoes",
        tags=["ativos"],
        summary="Cotação diária do ticker, como negociada (sem ajuste)",
    )
    def ver_cotacoes(
        codigo: str,
        de: date | None = None,
        ate: date | None = None,
        cursor: str | None = None,
        limite: int = Query(default=LIMITE_PADRAO, ge=1, le=LIMITE_MAXIMO),
        a: acesso.Acesso = Depends(autenticado),
    ) -> dict:
        inicio, fim = _janela(a, de, ate)
        with bancos.leitura.connect() as conn:
            dados, proximo = consultas.cotacoes(conn, codigo, inicio, fim, cursor, limite)
        return _resposta(dados, proximo)

    @app.get(
        "/v1/ativos/{codigo}/serie",
        tags=["ativos"],
        summary="Série ajustada do papel, atravessando trocas de ticker, com retorno total",
    )
    def ver_serie(
        codigo: str,
        de: date | None = None,
        ate: date | None = None,
        cursor: str | None = None,
        limite: int = Query(default=LIMITE_PADRAO, ge=1, le=LIMITE_MAXIMO),
        a: acesso.Acesso = Depends(autenticado),
    ) -> dict:
        acesso.exigir(a, "serie")
        inicio, fim = _janela(a, de, ate)
        with bancos.leitura.connect() as conn:
            dados, proximo = consultas.serie(
                conn, _papel(conn, codigo), inicio, fim, cursor, limite
            )
        return _resposta(dados, proximo)

    @app.get("/v1/ativos/{codigo}/proventos", tags=["ativos"], summary="Proventos por data-com")
    def ver_proventos(
        codigo: str,
        incluir_estimados: bool = False,
        a: acesso.Acesso = Depends(autenticado),
    ) -> dict:
        with bancos.leitura.connect() as conn:
            dados = consultas.proventos(conn, _papel(conn, codigo), _corte(a), incluir_estimados)
        return _resposta(dados)

    @app.get(
        "/v1/ativos/{codigo}/eventos",
        tags=["ativos"],
        summary="Desdobramentos, grupamentos e bonificações, com o status da conferência",
    )
    def ver_eventos(codigo: str, a: acesso.Acesso = Depends(autenticado)) -> dict:
        with bancos.leitura.connect() as conn:
            dados = consultas.eventos(conn, _papel(conn, codigo), _corte(a))
        return _resposta(dados)

    @app.get(
        "/v1/ativos/{codigo}/informes",
        tags=["ativos"],
        summary="Informe mensal do FII na CVM: patrimônio, cota, segmento",
    )
    def ver_informes(codigo: str, a: acesso.Acesso = Depends(autenticado)) -> dict:
        acesso.exigir(a, "informes")
        with bancos.leitura.connect() as conn:
            p = _papel(conn, codigo)
            if p.classe != "CI":
                raise HTTPException(422, f"{codigo.upper()} não é cota de fundo.")
            dados = consultas.informes_de_fii(conn, p, _corte(a))
        return _resposta(dados)

    @app.get("/v1/empresas/{cnpj}", tags=["empresas"], summary="Cadastro da companhia na CVM")
    def ver_empresa(cnpj: str, _: acesso.Acesso = Depends(autenticado)) -> dict:
        with bancos.leitura.connect() as conn:
            dados = consultas.empresa(conn, cnpj)
        if dados is None:
            raise HTTPException(404, "Companhia não encontrada.")
        return _resposta(dados)

    @app.get(
        "/v1/empresas/{cnpj}/demonstracoes",
        tags=["empresas"],
        summary="DFP e ITR: acumulado do ano, com a data de entrega à CVM",
        description=(
            "Receita e lucro são o **acumulado do exercício** até a data de referência. Com "
            "`sabido_em`, só entram as versões entregues até aquela data — o balanço como se "
            "sabia no dia."
        ),
    )
    def ver_demonstracoes(
        cnpj: str,
        tipo: Literal["DFP", "ITR"] | None = None,
        sabido_em: date | None = None,
        a: acesso.Acesso = Depends(autenticado),
    ) -> dict:
        if sabido_em is not None:
            acesso.exigir(a, "ponto_no_tempo")
        with bancos.leitura.connect() as conn:
            dados = consultas.demonstracoes(conn, cnpj, tipo, _corte(a), sabido_em)
        return _resposta(dados)

    @app.get("/v1/indicadores/{nome}", tags=["macro"], summary="Série do Banco Central")
    def ver_indicador(
        nome: str,
        de: date | None = None,
        ate: date | None = None,
        cursor: str | None = None,
        limite: int = Query(default=LIMITE_PADRAO, ge=1, le=LIMITE_MAXIMO),
        a: acesso.Acesso = Depends(autenticado),
    ) -> dict:
        if nome not in consultas.INDICADORES:
            raise HTTPException(404, f"Indicadores: {', '.join(consultas.INDICADORES)}.")
        inicio, fim = _janela(a, de, ate)
        with bancos.leitura.connect() as conn:
            dados, proximo = consultas.indicador(
                conn, consultas.INDICADORES[nome][0], inicio, fim, cursor, limite
            )
        return _resposta(dados, proximo)

    @app.get("/v1/tesouro", tags=["macro"], summary="Títulos do Tesouro Direto no último dia")
    def ver_tesouro(_: acesso.Acesso = Depends(autenticado)) -> dict:
        with bancos.leitura.connect() as conn:
            return _resposta(consultas.tesouro_hoje(conn))

    @app.get("/v1/tesouro/historico", tags=["macro"], summary="Taxa e preço de um título")
    def ver_tesouro_historico(
        titulo: str,
        vencimento: date,
        de: date | None = None,
        ate: date | None = None,
        cursor: str | None = None,
        limite: int = Query(default=LIMITE_PADRAO, ge=1, le=LIMITE_MAXIMO),
        a: acesso.Acesso = Depends(autenticado),
    ) -> dict:
        inicio, fim = _janela(a, de, ate)
        with bancos.leitura.connect() as conn:
            dados, proximo = consultas.tesouro_historico(
                conn, titulo, vencimento, inicio, fim, cursor, limite
            )
        return _resposta(dados, proximo)

    @app.get("/v1/conta", tags=["conta"], summary="A sua conta, plano, chaves e uso de hoje")
    def ver_conta(response: Response, conta_id: int = Depends(na_conta)) -> dict:
        conta = acesso.resumo_da_conta(bancos.acesso, conta_id)
        conta.pop("observacao")
        response.headers["X-Limite-Dia"] = str(conta["limite_por_dia"])
        response.headers["X-Restante-Dia"] = str(
            max(0, conta["limite_por_dia"] - conta["requisicoes_hoje"])
        )
        assinatura = conta["assinatura"]
        if assinatura is not None:
            assinatura_id = assinatura.pop("asaas_assinatura")
            assinatura["pagar_em"], assinatura["pagar_em_indisponivel"] = None, False
            if (
                asaas is not None
                and assinatura["situacao"] in ("aguardando", "ativa")
                and (assinatura["situacao"] == "aguardando" or conta["situacao"] != "ativa")
            ):
                try:
                    assinatura["pagar_em"] = cobranca.link_em_aberto(asaas, assinatura_id)
                except (httpx.HTTPError, acesso.SemAcesso):
                    assinatura["pagar_em_indisponivel"] = True
        return _resposta(conta)

    @app.post("/v1/conta/chaves", tags=["conta"], status_code=201, summary="Emitir outra chave")
    def nova_chave(corpo: NovaChave, conta_id: int = Depends(na_conta)) -> dict:
        return _resposta(
            acesso.emitir_chave(bancos.acesso, conta_id, corpo.nome, CHAVES_NOVAS_POR_DIA),
            aviso="A chave só aparece agora. Guarde-a: depois, só o prefixo.",
        )

    @app.delete("/v1/conta/chaves/{prefixo}", tags=["conta"], status_code=204)
    def revogar(prefixo: str, conta_id: int = Depends(na_conta)) -> None:
        acesso.revogar_chave(bancos.acesso, conta_id, prefixo)

    @app.get("/admin/planos", include_in_schema=False, dependencies=[Depends(administrador)])
    def admin_planos() -> list[dict]:
        return acesso.planos(bancos.acesso)

    @app.post("/admin/fumaca", include_in_schema=False, dependencies=[Depends(administrador)])
    def admin_fumaca(request: Request) -> dict:
        if not fumaca_rodando.acquire(blocking=False):
            raise HTTPException(409, "Já há uma fumaça rodando.")
        try:
            chaves: list[tuple[int, dict]] = []
            try:
                for plano in acesso.planos(bancos.acesso):
                    conta_id = acesso.preparar_conta_de_fumaca(bancos.acesso, plano["codigo"])
                    chaves.append(
                        (conta_id, acesso.emitir_chave(bancos.acesso, conta_id, "fumaça"))
                    )
                with cliente_da_fumaca(request) as cliente:
                    resultados = fumaca.rodar(cliente, [c["chave"] for _, c in chaves])
            finally:
                for conta_id, c in chaves:
                    acesso.revogar_chave(bancos.acesso, conta_id, c["prefixo"])
        finally:
            fumaca_rodando.release()
        return {"resultados": resultados, "falhas": sum(not r["ok"] for r in resultados)}

    @app.get("/admin/cobranca", include_in_schema=False, dependencies=[Depends(administrador)])
    def admin_cobranca() -> dict:
        return {
            "ligada": asaas is not None,
            "ultima_conferencia": conferencia["ultima"],
            "pendencias": cobranca.pendencias(bancos.acesso),
        }

    @app.post(
        "/admin/cobranca/conferir", include_in_schema=False, dependencies=[Depends(administrador)]
    )
    def admin_conferir_cobranca() -> dict:
        if asaas is None:
            raise HTTPException(503, "Cobrança desligada.")
        return conferir_cobranca()

    @app.get("/admin/uso", include_in_schema=False, dependencies=[Depends(administrador)])
    def admin_uso(
        dias: int = Query(default=30, ge=1, le=365), conta_id: int | None = None
    ) -> list[dict]:
        return acesso.uso_por_dia(bancos.acesso, dias, conta_id)

    @app.get("/admin/contas", include_in_schema=False, dependencies=[Depends(administrador)])
    def admin_contas() -> list[dict]:
        return acesso.listar_contas(bancos.acesso)

    @app.post(
        "/admin/contas",
        include_in_schema=False,
        status_code=201,
        dependencies=[Depends(administrador)],
    )
    def admin_criar_conta(corpo: NovaConta) -> dict:
        conta = acesso.criar_conta(
            bancos.acesso, corpo.email, corpo.nome, corpo.plano, corpo.observacao, corpo.pago_ate
        )
        chave = acesso.emitir_chave(bancos.acesso, conta["id"], "principal")
        return {"conta": conta, "chave": chave}

    @app.patch(
        "/admin/contas/{conta_id}", include_in_schema=False, dependencies=[Depends(administrador)]
    )
    def admin_alterar_conta(conta_id: int, corpo: AlteracaoDeConta) -> dict:
        enviados = corpo.model_fields_set
        return acesso.alterar_conta(
            bancos.acesso,
            conta_id,
            corpo.plano,
            corpo.ativa,
            corpo.pago_ate,
            mudar_pago_ate="pago_ate" in enviados,
            nome=corpo.nome,
            observacao=corpo.observacao,
            mudar_observacao="observacao" in enviados,
        )

    @app.post(
        "/admin/contas/{conta_id}/chaves",
        include_in_schema=False,
        status_code=201,
        dependencies=[Depends(administrador)],
    )
    def admin_nova_chave(conta_id: int, corpo: NovaChave) -> dict:
        return acesso.emitir_chave(bancos.acesso, conta_id, corpo.nome)

    @app.delete(
        "/admin/contas/{conta_id}/chaves/{prefixo}",
        include_in_schema=False,
        status_code=204,
        dependencies=[Depends(administrador)],
    )
    def admin_revogar_chave(conta_id: int, prefixo: str) -> None:
        acesso.revogar_chave(bancos.acesso, conta_id, prefixo)

    @app.get(
        "/admin/contas/{conta_id}", include_in_schema=False, dependencies=[Depends(administrador)]
    )
    def admin_ver_conta(conta_id: int) -> dict:
        return acesso.resumo_da_conta(bancos.acesso, conta_id)

    return app
