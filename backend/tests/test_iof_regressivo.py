from __future__ import annotations

from datetime import date, timedelta

import pytest

from app.analysis.renda_fixa_analysis import DIAS_POR_MES, aliquota_iof, analyze_one
from app.models.enums import Liquidez, RendaFixaType, TaxType
from app.models.renda_fixa import RendaFixaAsset
from tests.conftest import make_auth_headers


def _ativo(**overrides) -> RendaFixaAsset:
    campos = {
        "tipo": RendaFixaType.cdb,
        "valor_investido": 10_000.0,
        "taxa": 12.0,
        "prazo_meses": 12,
        "tipo_taxa": TaxType.pre_fixado,
        "liquidez": Liquidez.diaria,
        "nome": "CDB diário",
    }
    campos.update(overrides)
    return RendaFixaAsset(**campos)


def _resgate_em(dias: int, **overrides):
    return analyze_one(
        _ativo(**overrides),
        prazo_meses_override=dias / DIAS_POR_MES,
        prazo_dias_override=dias,
    )


class TestTabelaDoDecreto6306:
    @pytest.mark.parametrize(
        ("dias", "aliquota"),
        [(1, 0.96), (2, 0.93), (3, 0.90), (15, 0.50), (22, 0.26), (28, 0.06), (29, 0.03)],
    )
    def test_aliquota_do_dia(self, dias, aliquota):
        assert aliquota_iof(dias) == pytest.approx(aliquota)

    def test_do_trigesimo_dia_em_diante_nao_ha_iof(self):
        assert aliquota_iof(30) == 0.0
        assert aliquota_iof(31) == 0.0
        assert aliquota_iof(720) == 0.0

    def test_resgate_no_mesmo_dia_usa_a_primeira_linha(self):
        assert aliquota_iof(0) == pytest.approx(0.96), (
            "no dia da aplicação não há rendimento, e a tabela começa no dia 1"
        )


class TestIofVemAntesDoIr:
    @pytest.mark.parametrize(("dias", "aliquota"), [(1, 0.96), (15, 0.50), (29, 0.03)])
    def test_a_base_do_ir_e_o_rendimento_menos_o_iof(self, dias, aliquota):
        resultado = _resgate_em(dias)
        rendimento = resultado.rendimento_bruto
        iof = rendimento * aliquota
        ir = (rendimento - iof) * 0.225

        assert resultado.iof.aliquota_pct == pytest.approx(aliquota * 100)
        assert resultado.iof.valor_iof == pytest.approx(iof, abs=0.01)
        assert resultado.ir.valor_ir == pytest.approx(ir, abs=0.01), (
            "o IR incide sobre o que o IOF deixou, não sobre o rendimento inteiro"
        )
        assert resultado.rendimento_liquido == pytest.approx(rendimento - iof - ir, abs=0.01)

    def test_no_dia_15_o_iof_leva_metade_e_o_ir_22_5_por_cento_do_resto(self):
        resultado = _resgate_em(15)
        rendimento = resultado.rendimento_bruto

        assert resultado.rendimento_liquido == pytest.approx(
            rendimento * 0.5 * (1 - 0.225), abs=0.01
        )

    def test_no_dia_30_so_resta_o_ir(self):
        resultado = _resgate_em(30)

        assert resultado.iof.valor_iof == 0.0
        assert resultado.ir.valor_ir == pytest.approx(resultado.rendimento_bruto * 0.225, abs=0.01)

    def test_prazo_longo_nao_tem_iof(self):
        resultado = analyze_one(_ativo(prazo_meses=12))

        assert resultado.iof.valor_iof == 0.0


class TestQuemPagaIof:
    @pytest.mark.parametrize(
        "tipo",
        [RendaFixaType.lci, RendaFixaType.lca, RendaFixaType.cri, RendaFixaType.cra],
    )
    def test_isento_de_ir_nao_e_isento_de_iof(self, tipo):
        resultado = _resgate_em(15, tipo=tipo)

        assert resultado.isento_ir is True
        assert resultado.ir.valor_ir == 0.0
        assert resultado.iof.valor_iof == pytest.approx(resultado.rendimento_bruto * 0.5, abs=0.01)
        assert resultado.rendimento_liquido == pytest.approx(
            resultado.rendimento_bruto * 0.5, abs=0.01
        )

    def test_tesouro_paga_iof(self):
        resultado = _resgate_em(
            10,
            tipo=RendaFixaType.tesouro_selic,
            tipo_taxa=TaxType.pos_fixado,
            percentual_cdi=100,
        )

        assert resultado.iof.aliquota_pct == pytest.approx(66.0)

    def test_isencao_declarada_de_ir_nao_tira_o_iof(self):
        resultado = _resgate_em(15, isento_ir=True)

        assert resultado.ir.valor_ir == 0.0
        assert resultado.iof.valor_iof > 0


class TestMarcacaoAMercado:
    HOJE = date(2026, 9, 25)

    def _posicao(self, client, monkeypatch, dias: int, usuario: str) -> dict:
        import app.services.fixed_income_service as fi_mod

        monkeypatch.setattr(fi_mod, "_today", lambda: self.HOJE)
        corpo = {
            "nome": "CDB liquidez diária",
            "tipo": "cdb",
            "valor_investido": 10_000.0,
            "taxa": 12.0,
            "tipo_taxa": "pre_fixado",
            "data_aplicacao": (self.HOJE - timedelta(days=dias)).isoformat(),
            "liquidez": "diaria",
        }
        resposta = client.post("/api/fixed-income", headers=make_auth_headers(usuario), json=corpo)
        assert resposta.status_code in (200, 201), resposta.text
        return resposta.json()

    @pytest.mark.parametrize(("dias", "aliquota"), [(1, 0.96), (15, 0.50), (29, 0.03), (30, 0.0)])
    def test_valor_atual_e_o_que_sobra_se_resgatasse_hoje(
        self, client, monkeypatch, dias, aliquota
    ):
        posicao = self._posicao(client, monkeypatch, dias, f"iof_mtm_{dias}")
        rendimento = 10_000.0 * (1.12 ** (dias / DIAS_POR_MES / 12) - 1)
        liquido = rendimento * (1 - aliquota) * (1 - 0.225)

        assert posicao["valor_atual"] == pytest.approx(10_000.0 + liquido, abs=0.01), (
            "a marcação a mercado é o líquido do resgate hoje, com IOF antes do IR"
        )
