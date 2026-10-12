from __future__ import annotations

import json
from datetime import date
from decimal import Decimal
from pathlib import Path

import pytest
import sqlalchemy as sa

from datajob import coleta, rotina
from datajob.fontes import b3_proventos

MGLU = (Path(__file__).parent / "fixtures" / "b3_proventos_MGLU.json").read_bytes()


def test_multiplicador_de_cada_evento():
    assert b3_proventos.multiplicador("DESDOBRAMENTO", Decimal(100)) == 2
    assert b3_proventos.multiplicador("BONIFICACAO", Decimal(10)) == Decimal("1.1")
    assert b3_proventos.multiplicador("GRUPAMENTO", Decimal("0.1")) == Decimal("0.1")
    assert b3_proventos.multiplicador("CIS RED CAP", Decimal(100)) is None


def test_eventos_e_proventos_da_magazine_luiza():
    emissor, proventos, eventos, rejeitados = b3_proventos.interpretar(MGLU)

    assert emissor == "MGLU"
    assert {(e["tipo"], e["data_com"], e["multiplicador"]) for e in eventos} == {
        ("DESDOBRAMENTO", date(2020, 10, 13), Decimal(4)),
        ("GRUPAMENTO", date(2024, 5, 24), Decimal("0.1")),
        ("BONIFICACAO", date(2025, 12, 29), Decimal("1.05")),
    }
    assert len(proventos) == 17
    assert rejeitados == []


def test_provento_antigo_cotado_por_lote_de_mil():
    pacote = json.loads(MGLU)
    pacote["proventos"] = [
        {
            "typeStock": "ON",
            "lastDatePriorEx": "10/05/2005",
            "valueCash": "12,5",
            "quotedPerShares": "1000",
            "corporateAction": "DIVIDENDO",
            "dateApproval": "01/04/2005",
        }
    ]

    _, proventos, _, _ = b3_proventos.interpretar(json.dumps(pacote).encode())

    assert proventos[0]["valor"] == Decimal("0.0125")


def test_nome_de_pregao_com_barra_tem_variantes():
    assert b3_proventos.nomes_possiveis("AMBEV S/A   ") == ["AMBEV S/A", "AMBEV SA"]


def test_baixa_todas_as_paginas_e_tenta_o_nome_sem_barra():
    pedidos = []

    def baixar(url: str) -> bytes:
        pedidos.append(url)
        if url == b3_proventos.url_do_complemento("ABEV"):
            return json.dumps([{"tradingName": "AMBEV S/A", "stockDividends": []}]).encode()
        if url == b3_proventos.url_dos_proventos("AMBEV SA", 1):
            return json.dumps({"page": {"totalPages": 2}, "results": [{"x": 1}]}).encode()
        if url == b3_proventos.url_dos_proventos("AMBEV SA", 2):
            return json.dumps({"page": {"totalPages": 2}, "results": [{"x": 2}]}).encode()
        return json.dumps({"page": {"totalPages": 0}, "results": []}).encode()

    pacote = json.loads(b3_proventos.baixar_emissor("ABEV", baixar))

    assert pacote["proventos"] == [{"x": 1}, {"x": 2}]
    assert pacote["nome_pregao"] == "AMBEV S/A"


def test_fundo_nao_pede_o_historico_de_proventos():
    pedidos = []

    def baixar(url: str) -> bytes:
        pedidos.append(url)
        return json.dumps(
            [{"tradingName": "SPX FIA", "stockDividends": [], "cashDividends": [{"x": 1}]}]
        ).encode()

    pacote = json.loads(b3_proventos.baixar_emissor("SPXI", baixar, com_historico=False))

    assert pedidos == [b3_proventos.url_do_complemento("SPXI")]
    assert pacote["recentes"] == [{"x": 1}]


def test_proventos_so_as_sextas_depois_da_carga():
    assert rotina.proventos_hoje(False, date(2026, 10, 13))
    assert rotina.proventos_hoje(True, date(2026, 10, 9)), "9/10/2026 é sexta"
    assert not rotina.proventos_hoje(True, date(2026, 10, 13))


