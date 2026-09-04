"""A posição é projeção do razão — em toda escrita, não em metade delas.

Três caminhos passavam por `ledger_service` e reprojetavam; três iam direto ao
`ledger_store` e não reprojetavam nada. O usuário colava o extrato da
corretora, o produto respondia `{"imported": 47}`, e a tela de Carteira não
mudava — nada avisava que faltava chamar `POST /transactions/rebuild`.
"""

from __future__ import annotations

import pytest

from app.core.config import get_settings
from app.core.context import reset_current_user_id, set_current_user_id
from app.services import subscription_service
from app.storage import portfolio_store
from tests.conftest import make_auth_headers


@pytest.fixture()
def como():
    tokens = []

    def _enter(user_id: str):
        tokens.append(set_current_user_id(user_id))
        return user_id

    yield _enter

    for token in reversed(tokens):
        reset_current_user_id(token)


@pytest.fixture()
def regua_ligada(monkeypatch):
    monkeypatch.setattr(get_settings(), "entitlements_enabled", True, raising=False)


def _lancamento(kind: str, symbol: str, dia: str, quantity: float, price: float) -> dict:
    return {
        "kind": kind,
        "symbol": symbol,
        "traded_on": dia,
        "quantity": quantity,
        "price": price,
    }


class TestTodaEscritaReprojeta:
    def test_lancamento_manual_aparece_na_carteira(self, client, como):
        uid = como("u_porta_manual")
        headers = make_auth_headers(uid)

        client.post(
            "/api/transactions",
            json=_lancamento("buy", "PETR4", "2026-01-05", 100, 30.0),
            headers=headers,
        )

        assert portfolio_store.get_position("PETR4", user_id=uid)["quantity"] == 100

    def test_lote_aparece_na_carteira(self, client, como):
        uid = como("u_porta_lote")
        headers = make_auth_headers(uid)

        client.post(
            "/api/transactions/batch",
            json={
                "transactions": [
                    _lancamento("buy", "VALE3", "2026-01-05", 50, 60.0),
                    _lancamento("buy", "VALE3", "2026-02-05", 50, 70.0),
                ]
            },
            headers=headers,
        )

        posicao = portfolio_store.get_position("VALE3", user_id=uid)
        assert posicao["quantity"] == 100
        assert posicao["avg_price"] == pytest.approx(65.0)

    def test_apagar_lancamento_reprojeta(self, client, como):
        uid = como("u_porta_delete")
        headers = make_auth_headers(uid)

        primeiro = client.post(
            "/api/transactions",
            json=_lancamento("buy", "ITUB4", "2026-01-05", 100, 25.0),
            headers=headers,
        ).json()["id"]
        client.post(
            "/api/transactions",
            json=_lancamento("buy", "ITUB4", "2026-02-05", 100, 35.0),
            headers=headers,
        )

        client.delete(f"/api/transactions/{primeiro}", headers=headers)

        posicao = portfolio_store.get_position("ITUB4", user_id=uid)
        assert posicao["quantity"] == 100
        assert posicao["avg_price"] == pytest.approx(35.0)


class TestAncoraDaPosicaoDeclarada:
    def test_compra_anterior_a_declaracao_nao_dobra_a_posicao(self, client, como):
        """Declarar hoje e importar o histórico depois é o fluxo que o produto convida.

        A âncora era por ordem de gravação: a compra importada entrava depois
        do ADJUST, era aplicada em cima do estado declarado, e 100 viravam 200.
        """
        uid = como("u_ancora_import")
        headers = make_auth_headers(uid)

        client.post(
            "/api/portfolio/position",
            json={"ticker": "BBAS3", "quantity": 100, "avg_price": 25.0},
            headers=headers,
        )

        client.post(
            "/api/transactions",
            json=_lancamento("buy", "BBAS3", "2025-03-10", 100, 20.0),
            headers=headers,
        )

        assert portfolio_store.get_position("BBAS3", user_id=uid)["quantity"] == 100

    def test_o_que_foi_absorvido_e_dito_e_nao_sumido(self, client, como):
        uid = como("u_ancora_aviso")
        headers = make_auth_headers(uid)

        client.post(
            "/api/portfolio/position",
            json={"ticker": "WEGE3", "quantity": 100, "avg_price": 50.0},
            headers=headers,
        )
        client.post(
            "/api/transactions",
            json=_lancamento("buy", "WEGE3", "2025-01-10", 100, 40.0),
            headers=headers,
        )

        derivacao = client.get("/api/transactions/derivation/WEGE3", headers=headers).json()

        assert derivacao["position"]["warnings"], "o razão precisa dizer o que não somou"


class TestRendaFixaEhCarteira:
    def test_so_renda_fixa_ja_conta_como_carteira(self, client, como):
        """Quem tem R$ 300 mil em CDB e nenhuma ação já "começou"."""
        uid = como("u_rf_carteira")

        client.post(
            "/api/fixed-income",
            json={
                "nome": "CDB Banco X",
                "tipo": "cdb",
                "valor_investido": 300000.0,
                "taxa": 12.0,
                "tipo_taxa": "pos_fixado",
                "percentual_cdi": 110.0,
                "data_aplicacao": "2026-01-05",
                "vencimento": "2028-01-05",
                "liquidez": "no_vencimento",
            },
            headers=make_auth_headers(uid),
        )

        assert portfolio_store.has_holdings(uid) is True

    def test_so_renda_fixa_dispara_o_trial(self, client, como):
        uid = como("u_rf_trial")

        client.post(
            "/api/fixed-income",
            json={
                "nome": "LCI",
                "tipo": "lci",
                "valor_investido": 10000.0,
                "taxa": 11.0,
                "tipo_taxa": "pos_fixado",
                "percentual_cdi": 95.0,
                "data_aplicacao": "2026-01-05",
                "vencimento": "2027-01-05",
                "liquidez": "no_vencimento",
            },
            headers=make_auth_headers(uid),
        )

        assert subscription_service.get(uid)["trial_ends_at"] is not None


class TestACercaDoLote:
    def test_o_lote_tem_a_mesma_cerca_da_importacao(self, client, como, regua_ligada):
        """A cerca estava no parser, não no direito de escrever em lote.

        Qualquer cliente que fizesse o parse do CSV do próprio lado contornava
        `/transactions/import` mandando a mesma lista para `/transactions/batch`.
        """
        uid = como("u_cerca_lote")
        headers = make_auth_headers(uid)

        client.post(
            "/api/portfolio/position",
            json={"ticker": "PETR4", "quantity": 10, "avg_price": 30.0},
            headers=headers,
        )
        subscription_service.cancel(uid, reason="fim do trial")

        resposta = client.post(
            "/api/transactions/batch",
            json={"transactions": [_lancamento("buy", "VALE3", "2026-01-05", 10, 60.0)]},
            headers=headers,
        )

        assert resposta.status_code == 402
