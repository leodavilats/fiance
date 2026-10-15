from __future__ import annotations

import json
from contextlib import contextmanager
from datetime import UTC, date, datetime
from pathlib import Path

from pesquisa import preco_justo
from pesquisa.dados import Base
from pesquisa.periodos import Periodo

ARQUIVO = Path(__file__).resolve().parents[1] / "registro_calibracao.jsonl"

VARIACOES: dict[int, dict[str, float]] = {
    0: {},
    1: {"EQUITY_RISK_PREMIUM": 0.04},
    2: {"EQUITY_RISK_PREMIUM": 0.06},
    3: {"LONG_RUN_REAL_GROWTH": 0.01},
    4: {"LONG_RUN_REAL_GROWTH": 0.02},
}
_ANTERIOR = {"validacao": "estudo", "prova": "validacao"}

# Os da calibração, não os da primeira pesquisa: o balanço com data de entrega começa em 2010.
PERIODOS = {
    p.nome: p
    for p in (
        Periodo("estudo", date(2011, 1, 1), date(2018, 12, 31)),
        Periodo("validacao", date(2019, 1, 1), date(2022, 12, 31)),
        Periodo("prova", date(2023, 1, 1), None),
    )
}


class Recusado(RuntimeError):
    pass


def ler(arquivo: Path = ARQUIVO) -> list[dict]:
    if not arquivo.exists():
        return []
    return [json.loads(x) for x in arquivo.read_text(encoding="utf-8").splitlines() if x]


def _passou(registros: list[dict], variacao: int, periodo: str) -> bool:
    return any(
        r["variacao"] == variacao and r["periodo"] == periodo and r["resumo"].get("passou")
        for r in registros
    )


def conferir(variacao: int, periodo: str, forcar: bool, arquivo: Path = ARQUIVO) -> None:
    if variacao not in VARIACOES:
        raise Recusado(f"A variação {variacao} não está no protocolo.")
    if forcar:
        return
    registros = ler(arquivo)
    if any(r["variacao"] == variacao and r["periodo"] == periodo for r in registros):
        raise Recusado(f"A variação {variacao} já rodou em {periodo}: o protocolo não repete.")
    if periodo == "estudo":
        if variacao > 0 and not _passou(registros, 0, "estudo"):
            raise Recusado(
                "A calibração só existe se o modelo como está (variação 0) passar no estudo."
            )
        return
    if not _passou(registros, variacao, _ANTERIOR[periodo]):
        raise Recusado(
            f"A variação {variacao} não passou em {_ANTERIOR[periodo]}: {periodo} segue lacrada."
        )


@contextmanager
def parametros(valores: dict[str, float]):
    modelo = preco_justo.modelo
    originais = {nome: getattr(modelo, nome) for nome in (*valores, "LONG_RUN_GROWTH")}
    padroes = modelo.earnings_value.__defaults__
    try:
        for nome, valor in valores.items():
            setattr(modelo, nome, valor)
        modelo.LONG_RUN_GROWTH = modelo.INFLATION_TARGET + modelo.LONG_RUN_REAL_GROWTH
        # O crescimento de longo prazo entra como padrão de argumento, fixado na definição.
        modelo.earnings_value.__defaults__ = tuple(
            modelo.LONG_RUN_GROWTH if p == originais["LONG_RUN_GROWTH"] else p for p in padroes
        )
        yield
    finally:
        for nome, valor in originais.items():
            setattr(modelo, nome, valor)
        modelo.earnings_value.__defaults__ = padroes


def rodar(base: Base, variacao: int, periodo: str) -> tuple[dict, list[dict]]:
    with parametros(VARIACOES[variacao]):
        return preco_justo.avaliar(base, PERIODOS[periodo])


def anotar(
    variacao: int, periodo: str, retrato: str, resumo: dict, forcado: bool, arquivo: Path = ARQUIVO
) -> dict:
    registro = {
        "quando": datetime.now(UTC).isoformat(timespec="seconds"),
        "variacao": variacao,
        "parametros": VARIACOES[variacao],
        "periodo": periodo,
        "retrato": retrato,
        "forcado": forcado,
        "resumo": resumo,
    }
    with arquivo.open("a", encoding="utf-8") as saida:
        saida.write(json.dumps(registro, ensure_ascii=False) + "\n")
    return registro
