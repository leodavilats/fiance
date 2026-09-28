from datetime import date, timedelta

from tests.conftest import make_auth_headers

V1 = "/api/v1"


def _hoje() -> date:
    return date.today()


def _conta_cheia(client, headers) -> None:
    dia = (_hoje() - timedelta(days=40)).isoformat()
    compra = client.post(
        f"{V1}/transactions",
        headers=headers,
        json={
            "kind": "buy",
            "symbol": "PETR4",
            "traded_on": dia,
            "quantity": 100,
            "price": 30.5,
            "fees": 4.9,
        },
    ).json()["id"]
    client.post(
        f"{V1}/transactions",
        headers=headers,
        json={
            "kind": "sell",
            "symbol": "PETR4",
            "traded_on": (_hoje() - timedelta(days=10)).isoformat(),
            "quantity": 40,
            "price": 33.0,
        },
    )
    client.post(
        f"{V1}/portfolio/position",
        headers=headers,
        json={"ticker": "HGLG11", "quantity": 10, "avg_price": 160.0, "category": "fiis"},
    )
    client.post(
        f"{V1}/suggestions/followed",
        headers=headers,
        json={"entry_id": compra, "score_at_suggestion": 80.0},
    )
    client.post(
        f"{V1}/fixed-income",
        headers=headers,
        json={
            "nome": "CDB diário",
            "tipo": "cdb",
            "valor_investido": 5000.0,
            "taxa": 13.0,
            "tipo_taxa": "pre_fixado",
            "data_aplicacao": (_hoje() - timedelta(days=30)).isoformat(),
            "vencimento": (_hoje() + timedelta(days=365)).isoformat(),
            "liquidez": "diaria",
        },
    )
    client.post(
        f"{V1}/dividends/received",
        headers=headers,
        json={"ticker": "PETR4", "paid_at": dia, "amount": 123.45, "kind": "dividendo"},
    )
    client.post(
        f"{V1}/cashflow/entries",
        headers=headers,
        json={
            "kind": "income",
            "category": "salario",
            "description": "Salário",
            "amount": 8000.0,
            "due_on": _hoje().isoformat(),
            "paid_on": _hoje().isoformat(),
        },
    )
    divida = client.post(
        f"{V1}/cashflow/debts",
        headers=headers,
        json={"kind": "rotativo_cartao", "description": "Cartão", "balance": 890.0},
    ).json()["id"]
    client.post(f"{V1}/cashflow/debts/{divida}/settled", headers=headers)
    client.post(
        f"{V1}/cashflow/debts",
        headers=headers,
        json={"kind": "credito_pessoal", "description": "Empréstimo", "balance": 3000.0},
    )
    client.put(
        f"{V1}/goals",
        headers=headers,
        json={"goals": [{"category": "acoes_br", "target_pct": 60}]},
    )
    client.put(
        f"{V1}/preferences",
        headers=headers,
        json={"risk_profile": "aggressive", "excluded_tickers": ["MGLU3"]},
    )
    client.post(
        f"{V1}/alerts",
        headers=headers,
        json={"ticker": "VALE3", "condition": "below", "target_price": 50.0},
    )


def _leitura(client, headers) -> dict:
    razao = client.get(f"{V1}/transactions", headers=headers).json()["items"]
    carteira = client.get(f"{V1}/portfolio", headers=headers).json()
    seguidas = client.get(f"{V1}/suggestions/followed", headers=headers).json()["items"]
    return {
        "razao": sorted(
            (e["kind"], e["symbol"], e["traded_on"], e["quantity"], e["price"], e["fees"])
            for e in razao
        ),
        "posicoes": sorted(
            (p["ticker"], p["quantity"], p["avg_price"], p["category"]) for p in carteira["items"]
        ),
        "renda_fixa": sorted(
            (f["nome"], f["valor_investido"])
            for f in client.get(f"{V1}/fixed-income", headers=headers).json()["items"]
        ),
        "proventos": sorted(
            (d["ticker"], d["amount"])
            for d in client.get(f"{V1}/dividends/received", headers=headers).json()["items"]
        ),
        "seguidas": [(s["ticker"], s["quantity"], s["entry_id"] is not None) for s in seguidas],
        "caixa": sorted(
            (c["description"], c["amount"])
            for c in client.get(f"{V1}/cashflow/entries", headers=headers).json()
            if c.get("category") != "provento"
        ),
        "dividas": sorted(
            d["description"] for d in client.get(f"{V1}/cashflow/debts", headers=headers).json()
        ),
        "metas": [
            (g["category"], g["target_pct"], g["declared"])
            for g in client.get(f"{V1}/goals", headers=headers).json()
        ],
        "perfil": client.get(f"{V1}/preferences", headers=headers).json()["risk_profile"],
        "excluidos": client.get(f"{V1}/preferences", headers=headers).json()["excluded_tickers"],
        "alertas": [
            (a["ticker"], a["target_price"])
            for a in client.get(f"{V1}/alerts", headers=headers).json()
        ],
    }


