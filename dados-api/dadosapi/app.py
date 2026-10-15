from __future__ import annotations

import secrets
from datetime import date, timedelta
from typing import Literal

from fastapi import Depends, FastAPI, Header, HTTPException, Query, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from dadosapi import acesso, banco, consultas
from dadosapi.config import Configuracao, carregar

FONTES = (
    "B3 (COTAHIST, proventos e eventos); CVM, dados abertos sob ODbL (demonstrações, cadastro, "
    "informe de FII); BCB SGS; Tesouro Transparente. Organizado por fiance."
)
LIMITE_PADRAO = 500
LIMITE_MAXIMO = 5000
INICIO_DA_BASE = date(2000, 1, 1)

DESCRICAO = """
Dados de mercado da B3 organizados: cotação diária desde 2005 (com quem saiu da bolsa), série
ajustada por evento conferido pelo preço, proventos com data de pagamento, demonstrações com a data
em que foram entregues à CVM, informe mensal de FII, Tesouro Direto e séries do Banco Central.

**Autenticação:** `Authorization: Bearer <chave>`. Toda resposta traz `X-Limite-Dia` e
`X-Restante-Dia`.

**O dado é do fechamento**: a base é atualizada uma vez por dia útil, à noite. Não há cotação ao
longo do pregão.

**Lacunas conhecidas:** proventos de ETF e BDR só a partir de out/2025; data de pagamento só nos
proventos a partir de out/2025; rendimento de FII anterior a isso é estimado pelo informe da CVM e
só vem com `incluir_estimados=true`; cisão e redução de capital não ajustam a série.
"""


class NovaConta(BaseModel):
    email: str = Field(min_length=3, max_length=200)
    nome: str = Field(min_length=1, max_length=200)
    plano: str = "convidado"
    observacao: str | None = None


class AlteracaoDeConta(BaseModel):
    plano: str | None = None
    ativa: bool | None = None


class NovaChave(BaseModel):
    nome: str = Field(default="principal", min_length=1, max_length=60)


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


def criar(config: Configuracao | None = None, bancos: banco.Bancos | None = None) -> FastAPI:
    config = config or carregar()
    bancos = bancos or banco.criar(config.database_url)
    por_minuto = acesso.LimitePorMinuto()
    app = FastAPI(
        title="fiance dados",
        version="1.0.0",
        description=DESCRICAO,
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

    @app.middleware("http")
    async def _cabecalhos(request: Request, seguir):
        resposta = await seguir(request)
        resposta.headers["X-Fontes"] = "B3; CVM (ODbL); BCB SGS; Tesouro Transparente"
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

    def administrador(x_admin_token: str | None = Header(default=None)) -> None:
        if not x_admin_token or not secrets.compare_digest(x_admin_token, config.admin_token):
            raise HTTPException(401, "Rota de administração.")

    def _papel(conn, codigo: str) -> consultas.Papel:
        p = consultas.papel(conn, codigo)
        if p is None:
            raise HTTPException(404, f"Ativo {codigo.upper()} não encontrado na base.")
        return p

    @app.get("/saude", include_in_schema=False)
    def saude() -> dict:
        return {"ok": True}

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
    def ver_conta(a: acesso.Acesso = Depends(autenticado)) -> dict:
        return _resposta(acesso.resumo_da_conta(bancos.acesso, a.conta_id))

    @app.post("/v1/conta/chaves", tags=["conta"], status_code=201, summary="Emitir outra chave")
    def nova_chave(corpo: NovaChave, a: acesso.Acesso = Depends(autenticado)) -> dict:
        return _resposta(
            acesso.emitir_chave(bancos.acesso, a.conta_id, corpo.nome),
            aviso="A chave só aparece agora. Guarde-a: depois, só o prefixo.",
        )

    @app.delete("/v1/conta/chaves/{prefixo}", tags=["conta"], status_code=204)
    def revogar(prefixo: str, a: acesso.Acesso = Depends(autenticado)) -> None:
        acesso.revogar_chave(bancos.acesso, a.conta_id, prefixo)

    @app.get("/admin/planos", include_in_schema=False, dependencies=[Depends(administrador)])
    def admin_planos() -> list[dict]:
        return acesso.planos(bancos.acesso)

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
            bancos.acesso, corpo.email, corpo.nome, corpo.plano, corpo.observacao
        )
        chave = acesso.emitir_chave(bancos.acesso, conta["id"], "principal")
        return {"conta": conta, "chave": chave}

    @app.patch(
        "/admin/contas/{conta_id}", include_in_schema=False, dependencies=[Depends(administrador)]
    )
    def admin_alterar_conta(conta_id: int, corpo: AlteracaoDeConta) -> dict:
        return acesso.alterar_conta(bancos.acesso, conta_id, corpo.plano, corpo.ativa)

    @app.post(
        "/admin/contas/{conta_id}/chaves",
        include_in_schema=False,
        status_code=201,
        dependencies=[Depends(administrador)],
    )
    def admin_nova_chave(conta_id: int, corpo: NovaChave) -> dict:
        return acesso.emitir_chave(bancos.acesso, conta_id, corpo.nome)

    @app.get(
        "/admin/contas/{conta_id}", include_in_schema=False, dependencies=[Depends(administrador)]
    )
    def admin_ver_conta(conta_id: int) -> dict:
        return acesso.resumo_da_conta(bancos.acesso, conta_id)

    return app