def _coleta(conn) -> int:
    return conn.execute(
        sa.text(
            "INSERT INTO mercado.coleta (fonte, arquivo, status, iniciada_em) "
            "VALUES ('teste', 'teste', 'ok', now()) RETURNING id"
        )
    ).scalar_one()


def _papel(
    conn,
    isin: str,
    especie: str,
    precos: dict[str, tuple[str, str]],
    fator: int = 1,
    codbdi: str = "02",
):
    coleta_id = _coleta(conn)
    datas = sorted(precos)
    conn.execute(
        sa.text(
            "INSERT INTO mercado.ativo (isin, nome_resumido, especie, codbdi, primeiro_pregao, "
            "ultimo_pregao) VALUES (:i, 'TESTE', :e, :b, :p, :u)"
        ),
        {"i": isin, "e": especie, "b": codbdi, "p": datas[0], "u": datas[-1]},
    )
    conn.execute(
        sa.text(
            "INSERT INTO mercado.cotacao (isin, data, codigo, codbdi, abertura, maxima, minima, "
            "media, fechamento, negocios, quantidade, volume, fator_cotacao, coleta_id) VALUES "
            "(:i, :d, 'TEST3', :b, :a, :a, :f, :f, :f, 1, 1, 1, :fator, :c)"
        ),
        [
            {"i": isin, "d": d, "a": a, "f": f, "fator": fator, "b": codbdi, "c": coleta_id}
            for d, (a, f) in precos.items()
        ],
    )


def _evento(isin: str, data_com: date, tipo: str, fator: str) -> dict:
    return {
        "emissor": isin[2:6],
        "isin": isin,
        "data_com": data_com,
        "tipo": tipo,
        "fator": Decimal(fator),
        "multiplicador": b3_proventos.multiplicador(tipo, Decimal(fator)),
        "data_aprovacao": None,
    }


@pytest.fixture
def papel_com_desdobramento(engine):
    with engine.begin() as conn:
        _papel(
            conn,
            "BRTESTACNOR1",
            "ON NM",
            {
                "2024-04-12": ("40", "40"),
                "2024-04-15": ("40", "40"),
                "2024-04-16": ("20.2", "20"),
                "2024-04-17": ("20", "21"),
            },
        )
    return engine


def test_desdobramento_confirmado_pelo_preco(papel_com_desdobramento):
    eventos = [_evento("BRTESTACNOR1", date(2024, 4, 15), "DESDOBRAMENTO", "100")]
    with papel_com_desdobramento.connect() as conn:
        b3_proventos.validar(conn, eventos)

    assert eventos[0]["status"] == "confirmado"
    assert round(eventos[0]["razao_observada"], 2) == Decimal("1.98")


def test_evento_que_o_preco_desmente_fica_divergente(papel_com_desdobramento):
    eventos = [_evento("BRTESTACNOR1", date(2024, 4, 15), "GRUPAMENTO", "0.01")]
    with papel_com_desdobramento.connect() as conn:
        b3_proventos.validar(conn, eventos)

    assert eventos[0]["status"] == "divergente", "o Itaú de 2011 aparece assim na B3"


def test_eventos_do_mesmo_dia_se_combinam(papel_com_desdobramento):
    eventos = [
        _evento("BRTESTACNOR1", date(2024, 4, 15), "DESDOBRAMENTO", "4900"),
        _evento("BRTESTACNOR1", date(2024, 4, 15), "GRUPAMENTO", "0.04"),
    ]
    with papel_com_desdobramento.connect() as conn:
        b3_proventos.validar(conn, eventos)

    assert {e["status"] for e in eventos} == {"confirmado"}, "o Bradesco fez ×50 e ÷25 no mesmo dia"


def test_sem_pregao_em_volta_fica_sem_preco(papel_com_desdobramento):
    eventos = [_evento("BRTESTACNOR1", date(2019, 1, 2), "BONIFICACAO", "10")]
    with papel_com_desdobramento.connect() as conn:
        b3_proventos.validar(conn, eventos)

    assert eventos[0]["status"] == "sem_preco"


