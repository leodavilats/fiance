from tests.conftest import make_auth_headers


def _oportunidades(client, headers) -> list[dict]:
    resp = client.get(
        "/api/v1/opportunities",
        headers=headers,
        params={"include_held": "true", "page_size": 50},
    )
    assert resp.status_code == 200
    return resp.json()["items"]


def test_oportunidade_carrega_o_momento_da_leitura(client):
    itens = _oportunidades(client, make_auth_headers("idade_oportunidade"))

    assert itens, "esperava ao menos um ativo varrido"
    assert all("as_of" in o for o in itens), (
        "as_of tem de estar declarado no modelo de resposta — sem ele o campo some em silêncio"
    )

    carimbados = [o["as_of"] for o in itens if o["as_of"]]
    assert carimbados, "nenhum ativo trouxe carimbo, e a tela não teria o que mostrar"
    assert all(c > 1_600_000_000 for c in carimbados), (
        "o carimbo é epoch em segundos, como o de /asset e o de /portfolio/evaluate"
    )


def test_posicao_avaliada_carrega_o_momento_da_leitura(client):
    headers = make_auth_headers("idade_posicao")

    resp = client.post(
        "/api/v1/portfolio/evaluate",
        headers=headers,
        json={"items": [{"ticker": "PETR4", "quantity": 100, "avg_price": 30.0}]},
    )
    assert resp.status_code == 200

    posicoes = resp.json()["positions"]
    assert posicoes
    assert all("as_of" in p for p in posicoes)


def test_ativo_sem_carimbo_devolve_nulo_e_nao_zero(client):
    itens = _oportunidades(client, make_auth_headers("idade_nula"))

    for o in itens:
        assert o["as_of"] is None or o["as_of"] > 0, (
            f"{o['ticker']} veio com as_of=0, que a tela renderiza como 1970"
        )
