import asyncio

from app.models import AssetType, Opportunity
from app.services import OpportunityService


class _Carteira:
    def __init__(self, prefs):
        self._prefs = prefs

    def get_preferences(self):
        return self._prefs

    def list_positions(self):
        return []


def _score_com(prefs, sector):
    service = OpportunityService()
    service.portfolio_repo = _Carteira(prefs)
    opp = Opportunity(
        ticker="PETR4",
        asset_type=AssetType.br_stock,
        verdict="HOLD",
        label="Dentro do preço justo",
        score=50.0,
        sector=sector,
    )

    async def _varredura():
        return [opp], 1

    service.scan_for_current_user = _varredura
    resposta = asyncio.run(service.get_opportunities())
    return resposta.items[0].score


def test_setor_preferido_em_portugues_casa_com_o_setor_da_fonte():
    assert _score_com({"preferred_sectors": ["Energia"]}, "Energy Minerals") == 53.0, (
        "a tela grava o setor em português e a fonte manda em inglês: sem traduzir, a "
        "preferência nunca pesava"
    )


def test_setor_gravado_em_ingles_continua_valendo():
    assert _score_com({"preferred_sectors": ["Energy Minerals"]}, "Energy Minerals") == 53.0, (
        "quem gravou o nome cru da fonte não pode perder a preferência"
    )


def test_setor_que_nao_e_o_do_ativo_nao_pesa():
    assert _score_com({"preferred_sectors": ["Financeiro"]}, "Energy Minerals") == 50.0
