from datetime import UTC, date, datetime

import pytest

import app.services.opportunity_service as opp_mod
from app.collectors import circuit, mercado, universal
from app.core import cache
from app.core.brt import BRT
from app.core.pregao import (
    dias_sem_pregao,
    ha_pregao,
    pascoa,
    proxima_carga,
    ultimo_pregao_carregado,
)
from app.services import OpportunityService


def momento(
    ano: int, mes: int, dia: int, hora: int = 14, minuto: int = 0, segundo: int = 0
) -> datetime:
    return datetime(ano, mes, dia, hora, minuto, segundo, tzinfo=BRT)


class TestOCalendarioDaB3:
    @pytest.mark.parametrize(
        "ano,domingo",
        [
            (2024, date(2024, 3, 31)),
            (2025, date(2025, 4, 20)),
            (2026, date(2026, 4, 5)),
            (2027, date(2027, 3, 28)),
        ],
    )
    def test_a_pascoa_sai_do_calculo(self, ano, domingo):
        assert pascoa(ano) == domingo

    @pytest.mark.parametrize(
        "dia,motivo",
        [
            (date(2026, 1, 1), "Confraternização Universal"),
            (date(2026, 2, 16), "segunda de Carnaval"),
            (date(2026, 2, 17), "terça de Carnaval"),
            (date(2026, 4, 3), "Sexta-feira Santa"),
            (date(2026, 4, 21), "Tiradentes"),
            (date(2026, 5, 1), "Dia do Trabalho"),
            (date(2026, 6, 4), "Corpus Christi"),
            (date(2026, 9, 7), "Independência"),
            (date(2026, 10, 12), "Nossa Senhora Aparecida"),
            (date(2026, 11, 2), "Finados"),
            (date(2026, 11, 20), "Consciência Negra, nacional desde a Lei 14.759/2023"),
            (date(2026, 12, 24), "véspera de Natal, sem pregão por calendário da B3"),
            (date(2026, 12, 25), "Natal"),
            (date(2026, 12, 31), "último dia do ano, sem pregão por calendário da B3"),
            (date(2027, 2, 8), "segunda de Carnaval"),
            (date(2027, 2, 9), "terça de Carnaval"),
            (date(2027, 3, 26), "Sexta-feira Santa"),
            (date(2027, 5, 27), "Corpus Christi"),
            (date(2027, 11, 2), "Finados"),
            (date(2027, 11, 15), "Proclamação da República"),
            (date(2027, 12, 24), "véspera de Natal, sem pregão por calendário da B3"),
            (date(2027, 12, 31), "último dia do ano, sem pregão por calendário da B3"),
        ],
    )
    def test_dia_sem_pregao_na_b3(self, dia, motivo):
        assert dia.weekday() < 5, f"{dia} precisa ser dia útil para o teste provar o feriado"
        assert not ha_pregao(dia), f"{dia} ({motivo}) não tem pregão"

    @pytest.mark.parametrize(
        "dia,motivo",
        [
            (date(2026, 1, 26), "segunda comum depois do aniversário de São Paulo"),
            (date(2027, 1, 25), "aniversário de São Paulo, municipal"),
            (date(2026, 7, 9), "Revolução Constitucionalista, estadual de São Paulo"),
            (date(2027, 7, 9), "Revolução Constitucionalista, estadual de São Paulo"),
            (date(2026, 2, 18), "Quarta-feira de Cinzas, pregão à tarde"),
            (date(2023, 11, 20), "Consciência Negra antes de ser nacional"),
        ],
    )
    def test_dia_com_pregao_na_b3(self, dia, motivo):
        assert ha_pregao(dia), (
            f"{dia} ({motivo}) tem pregão: a B3 funciona em feriado municipal e estadual de "
            "São Paulo, e o calendário não pode fechar um dia em que o mercado negocia"
        )

    def test_o_calendario_e_so_dos_dias_uteis_que_a_b3_fecha(self):
        assert len(dias_sem_pregao(2026)) == 15, (
            "11 datas fixas e 4 móveis; um dia a mais é um pregão que a base nunca vai ter"
        )


