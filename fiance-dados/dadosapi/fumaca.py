"""Fumaça da API de dados: só GET, e o que cada rota devolve conforme o plano da chave.

    FIANCE_DADOS_CHAVE=fd_...,fd_... python -m dadosapi.fumaca [url]

O console roda a mesma conferência por POST /admin/fumaca, com uma chave temporária por plano.
"""

from __future__ import annotations

import os
import sys
import time
from datetime import date, timedelta

import httpx

from dadosapi.acesso import NOME_DO_RECURSO

URL_DE_PRODUCAO = "https://fiance-dados.up.railway.app"
ACAO = "PETR4"
FII = "HGLG11"
DIAS_SEM_PREGAO_TOLERADOS = 5


class Fumaca:
    def __init__(self, cliente: httpx.Client):
        self.cliente = cliente
        self.grupo = ""
        self.resultados: list[dict] = []

    @property
    def falhas(self) -> int:
        return sum(not r["ok"] for r in self.resultados)

    def conferir(self, nome: str, ok: bool, detalhe: str = "") -> bool:
        self.resultados.append(
            {"grupo": self.grupo, "nome": nome, "ok": ok, "detalhe": "" if ok else detalhe}
        )
        return ok

    def get(self, caminho: str, chave: str | None = None, **params) -> httpx.Response:
        cabecalhos = {"Authorization": f"Bearer {chave}"} if chave else {}
        for _ in range(3):
            r = self.cliente.get(caminho, params=params, headers=cabecalhos)
            if r.status_code != 429 or "retry-after" not in r.headers:
                return r
            time.sleep(int(r.headers["retry-after"]))
        return r

    def status(self, caminho: str, esperado: int, chave: str | None = None, **params) -> dict:
        try:
            r = self.get(caminho, chave, **params)
        except httpx.HTTPError as erro:
            self.conferir(f"GET {caminho} → {esperado}", False, f"sem resposta: {erro}")
            return {}
        rotulo = f"GET {caminho}{'?' + str(httpx.QueryParams(params)) if params else ''}"
        detalhe = f"{r.status_code}: {r.text[:200]}"
        self.conferir(f"{rotulo} → {esperado}", r.status_code == esperado, detalhe)
        if r.status_code == 200 and r.headers.get("content-type", "").startswith(
            "application/json"
        ):
            return r.json()
        return {}


def publicas(f: Fumaca) -> None:
    f.grupo = "sem chave"
    f.status("/saude", 200)
    for caminho in ("/", "/console"):
        f.status(caminho, 200)
    indice = f.status("/v1", 200)
    f.conferir("o índice lista os indicadores", bool(indice.get("indicadores")))
    planos = f.status("/v1/planos", 200).get("dados", [])
    codigos = {p["codigo"] for p in planos}
    f.conferir("planos públicos são essencial e pro", codigos == {"essencial", "pro"}, str(codigos))
    f.status("/v1/vitrine", 200)
    f.status("/v1/ativos", 401)
    f.status("/v1/ativos", 401, "fd_chave_que_nao_existe")


