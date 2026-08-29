from __future__ import annotations

import pytest

from app.core.context import reset_current_user_id, set_current_user_id
from app.ledger import LedgerEntry, TransactionKind
from app.services import ledger_service
from app.storage import audit_store, ledger_store
from tests.conftest import make_auth_headers


@pytest.fixture()
def como(request):
    tokens = []

    def _enter(user_id: str):
        tokens.append(set_current_user_id(user_id))
        return user_id

    yield _enter

    for token in reversed(tokens):
        reset_current_user_id(token)


class TestEspelhamento:
    def test_salvar_posicao_grava_no_razao_como_estado_declarado(self, client):
        headers = make_auth_headers("u_ledger_mirror")

        client.post(
            "/api/portfolio/position",
            json={"ticker": "PETR4", "quantity": 100, "avg_price": 30.0},
            headers=headers,
        )

        corpo = client.get("/api/transactions", headers=headers).json()
        assert corpo["count"] == 1
        lancamento = corpo["items"][0]
        assert lancamento["kind"] == "adjust", (
            "a tela de posição declara estado, não uma compra que não aconteceu"
        )
        assert lancamento["quantity"] == 100
        assert lancamento["price"] == 30.0

    def test_vender_grava_venda_de_verdade(self, client):
        headers = make_auth_headers("u_ledger_sell")
        client.post(
            "/api/portfolio/position",
            json={"ticker": "PETR4", "quantity": 100, "avg_price": 30.0},
            headers=headers,
        )

        client.post(
            "/api/portfolio/sell",
            json={"ticker": "PETR4", "quantity": 40, "sell_price": 35.0},
            headers=headers,
        )

        tipos = [
            i["kind"] for i in client.get("/api/transactions", headers=headers).json()["items"]
        ]
        assert tipos == ["sell", "adjust"]

    def test_apagar_posicao_zera_o_razao_em_vez_de_deixar_fantasma(self, client):
        headers = make_auth_headers("u_ledger_del")
        client.post(
            "/api/portfolio/position",
            json={"ticker": "PETR4", "quantity": 100, "avg_price": 30.0},
            headers=headers,
        )

        client.delete("/api/portfolio/position/PETR4", headers=headers)

        assert client.get("/api/transactions/reconciliation", headers=headers).json()["in_sync"]


class TestReconciliacao:
    def test_reconciliacao_verde_apos_uso_normal(self, client):
        headers = make_auth_headers("u_reconcile")

        for ticker, qty, price in [("PETR4", 100, 30.0), ("VALE3", 50, 60.0)]:
            client.post(
                "/api/portfolio/position",
                json={"ticker": ticker, "quantity": qty, "avg_price": price},
                headers=headers,
            )
        client.post(
            "/api/portfolio/sell",
            json={"ticker": "PETR4", "quantity": 40, "sell_price": 35.0},
            headers=headers,
        )

        resultado = client.get("/api/transactions/reconciliation", headers=headers).json()

        assert resultado["differences"] == []
        assert resultado["in_sync"] is True

    def test_reconciliacao_acusa_divergencia_com_os_dois_numeros_a_vista(self, client, como):
        headers = make_auth_headers("u_reconcile_off")
        client.post(
            "/api/portfolio/position",
            json={"ticker": "PETR4", "quantity": 100, "avg_price": 30.0},
            headers=headers,
        )

        como("u_reconcile_off")
        ledger_store.record(
            LedgerEntry(
                kind=TransactionKind.BUY,
                symbol="PETR4",
                traded_on="2030-01-15",
                quantity=50,
                price=40.0,
            )
        )

        resultado = client.get("/api/transactions/reconciliation", headers=headers).json()

        assert resultado["in_sync"] is False
        divergencia = resultado["differences"][0]
        assert divergencia["ticker"] == "PETR4"
        assert divergencia["stored"]["quantity"] == 100
        assert divergencia["projected"]["quantity"] == 150

    def test_backfill_semeia_carteira_anterior_ao_razao(self, como):
        from app.storage import portfolio_store

        uid = como("u_backfill")
        portfolio_store.upsert_position("PETR4", 100, 30.0, user_id=uid)
        ledger_store.delete_symbol_entries("PETR4", user_id=uid)

        assert ledger_service.reconcile(user_id=uid)["in_sync"] is False

        semeadas = ledger_service.backfill_from_positions(user_id=uid)

        assert semeadas == 1
        assert ledger_service.reconcile(user_id=uid)["in_sync"] is True

    def test_backfill_nao_duplica_quem_ja_tem_razao(self, como):
        uid = como("u_backfill_twice")
        from app.storage import portfolio_store

        portfolio_store.upsert_position("VALE3", 10, 60.0, user_id=uid)
        assert ledger_service.backfill_from_positions(user_id=uid) == 1

        assert ledger_service.backfill_from_positions(user_id=uid) == 0


