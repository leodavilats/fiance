from datetime import datetime, timedelta

from app.core.brt import BRT
from tests.conftest import make_auth_headers


def _comprar(client, headers, **campos) -> int:
    dia = (datetime.now(BRT).date() - timedelta(days=30)).isoformat()
    corpo = {"kind": "buy", "symbol": "PETR4", "traded_on": dia, "quantity": 100, "price": 30.0}
    resposta = client.post("/api/v1/transactions", headers=headers, json={**corpo, **campos})
    assert resposta.status_code == 200, resposta.text
    return resposta.json()["id"]


def test_a_sugestao_seguida_sai_do_lancamento_sem_pedir_de_novo(client):
    headers = make_auth_headers("seguida_do_razao")
    entry_id = _comprar(client, headers)

    criada = client.post(
        "/api/v1/suggestions/followed",
        headers=headers,
        json={"entry_id": entry_id, "source": "opportunities", "score_at_suggestion": 80.0},
    )

    assert criada.status_code == 201, criada.text
    corpo = criada.json()
    assert (corpo["ticker"], corpo["quantity"], corpo["price"]) == ("PETR4", 100, 30.0), (
        "ativo, quantidade e preço vêm do razão; a pessoa não digita o que já lançou"
    )
    assert corpo["entry_id"] == entry_id
    assert corpo["action"] == "comprar"
    assert corpo["invested"] == 3000.0


def test_apagar_a_compra_tira_a_sugestao_do_resultado(client):
    headers = make_auth_headers("seguida_apagada")
    entry_id = _comprar(client, headers)
    client.post("/api/v1/suggestions/followed", headers=headers, json={"entry_id": entry_id})

    client.delete(f"/api/v1/transactions/{entry_id}", headers=headers)
    corpo = client.get("/api/v1/suggestions/followed", headers=headers).json()

    assert corpo["items"] == [], "o razão é a fonte: compra apagada não tem resultado a medir"
    assert corpo["total_invested"] == 0


def test_o_lancamento_de_outra_conta_nao_serve(client):
    dono = make_auth_headers("seguida_dono")
    intruso = make_auth_headers("seguida_intruso")
    entry_id = _comprar(client, dono)

    resposta = client.post(
        "/api/v1/suggestions/followed", headers=intruso, json={"entry_id": entry_id}
    )

    assert resposta.status_code == 404


def test_o_mesmo_lancamento_nao_e_seguido_duas_vezes(client):
    headers = make_auth_headers("seguida_dupla")
    entry_id = _comprar(client, headers)
    client.post("/api/v1/suggestions/followed", headers=headers, json={"entry_id": entry_id})

    segunda = client.post(
        "/api/v1/suggestions/followed", headers=headers, json={"entry_id": entry_id}
    )

    assert segunda.status_code == 409, "a mesma compra contada duas vezes dobra o resultado"


def test_evento_corporativo_nao_e_sugestao_seguida(client):
    headers = make_auth_headers("seguida_evento")
    dia = datetime.now(BRT).date().isoformat()
    _comprar(client, headers)
    evento = client.post(
        "/api/v1/transactions",
        headers=headers,
        json={"kind": "split", "symbol": "PETR4", "traded_on": dia, "ratio_from": 1, "ratio_to": 2},
    ).json()["id"]

    resposta = client.post(
        "/api/v1/suggestions/followed", headers=headers, json={"entry_id": evento}
    )

    assert resposta.status_code == 400


def test_sem_lancamento_ainda_se_pede_quantidade_e_preco(client):
    headers = make_auth_headers("seguida_sem_nada")

    resposta = client.post(
        "/api/v1/suggestions/followed", headers=headers, json={"ticker": "PETR4"}
    )

    assert resposta.status_code == 422
