from __future__ import annotations

import threading
from datetime import date, timedelta

import httpx

from app.core.config import get_settings

TIMEOUT = 20.0
LOTE_DE_RETRATOS = 50
LIMITE_DE_PAGINA = 5000


class SemBaseDeMercado(RuntimeError):
    pass


_cliente: httpx.Client | None = None
_cliente_lock = threading.Lock()


def cliente() -> httpx.Client:
    global _cliente
    if _cliente is not None:
        return _cliente
    with _cliente_lock:
        if _cliente is None:
            settings = get_settings()
            url, chave = settings.dados_api_url.strip(), settings.dados_api_chave.strip()
            if not url or not chave:
                raise SemBaseDeMercado("DADOS_API_URL e DADOS_API_CHAVE precisam estar definidas.")
            _cliente = httpx.Client(
                base_url=url.rstrip("/"),
                headers={"Authorization": f"Bearer {chave}"},
                timeout=TIMEOUT,
            )
    return _cliente


def _get(rota: str, **parametros) -> dict:
    resposta = cliente().get(rota, params={k: v for k, v in parametros.items() if v is not None})
    resposta.raise_for_status()
    return resposta.json()


def _todas_as_paginas(rota: str, **parametros) -> list[dict]:
    linhas, cursor = [], None
    while True:
        pagina = _get(rota, limite=LIMITE_DE_PAGINA, cursor=cursor, **parametros)
        linhas += pagina["dados"]
        cursor = pagina.get("proximo")
        if not cursor:
            return linhas


_DO_RESULTADO = ("tipo", "data_referencia", "versao", "fim_exercicio", "receita",
                 "lucro_controladores")  # fmt: skip
_DO_BALANCO = ("tipo", "data_referencia", "versao", "patrimonio_controladores", "divida_bruta")


def pacote_do_retrato(retrato: dict) -> dict:
    demonstracoes = retrato["demonstracoes"]
    return {
        "ativo": retrato["ativo"],
        "irmaos": retrato["irmaos"],
        "resultados": [{k: d[k] for k in _DO_RESULTADO} for d in demonstracoes],
        "balancos": [
            {k: d[k] for k in _DO_BALANCO}
            for d in demonstracoes
            if d["patrimonio_controladores"] is not None
        ],
    }


def ler_pacotes(codigos: list[str]) -> dict[str, dict]:
    pacotes = {}
    for inicio in range(0, len(codigos), LOTE_DE_RETRATOS):
        lote = codigos[inicio : inicio + LOTE_DE_RETRATOS]
        retratos = _get("/v1/retratos", codigos=",".join(lote))["dados"]
        pacotes.update({codigo: pacote_do_retrato(r) for codigo, r in retratos.items()})
    return pacotes


def ler_lista() -> list[dict]:
    return [
        {k: a.get(k) for k in ("codigo", "tipo", "nome", "setor", "volume_medio")}
        for a in _todas_as_paginas("/v1/ativos")
    ]


def ler_historico(codigo: str, dias: int) -> dict[str, float]:
    desde = (date.today() - timedelta(days=dias)).isoformat()
    try:
        cotacoes = _todas_as_paginas(f"/v1/ativos/{codigo}/cotacoes", de=desde)
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            return {}
        raise
    return {c["data"]: c["fechamento"] for c in cotacoes}


def ler_proventos(codigo: str) -> list[dict]:
    try:
        proventos = _get(f"/v1/ativos/{codigo}/proventos")["dados"]
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            return []
        raise
    return [{k: p[k] for k in ("data_com", "data_pagamento", "valor")} for p in proventos]
