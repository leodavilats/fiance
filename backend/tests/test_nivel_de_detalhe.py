from __future__ import annotations

from tests.conftest import make_auth_headers

ROTA = "/api/v1/preferences"


def test_o_nivel_de_detalhe_comeca_completo(client):
    headers = make_auth_headers("detalhe_user")

    assert client.get(ROTA, headers=headers).json()["detail_level"] == "completo", (
        "sem escolha declarada, a tela mostra o que mostra hoje: premissas, confirmação e "
        "indicadores"
    )


def test_a_pessoa_escolhe_o_nivel(client):
    headers = make_auth_headers("detalhe_user2")

    resposta = client.put(ROTA, headers=headers, json={"detail_level": "avancado"})

    assert resposta.status_code == 200, resposta.text
    assert client.get(ROTA, headers=headers).json()["detail_level"] == "avancado"


def test_nivel_fora_do_vocabulario_e_recusado(client):
    headers = make_auth_headers("detalhe_user3")

    assert client.put(ROTA, headers=headers, json={"detail_level": "compact"}).status_code == 422


def test_density_saiu_sem_consumidor(client):
    headers = make_auth_headers("detalhe_user4")

    assert "density" not in client.get(ROTA, headers=headers).json(), (
        "density era gravada e nenhuma tela a lia: vocabulário sem consumidor"
    )
