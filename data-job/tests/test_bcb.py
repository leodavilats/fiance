from __future__ import annotations

import json
from datetime import date
from decimal import Decimal

import pytest
import sqlalchemy as sa

from datajob import coleta
from datajob.erros import ArquivoInvalido
from datajob.fontes import bcb_sgs

CDI = json.dumps(
    [
        {"data": "02/01/2025", "valor": "0.045513"},
        {"data": "03/01/2025", "valor": "0.045513"},
    ]
).encode()


def test_carga_inicial_vai_em_janelas_de_ate_dez_anos():
    janelas = bcb_sgs.janelas(None, date(2026, 10, 10))

    assert janelas[0][0] == bcb_sgs.PRIMEIRA_DATA
    assert janelas[-1][1] == date(2026, 10, 10)
    assert all((fim - inicio).days < 3650 for inicio, fim in janelas), (
        "o BCB recusa séries diárias com janela acima de 10 anos"
    )
    assert all(b[0] > a[1] for a, b in zip(janelas, janelas[1:], strict=False))


def test_dia_a_dia_recobre_as_ultimas_semanas():
    (janela,) = bcb_sgs.janelas(date(2026, 10, 9), date(2026, 10, 10))

    assert janela[0] < date(2026, 9, 1), "o BCB corrige pontos recentes; a janela os relê"


def test_pontos_em_decimal_e_data_brasileira():
    linhas, rejeitadas = bcb_sgs.interpretar(CDI, 12)

    assert linhas[0] == {"serie": 12, "data": date(2025, 1, 2), "valor": Decimal("0.045513")}
    assert rejeitadas == []


def test_ponto_ilegivel_vai_para_a_quarentena():
    conteudo = json.dumps([{"data": "32/01/2025", "valor": "1"}, {"data": "02/01/2025"}]).encode()

    linhas, rejeitadas = bcb_sgs.interpretar(conteudo, 12)

    assert linhas == []
    assert len(rejeitadas) == 2


def test_erro_do_bcb_recusa_o_arquivo():
    erro = json.dumps({"error": "janela de no máximo 10 anos"}).encode()

    with pytest.raises(ArquivoInvalido, match="erro"):
        bcb_sgs.interpretar(erro, 12)


def test_grava_serie_e_papel_de_leitura_enxerga(engine, tmp_path):
    resultado = coleta.executar(
        engine, tmp_path, bcb_sgs.FONTE, "sgs_12.json", CDI, bcb_sgs.processador(12)
    )

    assert resultado.gravadas == 2
    with engine.connect() as conn:
        pode = conn.execute(
            sa.text(
                "SELECT has_table_privilege('mercado_leitura', 'mercado.indicador', 'SELECT'), "
                "has_table_privilege('mercado_leitura', 'mercado.cotacao', 'INSERT')"
            )
        ).one()
    assert tuple(pode) == (True, False), "o papel de leitura lê tudo e não escreve nada"
