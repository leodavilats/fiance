import httpx
import pytest

from app.collectors import circuit, universal
from app.core import cache


class _RespostaFalsa:
    def __init__(self, payload):
        self._payload = payload

    def raise_for_status(self):
        return None

    def json(self):
        return self._payload


def _balanco(end_date: str, patrimonio):
    return {"endDate": end_date, "shareholdersEquity": patrimonio, "totalLiab": 24091666000}


def _balanco_wege():
    return {
        "endDate": "2025-12-31",
        "shareholdersEquity": 18553364000,
        "totalAssets": 42645030000,
        "totalLiab": 24091666000,
        "loansAndFinancing": 3549314000,
        "loansAndFinancingInNationalCurrency": 1475622000,
        "loansAndFinancingInForeignCurrency": 2073692000,
        "longTermLoansAndFinancing": 1041507970,
        "longTermLoansAndFinancingInNationalCurrency": 394588000,
        "longTermLoansAndFinancingInForeignCurrency": 646920000,
        "debentures": 0,
        "leaseFinancing": 0,
        "longTermDebentures": 0,
        "longTermLeaseFinancing": 0,
        "providers": 2789346000,
        "taxObligations": 671111000,
        "socialAndLaborObligations": 820283000,
    }


def _resultado(end_date: str, receita, lucro):
    return {"endDate": end_date, "totalRevenue": receita, "netIncome": lucro}


@pytest.fixture()
def chamadas(monkeypatch):
    circuit.reset()
    registro = []

    def _get(url, params=None, timeout=None):
        registro.append({"url": url, "params": params or {}})
        return _RespostaFalsa({"results": [{"symbol": "WEGE3", "regularMarketPrice": 52.17}]})

    monkeypatch.setattr(httpx, "get", _get)
    monkeypatch.setattr(universal.cache, "get", lambda *a, **k: None)
    monkeypatch.setattr(universal.cache, "set", lambda *a, **k: None)
    monkeypatch.setattr(cache, "get", lambda *a, **k: None)
    monkeypatch.setattr(cache, "set", lambda *a, **k: None)
    return registro


class TestOsModulosSaoPedidos:
    def test_a_chamada_pede_os_modulos(self, chamadas):
        universal._brapi_raw("WEGE3")

        pedidos = chamadas[0]["params"].get("modules", "")

        assert "defaultKeyStatistics" in pedidos, (
            "sem este módulo não vêm bookValue nem priceToBook, e sem bookValue "
            "graham_fair_price devolve None para todo ativo — um método de preço justo inteiro"
        )
        assert "balanceSheetHistory" in pedidos
        assert "incomeStatementHistory" in pedidos


class TestOQueVemPronto:
    def test_valor_patrimonial_sai_do_modulo_e_nao_da_raiz(self):
        raw = {"defaultKeyStatistics": {"bookValue": 4.4936814, "priceToBook": 11.609634}}

        assert universal._estatistica(raw, "bookValue") == 4.4936814
        assert universal._estatistica(raw, "priceToBook") == 11.609634

    def test_margem_vem_como_razao_e_sai_em_percentual(self):
        raw = {"defaultKeyStatistics": {"profitMargins": 0.1662679}}

        margem = universal._ratio_to_pct(universal._estatistica(raw, "profitMargins"))

        assert margem == pytest.approx(16.63, abs=0.01)