def test_serie_ajustada_com_desdobramento_e_provento(papel_com_desdobramento, tmp_path):
    engine = papel_com_desdobramento
    with engine.begin() as conn:
        conn.execute(
            sa.text(
                "INSERT INTO mercado.emissor (codigo, cnpj, metodo) VALUES ('TEST', '1', 'fca')"
            )
        )
    pacote = {
        "emissor": "TEST",
        "nome_pregao": "TESTE",
        "eventos": [
            {
                "isinCode": "BRTESTACNOR1",
                "lastDatePrior": "15/04/2024",
                "label": "DESDOBRAMENTO",
                "factor": "100,00000000000",
                "approvedOn": "01/04/2024",
            }
        ],
        "proventos": [
            {
                "typeStock": "ON",
                "lastDatePriorEx": "12/04/2024",
                "valueCash": "2,0",
                "quotedPerShares": "1",
                "corporateAction": "DIVIDENDO",
                "dateApproval": "01/04/2024",
            }
        ],
    }
    coleta.executar(
        engine,
        tmp_path,
        b3_proventos.FONTE,
        "b3_proventos_TEST.json",
        json.dumps(pacote).encode(),
        b3_proventos.processar,
    )
    with engine.begin() as conn:
        conn.execute(sa.text("REFRESH MATERIALIZED VIEW mercado.serie_papel"))
        serie = {
            str(r.data): r
            for r in conn.execute(
                sa.text("SELECT * FROM mercado.serie_papel WHERE cnpj = '1' ORDER BY data")
            )
        }

    def r(valor) -> Decimal:
        return round(valor, 8)

    assert r(serie["2024-04-12"].fechamento_ajustado) == 20, "antes do desdobramento, preço ÷ 2"
    assert r(serie["2024-04-16"].fechamento_ajustado) == 20
    assert r(serie["2024-04-15"].provento) == 1, "R$ 2 por ação antiga = R$ 1 por ação nova"
    assert r(serie["2024-04-15"].retorno_total) == Decimal("0.05"), "(20 + 1) / 20 - 1"
    assert r(serie["2024-04-16"].retorno_total) == 0
    assert r(serie["2024-04-17"].retorno_total) == Decimal("0.05")
    assert not serie["2024-04-16"].salto_sem_evento
    assert serie["2024-04-15"].dias_desde_anterior == 3


def test_salto_que_nenhum_evento_explica_fica_marcado(engine):
    with engine.begin() as conn:
        _papel(
            conn,
            "BRKEPLACNOR1",
            "ON NM",
            {"2022-05-05": ("55", "55.15"), "2022-05-06": ("18.42", "19.04")},
        )
        conn.execute(
            sa.text(
                "INSERT INTO mercado.emissor (codigo, cnpj, metodo) VALUES ('KEPL', '2', 'fca')"
            )
        )
        conn.execute(sa.text("REFRESH MATERIALIZED VIEW mercado.serie_papel"))
        dia = conn.execute(
            sa.text("SELECT * FROM mercado.serie_papel WHERE cnpj = '2' AND data = '2022-05-06'")
        ).one()

    assert dia.salto_sem_evento, "o desdobramento de 1 para 3 da Kepler em 2022 não está na B3"


def _recente(data_com: str, valor: str) -> dict:
    return {
        "isinCode": "BRXPMLCTF000",
        "lastDatePrior": data_com,
        "label": "RENDIMENTO",
        "rate": valor,
        "approvedOn": data_com,
    }


def _gravar(engine, tmp_path, pacote: dict) -> coleta.Resultado:
    return coleta.executar(
        engine,
        tmp_path,
        b3_proventos.FONTE,
        f"b3_proventos_{pacote['emissor']}.json",
        json.dumps(pacote).encode(),
        b3_proventos.processar,
    )


def _proventos(engine, emissor: str) -> list[tuple]:
    with engine.connect() as conn:
        return [
            tuple(r)
            for r in conn.execute(
                sa.text(
                    "SELECT classe, data_com, valor, origem FROM mercado.provento "
                    "WHERE emissor = :e ORDER BY data_com"
                ),
                {"e": emissor},
            )
        ]


