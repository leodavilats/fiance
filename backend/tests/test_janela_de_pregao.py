from datetime import UTC, date, datetime

import pytest

import app.services.opportunity_service as opp_mod
from app.collectors import universal
from app.core import cache
from app.core.brt import BRT
from app.core.pregao import dias_sem_pregao, em_pregao, ha_pregao, pascoa
from app.services import OpportunityService


def instante(dia: int, hora: int, minuto: int = 0) -> datetime:
    return datetime(2026, 9, dia, hora, minuto, tzinfo=BRT)


class TestAJanela:
    @pytest.mark.parametrize(
        "dia,hora,minuto,aberto",
        [
            (8, 9, 59, False),
            (8, 10, 0, True),
            (9, 13, 0, True),
            (11, 17, 30, True),
            (11, 18, 30, True),
            (11, 18, 31, False),
            (8, 3, 0, False),
            (12, 13, 0, False),
            (13, 13, 0, False),
        ],
    )
    def test_a_janela_e_o_pregao_mais_o_fechamento(self, dia, hora, minuto, aberto):
        assert em_pregao(instante(dia, hora, minuto)) is aberto

    def test_o_instante_e_parametro(self):
        assert em_pregao(instante(12, 13)) is False, (
            "regra de horário sem injeção do instante é suíte que passa às 14h e falha às 3h"
        )


def momento(ano: int, mes: int, dia: int, hora: int = 14, minuto: int = 0) -> datetime:
    return datetime(ano, mes, dia, hora, minuto, tzinfo=BRT)


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
            "11 datas fixas e 4 móveis; um dia a mais é um pregão perdido na varredura"
        )


class TestAJanelaNoFeriado:
    @pytest.mark.parametrize(
        "instante_",
        [
            momento(2026, 2, 16, 10),
            momento(2026, 2, 17, 15),
            momento(2026, 4, 3, 12),
            momento(2026, 6, 4, 18, 30),
            momento(2027, 2, 9, 11),
            momento(2027, 3, 26, 14),
        ],
    )
    def test_no_feriado_a_janela_nao_abre(self, instante_):
        assert em_pregao(instante_) is False, (
            "no feriado a varredura do universo gastaria cota relendo o fechamento da véspera"
        )

    @pytest.mark.parametrize(
        "hora,minuto,aberto",
        [(10, 0, False), (12, 59, False), (13, 0, True), (18, 30, True), (18, 31, False)],
    )
    def test_na_quarta_de_cinzas_a_janela_abre_as_13h(self, hora, minuto, aberto):
        assert em_pregao(momento(2026, 2, 18, hora, minuto)) is aberto, (
            "na Quarta-feira de Cinzas o pregão começa às 13h; antes disso não há preço novo"
        )

    def test_a_quarta_de_cinzas_de_2027_tambem_abre_as_13h(self):
        assert em_pregao(momento(2027, 2, 10, 11)) is False
        assert em_pregao(momento(2027, 2, 10, 13)) is True

    def test_uma_quarta_comum_abre_as_10h(self):
        assert em_pregao(momento(2026, 2, 25, 10)) is True, (
            "a abertura tardia é só da Quarta-feira de Cinzas"
        )

    def test_na_vespera_do_feriado_a_janela_funciona(self):
        assert em_pregao(momento(2026, 4, 2, 14)) is True

    def test_o_instante_em_utc_e_lido_no_fuso_brasileiro(self):
        assert em_pregao(datetime(2026, 4, 2, 23, 0, tzinfo=UTC)) is False, (
            "23h UTC são 20h em Brasília: a janela já fechou"
        )
        assert em_pregao(datetime(2026, 4, 2, 21, 0, tzinfo=UTC)) is True, (
            "21h UTC são 18h em Brasília: lido como hora local, o fechamento sairia da janela"
        )
        assert em_pregao(datetime(2026, 4, 3, 16, 0, tzinfo=UTC)) is False, (
            "16h UTC são 13h em Brasília, mas o dia é Sexta-feira Santa"
        )


class TestOPrazoSegueOMercado:
    def test_no_pregao_o_preco_vence_rapido(self, monkeypatch):
        monkeypatch.setattr(universal, "em_pregao", lambda momento=None: True)
        assert universal.fund_ttl() == universal.FUND_TTL_PREGAO

    def test_fechado_o_preco_dura(self, monkeypatch):
        monkeypatch.setattr(universal, "em_pregao", lambda momento=None: False)
        assert universal.fund_ttl() == universal.FUND_TTL_FECHADO

    def test_o_prazo_de_pregao_e_menor(self):
        assert universal.FUND_TTL_PREGAO < universal.FUND_TTL_FECHADO


class TestForaDoPregaoNaoSeVarre:
    @pytest.fixture(autouse=True)
    def _limpa(self):
        opp_mod._refresh_task = None
        yield
        opp_mod._refresh_task = None

    @pytest.mark.anyio
    async def test_com_cache_a_varredura_nao_vai_a_rede(self, monkeypatch):
        service = OpportunityService()
        await service._scan_market()

        monkeypatch.setattr(opp_mod, "em_pregao", lambda momento=None: False)

        buscas = {"n": 0}

        async def contando(self, symbol):
            buscas["n"] += 1
            return None

        monkeypatch.setattr(OpportunityService, "_fetch_market_record", contando)

        vencido = cache.get(opp_mod._SCAN_CACHE_KEY)
        monkeypatch.setattr(opp_mod.cache, "get_with_age", lambda key: (vencido, 7200.0))

        registros, _ = await service._refresh_market()

        assert buscas["n"] == 0, "fora do pregão a varredura serve o cache em vez de buscar"
        assert registros, "e o que ela serve não é vazio"

    @pytest.mark.anyio
    async def test_sem_cache_nenhum_o_portao_nao_fecha(self, monkeypatch):
        service = OpportunityService()

        monkeypatch.setattr(opp_mod, "em_pregao", lambda momento=None: False)
        monkeypatch.setattr(opp_mod.cache, "get_with_age", lambda key: (None, None))

        buscas = {"n": 0}
        original = OpportunityService._fetch_market_record

        async def contando(self, symbol):
            buscas["n"] += 1
            return await original(self, symbol)

        monkeypatch.setattr(OpportunityService, "_fetch_market_record", contando)

        await service._refresh_market()

        assert buscas["n"] > 0, (
            "um deploy no sábado deixaria o Descobrir vazio até segunda: sem nada para servir, "
            "o portão não fecha"
        )

    def test_a_tolerancia_atravessa_o_fim_de_semana(self):
        fim_de_semana = 63.5 * 3600
        assert opp_mod._SCAN_STALE_TOLERANCE > fim_de_semana, (
            "com tolerância menor que o fim de semana o scan estoura no sábado e vai à rede, "
            "que é o que a janela existe para evitar"
        )
