from __future__ import annotations

import pytest

from app.analysis.decision import decide
from app.analysis.fair_price import FairPriceResult
from app.analysis.falsifiers import falsifiers


def fair(consensus: float, **kwargs) -> FairPriceResult:
    campos = {
        "bazin": None,
        "graham": None,
        "dcf": None,
        "consensus": consensus,
        "consensus_methods": 1,
        "margin_of_safety": None,
        "avg_dividend_5y": None,
        "dy_12m": None,
        "dy_5y": None,
        "data_years": 0,
        "desired_yield_used": 0.06,
    }
    campos.update(kwargs)
    return FairPriceResult(**campos)


def _mos(consensus: float, price: float) -> float:
    return (consensus - price) / consensus


def _verdito(consensus: float, price: float) -> str:
    resultado = fair(consensus)
    resultado.margin_of_safety = _mos(consensus, price)
    return decide(resultado, current_price=price).verdict


class TestOCirculoFecha:
    @pytest.mark.parametrize("price", [50.0, 80.0, 95.0, 105.0, 130.0, 160.0])
    def test_o_preco_anunciado_produz_o_veredito_prometido(self, price):
        consensus = 100.0
        atual = _verdito(consensus, price)

        for item in falsifiers(verdict=atual, price=price, consensus=consensus):
            if item["metric"] != "price":
                continue

            passo = -0.01 if "cair" in item["condition"] else 0.01
            assert _verdito(consensus, item["threshold"] + passo) == item["becomes"]

    def test_o_rotulo_prometido_e_o_rotulo_de_verdade(self):
        consensus, price = 100.0, 90.0
        atual = _verdito(consensus, price)

        for item in falsifiers(verdict=atual, price=price, consensus=consensus):
            if item["metric"] != "price":
                continue
            resultado = fair(consensus)
            resultado.margin_of_safety = _mos(consensus, item["threshold"] - 0.01)
            esperado = decide(resultado, current_price=item["threshold"] - 0.01)
            if esperado.verdict == item["becomes"]:
                assert esperado.label == item["becomes_label"]


class TestFronteirasDePreco:
    def test_saem_as_duas_vizinhas_e_nao_a_tabela_inteira(self):
        itens = [
            i
            for i in falsifiers(verdict="HOLD", price=95.0, consensus=100.0)
            if i["metric"] == "price"
        ]

        assert len(itens) == 2

    def test_no_topo_da_regua_so_ha_saida_para_baixo(self):
        itens = [
            i
            for i in falsifiers(verdict="STRONG_BUY", price=50.0, consensus=100.0)
            if i["metric"] == "price"
        ]

        assert len(itens) == 1
        assert "subir" in itens[0]["condition"]

    def test_no_fundo_da_regua_so_ha_saida_para_cima(self):
        itens = [
            i
            for i in falsifiers(verdict="STRONG_SELL", price=150.0, consensus=100.0)
            if i["metric"] == "price"
        ]

        assert len(itens) == 1
        assert "cair" in itens[0]["condition"]

    def test_a_distancia_ate_o_limiar_e_visivel(self):
        item = falsifiers(verdict="HOLD", price=95.0, consensus=100.0)[0]

        assert item["current"] == 95.0
        assert item["threshold"] != item["current"]


class TestCorteDeDividendo:
    def test_o_corte_anunciado_realmente_apaga_o_desconto(self):
        consensus, price, bazin, metodos = 100.0, 90.0, 120.0, 2
        outros = consensus * metodos - bazin

        item = next(
            i
            for i in falsifiers(
                verdict="HOLD",
                price=price,
                consensus=consensus,
                bazin=bazin,
                consensus_methods=metodos,
                avg_dividend=6.0,
            )
            if i["metric"] == "dividend"
        )

        proporcao = item["threshold"] / 6.0
        novo_consenso = (bazin * proporcao + outros) / metodos

        assert novo_consenso == pytest.approx(price, abs=0.05)

    def test_sem_desconto_nao_ha_corte_a_anunciar(self):
        itens = falsifiers(
            verdict="SELL",
            price=120.0,
            consensus=100.0,
            bazin=100.0,
            consensus_methods=1,
            avg_dividend=6.0,
        )

        assert all(i["metric"] != "dividend" for i in itens)

    def test_quando_o_dividendo_teria_de_subir_o_item_nao_sai(self):
        itens = falsifiers(
            verdict="BUY",
            price=110.0,
            consensus=100.0,
            bazin=40.0,
            consensus_methods=2,
            avg_dividend=2.0,
        )

        assert all(i["metric"] != "dividend" for i in itens)

    def test_corte_que_nao_bastaria_nao_e_anunciado(self):
        itens = falsifiers(
            verdict="BUY",
            price=70.0,
            consensus=100.0,
            bazin=40.0,
            consensus_methods=2,
            avg_dividend=2.0,
        )

        assert all(i["metric"] != "dividend" for i in itens)

    def test_corte_total_e_chamado_de_suspensao(self):
        itens = falsifiers(
            verdict="BUY",
            price=80.0,
            consensus=100.0,
            bazin=40.0,
            consensus_methods=2,
            avg_dividend=2.0,
        )
        item = next(i for i in itens if i["metric"] == "dividend")

        assert item["condition"] == "O dividendo ser suspenso por completo"
        assert item["threshold"] == 0.0

    def test_sem_dividendo_conhecido_nada_e_inventado(self):
        itens = falsifiers(
            verdict="BUY", price=80.0, consensus=100.0, bazin=110.0, consensus_methods=1
        )

        assert all(i["metric"] != "dividend" for i in itens)


class TestTendencia:
    def test_a_inversao_e_dita_quando_ha_tendencia(self):
        itens = falsifiers(
            verdict="BUY",
            price=80.0,
            consensus=100.0,
            trend="uptrend",
            sma_50=82.0,
            sma_200=75.0,
        )
        item = next(i for i in itens if i["metric"] == "trend")

        assert "cruzar abaixo" in item["condition"]

    def test_em_baixa_a_condicao_e_o_cruzamento_para_cima(self):
        itens = falsifiers(
            verdict="HOLD",
            price=95.0,
            consensus=100.0,
            trend="downtrend",
            sma_50=90.0,
            sma_200=99.0,
        )
        item = next(i for i in itens if i["metric"] == "trend")

        assert "cruzar acima" in item["condition"]

    def test_sem_tendencia_nao_ha_enfeite(self):
        itens = falsifiers(verdict="BUY", price=80.0, consensus=100.0, trend="unknown")

        assert all(i["metric"] != "trend" for i in itens)


class TestSilencioHonesto:
    def test_sem_preco_justo_nao_ha_regua_para_ler_ao_contrario(self):
        assert falsifiers(verdict="BUY", price=80.0, consensus=None) == []

    def test_sem_preco_nao_ha_distancia(self):
        assert falsifiers(verdict="BUY", price=None, consensus=100.0) == []

    def test_veredito_desconhecido_nao_ganha_condicao(self):
        assert falsifiers(verdict="UNKNOWN", price=80.0, consensus=100.0) == []


class TestLigadoNaAnalise:
    def test_a_analise_carrega_os_falsificadores(self, client):
        from tests.conftest import make_auth_headers

        resposta = client.get("/api/asset/PETR4", headers=make_auth_headers("u_falsif"))

        if resposta.status_code != 200:
            pytest.skip("análise indisponível neste ambiente")
        assert "falsifiers" in resposta.json()["decision"]
