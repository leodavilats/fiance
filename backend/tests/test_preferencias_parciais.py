from tests.conftest import make_auth_headers

ROTA = "/api/v1/preferences"


def _salvar(client, headers, corpo):
    return client.put(ROTA, json=corpo, headers=headers)


def _ler(client, headers):
    return client.get(ROTA, headers=headers).json()


class TestSalvarUmCampoNaoApagaOsOutros:
    def test_salvar_categorias_depois_do_perfil_nao_derruba_o_perfil(self, client):
        headers = make_auth_headers("prefs_parciais_1")

        _salvar(client, headers, {"risk_profile": "conservative"})
        _salvar(client, headers, {"preferred_categories": ["fiis", "renda_fixa"]})

        prefs = _ler(client, headers)
        assert prefs["risk_profile"] == "conservative"
        assert prefs["preferred_categories"] == ["fiis", "renda_fixa"]

    def test_salvar_o_perfil_depois_das_categorias_nao_derruba_as_categorias(self, client):
        headers = make_auth_headers("prefs_parciais_2")

        _salvar(client, headers, {"preferred_categories": ["etfs"]})
        _salvar(client, headers, {"risk_profile": "aggressive"})

        prefs = _ler(client, headers)
        assert prefs["preferred_categories"] == ["etfs"]
        assert prefs["risk_profile"] == "aggressive"


class TestNullNoCorpoNaoQuebraNemApaga:
    def test_o_corpo_do_mobile_com_nulls_nao_derruba_a_requisicao(self, client):
        headers = make_auth_headers("prefs_nulls_1")

        _salvar(client, headers, {"risk_profile": "conservative"})

        resposta = _salvar(
            client,
            headers,
            {
                "passive_income_goal": None,
                "notify_price_alerts": None,
                "opportunities_frequency": None,
                "risk_profile": None,
                "preferred_categories": ["fiis"],
                "preferred_sectors": None,
                "excluded_tickers": None,
            },
        )

        assert resposta.status_code == 200, resposta.text

    def test_null_significa_nao_mexi_nisso(self, client):
        headers = make_auth_headers("prefs_nulls_2")

        _salvar(client, headers, {"risk_profile": "conservative"})
        _salvar(
            client,
            headers,
            {"risk_profile": None, "preferred_categories": ["fiis"]},
        )

        prefs = _ler(client, headers)
        assert prefs["risk_profile"] == "conservative"
        assert prefs["notify_price_alerts"] is True
        assert prefs["opportunities_frequency"] == "weekly"

    def test_a_meta_de_renda_passiva_ainda_pode_ser_limpa(self, client):
        headers = make_auth_headers("prefs_nulls_3")

        _salvar(client, headers, {"passive_income_goal": 3000.0})
        assert _ler(client, headers)["passive_income_goal"] == 3000.0

        _salvar(client, headers, {"passive_income_goal": None})
        assert _ler(client, headers)["passive_income_goal"] is None
