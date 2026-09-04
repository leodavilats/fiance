from datetime import UTC, date, datetime, timedelta

from tests.conftest import make_auth_headers


def _hoje() -> date:
    return datetime.now(UTC).date()


def _cdb(valor: float) -> dict:
    return {
        "nome": "CDB Banco X",
        "tipo": "cdb",
        "valor_investido": valor,
        "taxa": 13.0,
        "tipo_taxa": "pre_fixado",
        "data_aplicacao": (_hoje() - timedelta(days=365)).isoformat(),
        "vencimento": (_hoje() + timedelta(days=365)).isoformat(),
        "liquidez": "no_vencimento",
    }


def _gap_de(resposta, categoria):
    for gap in resposta.get("allocation_gaps", []):
        if gap["category"] == categoria:
            return gap
    return None


class TestARendaFixaEntraNaEstrategia:
    def _cenario(self, client, user_id, com_rf=True):
        headers = make_auth_headers(user_id)

        client.post(
            "/api/v1/portfolio/position",
            headers=headers,
            json={
                "ticker": "PETR4",
                "quantity": 1000,
                "avg_price": 30.0,
                "category": "acoes_br",
            },
        )
        if com_rf:
            client.post("/api/v1/fixed-income", headers=headers, json=_cdb(30000.0))

        client.post(
            "/api/v1/goals",
            headers=headers,
            json={
                "goals": [
                    {"category": "acoes_br", "target_pct": 50.0},
                    {"category": "renda_fixa", "target_pct": 50.0},
                ]
            },
        )
        return headers

    def test_a_meta_de_renda_fixa_deixa_de_ler_zero(self, client):
        headers = self._cenario(client, "estrat_rf_1")

        resposta = client.get("/api/v1/rebalance-suggestions", headers=headers).json()
        gap = _gap_de(resposta, "renda_fixa")

        assert gap is not None, "a categoria renda_fixa sumiu dos gaps"
        assert gap["current_value"] > 0, "renda fixa cadastrada continua lendo zero na Estratégia"
        assert gap["current_pct"] > 0

    def test_o_capital_total_inclui_a_renda_fixa(self, client):
        com = self._cenario(client, "estrat_rf_2", com_rf=True)
        sem = self._cenario(client, "estrat_rf_3", com_rf=False)

        gap_com = _gap_de(
            client.get("/api/v1/rebalance-suggestions", headers=com).json(), "acoes_br"
        )
        gap_sem = _gap_de(
            client.get("/api/v1/rebalance-suggestions", headers=sem).json(), "acoes_br"
        )

        assert gap_com is not None and gap_sem is not None
        assert gap_com["target_value"] > gap_sem["target_value"], (
            "o alvo em reais das ações não cresceu com a renda fixa no capital — "
            "sinal de que o total_capital continua excluindo a RF"
        )

    def test_carteira_so_de_renda_fixa_ainda_produz_estrategia(self, client):
        headers = make_auth_headers("estrat_rf_4")
        client.post("/api/v1/fixed-income", headers=headers, json=_cdb(20000.0))
        client.post(
            "/api/v1/goals",
            headers=headers,
            json={"goals": [{"category": "renda_fixa", "target_pct": 100.0}]},
        )

        resposta = client.get("/api/v1/rebalance-suggestions", headers=headers)

        assert resposta.status_code == 200
        gap = _gap_de(resposta.json(), "renda_fixa")
        assert gap is None or gap["current_value"] > 0