class TestACargaDaNoite:
    @pytest.mark.parametrize(
        "instante,pregao,motivo",
        [
            (momento(2026, 10, 23, 14), date(2026, 10, 22), "no pregão, a base tem o de ontem"),
            (momento(2026, 10, 23, 22, 59), date(2026, 10, 22), "a carga ainda não começou"),
            (momento(2026, 10, 23, 23), date(2026, 10, 23), "às 23h a sexta já é devida"),
            (momento(2026, 10, 24, 12), date(2026, 10, 23), "no sábado vale a sexta"),
            (momento(2026, 10, 26, 10), date(2026, 10, 23), "segunda de manhã ainda é a sexta"),
            (momento(2026, 11, 2, 23, 30), date(2026, 10, 30), "Finados não tem pregão a carregar"),
        ],
    )
    def test_o_pregao_que_a_base_ja_deveria_ter(self, instante, pregao, motivo):
        assert ultimo_pregao_carregado(instante) == pregao, motivo

    @pytest.mark.parametrize(
        "instante,carga",
        [
            (momento(2026, 10, 23, 22, 59), momento(2026, 10, 23, 23)),
            (momento(2026, 10, 23, 23), momento(2026, 10, 26, 23)),
            (momento(2026, 10, 24, 12), momento(2026, 10, 26, 23)),
            (momento(2026, 10, 30, 23, 30), momento(2026, 11, 3, 23)),
        ],
    )
    def test_a_proxima_carga_pula_fim_de_semana_e_feriado(self, instante, carga):
        assert proxima_carga(instante) == carga

    def test_o_instante_em_utc_e_lido_no_fuso_brasileiro(self):
        assert ultimo_pregao_carregado(datetime(2026, 10, 24, 2, 0, tzinfo=UTC)) == date(
            2026, 10, 23
        ), "2h UTC de sábado são 23h de sexta em Brasília: a carga da sexta já começou"


class TestAValidadeSegueABase:
    def test_base_em_dia_vale_ate_a_proxima_carga(self):
        assert universal.validade(date(2026, 10, 22), momento(2026, 10, 23, 14)) == 9 * 3600, (
            "às 14h de sexta, com a quinta na base, nada novo chega antes das 23h"
        )

    def test_o_fim_de_semana_inteiro_vale_o_mesmo_dado(self):
        assert universal.validade(date(2026, 10, 23), momento(2026, 10, 24, 23)) == 48 * 3600

    def test_base_atrasada_revalida_logo(self):
        assert universal.validade(date(2026, 10, 22), momento(2026, 10, 23, 23, 10)) == (
            universal.REVALIDAR
        ), "com a carga rodando, guardar o dado velho até amanhã atrasaria o fechamento um dia"

    def test_sem_saber_a_base_revalida_logo(self):
        assert universal.validade(None, momento(2026, 10, 23, 14)) == universal.REVALIDAR

    def test_perto_da_carga_o_prazo_nao_zera(self):
        assert universal.validade(date(2026, 10, 22), momento(2026, 10, 23, 22, 59, 59)) == 60


class TestOPregaoDaBase:
    @pytest.fixture(autouse=True)
    def _disjuntor_fechado(self):
        circuit.reset()
        yield
        circuit.reset()

    def test_a_resposta_fica_guardada(self, monkeypatch):
        chamadas = []

        def ler():
            chamadas.append(1)
            return date(2026, 10, 23)

        monkeypatch.setattr(mercado, "ler_pregao_da_base", ler)

        assert universal.pregao_da_base() == date(2026, 10, 23)
        assert universal.pregao_da_base() == date(2026, 10, 23)
        assert len(chamadas) == 1

    def test_falha_de_rede_nao_fica_guardada(self, monkeypatch):
        def falha():
            raise ConnectionError("fora do ar")

        monkeypatch.setattr(mercado, "ler_pregao_da_base", falha)
        assert universal.pregao_da_base() is None

        monkeypatch.setattr(mercado, "ler_pregao_da_base", lambda: date(2026, 10, 23))
        assert universal.pregao_da_base() == date(2026, 10, 23), (
            "a falha não pode ficar guardada como resposta, ou a base fica muda até o prazo vencer"
        )


class TestAVarredura:
    @pytest.fixture(autouse=True)
    def _limpa(self):
        opp_mod._refresh_task = None
        yield
        opp_mod._refresh_task = None

    @pytest.mark.anyio
    async def test_varredura_vencida_vai_a_rede_a_qualquer_hora(self, monkeypatch):
        service = OpportunityService()
        await service._scan_market()

        buscas = {"n": 0}
        original = OpportunityService._fetch_market_record

        async def contando(self, symbol):
            buscas["n"] += 1
            return await original(self, symbol)

        monkeypatch.setattr(OpportunityService, "_fetch_market_record", contando)
        vencido = cache.get(opp_mod._SCAN_CACHE_KEY)
        monkeypatch.setattr(opp_mod.cache, "get_with_age", lambda key: (vencido, 7200.0))

        await service._refresh_market()

        assert buscas["n"] > 0, (
            "a base vira às 23h, fora do pregão: um portão de horário seguraria o fechamento novo "
            "até a manhã seguinte"
        )

    @pytest.mark.anyio
    async def test_o_prazo_da_varredura_e_o_da_base(self, monkeypatch):
        prazos = []
        guardar = opp_mod.cache.set

        def anotando(key, value, ttl_seconds):
            if key == opp_mod._SCAN_CACHE_KEY:
                prazos.append(ttl_seconds)
            guardar(key, value, ttl_seconds)

        monkeypatch.setattr(opp_mod.cache, "set", anotando)
        monkeypatch.setattr(opp_mod, "validade_do_mercado", lambda: 4321)

        await OpportunityService()._refresh_market()

        assert prazos == [4321]
