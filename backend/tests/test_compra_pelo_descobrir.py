from __future__ import annotations

import pytest

from app.core.context import reset_current_user_id, set_current_user_id
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


def _comprar(client, headers, ticker, quantidade, preco, dia="2026-02-10", taxas=0.0):
    return client.post(
        "/api/transactions",
        json={
            "kind": "buy",
            "symbol": ticker,
            "traded_on": dia,
            "quantity": quantidade,
            "price": preco,
            "fees": taxas,
        },
        headers=headers,
    )


def _posicao(client, headers, ticker):
    corpo = client.get("/api/portfolio", headers=headers).json()
    for item in corpo.get("items", []):
        if item["ticker"].upper() == ticker:
            return item
    return None


class TestCompraDeAtivoNovo:
    def test_a_compra_cria_a_posicao_na_carteira(self, client, como):
        uid = como("u_descobrir_novo")
        headers = make_auth_headers(uid)

        assert _comprar(client, headers, "PETR4", 100, 30.0).status_code == 200

        posicao = _posicao(client, headers, "PETR4")

        assert posicao is not None, (
            "comprar pelo Descobrir precisa colocar o ativo na carteira — é a razão de o botão "
            "existir"
        )
        assert posicao["quantity"] == 100
        assert posicao["avg_price"] == pytest.approx(30.0)

    def test_a_categoria_fica_para_a_leitura_resolver(self, client, como):
        uid = como("u_descobrir_categoria")
        headers = make_auth_headers(uid)

        _comprar(client, headers, "PETR4", 10, 30.0)

        posicao = _posicao(client, headers, "PETR4")

        assert posicao["category"] == "auto", (
            "a rota de transações não recebe categoria — ela não é derivável do razão. O store "
            "guarda 'auto' e quem resolve é a leitura enriquecida, em category_resolved, a "
            "partir do tipo do ativo. Se este teste falhar porque a categoria veio preenchida, "
            "alguém passou a adivinhá-la na escrita, e aí a alocação passa a depender de quando "
            "o ativo foi comprado."
        )


class TestCompraSobrePosicaoExistente:
    def test_a_segunda_compra_soma_e_recalcula_a_media(self, client, como):
        uid = como("u_descobrir_soma")
        headers = make_auth_headers(uid)

        _comprar(client, headers, "PETR4", 100, 20.0, dia="2026-01-10")
        _comprar(client, headers, "PETR4", 100, 40.0, dia="2026-02-10")

        posicao = _posicao(client, headers, "PETR4")

        assert posicao["quantity"] == 200
        assert posicao["avg_price"] == pytest.approx(30.0), (
            "duas compras iguais a 20 e a 40 dão média 30. Se a segunda compra substituísse a "
            "posição em vez de somar, a média sairia 40 e o imposto da venda futura viria errado."
        )

    def test_as_taxas_entram_no_custo(self, client, como):
        uid = como("u_descobrir_taxas")
        headers = make_auth_headers(uid)

        _comprar(client, headers, "VALE3", 100, 50.0, taxas=100.0)

        posicao = _posicao(client, headers, "VALE3")

        assert posicao["avg_price"] == pytest.approx(51.0), (
            "corretagem e emolumentos fazem parte do custo de aquisição, e é sobre ele que o "
            "ganho é apurado"
        )