class TestIdentidadeDeInstrumento:
    def test_ticker_reutilizado_pela_b3_nao_mistura_historicos(self, como):
        uid = como("u_instrument")

        antigo = ledger_store.record(
            LedgerEntry(
                kind=TransactionKind.BUY,
                symbol="XPTO3",
                traded_on="2015-03-10",
                quantity=100,
                price=10.0,
            ),
            user_id=uid,
        )

        ledger_store.reassign_symbol("XPTO3", from_day="2020-01-01", name="Outra Companhia")

        novo = ledger_store.record(
            LedgerEntry(
                kind=TransactionKind.BUY,
                symbol="XPTO3",
                traded_on="2024-06-10",
                quantity=100,
                price=50.0,
            ),
            user_id=uid,
        )

        entradas = {e.id: e for e in ledger_store.list_entries(symbol="XPTO3", user_id=uid)}

        assert entradas[antigo].instrument_id != entradas[novo].instrument_id, (
            "operação de 2015 e de 2024 pertencem a companhias diferentes"
        )

    def test_operacoes_do_mesmo_periodo_compartilham_o_instrumento(self, como):
        uid = como("u_instrument_same")

        primeiro = ledger_store.record(
            LedgerEntry(
                kind=TransactionKind.BUY,
                symbol="ABCD4",
                traded_on="2024-01-10",
                quantity=1,
                price=1.0,
            ),
            user_id=uid,
        )
        segundo = ledger_store.record(
            LedgerEntry(
                kind=TransactionKind.BUY,
                symbol="ABCD4",
                traded_on="2024-08-10",
                quantity=1,
                price=1.0,
            ),
            user_id=uid,
        )

        entradas = {e.id: e for e in ledger_store.list_entries(symbol="ABCD4", user_id=uid)}
        assert entradas[primeiro].instrument_id == entradas[segundo].instrument_id


class TestDerivacaoNaTela:
    def test_a_conta_do_preco_medio_e_exposta_passo_a_passo(self, client):
        headers = make_auth_headers("u_derivation")
        client.post(
            "/api/transactions",
            json={
                "kind": "buy",
                "symbol": "PETR4",
                "traded_on": "2024-01-10",
                "quantity": 100,
                "price": 30.0,
                "fees": 10.0,
            },
            headers=headers,
        )
        client.post(
            "/api/transactions",
            json={
                "kind": "split",
                "symbol": "PETR4",
                "traded_on": "2024-05-02",
                "ratio_from": 1,
                "ratio_to": 2,
            },
            headers=headers,
        )

        corpo = client.get("/api/transactions/derivation/PETR4", headers=headers).json()

        assert [s["kind"] for s in corpo["steps"]] == ["buy", "split"]
        assert corpo["steps"][0]["total_cost_after"] == pytest.approx(3010.0)
        assert corpo["steps"][1]["quantity_after"] == 200
        assert corpo["steps"][1]["avg_price_after"] == pytest.approx(15.05)
        assert "custo total intacto" in corpo["steps"][1]["description"]
        assert corpo["position"]["avg_price"] == pytest.approx(15.05)


class TestLoteAtomico:
    def test_lote_com_um_lancamento_invalido_nao_grava_nenhum(self, client):
        headers = make_auth_headers("u_batch")

        resposta = client.post(
            "/api/transactions/batch",
            json={
                "transactions": [
                    {
                        "kind": "buy",
                        "symbol": "PETR4",
                        "traded_on": "2024-01-10",
                        "quantity": 100,
                        "price": 30.0,
                    },
                    {
                        "kind": "buy",
                        "symbol": "VALE3",
                        "traded_on": "10/01/2024",
                        "quantity": 10,
                        "price": 60.0,
                    },
                ]
            },
            headers=headers,
        )

        assert resposta.status_code == 400
        assert client.get("/api/transactions", headers=headers).json()["count"] == 0


class TestAuditoria:
    def test_escrever_posicao_deixa_rastro_legivel(self, client):
        headers = make_auth_headers("u_audit")

        client.post(
            "/api/portfolio/position",
            json={"ticker": "PETR4", "quantity": 100, "avg_price": 30.0},
            headers=headers,
        )

        itens = client.get("/api/activity", headers=headers).json()["items"]
        acoes = {i["action"] for i in itens}

        assert audit_store.POSITION_WRITE in acoes
        escrita = next(i for i in itens if i["action"] == audit_store.POSITION_WRITE)
        assert "PETR4" in escrita["summary"]

    def test_a_auditoria_e_do_titular_e_de_mais_ninguem(self, client):
        dono = make_auth_headers("u_audit_a")
        vizinho = make_auth_headers("u_audit_b")
        client.post(
            "/api/portfolio/position",
            json={"ticker": "PETR4", "quantity": 1, "avg_price": 1.0},
            headers=dono,
        )

        assert client.get("/api/activity", headers=vizinho).json()["items"] == []

    def test_falha_de_auditoria_nao_derruba_a_operacao(self, monkeypatch, client):

        def explode(*_args, **_kwargs):
            raise RuntimeError("banco de auditoria fora do ar")

        monkeypatch.setattr("app.storage.audit_store.db_session", explode)
        headers = make_auth_headers("u_audit_fail")

        resposta = client.post(
            "/api/portfolio/position",
            json={"ticker": "PETR4", "quantity": 100, "avg_price": 30.0},
            headers=headers,
        )

        assert resposta.status_code == 200