class TestOQuePrecisaSerDerivado:
    def test_roe_sai_do_lucro_sobre_o_patrimonio(self):
        raw = {
            "balanceSheetHistory": [_balanco("2025-12-31", 18553364000)],
            "incomeStatementHistory": [_resultado("2025-12-31", 41093000000, 6254051000)],
        }

        assert universal._roe_do_balanco(raw) == pytest.approx(33.71, abs=0.01)

    def test_exercicios_diferentes_nao_viram_roe(self):
        raw = {
            "balanceSheetHistory": [_balanco("2025-12-31", 18553364000)],
            "incomeStatementHistory": [_resultado("2024-12-31", 38000000000, 5800000000)],
        }

        assert universal._roe_do_balanco(raw) is None, (
            "patrimônio de um ano com lucro de outro dá um ROE que não existiu em exercício "
            "nenhum; melhor não saber do que publicar um número inventado"
        )

    def test_patrimonio_negativo_nao_vira_roe(self):
        raw = {
            "balanceSheetHistory": [_balanco("2025-12-31", -1200000000)],
            "incomeStatementHistory": [_resultado("2025-12-31", 9000000000, 300000000)],
        }

        assert universal._roe_do_balanco(raw) is None, (
            "com patrimônio negativo a razão troca de sinal e uma empresa quebrada apareceria "
            "com ROE negativo modesto, que a régua lê como apenas fraca"
        )

    def test_crescimento_de_receita_compara_os_dois_ultimos_exercicios(self):
        raw = {
            "incomeStatementHistory": [
                _resultado("2025-12-31", 319462100000, 16781938000),
                _resultado("2024-12-31", 273505270000, 29171565000),
            ]
        }

        assert universal._crescimento_de_receita(raw) == pytest.approx(16.80, abs=0.01)

    def test_ordem_da_fonte_nao_inverte_o_crescimento(self):
        crescente = {
            "incomeStatementHistory": [
                _resultado("2024-12-31", 273505270000, 29171565000),
                _resultado("2025-12-31", 319462100000, 16781938000),
            ]
        }

        assert universal._crescimento_de_receita(crescente) == pytest.approx(16.80, abs=0.01), (
            "a fonte manda o mais recente primeiro hoje, e depender disso faria o sinal do "
            "crescimento se inverter em silêncio no dia em que ela mudar a ordem"
        )

    def test_um_exercicio_so_nao_da_crescimento(self):
        raw = {"incomeStatementHistory": [_resultado("2025-12-31", 319462100000, 16781938000)]}

        assert universal._crescimento_de_receita(raw) is None


class TestOEndividamentoEDividaQueCobraJuros:
    def test_entra_a_divida_financeira_e_nao_o_passivo_inteiro(self):
        raw = {"balanceSheetHistory": [_balanco_wege()]}

        assert universal._endividamento_do_balanco(raw) == pytest.approx(24.74, abs=0.01), (
            "pelo passivo inteiro a WEGE3 daria 129,85% e sairia como alavancagem moderada; "
            "fornecedor, imposto e obrigação trabalhista não são dívida que cobra juros"
        )

    def test_parcelas_por_moeda_nao_contam_duas_vezes(self):
        balanco = _balanco_wege()

        divida = universal._divida_financeira(balanco)

        assert divida == 3549314000 + 1041507970, (
            "`loansAndFinancing` já é a soma das parcelas em moeda nacional e estrangeira; "
            "somar as três infla a dívida em cima do dobro"
        )

    def test_balanco_de_banco_nao_vira_divida_zero(self):
        raw = {
            "balanceSheetHistory": [
                {
                    "endDate": "2025-12-31",
                    "shareholdersEquity": 180000000000,
                    "totalLiab": 2261575800000,
                    "thirdPartyDeposits": None,
                    "loansAndFinancing": None,
                    "longTermLoansAndFinancing": None,
                }
            ]
        }

        assert universal._endividamento_do_balanco(raw) is None, (
            "banco não preenche estas chaves, e somar ausência daria 0% — o produto diria "
            "'dívida muito baixa, empresa sólida' para toda instituição financeira"
        )

    def test_empresa_sem_divida_da_zero_e_nao_ausencia(self):
        balanco = _balanco_wege() | {
            "loansAndFinancing": 0,
            "longTermLoansAndFinancing": 0,
        }

        assert universal._endividamento_do_balanco({"balanceSheetHistory": [balanco]}) == 0.0, (
            "zero declarado é informação: quem não deve precisa aparecer como quem não deve, "
            "e não como quem não informou"
        )
