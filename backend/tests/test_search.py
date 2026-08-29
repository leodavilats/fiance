from __future__ import annotations

import pytest

from app.services import search_service
from tests.conftest import make_auth_headers


def salvar_posicao(client, user_id: str, ticker: str = "PETR4"):
    return client.post(
        "/api/portfolio/position",
        json={"ticker": ticker, "quantity": 100, "avg_price": 30.0},
        headers=make_auth_headers(user_id),
    )


def salvar_rf(client, user_id: str, nome: str = "CDB Banco Inter"):
    return client.post(
        "/api/fixed-income",
        json={
            "nome": nome,
            "tipo": "cdb",
            "valor_investido": 10000,
            "taxa": 13.5,
            "tipo_taxa": "pos_fixado",
            "percentual_cdi": 110,
            "data_aplicacao": "2026-01-10",
            "liquidez": "no_vencimento",
        },
        headers=make_auth_headers(user_id),
    )


def grupos(corpo) -> dict:
    return {g["label"]: g["items"] for g in corpo["groups"]}


class TestOrdemDaResposta:
    def test_a_propria_posicao_vem_antes_do_ativo_do_mercado(self, client):
        uid = "u_busca_ordem"
        salvar_posicao(client, uid, "PETR4")

        corpo = client.get("/api/search?q=PETR", headers=make_auth_headers(uid)).json()
        rotulos = [g["label"] for g in corpo["groups"]]

        assert rotulos[0] == "Na sua carteira"
        assert rotulos.index("Na sua carteira") < rotulos.index("Ativos")

    def test_o_papel_da_carteira_nao_aparece_duas_vezes(self, client):
        uid = "u_busca_dup"
        salvar_posicao(client, uid, "PETR4")

        corpo = client.get("/api/search?q=PETR4", headers=make_auth_headers(uid)).json()
        por_grupo = grupos(corpo)

        em_ativos = [i["title"] for i in por_grupo.get("Ativos", [])]
        assert "PETR4" not in em_ativos

    def test_grupo_vazio_nao_aparece(self, client):
        uid = "u_busca_vazio_grupo"

        corpo = client.get("/api/search?q=metas", headers=make_auth_headers(uid)).json()

        assert all(g["items"] for g in corpo["groups"])


class TestFronteiraComOCliente:
    def test_o_servidor_nao_devolve_rota(self):
        hit = search_service.SearchHit(kind="position", title="PETR4", subtitle="", ref="PETR4")

        assert "route" not in hit.as_dict()

    def test_o_resultado_traz_o_identificador_para_o_cliente_montar_o_link(self, client):
        uid = "u_busca_ref"
        salvar_posicao(client, uid, "PETR4")

        corpo = client.get("/api/search?q=PETR4", headers=make_auth_headers(uid)).json()
        posicao = grupos(corpo)["Na sua carteira"][0]

        assert posicao["ref"] == "PETR4"

    def test_o_servidor_nao_inventa_destino_de_tela(self, client):
        corpo = client.get(
            "/api/search?q=provento", headers=make_auth_headers("u_busca_destino")
        ).json()

        assert all(g["label"] != "Ir para" for g in corpo["groups"])


class TestOQueEDaPessoa:
    def test_acha_renda_fixa_pelo_nome(self, client):
        uid = "u_busca_rf"
        assert salvar_rf(client, uid, "CDB Banco Inter").status_code in (200, 201)

        corpo = client.get("/api/search?q=inter", headers=make_auth_headers(uid)).json()

        assert any(i["kind"] == "fixed_income" for g in corpo["groups"] for i in g["items"])

    def test_acha_renda_fixa_ignorando_acento(self, client):
        uid = "u_busca_acento"
        salvar_rf(client, uid, "Tesouro Selic 2029")

        corpo = client.get("/api/search?q=tesouro", headers=make_auth_headers(uid)).json()

        assert any(i["title"].startswith("Tesouro") for g in corpo["groups"] for i in g["items"])

    def test_a_renda_fixa_e_identificada_pelo_id(self, client):
        uid = "u_busca_rf_id"
        criada = salvar_rf(client, uid, "CDB Duplicado").json()

        corpo = client.get("/api/search?q=duplicado", headers=make_auth_headers(uid)).json()
        achado = grupos(corpo)["Sua renda fixa"][0]

        assert achado["ref"] == str(criada["id"])

    def test_a_posicao_mostra_quanto_a_pessoa_tem(self, client):
        uid = "u_busca_quantidade"
        salvar_posicao(client, uid, "VALE3")

        corpo = client.get("/api/search?q=VALE", headers=make_auth_headers(uid)).json()
        posicao = grupos(corpo)["Na sua carteira"][0]

        assert "100" in posicao["subtitle"]

    def test_renda_fixa_oculta_nao_aparece(self, client):
        uid = "u_busca_oculta"
        criada = salvar_rf(client, uid, "CDB Escondido").json()
        client.put(
            f"/api/fixed-income/{criada['id']}",
            json={"oculto": True},
            headers=make_auth_headers(uid),
        )

        corpo = client.get("/api/search?q=escondido", headers=make_auth_headers(uid)).json()

        assert not any(i["kind"] == "fixed_income" for g in corpo["groups"] for i in g["items"])


class TestIsolamentoEntreContas:
    def test_a_busca_nao_alcanca_a_carteira_do_vizinho(self, client):
        salvar_posicao(client, "u_busca_dono", "ITUB4")
        salvar_rf(client, "u_busca_dono", "CDB Secreto")

        corpo = client.get(
            "/api/search?q=secreto", headers=make_auth_headers("u_busca_vizinho")
        ).json()

        assert corpo["total"] == 0

    def test_a_busca_exige_sessao(self, client):
        assert client.get("/api/search?q=petr").status_code == 401


class TestSilencio:
    def test_consulta_vazia_devolve_vazio_e_nao_o_catalogo(self, client):
        corpo = client.get("/api/search?q=", headers=make_auth_headers("u_busca_nada")).json()

        assert corpo["groups"] == []
        assert corpo["total"] == 0

    def test_so_espaco_tambem_e_vazio(self, client):
        corpo = client.get(
            "/api/search?q=%20%20", headers=make_auth_headers("u_busca_espaco")
        ).json()

        assert corpo["total"] == 0

    def test_termo_sem_resultado_devolve_lista_vazia_e_nao_erro(self, client):
        corpo = client.get(
            "/api/search?q=zzzzqqqq", headers=make_auth_headers("u_busca_semnada")
        ).json()

        assert corpo["total"] == 0


class TestTeto:
    def test_cada_grupo_tem_teto(self, client):
        uid = "u_busca_teto"
        for ticker in ("PETR4", "PETR3", "PETRA1", "PETRB2", "PETRC3", "PETRD4", "PETRE5"):
            salvar_posicao(client, uid, ticker)

        corpo = client.get("/api/search?q=PETR", headers=make_auth_headers(uid)).json()

        assert len(grupos(corpo)["Na sua carteira"]) <= search_service.GROUP_LIMIT


class TestDobramento:
    @pytest.mark.parametrize(
        ("entrada", "esperado"),
        [
            ("Tesouro Selic", "tesouro selic"),
            ("AÇÃO", "acao"),
            ("Provisão", "provisao"),
        ],
    )
    def test_dobra_caixa_e_acento(self, entrada, esperado):
        assert search_service.fold(entrada) == esperado
