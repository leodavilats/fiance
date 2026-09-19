from __future__ import annotations

from tests.conftest import make_auth_headers


def _com_carteira(client, user_id: str):
    headers = make_auth_headers(user_id)
    client.post(
        "/api/v1/portfolio/position",
        headers=headers,
        json={"ticker": "PETR4", "quantity": 1000, "avg_price": 30.0, "category": "acoes_br"},
    )
    return headers


class TestAMetaNaoDeclaradaSeDeclara:
    def test_sem_declarar_a_resposta_avisa_que_o_alvo_e_do_produto(self, client):
        headers = make_auth_headers("meta_nao_declarada")

        metas = client.get("/api/v1/goals", headers=headers).json()

        assert metas, "o padrão continua sendo oferecido como ponto de partida"
        assert all(m["declared"] is False for m in metas), (
            "sem esta bandeira a tela desenha 30/35/15/15/5 como se fosse escolha de quem olha"
        )

    def test_depois_de_declarar_a_bandeira_vira(self, client):
        headers = make_auth_headers("meta_declarada")

        client.put(
            "/api/v1/goals",
            headers=headers,
            json={"goals": [{"category": "acoes_br", "target_pct": 100.0}]},
        )
        metas = client.get("/api/v1/goals", headers=headers).json()

        assert all(m["declared"] is True for m in metas)


class TestNinguemJulgaContraMetaQueNinguemEscolheu:
    def test_sem_meta_declarada_a_composicao_nao_tem_alvo(self, client):
        headers = _com_carteira(client, "meta_sem_alvo")

        painel = client.get("/api/v1/dashboard", headers=headers).json()
        alocacoes = painel.get("allocations") or []

        assert alocacoes, "a composição continua sendo mostrada: ela é fato, não julgamento"
        assert all(a["target_pct"] is None for a in alocacoes)
        assert all(a["delta_pct"] is None for a in alocacoes), (
            "delta contra meta não declarada é a diferença para um objetivo alheio"
        )

    def test_sem_meta_declarada_nao_ha_alerta_de_rebalanceamento(self, client):
        headers = _com_carteira(client, "meta_sem_alerta")

        painel = client.get("/api/v1/dashboard", headers=headers).json()
        alertas = painel.get("alerts") or []

        assert not [a for a in alertas if a.get("kind") == "rebalance"], (
            "uma carteira 100% em ações disparava 'abaixo da meta' contra os 30% de renda fixa "
            "que o produto sugeriu sozinho"
        )

    def test_com_meta_declarada_o_julgamento_volta(self, client):
        headers = _com_carteira(client, "meta_com_alvo")
        client.put(
            "/api/v1/goals",
            headers=headers,
            json={
                "goals": [
                    {"category": "acoes_br", "target_pct": 50.0},
                    {"category": "renda_fixa", "target_pct": 50.0},
                ]
            },
        )

        painel = client.get("/api/v1/dashboard", headers=headers).json()
        alocacoes = painel.get("allocations") or []
        acoes = next(a for a in alocacoes if a["category"] == "acoes_br")

        assert acoes["target_pct"] == 50.0
        assert acoes["delta_pct"] is not None, (
            "quem declarou meta quer ser cobrado por ela — é o outro lado da mesma decisão"
        )
