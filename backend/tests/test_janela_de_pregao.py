"""A janela em que vale gastar cota, e o que acontece fora dela."""

from datetime import datetime

import pytest

import app.services.opportunity_service as opp_mod
from app.collectors import universal
from app.core import cache
from app.core.brt import BRT
from app.core.pregao import em_pregao
from app.services import OpportunityService


def instante(dia: int, hora: int, minuto: int = 0) -> datetime:
    """Setembro de 2026: 7 é segunda, 11 é sexta, 12 sábado, 13 domingo."""
    return datetime(2026, 9, dia, hora, minuto, tzinfo=BRT)


class TestAJanela:
    @pytest.mark.parametrize(
        "dia,hora,minuto,aberto",
        [
            (7, 9, 59, False),
            (7, 10, 0, True),
            (9, 13, 0, True),
            (11, 17, 30, True),
            # O fim da janela é 18h30, e não o fechamento: o último preço assenta depois do
            # leilão, e balanço na B3 sai depois do pregão.
            (11, 18, 30, True),
            (11, 18, 31, False),
            (7, 3, 0, False),
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
        # Sexta 18h30 -> segunda 10h.
        fim_de_semana = 63.5 * 3600
        assert opp_mod._SCAN_STALE_TOLERANCE > fim_de_semana, (
            "com tolerância menor que o fim de semana o scan estoura no sábado e vai à rede, "
            "que é o que a janela existe para evitar"
        )
