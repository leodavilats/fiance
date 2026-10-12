from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo

import pytest

from app.collectors import circuit, universal
from app.collectors.universal import proventos_do_app, snapshot_do_pacote


def _ativo(**kw) -> dict:
    base = {
        "codigo": "TEST3",
        "tipo": "stock",
        "emissor": "TEST",
        "classe": "ON",
        "data": "2026-10-09",
        "preco": 20.0,
        "preco_anterior": 19.0,
        "maxima_52s": 25.0,
        "minima_52s": 15.0,
        "volume_medio": 1e7,
        "nome": "Teste",
        "setor": "Energia",
        "cnpj": "1",
        "acoes_ordinarias": 100_000_000,
        "acoes_preferenciais": 0,
        "valor_patrimonial_cota": None,
        "referencia_cota": None,
        "proventos_12m": 1.0,
    }
    base.update(kw)
    return base


def _resultado(tipo: str, fim: str, lucro: float, receita: float, versao: int = 1) -> dict:
    return {
        "tipo": tipo,
        "data_referencia": fim,
        "versao": versao,
        "fim_exercicio": fim,
        "receita": receita,
        "lucro_controladores": lucro,
    }


def _balanco(tipo: str, data: str, patrimonio: float, divida: float | None = 500.0) -> dict:
    return {
        "tipo": tipo,
        "data_referencia": data,
        "versao": 1,
        "patrimonio_controladores": patrimonio,
        "divida_bruta": divida,
    }


def _pacote(ativo: dict | None = None, irmaos=None, resultados=None, balancos=None) -> dict:
    ativo = ativo or _ativo()
    return {
        "ativo": ativo,
        "irmaos": irmaos
        if irmaos is not None
        else [
            {
                "codigo": ativo["codigo"],
                "classe": ativo["classe"],
                "preco": ativo["preco"],
                "volume_medio": ativo["volume_medio"],
            }
        ],  # fmt: skip
        "resultados": resultados
        if resultados is not None
        else [
            _resultado("DFP", "2024-12-31", 100.0, 1000.0),
            _resultado("DFP", "2025-12-31", 200.0, 1100.0),
            _resultado("ITR", "2025-06-30", 80.0, 500.0),
            _resultado("ITR", "2026-06-30", 120.0, 600.0),
        ],
        "balancos": balancos
        if balancos is not None
        else [_balanco("ITR", "2026-06-30", 1_000_000_000.0)],
    }


def _snap(pacote: dict, tipo: str = "br_stock"):
    return snapshot_do_pacote(pacote, pacote["ativo"]["codigo"], tipo)


class TestAcao:
    def test_lucro_de_doze_meses_soma_o_ano_e_tira_o_mesmo_ponto_do_anterior(self):
        snap = _snap(_pacote())

        assert snap.net_income_ttm == 240.0, "120 do semestre + 200 do ano anterior - 80"

    def test_lucro_de_fim_de_ano_e_o_proprio_anual(self):
        resultados = [_resultado("DFP", "2025-12-31", 200.0, 1100.0)]

        assert _snap(_pacote(resultados=resultados)).net_income_ttm == 200.0

    def test_sem_o_mesmo_ponto_do_ano_anterior_nao_ha_doze_meses(self):
        resultados = [
            _resultado("DFP", "2025-12-31", 200.0, 1100.0),
            _resultado("ITR", "2026-06-30", 120.0, 600.0),
        ]

        snap = _snap(_pacote(resultados=resultados))

        assert snap.net_income_ttm is None and snap.pe_ratio is None, (
            "somar o semestre ao ano inteiro sem descontar daria um lucro inventado"
        )

    def test_versao_reapresentada_vence_a_original(self):
        resultados = [
            _resultado("DFP", "2025-12-31", 200.0, 1100.0, versao=1),
            _resultado("DFP", "2025-12-31", 150.0, 1100.0, versao=2),
        ]

        assert _snap(_pacote(resultados=resultados)).net_income_ttm == 150.0

    def test_indices_saem_do_preco_das_acoes_e_do_balanco(self):
        snap = _snap(_pacote())

        assert snap.market_cap == 2_000_000_000.0
        assert snap.eps == pytest.approx(240.0 / 100_000_000)
        assert snap.book_value == pytest.approx(10.0)
        assert snap.pb_ratio == pytest.approx(2.0)
        assert snap.roe == pytest.approx(240.0 / 1e9 * 100, abs=1e-4)
        assert snap.dividend_yield == 5.0
        assert snap.change_percent_day == pytest.approx(5.2632, abs=1e-4)
        assert snap.revenue_growth == pytest.approx(10.0)

    def test_quantidade_declarada_em_milhares_e_corrigida(self):
        ativo = _ativo(acoes_ordinarias=100_000)

        snap = _snap(_pacote(ativo))

        assert snap.market_cap == 2_000_000_000.0, (
            "o Itaú declara 11 milhões de ações no ITR, que são 11 bilhões: o valor de mercado "
            "ficava abaixo de 2% do patrimônio"
        )
        assert snap.book_value == pytest.approx(10.0)

    def test_unit_vale_as_acoes_que_contem(self):
        unit = _ativo(codigo="TEST11", classe="UNT", preco=60.0, acoes_preferenciais=200_000_000)
        irmaos = [
            {"codigo": "TEST3", "classe": "ON", "preco": 20.0, "volume_medio": 1e6},
            {"codigo": "TEST4", "classe": "PN", "preco": 20.0, "volume_medio": 1e6},
            {"codigo": "TEST11", "classe": "UNT", "preco": 60.0, "volume_medio": 1e8},
        ]

        snap = _snap(_pacote(unit, irmaos=irmaos))

        assert snap.book_value == pytest.approx(3 * 1e9 / 300_000_000), "uma unit, três ações"
        assert snap.pb_ratio == pytest.approx(60.0 / (3 * 1e9 / 300_000_000))

    def test_valor_de_mercado_soma_cada_classe_pelo_seu_preco(self):
        ativo = _ativo(codigo="TEST4", classe="PN", acoes_preferenciais=50_000_000)
        irmaos = [
            {"codigo": "TEST3", "classe": "ON", "preco": 22.0, "volume_medio": 1e6},
            {"codigo": "TEST4", "classe": "PN", "preco": 20.0, "volume_medio": 1e7},
        ]

        assert _snap(_pacote(ativo, irmaos=irmaos)).market_cap == 22.0 * 1e8 + 20.0 * 5e7

    def test_sem_balanco_nao_ha_indice(self):
        snap = _snap(_pacote(resultados=[], balancos=[]))

        assert snap.price == 20.0
        assert snap.pe_ratio is None and snap.pb_ratio is None and snap.roe is None

    def test_a_idade_e_a_do_fechamento_do_pregao(self):
        snap = _snap(_pacote())

        fechamento = datetime(2026, 10, 9, 18, 0, tzinfo=ZoneInfo("America/Sao_Paulo"))
        assert snap.as_of == fechamento.timestamp(), "o app carimba a idade do preço com isto"
        assert snap.source == "b3"


