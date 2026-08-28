"""Projeção com faixa: nenhum número projetado sai sozinho.

Uma projeção a cinco anos é a multiplicação de três chutes. Apresentá-la como
``R$ 3.847,21`` empresta a essa pilha uma precisão de centavo que ela não tem —
e a pessoa decide quanto poupar em cima disso.
"""

from __future__ import annotations

import asyncio

import pytest
from pydantic import ValidationError

from app.analysis.scenarios import OPTIMISTIC_FACTOR, SCENARIOS, band
from app.models.projection import PassiveIncomeMonth, PassiveIncomeProjectionRequest
from app.services.projection_service import ProjectionService


class _CarteiraFalsa:
    """Uma posição só, preço e DY fixos — a conta a testar é a projeção."""

    def list_positions(self):
        return [{"ticker": "PETR4", "quantity": 1000.0}]


class _AtivoFalso:
    async def get_asset(self, ticker: str):
        class Snap:
            price = 30.0
            dividend_yield = 8.0

        return Snap()


class _RendaFixaFalsa:
    def as_portfolio_positions(self):
        return []


@pytest.fixture()
def servico():
    svc = ProjectionService()
    svc.portfolio_repo = _CarteiraFalsa()
    svc.asset_repo = _AtivoFalso()
    svc.fixed_income = _RendaFixaFalsa()
    return svc


def projetar(servico, **kwargs):
    req = PassiveIncomeProjectionRequest(**kwargs)
    return asyncio.run(servico.project_passive_income(req))


class TestNenhumNumeroSozinho:
    def test_o_modelo_recusa_um_mes_sem_faixa(self):
        """A faixa é obrigatória no schema, não uma convenção de quem monta.

        Com default, existiria um caminho em que o número sai sozinho — e é
        justamente esse caminho que a tela acabaria usando.
        """
        with pytest.raises(ValidationError):
            PassiveIncomeMonth(
                month="2027-01",
                portfolio_value=100.0,
                passive_income_monthly=1.0,
                passive_income_yearly=12.0,
                dividend_yield_avg=8.0,
            )

    def test_todo_mes_projetado_traz_piso_e_teto(self, servico):
        r = projetar(servico, monthly_contribution=500, months_ahead=24)

        for mes in r.projections:
            assert mes.passive_income_monthly_low <= mes.passive_income_monthly
            assert mes.passive_income_monthly <= mes.passive_income_monthly_high
            assert mes.portfolio_value_low <= mes.portfolio_value <= mes.portfolio_value_high

    def test_a_resposta_carrega_o_aviso(self, servico):
        r = projetar(servico, months_ahead=12)

        assert "não é previsão" in r.disclaimer

    def test_todo_numero_de_cenario_diz_de_qual_cenario_veio(self, servico):
        r = projetar(servico, months_ahead=6)

        for serie in r.scenarios:
            assert all(m.scenario == serie.code for m in serie.months)


class TestOsTresCenarios:
    def test_saem_os_tres_na_ordem_da_faixa(self, servico):
        r = projetar(servico, months_ahead=12)

        assert [s.code for s in r.scenarios] == ["conservador", "base", "otimista"]

    def test_cada_cenario_declara_a_premissa(self, servico):
        r = projetar(servico, months_ahead=12)

        assert all(len(s.rationale) > 20 for s in r.scenarios)

    def test_o_conservador_nao_depende_de_previsao_nenhuma(self, servico):
        """Zero crescimento: só o aporte trabalha. É o que a pessoa precisa
        conseguir suportar."""
        r = projetar(servico, monthly_contribution=1000, months_ahead=12)
        conservador = r.scenarios[0]

        assert conservador.portfolio_growth_rate == 0.0
        assert conservador.dividend_growth_rate == 0.0

    def test_o_conservador_ainda_cresce_porque_o_aporte_existe(self, servico):
        r = projetar(servico, monthly_contribution=1000, months_ahead=12)
        conservador = r.scenarios[0]

        assert conservador.final_portfolio_value > r.current_portfolio_value

    def test_sem_aporte_e_sem_reinvestir_o_conservador_fica_parado(self, servico):
        r = projetar(servico, monthly_contribution=0, reinvest_dividends=False, months_ahead=36)
        conservador = r.scenarios[0]

        assert conservador.final_portfolio_value == pytest.approx(r.current_portfolio_value)

    def test_o_otimista_estica_as_premissas_pelo_fator_declarado(self, servico):
        r = projetar(servico, portfolio_growth_rate=0.10, months_ahead=12)
        otimista = r.scenarios[2]

        assert otimista.portfolio_growth_rate == pytest.approx(0.10 * OPTIMISTIC_FACTOR)

    def test_o_base_e_exatamente_o_que_a_pessoa_pediu(self, servico):
        r = projetar(servico, portfolio_growth_rate=0.07, dividend_growth_rate=0.04)
        base = r.scenarios[1]

        assert base.portfolio_growth_rate == pytest.approx(0.07)
        assert base.dividend_growth_rate == pytest.approx(0.04)

    def test_a_faixa_e_larga_o_bastante_para_ser_honesta(self, servico):
        """Se piso e teto coincidissem, a faixa seria um enfeite em volta de um
        número único — o problema que ela existe para resolver."""
        r = projetar(servico, monthly_contribution=500, months_ahead=60)
        ultimo = r.projections[-1]

        assert ultimo.passive_income_monthly_high > ultimo.passive_income_monthly_low


class TestMetaComoFaixaDeDatas:
    def test_sem_meta_nao_ha_estimativa(self, servico):
        r = projetar(servico, months_ahead=12)

        assert r.target is None

    def test_a_meta_vira_faixa_e_nao_data_unica(self, servico):
        r = projetar(
            servico, monthly_contribution=3000, target_monthly_income=2500, months_ahead=120
        )

        assert r.target is not None
        assert r.target.earliest_months <= r.target.expected_months

    def test_o_cenario_que_nao_alcanca_e_dito_e_nao_omitido(self, servico):
        """Omitir o cenário que não chega faria a meta parecer garantida."""
        r = projetar(
            servico, monthly_contribution=0, target_monthly_income=999_999, months_ahead=24
        )

        assert r.target.latest_months is None
        assert r.target.reached_in_all_scenarios is False

    def test_quando_todos_alcancam_isso_tambem_e_dito(self, servico):
        r = projetar(
            servico, monthly_contribution=50_000, target_monthly_income=300, months_ahead=24
        )

        assert r.target.reached_in_all_scenarios is True


class TestFaixa:
    def test_faixa_vazia_nao_estoura(self):
        assert band([]) == (0.0, 0.0)

    def test_a_faixa_e_o_min_e_o_max(self):
        assert band([3.0, 1.0, 2.0]) == (1.0, 3.0)


class TestCatalogoDeCenarios:
    def test_sao_tres_e_o_conservador_vem_primeiro(self):
        assert len(SCENARIOS) == 3
        assert SCENARIOS[0].code == "conservador"