def _exportar(client, headers) -> dict:
    resposta = client.get(f"{V1}/account/export", headers=headers)
    assert resposta.status_code == 200
    return resposta.json()


def test_a_conta_exportada_volta_igual_em_outra_conta(client):
    origem = make_auth_headers("importa_origem")
    destino = make_auth_headers("importa_destino")
    _conta_cheia(client, origem)
    arquivo = _exportar(client, origem)

    previa = client.post(f"{V1}/account/import/preview", headers=destino, json={"export": arquivo})
    assert previa.status_code == 200, previa.text
    assert previa.json()["ok"] is True, previa.json()
    assert {s["section"] for s in previa.json()["sections"]} >= {
        "transactions",
        "fixed_income_positions",
        "cash_entries",
        "debts",
    }

    feito = client.post(f"{V1}/account/import", headers=destino, json={"export": arquivo})
    assert feito.status_code == 200, feito.text

    assert _leitura(client, destino) == _leitura(client, origem), (
        "o que a pessoa exportou tem de voltar como estava: razão, carteira, renda fixa, "
        "proventos, caixa, dívidas, metas, preferências e alertas"
    )


def test_conta_com_dados_recusa_e_nada_muda(client):
    origem = make_auth_headers("importa_origem_2")
    destino = make_auth_headers("importa_destino_2")
    _conta_cheia(client, origem)
    arquivo = _exportar(client, origem)
    client.post(
        f"{V1}/cashflow/entries",
        headers=destino,
        json={
            "kind": "expense",
            "category": "mercado",
            "description": "Feira",
            "amount": 200.0,
            "due_on": _hoje().isoformat(),
        },
    )

    previa = client.post(
        f"{V1}/account/import/preview", headers=destino, json={"export": arquivo}
    ).json()
    assert previa["ok"] is False
    assert "lançamentos do mês" in previa["blockers"]

    feito = client.post(f"{V1}/account/import", headers=destino, json={"export": arquivo})
    assert feito.status_code == 409, "somar o arquivo ao que já existe duplicaria a carteira"
    assert client.get(f"{V1}/transactions", headers=destino).json()["items"] == []


def test_arquivo_com_item_invalido_nao_grava_nada(client):
    origem = make_auth_headers("importa_origem_3")
    destino = make_auth_headers("importa_destino_3")
    _conta_cheia(client, origem)
    arquivo = _exportar(client, origem)
    arquivo["data"]["cash_entries"][0]["amount"] = "-10"

    previa = client.post(
        f"{V1}/account/import/preview", headers=destino, json={"export": arquivo}
    ).json()
    assert previa["issues"][0]["section"] == "cash_entries"
    assert previa["issues"][0]["index"] == 1, "o erro diz onde está, como na importação de extrato"

    feito = client.post(f"{V1}/account/import", headers=destino, json={"export": arquivo})
    assert feito.status_code == 422
    assert client.get(f"{V1}/transactions", headers=destino).json()["items"] == [], (
        "a gravação é tudo ou nada"
    )


def test_arquivo_que_nao_e_exportacao_e_recusado(client):
    headers = make_auth_headers("importa_lixo")

    resposta = client.post(
        f"{V1}/account/import/preview", headers=headers, json={"export": {"foo": 1}}
    )

    assert resposta.status_code == 422


def test_quem_excluiu_a_conta_traz_os_dados_de_volta(client):
    arquivo_de = make_auth_headers("importa_volta")
    _conta_cheia(client, arquivo_de)
    antes = _leitura(client, arquivo_de)
    arquivo = _exportar(client, arquivo_de)

    excluida = client.request(
        "DELETE", f"{V1}/account", headers=arquivo_de, json={"confirm": "EXCLUIR"}
    )
    assert excluida.status_code == 200, excluida.text

    de_volta = make_auth_headers("importa_volta")
    feito = client.post(f"{V1}/account/import", headers=de_volta, json={"export": arquivo})

    assert feito.status_code == 200, feito.text
    assert _leitura(client, de_volta) == antes
