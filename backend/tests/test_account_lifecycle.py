"""Portabilidade e eliminação — os dois direitos que a loja também exige."""

from __future__ import annotations

from app.storage import account_store
from tests.conftest import make_auth_headers


def _seed(client, headers) -> None:
    client.post(
        "/api/portfolio/position",
        json={"ticker": "PETR4", "quantity": 100, "avg_price": 30.0},
        headers=headers,
    )
    client.post(
        "/api/alerts",
        json={"ticker": "PETR4", "condition": "below", "target_price": 25.0},
        headers=headers,
    )
    client.post(
        "/api/events",
        json={"events": [{"name": "signup_completed", "platform": "web"}]},
        headers=headers,
    )


def test_export_traz_o_dado_do_usuario_e_nada_do_vizinho(client):
    dono = make_auth_headers("u_export_a")
    vizinho = make_auth_headers("u_export_b")
    _seed(client, dono)
    client.post(
        "/api/portfolio/position",
        json={"ticker": "VALE3", "quantity": 10, "avg_price": 60.0},
        headers=vizinho,
    )

    response = client.get("/api/account/export", headers=dono)

    assert response.status_code == 200
    assert "attachment" in response.headers["content-disposition"]
    payload = response.json()
    tickers = {p["ticker"] for p in payload["data"]["positions"]}
    assert tickers == {"PETR4"}
    assert payload["data"]["price_alerts"], "alertas fazem parte do que é do titular"


def test_export_cobre_toda_tabela_com_dono():
    """Tabela nova com `user_id` tem que entrar na exportação e na exclusão.

    Este é o teste que impede o modo de falha silencioso: alguém adiciona uma
    tabela por usuário, esquece de listá-la, e a exclusão passa a deixar rastro.
    """
    account_store.export_account("u_cobertura")

    declaradas = account_store.user_scoped_table_names()
    reais = account_store.tables_with_user_column()

    assert reais - declaradas == set(), (
        f"tabelas com user_id fora de USER_SCOPED_MODELS: {sorted(reais - declaradas)}"
    )


def test_exclusao_exige_confirmacao_escrita(client):
    headers = make_auth_headers("u_delete_guard")

    resposta = client.request("DELETE", "/api/account", json={}, headers=headers)

    assert resposta.status_code == 400
    assert client.get("/api/portfolio", headers=headers).status_code == 200


def test_exclusao_apaga_tudo_e_encerra_a_sessao(client):
    headers = make_auth_headers("u_delete")
    _seed(client, headers)

    resposta = client.request(
        "DELETE", "/api/account", json={"confirm": "EXCLUIR"}, headers=headers
    )

    assert resposta.status_code == 200
    corpo = resposta.json()
    assert corpo["deleted"] is True
    assert corpo["removed"]["positions"] >= 1
    assert corpo["sla_days"] == account_store.DELETION_SLA_DAYS

    # O token continua criptograficamente válido — e mesmo assim não abre nada.
    assert client.get("/api/portfolio", headers=headers).status_code == 401

    # Entrar de novo com o mesmo `sub` do Google dá uma conta vazia, não a antiga.
    novo = make_auth_headers("u_delete")
    assert client.get("/api/portfolio", headers=novo).json()["items"] == []
    assert client.get("/api/alerts", headers=novo).json() == []


def test_politica_de_exclusao_e_publica_e_declara_prazo(client):
    headers = make_auth_headers("u_policy")

    corpo = client.get("/api/account/deletion-policy", headers=headers).json()

    assert corpo["sla_days"] == 30
    assert "positions" in corpo["removes"]
    assert corpo["confirmation_phrase"] == "EXCLUIR"
