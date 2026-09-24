import pytest

from app.collectors import rates


class _Resposta:
    def __init__(self, pontos):
        self._pontos = pontos

    def raise_for_status(self):
        return None

    def json(self):
        return self._pontos


class _Cliente:
    def __init__(self, valores):
        self.valores = valores
        self.urls = []

    def get(self, url):
        self.urls.append(url)
        return _Resposta([{"data": "01/01/2020", "valor": str(v)} for v in self.valores])


def test_a_media_cobre_o_ciclo_inteiro():
    cliente = _Cliente([2.0] * 60 + [14.0] * 60)

    assert rates._selic_media(cliente) == pytest.approx(8.0), (
        "custo de capital é taxa de longo prazo: dez anos atravessam mais de um ciclo do Copom, "
        "e a média de dois anos no pico dava 19% de taxa e quase toda ação cara"
    )
    assert "bcdata.sgs.4189" in cliente.urls[0]


def test_serie_curta_demais_nao_vira_media():
    assert rates._selic_media(_Cliente([10.0] * 12)) is None


def test_valor_implausivel_fica_de_fora():
    cliente = _Cliente([10.0] * 119 + [900.0])

    assert rates._selic_media(cliente) == pytest.approx(10.0)