def test_rendimento_recente_de_fii_se_acumula(engine, tmp_path):
    with engine.begin() as conn:
        _papel(conn, "BRXPMLCTF000", "CI", {"2026-08-31": ("100", "100")}, codbdi="12")
    pacote = {"emissor": "XPML", "nome_pregao": "FII XP MALLS", "eventos": [], "proventos": []}

    _gravar(engine, tmp_path, {**pacote, "recentes": [_recente("31/08/2026", "0,92")]})
    _gravar(engine, tmp_path, {**pacote, "recentes": [_recente("30/09/2026", "0,92")]})
    _gravar(engine, tmp_path, {**pacote, "recentes": [_recente("30/09/2026", "0,92")]})

    assert _proventos(engine, "XPML") == [
        ("CI", date(2026, 8, 31), Decimal("0.92"), "b3_recente"),
        ("CI", date(2026, 9, 30), Decimal("0.92"), "b3_recente"),
    ], "a B3 só mostra os últimos meses: o que saiu da lista continua guardado, e nada duplica"


def test_historico_completo_substitui_os_recentes(engine, tmp_path):
    with engine.begin() as conn:
        _papel(conn, "BRXPMLCTF000", "CI", {"2026-08-31": ("100", "100")}, codbdi="12")
    pacote = {"emissor": "XPML", "nome_pregao": "FII XP MALLS", "eventos": [], "proventos": []}
    _gravar(engine, tmp_path, {**pacote, "recentes": [_recente("31/08/2026", "0,92")]})

    historico = {
        "typeStock": "CI",
        "lastDatePriorEx": "31/08/2026",
        "valueCash": "0,92",
        "quotedPerShares": "1",
        "corporateAction": "RENDIMENTO",
        "dateApproval": "31/08/2026",
    }
    _gravar(engine, tmp_path, {**pacote, "proventos": [historico], "recentes": []})

    assert _proventos(engine, "XPML") == [
        ("CI", date(2026, 8, 31), Decimal("0.92"), "b3_historico")
    ]


def test_serie_de_fundo_com_desdobramento_e_rendimento(engine, tmp_path):
    with engine.begin() as conn:
        _papel(
            conn,
            "BRSPXICTF006",
            "CI",
            {
                "2025-03-14": ("80", "80"),
                "2025-03-17": ("10", "10"),
                "2025-03-18": ("10", "10.5"),
            },
            codbdi="14",
        )
    pacote = {
        "emissor": "SPXI",
        "nome_pregao": "SPX FIA",
        "eventos": [
            {
                "isinCode": "BRSPXICTF006",
                "lastDatePrior": "14/03/2025",
                "label": "DESDOBRAMENTO",
                "factor": "700,00000000000",
                "approvedOn": "01/03/2025",
            }
        ],
        "proventos": [],
        "recentes": [
            {
                "isinCode": "BRSPXICTF006",
                "lastDatePrior": "17/03/2025",
                "label": "RENDIMENTO",
                "rate": "0,5",
                "approvedOn": "10/03/2025",
            }
        ],
    }
    _gravar(engine, tmp_path, pacote)
    with engine.begin() as conn:
        conn.execute(sa.text("REFRESH MATERIALIZED VIEW mercado.serie_fundo"))
        serie = {
            str(r.data): r
            for r in conn.execute(
                sa.text("SELECT * FROM mercado.serie_fundo WHERE emissor = 'SPXI' ORDER BY data")
            )
        }

    def r(valor) -> Decimal:
        return round(valor, 8)

    assert serie["2025-03-17"].tipo_ativo == "fundo"
    assert r(serie["2025-03-14"].fechamento_ajustado) == 10, "desdobramento de 700%: cota ÷ 8"
    assert r(serie["2025-03-17"].retorno_total) == 0
    assert not serie["2025-03-17"].salto_sem_evento
    assert r(serie["2025-03-18"].provento) == Decimal("0.5")
    assert r(serie["2025-03-18"].retorno_total) == Decimal("0.1"), "(10,5 + 0,5) / 10 - 1"