class TestFundo:
    def test_fii_tem_p_vp_pelo_valor_patrimonial_da_cota(self):
        fii = _ativo(
            codigo="TEST11", tipo="fii", classe="CI", preco=100.0, valor_patrimonial_cota=125.0,
            cnpj=None, acoes_ordinarias=None, proventos_12m=10.0,
        )  # fmt: skip

        snap = _snap({"ativo": fii, "irmaos": [], "resultados": [], "balancos": []}, "fii")

        assert snap.pb_ratio == 0.8 and snap.book_value == 125.0
        assert snap.dividend_yield == 10.0
        assert snap.pe_ratio is None

    def test_etf_sem_provento_nao_tem_yield(self):
        etf = _ativo(codigo="BOVA11", tipo="etf", classe="CI", proventos_12m=None, cnpj=None)

        snap = _snap({"ativo": etf, "irmaos": [], "resultados": [], "balancos": []}, "etf")

        assert snap.dividend_yield is None, "ausência não vira zero"

    def test_preco_implausivel_recusa_o_retrato(self):
        absurdo = _ativo(preco=1e9)

        assert _snap(_pacote(absurdo)) is None


class TestProventos:
    def test_a_data_e_a_do_pagamento_e_a_data_com_vai_junto(self):
        linhas = [
            {"data_com": "2026-03-01", "data_pagamento": "2026-03-20", "valor": 1.0},
            {"data_com": "2020-03-01", "data_pagamento": None, "valor": 0.5},
        ]

        assert proventos_do_app(linhas) == [
            {"date": "2020-03-01", "value": 0.5, "ex_date": "2020-03-01"},
            {"date": "2026-03-20", "value": 1.0, "ex_date": "2026-03-01"},
        ]


class TestLeituraDaBase:
    @pytest.fixture(autouse=True)
    def _disjuntor(self):
        circuit.reset()
        yield
        circuit.reset()

    def test_ticker_que_a_base_nao_tem_fica_lembrado_como_ausente(self, monkeypatch):
        chamadas = []

        def ler(codigos):
            chamadas.append(codigos)
            return {}

        monkeypatch.setattr(universal.mercado, "ler_pacotes", ler)

        assert universal._pacote("XPTO3") == {}
        assert universal._pacote("XPTO3") == {}
        assert len(chamadas) == 1, "a ausência fica em cache e não volta à base a cada varredura"

    def test_falha_da_base_nao_carimba_ausencia(self, monkeypatch):
        def fora(codigos):
            raise ConnectionError("fora do ar")

        monkeypatch.setattr(universal.mercado, "ler_pacotes", fora)

        assert universal._pacote("PETR4") == {}
        assert universal._ler_raw("PETR4") is None, "falha de rede não vira ausência"

    def test_varredura_le_o_lote_numa_consulta(self, monkeypatch):
        chamadas = []

        def ler(codigos):
            chamadas.append(list(codigos))
            return {c: _pacote(_ativo(codigo=c)) for c in codigos}

        monkeypatch.setattr(universal.mercado, "ler_pacotes", ler)

        assert universal.prefetch(["AAAA3", "BBBB3", "CCCC3"]) == 1
        assert chamadas == [["AAAA3", "BBBB3", "CCCC3"]]
        assert universal.prefetch(["AAAA3"]) == 0, "o que está em cache não volta à base"
