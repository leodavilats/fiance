from __future__ import annotations

import importlib.util
from datetime import date
from decimal import Decimal
from pathlib import Path

import pytest
import sqlalchemy as sa

from datajob.fontes import b3_proventos
from tests.test_proventos import _coleta, _evento, _papel

D = Decimal


def test_evento_grande_confirma_dentro_de_metade_da_distancia_ate_1():
    assert b3_proventos.confere(D("0.0116"), D("0.01")), "BTYU11: 100 para 1 com razão 86 aconteceu"
    assert b3_proventos.confere(D("1.48"), D("2")), "2 para 1 aceita de 1,41 a 2,83"
    assert not b3_proventos.confere(D("14.9"), D("2")), (
        "GSHP3: 2 para 1 com razão 14,9 é outra coisa"
    )
    assert not b3_proventos.confere(D("1.04"), D("0.01")), (
        "o Itaú de 2011: 100 para 1 com o preço parado"
    )


def test_evento_pequeno_vale_pela_publicacao_a_menos_que_o_preco_desminta():
    assert b3_proventos.confere(D("1.0"), D("1.1")), "bonificação de 10% com o preço parado"
    assert b3_proventos.confere(D("1.11"), D("1.25")), (
        "CRPG3: 25% ainda é pequeno, e 1,11 não desmente"
    )
    assert not b3_proventos.confere(D("2.09"), D("1.05")), (
        "ETER3: 5% publicado, o preço caiu à metade"
    )


@pytest.mark.parametrize(
    ("tipo", "fator", "abertura", "status"),
    [
        ("GRUPAMENTO", "0.01", "86.66", "confirmado"),
        ("BONIFICACAO", "100", "0.067", "divergente"),
        ("BONIFICACAO", "10", "1.00", "confirmado"),
    ],
)
def test_validar_aplica_a_regra_pelo_preco_em_volta(engine, tipo, fator, abertura, status):
    with engine.begin() as conn:
        _papel(
            conn,
            "BRCONFACNOR1",
            "ON",
            {"2026-08-31": ("1", "1"), "2026-09-01": (abertura, abertura)},
        )
    eventos = [_evento("BRCONFACNOR1", date(2026, 8, 31), tipo, fator)]
    with engine.connect() as conn:
        b3_proventos.validar(conn, eventos)

    assert eventos[0]["status"] == status


def _migracao():
    caminho = (
        Path(__file__).parents[1] / "migrations" / "versions" / "0022_confirmacao_pelo_tamanho.py"
    )
    especificacao = importlib.util.spec_from_file_location("migracao_0022", caminho)
    modulo = importlib.util.module_from_spec(especificacao)
    especificacao.loader.exec_module(modulo)
    return modulo


def test_a_migracao_reconfere_como_a_coleta_confere(engine):
    casos = [
        ("BRAAAAACNOR1", "GRUPAMENTO", "0.01", "0.0116"),
        ("BRBBBBACNOR1", "BONIFICACAO", "2", "14.9"),
        ("BRCCCCACNOR1", "BONIFICACAO", "1.05", "2.09"),
        ("BRDDDDACNOR1", "BONIFICACAO", "1.1", "1.0"),
        ("BREEEEACNOR1", "DESDOBRAMENTO", "4", "3.36"),
        ("BRFFFFACNOR1", "GRUPAMENTO", "0.01", "1.04"),
    ]
    with engine.begin() as conn:
        coleta = _coleta(conn)
        for isin, tipo, multiplicador, observada in casos:
            conn.execute(
                sa.text(
                    "INSERT INTO mercado.evento (emissor, isin, data_com, tipo, fator, multiplicador, "
                    "status, razao_observada, coleta_id) VALUES (:e, :i, '2020-01-02', :t, 1, :m, "
                    "'divergente', :r, :c)"
                ),
                {
                    "e": isin[2:6],
                    "i": isin,
                    "t": tipo,
                    "m": multiplicador,
                    "r": observada,
                    "c": coleta,
                },
            )
        conn.execute(sa.text(_migracao()._RECONFERIR))
        gravado = dict(conn.execute(sa.text("SELECT isin, status FROM mercado.evento")).all())

    for isin, _, multiplicador, observada in casos:
        esperado = (
            "confirmado" if b3_proventos.confere(D(observada), D(multiplicador)) else "divergente"
        )
        assert gravado[isin] == esperado, f"{isin}: a migração e a coleta precisam decidir igual"
