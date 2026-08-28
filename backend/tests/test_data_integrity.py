"""Plausibilidade do dado externo e disjuntor da fonte.

Dado errado em produto pago é a reclamação número 1 dos concorrentes
brasileiros, e o modo de falha é o pior possível: o número absurdo não levanta
exceção — vira um veredito.
"""

from __future__ import annotations

import pytest

from app.collectors import circuit, plausibility
from tests.conftest import make_auth_headers


@pytest.fixture(autouse=True)
def _circuito_limpo():
    circuit.reset()
    yield
    circuit.reset()


class TestPlausibilidade:
    def test_campo_implausivel_vira_ausente_e_nao_derruba_o_resto(self):
        """O produto sabe conviver com indicador ausente; com número errado, não."""
        limpo, veredito = plausibility.screen(
            {"price": 30.0, "roe": 12_000.0, "pe_ratio": 8.0}, symbol="PETR4"
        )

        assert veredito.accepted is True
        assert limpo["roe"] is None
        assert limpo["price"] == 30.0
        assert limpo["pe_ratio"] == 8.0
        assert veredito.dropped == {"roe": 12_000.0}

    def test_preco_implausivel_rejeita_o_snapshot_inteiro(self):
        """Sem preço não há posição, patrimônio nem veredito."""
        _, veredito = plausibility.screen({"price": 0.0001, "roe": 15.0}, symbol="XPTO3")

        assert veredito.accepted is False
        assert "price" in veredito.dropped
        assert "não há veredito possível" in veredito.reason

    def test_o_extremo_legitimo_da_b3_continua_passando(self):
        """Existe empresa com ROE de 80% e ação de R$ 0,90. Rejeitá-las seria
        trocar um erro por outro."""
        limpo, veredito = plausibility.screen(
            {"price": 0.90, "roe": 80.0, "dividend_yield": 18.0, "pb_ratio": 0.3}
        )

        assert veredito.accepted is True
        assert veredito.dropped == {}
        assert limpo["price"] == 0.90

    def test_dupla_conversao_de_unidade_e_barrada(self):
        """`_ratio_to_pct` aplicado duas vezes dá 2.039 onde deveria dar 20,39."""
        limpo, _ = plausibility.screen({"price": 30.0, "roe": 2039.0})

        assert limpo["roe"] is None

    def test_campo_ausente_da_tabela_passa_sem_verificacao(self):
        limpo, veredito = plausibility.screen({"price": 30.0, "campo_novo": 9e18})

        assert veredito.accepted is True
        assert limpo["campo_novo"] == 9e18

    def test_none_nao_e_implausivel(self):
        _, veredito = plausibility.screen({"price": 30.0, "roe": None})

        assert veredito.dropped == {}

    def test_a_entrada_nao_e_mutada(self):
        original = {"price": 30.0, "roe": 12_000.0}

        plausibility.screen(original)

        assert original["roe"] == 12_000.0

    def test_as_faixas_sao_publicadas_com_o_motivo(self):
        faixas = {f["field"]: f for f in plausibility.describe_ranges()}

        assert faixas["price"]["rejects_snapshot"] is True
        assert faixas["roe"]["rejects_snapshot"] is False
        assert all(f["reason"] for f in faixas.values())
        assert all(f["low"] < f["high"] for f in faixas.values())


class TestDisjuntor:
    def test_fechado_por_padrao(self):
        assert circuit.allows("brapi") is True
        assert circuit.status("brapi")["state"] == "fechado"

    def test_abre_apos_falhas_seguidas(self):
        for _ in range(circuit.FAILURE_THRESHOLD):
            circuit.record_failure("brapi", "timeout")

        assert circuit.allows("brapi") is False
        assert circuit.status("brapi")["state"] == "aberto"

    def test_sucesso_no_meio_zera_a_contagem(self):
        """Soluço de rede não pode abrir o disjuntor."""
        for _ in range(circuit.FAILURE_THRESHOLD - 1):
            circuit.record_failure("brapi", "timeout")
        circuit.record_success("brapi")
        circuit.record_failure("brapi", "timeout")

        assert circuit.allows("brapi") is True

    def test_depois_do_descanso_deixa_uma_tentativa_passar(self):
        agora = 1_000.0
        for _ in range(circuit.FAILURE_THRESHOLD):
            circuit.record_failure("brapi", "timeout", now=agora)

        assert circuit.allows("brapi", now=agora + 1) is False
        assert circuit.allows("brapi", now=agora + circuit.OPEN_SECONDS + 1) is True
        assert circuit.status("brapi", now=agora + circuit.OPEN_SECONDS + 1)["state"] == (
            "meia-abertura"
        )

    def test_uma_resposta_boa_isolada_nao_reabre_a_torneira(self):
        agora = 1_000.0
        for _ in range(circuit.FAILURE_THRESHOLD):
            circuit.record_failure("brapi", "timeout", now=agora)

        circuit.record_success("brapi")

        assert circuit.status("brapi", now=agora + 1)["state"] == "aberto"

    def test_sucessos_suficientes_fecham_o_circuito(self):
        for _ in range(circuit.FAILURE_THRESHOLD):
            circuit.record_failure("brapi", "timeout")
        for _ in range(circuit.RECOVERY_SUCCESSES):
            circuit.record_success("brapi")

        assert circuit.status("brapi")["state"] == "fechado"
        assert circuit.allows("brapi") is True

    def test_falhar_na_meia_abertura_recomeca_o_descanso(self):
        agora = 1_000.0
        for _ in range(circuit.FAILURE_THRESHOLD):
            circuit.record_failure("brapi", "timeout", now=agora)

        depois = agora + circuit.OPEN_SECONDS + 1
        circuit.record_failure("brapi", "timeout de novo", now=depois)

        assert circuit.allows("brapi", now=depois + 1) is False

    def test_o_estado_conta_quantas_chamadas_foram_evitadas(self):
        for _ in range(circuit.FAILURE_THRESHOLD):
            circuit.record_failure("brapi", "timeout")
        for _ in range(3):
            circuit.allows("brapi")

        assert circuit.status("brapi")["rejected_while_open"] == 3

    def test_provedores_sao_independentes(self):
        for _ in range(circuit.FAILURE_THRESHOLD):
            circuit.record_failure("brapi", "timeout")

        assert circuit.allows("bcb") is True


class TestSaudeDaFonte:
    def test_a_rota_de_saude_nao_varre_o_universo(self, client):
        """Quando a fonte caiu, disparar o scan é o que menos se quer fazer."""
        headers = make_auth_headers("u_source_health")

        corpo = client.get("/api/data-quality/source", headers=headers).json()

        assert corpo["circuit"]["state"] == "fechado"
        assert any(f["field"] == "price" for f in corpo["plausibility_ranges"])

    def test_a_saude_reflete_o_disjuntor_aberto(self, client):
        headers = make_auth_headers("u_source_open")
        for _ in range(circuit.FAILURE_THRESHOLD):
            circuit.record_failure("brapi", "HTTP 503")

        corpo = client.get("/api/data-quality/source", headers=headers).json()

        assert corpo["circuit"]["state"] == "aberto"
        assert corpo["circuit"]["last_failure"] == "HTTP 503"
        assert corpo["circuit"]["retry_in_seconds"] > 0
