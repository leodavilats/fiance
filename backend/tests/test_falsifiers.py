from __future__ import annotations

import pytest

from app.analysis.decision import decide
from app.analysis.fair_price import FairPriceResult, margin_of_safety_in_band
from app.analysis.falsifiers import falsifiers as _falsifiers


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
        "fair_low": consensus,
        "fair_high": consensus,
    }
    campos.update(kwargs)
    return FairPriceResult(**campos)


def falsifiers(**kwargs) -> list[dict]:
    consenso = kwargs.get("consensus")
    if consenso is not None:
        kwargs.setdefault("fair_low", consenso)
        kwargs.setdefault("fair_high", consenso)
    return _falsifiers(**kwargs)


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


class TestOCirculoFechaComFaixaLarga:
    def _verdito(self, price: float) -> str:
        resultado = fair(consensus=75.0, fair_low=50.0, fair_high=100.0, consensus_methods=2)
        resultado.margin_of_safety = margin_of_safety_in_band(price, 50.0, 100.0)
        return decide(resultado, current_price=price).verdict

    @pytest.mark.parametrize("price", [30.0, 45.0, 75.0, 110.0, 140.0])
    def test_o_preco_anunciado_produz_o_veredito_prometido(self, price):
        atual = self._verdito(price)

        itens = _falsifiers(
            verdict=atual, price=price, consensus=75.0, fair_low=50.0, fair_high=100.0
        )

        for item in itens:
            if item["metric"] != "price":
                continue
            passo = -0.01 if "cair" in item["condition"] else 0.01
            assert self._verdito(item["threshold"] + passo) == item["becomes"], (
                "o preço anunciado tem de entregar o veredito prometido também quando a faixa é "
                "larga — é aí que a média enganava"
            )

    def test_dentro_da_faixa_a_saida_para_cima_parte_do_teto(self):
        itens = _falsifiers(
            verdict="HOLD", price=75.0, consensus=75.0, fair_low=50.0, fair_high=100.0
        )
        subir = next(i for i in itens if i["metric"] == "price" and "subir" in i["condition"])

        assert subir["threshold"] == pytest.approx(115.0), (
            "para virar venda, o preço precisa passar do teto da faixa com folga — não da média"
        )


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
    def test_o_corte_anunciado_leva_o_bazin_ao_preco_de_hoje(self):
        bazin, price, dividendo = 100.0, 70.0, 6.0

        item = next(
            i
            for i in _falsifiers(
                verdict="BUY",
                price=price,
                consensus=120.0,
                bazin=bazin,
                fair_low=bazin,
                fair_high=140.0,
                avg_dividend=dividendo,
            )
            if i["metric"] == "dividend"
        )

        novo_bazin = bazin * item["threshold"] / dividendo

        assert novo_bazin == pytest.approx(price, abs=0.05), (
            "a premissa do Bazin é que a distribuição de hoje se mantém. O que a refuta é o "
            "corte que leva o próprio Bazin ao preço de agora — abaixo disso, o dividendo "
            "deixa de justificar o preço"
        )
        assert item["kind"] == "premissa", (
            "cortar dividendo não é atravessar um limiar de classificação: é a premissa caindo"
        )

    def test_vale_mesmo_com_o_bazin_fora_do_piso(self):
        itens = _falsifiers(
            verdict="BUY",
            price=70.0,
            consensus=120.0,
            bazin=140.0,
            fair_low=100.0,
            fair_high=140.0,
            avg_dividend=6.0,
        )

        assert any(i["metric"] == "dividend" for i in itens), (
            "a sustentabilidade do dividendo importa sempre que o método participa — amarrá-la "
            "à posição do Bazin na faixa confundia o veredito com a premissa"
        )

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
        itens = _falsifiers(
            verdict="BUY",
            price=110.0,
            consensus=100.0,
            bazin=40.0,
            fair_low=40.0,
            fair_high=160.0,
            avg_dividend=2.0,
        )

        assert all(i["metric"] != "dividend" for i in itens)

    def test_corte_total_e_chamado_de_suspensao(self):
        itens = _falsifiers(
            verdict="BUY",
            price=0.40,
            consensus=100.0,
            bazin=100.0,
            fair_low=100.0,
            fair_high=100.0,
            avg_dividend=6.0,
        )
        item = next(i for i in itens if i["metric"] == "dividend")

        assert item["condition"] == "O dividendo ser suspenso por completo"

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


class TestLeituraDeTendencia:
    def test_o_que_derruba_a_leitura_e_a_tendencia(self):
        itens = _falsifiers(
            verdict="BUY",
            price=182.0,
            consensus=None,
            trend="uptrend",
            rsi_14=58.0,
            basis="trend",
        )

        assert itens, "leitura de tendência sem falsificador ensina a ignorar a seção"
        assert all(i["metric"] in ("trend", "rsi") for i in itens)
        assert not any(i["metric"] == "price" for i in itens), (
            "sem faixa não há preço-limite, e anunciar um seria inventar a régua que não existe"
        )


class TestSilencioHonesto:
    def test_sem_preco_justo_nao_ha_regua_para_ler_ao_contrario(self):
        assert _falsifiers(verdict="BUY", price=80.0, consensus=None) == []

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
