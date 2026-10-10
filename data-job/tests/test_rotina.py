from __future__ import annotations

from datetime import date

from datajob import rotina
from datajob.rede import Ausente
from tests.conftest import TRECHO, zipar


def _nomes(urls: list[str]) -> list[str]:
    return [url.rsplit("/", 1)[1] for url in urls]


def test_banco_vazio_carrega_todos_os_anos():
    nomes = _nomes(rotina.pendencias(None, date(2026, 10, 9)))

    assert nomes[0] == f"COTAHIST_A{rotina.PRIMEIRO_ANO}.ZIP"
    assert nomes[-1] == "COTAHIST_A2026.ZIP"
    assert len(nomes) == 2026 - rotina.PRIMEIRO_ANO + 1


def test_ano_anterior_incompleto_rebusca_o_ano_dele_e_os_seguintes():
    nomes = _nomes(rotina.pendencias(date(2025, 12, 20), date(2026, 1, 5)))

    assert nomes == ["COTAHIST_A2025.ZIP", "COTAHIST_A2026.ZIP"]


def test_lacuna_curta_busca_os_dias_uteis():
    nomes = _nomes(rotina.pendencias(date(2026, 10, 8), date(2026, 10, 13)))

    assert nomes == [
        "COTAHIST_D09102026.ZIP",
        "COTAHIST_D12102026.ZIP",
        "COTAHIST_D13102026.ZIP",
    ], "sábado e domingo não têm pregão"


def test_em_dia_nao_busca_nada():
    assert rotina.pendencias(date(2026, 10, 9), date(2026, 10, 9)) == []


def test_lacuna_longa_no_mesmo_ano_usa_o_anual():
    nomes = _nomes(rotina.pendencias(date(2026, 8, 1), date(2026, 10, 9)))

    assert nomes == ["COTAHIST_A2026.ZIP"]


def test_diario_grava_o_que_saiu_e_registra_o_que_nao_saiu(engine, tmp_path):
    texto = TRECHO.read_text(encoding="latin-1").replace("20261008", "20261007")
    relatos: list[tuple[str, str | None]] = []

    def baixar(url: str) -> bytes:
        if url.endswith("COTAHIST_A2026.ZIP"):
            return zipar(texto)
        raise Ausente(url)

    rotina.diario(
        engine,
        tmp_path,
        baixar,
        lambda nome, r: relatos.append((nome, r.status if r else None)),
        hoje=date(2026, 1, 2),
    )
    relatos.clear()
    rotina.diario(
        engine,
        tmp_path,
        baixar,
        lambda nome, r: relatos.append((nome, r.status if r else None)),
        hoje=date(2026, 10, 9),
    )

    assert rotina.ultimo_pregao_gravado(engine) == date(2026, 10, 7)
    assert relatos == [
        ("COTAHIST_D08102026.ZIP", None),
        ("COTAHIST_D09102026.ZIP", None),
    ], "o pregão que ainda não saiu fica para a próxima rodada"
