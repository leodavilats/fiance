from __future__ import annotations

import sqlalchemy as sa

from tests.test_proventos import _coleta, _papel


def _emissor(conn, codigo: str, cnpj: str) -> None:
    conn.execute(
        sa.text("INSERT INTO mercado.emissor (codigo, cnpj, metodo) VALUES (:c, :j, 'fca')"),
        {"c": codigo, "j": cnpj},
    )


def _evento(conn, isin: str, data_com: str, tipo: str, multiplicador: str, status: str) -> None:
    conn.execute(
        sa.text(
            "INSERT INTO mercado.evento (emissor, isin, data_com, tipo, fator, multiplicador, "
            "status, coleta_id) VALUES (:e, :i, :d, :t, 1, :m, :s, :c)"
        ),
        {"e": isin[2:6], "i": isin, "d": data_com, "t": tipo, "m": multiplicador, "s": status,
         "c": _coleta(conn)},
    )  # fmt: skip


def _dia(conn, cnpj: str, data: str, classe: str = "ON"):
    conn.execute(sa.text("REFRESH MATERIALIZED VIEW mercado.serie_papel"))
    return conn.execute(
        sa.text("SELECT * FROM mercado.serie_papel WHERE cnpj = :c AND data = :d AND classe = :k"),
        {"c": cnpj, "d": data, "k": classe},
    ).one()


def test_evento_recusado_pelo_preco_nao_esconde_o_salto(engine):
    with engine.begin() as conn:
        _papel(
            conn,
            "BRSEQLACNOR1",
            "ON NM",
            {"2025-12-01": ("0.42", "0.42"), "2025-12-02": ("3.77", "3.77")},
        )
        _emissor(conn, "SEQL", "10")
        _evento(conn, "BRSEQLACNOR1", "2025-12-01", "GRUPAMENTO", "0.1", "divergente")
        dia = _dia(conn, "10", "2025-12-02")

    assert dia.salto_sem_evento, (
        "a SEQL3 subiu 797% no dia do grupamento que o preço recusou: a série não ajustou, e o salto "
        "precisa aparecer"
    )


def test_evento_de_outra_classe_nao_esconde_o_salto(engine):
    with engine.begin() as conn:
        _papel(conn, "BRCLSCACNOR1", "ON", {"2024-04-15": ("50", "50"), "2024-04-16": ("20", "20")})
        _papel(conn, "BRCLSCACNPR1", "PN", {"2024-04-15": ("50", "50"), "2024-04-16": ("25", "25")})
        _emissor(conn, "CLSC", "11")
        _evento(conn, "BRCLSCACNPR1", "2024-04-15", "DESDOBRAMENTO", "2", "confirmado")
        on = _dia(conn, "11", "2024-04-16")

    assert on.classe == "ON" and on.salto_sem_evento, (
        "o desdobramento foi da PN; a ON caiu 60% sozinha"
    )


def test_queda_perto_de_um_fator_comum_fica_marcada_mesmo_abaixo_de_cinquenta_por_cento(engine):
    with engine.begin() as conn:
        _papel(
            conn, "BRDAMTACNOR1", "ON", {"2026-06-03": ("40", "40"), "2026-06-05": ("20.8", "20.8")}
        )
        _papel(conn, "BRPEQUACNOR1", "ON", {"2026-06-03": ("30", "30"), "2026-06-05": ("20", "20")})
        _emissor(conn, "DAMT", "12")
        _emissor(conn, "PEQU", "13")
        metade = _dia(conn, "12", "2026-06-05")
        um_terco = _dia(conn, "13", "2026-06-05")

    assert metade.salto_sem_evento, (
        "−48% é um desdobramento 2:1 que nenhuma lista trouxe, até prova contrária"
    )
    assert not um_terco.salto_sem_evento, (
        "−33% é perto de 1,5, mas em papel pouco líquido é dia comum: 1,5 fica de fora da marca"
    )
