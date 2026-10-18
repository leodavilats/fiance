from __future__ import annotations

from datetime import date

import sqlalchemy as sa

from tests.test_proventos import _gravar, _papel


def _historico(classe: str, data_com: str, valor: str, aprovacao: str) -> dict:
    return {
        "typeStock": classe,
        "lastDatePriorEx": data_com,
        "valueCash": valor,
        "quotedPerShares": "1",
        "corporateAction": "JRS CAP PROPRIO",
        "dateApproval": aprovacao,
    }


def _recente(isin: str, data_com: str, valor: str, pagamento: str) -> dict:
    return {
        "isinCode": isin,
        "lastDatePrior": data_com,
        "label": "JRS CAP PROPRIO",
        "rate": valor,
        "approvedOn": data_com,
        "paymentDate": pagamento,
    }


def _linhas(engine, emissor: str) -> list[tuple]:
    with engine.connect() as conn:
        return conn.execute(
            sa.text(
                "SELECT valor, data_pagamento, origem FROM mercado.provento WHERE emissor = :e "
                "ORDER BY data_pagamento NULLS LAST, id"
            ),
            {"e": emissor},
        ).all()


def test_cada_parcela_do_historico_recebe_a_sua_data(engine, tmp_path):
    with engine.begin() as conn:
        _papel(conn, "BRCMIGACNOR6", "ON", {"2026-09-22": ("17", "17")})
    parcela = _historico("ON", "22/09/2026", "0,03495670057", "17/09/2026")
    _gravar(
        engine,
        tmp_path,
        {
            "emissor": "CMIG",
            "nome_pregao": "CEMIG",
            "eventos": [],
            "proventos": [parcela, parcela],
            "recentes": [
                _recente("BRCMIGACNOR6", "22/09/2026", "0,03495670057", "30/12/2027"),
                _recente("BRCMIGACNOR6", "22/09/2026", "0,03495670057", "30/06/2027"),
            ],
        },
    )

    pagamentos = [linha.data_pagamento for linha in _linhas(engine, "CMIG")]

    assert pagamentos == [date(2027, 6, 30), date(2027, 12, 30)], (
        "a CEMIG paga o JCP de 22/09/2026 em duas parcelas: antes, as duas ficavam com a última data"
    )


def test_parcela_que_o_historico_nao_trouxe_entra_pelos_recentes(engine, tmp_path):
    with engine.begin() as conn:
        _papel(conn, "BRBTSAACNOR8", "ON", {"2025-12-30": ("12", "12")})
    parcela = _historico("ON", "30/12/2025", "0,12", "20/12/2025")
    datas = ("30/01/2026", "30/04/2026", "30/07/2026", "30/10/2026")
    _gravar(
        engine,
        tmp_path,
        {
            "emissor": "BTSA",
            "nome_pregao": "B3",
            "eventos": [],
            "proventos": [parcela, parcela],
            "recentes": [_recente("BRBTSAACNOR8", "30/12/2025", "0,12", d) for d in datas],
        },
    )

    linhas = _linhas(engine, "BTSA")

    assert len(linhas) == 4 and all(linha.data_pagamento for linha in linhas), (
        "a B3 lista quatro parcelas; o histórico trouxe duas"
    )
    assert [linha.origem for linha in linhas].count("b3_recente") == 2


def test_parcelas_de_fii_com_o_mesmo_valor_se_acumulam(engine, tmp_path):
    with engine.begin() as conn:
        _papel(conn, "BRPARCCTF000", "CI", {"2026-08-31": ("100", "100")}, codbdi="12")
    recentes = [
        _recente("BRPARCCTF000", "31/08/2026", "0,50", "15/09/2026"),
        _recente("BRPARCCTF000", "31/08/2026", "0,50", "15/10/2026"),
    ]
    pacote = {"emissor": "PARC", "nome_pregao": "FII PARCELAS", "eventos": [], "proventos": []}
    _gravar(engine, tmp_path, {**pacote, "recentes": recentes})
    _gravar(engine, tmp_path, {**pacote, "recentes": recentes[::-1]})

    pagamentos = [linha.data_pagamento for linha in _linhas(engine, "PARC")]

    assert pagamentos == [date(2026, 9, 15), date(2026, 10, 15)], (
        "a segunda parcela era barrada como repetida; coletar de novo não pode duplicar"
    )
