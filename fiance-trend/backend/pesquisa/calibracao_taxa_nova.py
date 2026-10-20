from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

from pesquisa import preco_justo, taxa_de_desconto
from pesquisa.calibracao import PERIODOS
from pesquisa.dados import Base

ARQUIVO = Path(__file__).resolve().parents[1] / "registro_calibracao_taxa_nova.jsonl"
CANDIDATA_DA_ADR = 3
_ANTERIOR = {"validacao": "estudo", "prova": "validacao"}


class Recusado(RuntimeError):
    pass


def ler(arquivo: Path = ARQUIVO) -> list[dict]:
    if not arquivo.exists():
        return []
    return [json.loads(x) for x in arquivo.read_text(encoding="utf-8").splitlines() if x]


def conferir(periodo: str, forcar: bool, arquivo: Path = ARQUIVO) -> None:
    if periodo not in PERIODOS:
        raise Recusado(f"O período {periodo} não está no protocolo.")
    if forcar:
        return
    registros = ler(arquivo)
    if any(r["periodo"] == periodo for r in registros):
        raise Recusado(f"A taxa da ADR já rodou em {periodo}: o protocolo não repete.")
    anterior = _ANTERIOR.get(periodo)
    if anterior and not any(
        r["periodo"] == anterior and r["resumo"].get("passou") for r in registros
    ):
        raise Recusado(f"A taxa da ADR não passou em {anterior}: {periodo} segue lacrada.")


def rodar(base: Base, periodo: str) -> tuple[dict, list[dict]]:
    tesouro = taxa_de_desconto._tesouro(base)
    selic = preco_justo.Dados(base).selic

    def juro_do_mes(dia):
        juros, _ = taxa_de_desconto.juros_do_mes(selic, tesouro, dia)
        return juros[CANDIDATA_DA_ADR]

    return preco_justo.avaliar(base, PERIODOS[periodo], juro_do_mes)


def anotar(
    periodo: str, retrato: str, resumo: dict, forcado: bool, arquivo: Path = ARQUIVO
) -> dict:
    registro = {
        "quando": datetime.now(UTC).isoformat(timespec="seconds"),
        "candidata": taxa_de_desconto.CANDIDATAS[CANDIDATA_DA_ADR],
        "periodo": periodo,
        "retrato": retrato,
        "forcado": forcado,
        "resumo": resumo,
    }
    with arquivo.open("a", encoding="utf-8") as saida:
        saida.write(json.dumps(registro, ensure_ascii=False) + "\n")
    return registro