def com_chave(f: Fumaca, chave: str) -> None:
    f.grupo = f"chave {chave[:11]}…"
    r = f.get("/v1/conta", chave)
    if r.status_code != 200:
        f.conferir("a chave autentica", False, f"{r.status_code}: {r.text[:200]}")
        return
    conta = r.json()["dados"]
    plano, recursos, dias = conta["plano"], set(conta["recursos"]), conta["historico_dias"]
    f.grupo = f"plano {plano}"
    f.conferir(
        "X-Limite-Dia é o limite do plano",
        r.headers.get("x-limite-dia") == str(conta["limite_por_dia"]),
        f"{r.headers.get('x-limite-dia')} ≠ {conta['limite_por_dia']}",
    )
    corte = date.today() - timedelta(days=dias + 1) if dias is not None else None

    ate = f.status("/v1/atualidade", 200, chave).get("dados", {}).get("ate", {})
    if ate.get("cotacao"):
        atraso = (date.today() - date.fromisoformat(ate["cotacao"])).days
        f.conferir(
            "a última cotação é recente",
            atraso <= DIAS_SEM_PREGAO_TOLERADOS,
            f"{ate['cotacao']}, {atraso} dias atrás",
        )

    lista = f.status("/v1/ativos", 200, chave, limite=5).get("dados", [])
    f.conferir("a lista de ativos não vem vazia", bool(lista))
    retrato = f.status(f"/v1/ativos/{ACAO}", 200, chave).get("dados", {})
    retratos = f.status("/v1/retratos", 200, chave, codigos=f"{ACAO},{FII}").get("dados", [])
    f.conferir("retratos traz os dois tickers", len(retratos) == 2, f"vieram {len(retratos)}")

    cotacoes = f.status(f"/v1/ativos/{ACAO}/cotacoes", 200, chave, de="2000-01-01", limite=1)
    primeira = (cotacoes.get("dados") or [{}])[0].get("data")
    if primeira:
        if corte is None:
            f.conferir(
                "histórico inteiro: cotação de antes de 2010",
                primeira < "2010-01-01",
                f"a primeira é {primeira}",
            )
        else:
            f.conferir(
                f"histórico cortado em {dias} dias",
                date.fromisoformat(primeira) >= corte,
                f"a primeira é {primeira}, o corte é {corte}",
            )

    for recurso, caminho, params in (
        ("serie", f"/v1/ativos/{ACAO}/serie", {"limite": 5}),
        ("informes", f"/v1/ativos/{FII}/informes", {}),
    ):
        f.status(caminho, 200 if recurso in recursos else 403, chave, **params)
    f.status(f"/v1/ativos/{ACAO}/proventos", 200, chave)
    f.status(f"/v1/ativos/{ACAO}/eventos", 200, chave)

    cnpj = retrato.get("cnpj")
    if f.conferir(f"{ACAO} tem CNPJ", bool(cnpj)):
        f.status(f"/v1/empresas/{cnpj}", 200, chave)
        demonstracoes = f.status(f"/v1/empresas/{cnpj}/demonstracoes", 200, chave, tipo="DFP")
        if corte is not None:
            antigas = [
                d
                for d in demonstracoes.get("dados", [])
                if d["data_referencia"] < corte.isoformat()
            ]
            f.conferir(
                "demonstração respeita o corte", not antigas, f"{len(antigas)} antes do corte"
            )
        f.status(
            f"/v1/empresas/{cnpj}/demonstracoes",
            200 if "ponto_no_tempo" in recursos else 403,
            chave,
            sabido_em=date.today().isoformat(),
        )

    for nome in f.status("/v1", 200).get("indicadores", {}):
        f.status(f"/v1/indicadores/{nome}", 200, chave, limite=5)
    titulos = f.status("/v1/tesouro", 200, chave).get("dados", [])
    if f.conferir("o Tesouro tem títulos no último dia", bool(titulos)):
        t = titulos[0]
        f.status(
            "/v1/tesouro/historico", 200, chave, titulo=t["titulo"], vencimento=t["vencimento"]
        )
    desconhecidos = recursos - set(NOME_DO_RECURSO)
    f.conferir("recursos do plano são conhecidos", not desconhecidos, str(desconhecidos))


def rodar(cliente: httpx.Client, chaves: list[str]) -> list[dict]:
    f = Fumaca(cliente)
    publicas(f)
    for chave in chaves:
        com_chave(f, chave)
    return f.resultados


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    url = (sys.argv[1] if len(sys.argv) > 1 else URL_DE_PRODUCAO).rstrip("/")
    chaves = [c.strip() for c in os.environ.get("FIANCE_DADOS_CHAVE", "").split(",") if c.strip()]
    with httpx.Client(base_url=url, timeout=30) as cliente:
        resultados = rodar(cliente, chaves)
    print(url)
    grupo = None
    for r in resultados:
        if r["grupo"] != grupo:
            grupo = r["grupo"]
            print(grupo)
        detalhe = f" — {r['detalhe']}" if r["detalhe"] else ""
        print(f"  {'ok   ' if r['ok'] else 'FALHA'} {r['nome']}{detalhe}")
    if not chaves:
        print("sem FIANCE_DADOS_CHAVE: só as rotas públicas foram conferidas")
    falhas = sum(not r["ok"] for r in resultados)
    print(f"\n{falhas} falha(s)" if falhas else "\ntudo certo")
    return 1 if falhas else 0


if __name__ == "__main__":
    sys.exit(main())
