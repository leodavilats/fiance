from __future__ import annotations

from datetime import UTC, date, datetime, timedelta

from tests.conftest import make_auth_headers


def _hoje() -> date:
    return datetime.now(UTC).date()


def _aplicacao(valor: float, liquidez: str) -> dict:
    return {
        "nome": f"CDB {liquidez}",
        "tipo": "cdb",
        "valor_investido": valor,
        "taxa": 13.0,
        "tipo_taxa": "pre_fixado",
        "data_aplicacao": (_hoje() - timedelta(days=30)).isoformat(),
        "vencimento": (_hoje() + timedelta(days=365)).isoformat(),
        "liquidez": liquidez,
    }


def _caixa_do_mes(client, headers) -> None:
    hoje = _hoje().isoformat()
    client.post(
        "/api/v1/cashflow/entries",
        headers=headers,
        json={
            "kind": "income",
            "category": "salario",
            "description": "Salário",
            "amount": 10000.0,
            "due_on": hoje,
            "paid_on": hoje,
        },
    )
    client.post(
        "/api/v1/cashflow/entries",
        headers=headers,
        json={
            "kind": "expense",
            "category": "moradia",
            "description": "Aluguel",
            "amount": 2000.0,
            "due_on": hoje,
            "paid_on": hoje,
            "fixed": True,
        },
    )


def _passos(client, headers) -> list[dict]:
    resposta = client.get("/api/v1/surplus", headers=headers)
    assert resposta.status_code == 200
    return resposta.json()["cascade"]["steps"]


def _reserva(passos: list[dict]) -> dict | None:
    for passo in passos:
        if passo["type"] == "reserve":
            return passo
    return None


class TestSemAlvoDeclaradoNaoHaPasso:
    def test_a_cascata_nao_inventa_meses(self, client):
        headers = make_auth_headers("reserva_sem_alvo")
        _caixa_do_mes(client, headers)
        client.post("/api/v1/fixed-income", headers=headers, json=_aplicacao(1000.0, "diaria"))

        assert _reserva(_passos(client, headers)) is None, (
            "'seis meses' é o número de mercado solto que a régua de dívida proíbe: sem alvo "
            "declarado, o passo não existe"
        )


class TestComAlvoDeclaradoOPassoAparece:
    def _cenario(self, client, user_id: str, meses: int, reserva: float, presa: float = 0.0):
        headers = make_auth_headers(user_id)
        _caixa_do_mes(client, headers)
        if reserva:
            client.post("/api/v1/fixed-income", headers=headers, json=_aplicacao(reserva, "diaria"))
        if presa:
            client.post(
                "/api/v1/fixed-income",
                headers=headers,
                json=_aplicacao(presa, "no_vencimento"),
            )
        salvou = client.put(
            "/api/v1/preferences",
            headers=headers,
            json={"reserve_months_target": meses},
        )
        assert salvou.status_code == 200
        assert salvou.json()["reserve_months_target"] == meses
        return headers

    def test_o_passo_entra_e_diz_quanto_falta(self, client):
        headers = self._cenario(client, "reserva_com_alvo", meses=6, reserva=1000.0)

        passo = _reserva(_passos(client, headers))

        assert passo is not None, (
            "a matemática do passo estava escrita e testada desde sempre, e nenhuma rota passava "
            "os dois parâmetros — era o item 30"
        )
        assert passo["amount"] > 0
        assert "6" in passo["reason"], "o motivo precisa citar o alvo que a pessoa declarou"

    def test_a_base_e_o_gasto_fixo_da_pessoa(self, client):
        headers = self._cenario(client, "reserva_base", meses=1, reserva=100.0)

        passo = _reserva(_passos(client, headers))

        assert passo is not None
        assert passo["reference"] == "gasto_fixo_proprio", (
            "a base é o custo fixo de quem guarda, e é isso que o falsificador promete"
        )

    def test_so_a_liquidez_diaria_conta_como_reserva(self, client):
        so_presa = self._cenario(client, "reserva_presa", meses=1, reserva=0.0, presa=50000.0)
        com_liquida = self._cenario(client, "reserva_liquida", meses=1, reserva=50000.0, presa=0.0)

        passo_presa = _reserva(_passos(client, so_presa))
        passo_liquida = _reserva(_passos(client, com_liquida))

        assert passo_presa is not None, (
            "papel preso até o vencimento não cobre emergência, então a reserva ainda falta"
        )
        assert passo_liquida is None, (
            "com o alvo já coberto por aplicação de liquidez diária, não há o que guardar"
        )

    def test_alvo_coberto_deixa_a_sobra_seguir_para_o_aporte(self, client):
        headers = self._cenario(client, "reserva_coberta", meses=1, reserva=50000.0)

        tipos = [p["type"] for p in _passos(client, headers)]

        assert "reserve" not in tipos
        assert "contribution" in tipos
