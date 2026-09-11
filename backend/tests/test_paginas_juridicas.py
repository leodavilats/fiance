from __future__ import annotations

import pytest

PAGINAS = ("/termos", "/privacidade", "/aviso-cvm")


class TestAbremSozinhas:
    @pytest.mark.parametrize("caminho", PAGINAS)
    def test_responde_sem_token_e_como_html(self, client, caminho):
        resposta = client.get(caminho)

        assert resposta.status_code == 200, (
            f"{caminho} precisa abrir sem sessão: é a URL que a loja exige e que o aplicativo "
            "linka de dentro das configurações"
        )
        assert resposta.headers["content-type"].startswith("text/html")

    @pytest.mark.parametrize("caminho", PAGINAS)
    def test_nao_depende_de_javascript_nem_de_asset_externo(self, client, caminho):
        corpo = client.get(caminho).text

        assert "<script" not in corpo, "página jurídica que só monta com JS abre em branco no robô"
        assert "http://" not in corpo and "https://" not in corpo, (
            "asset externo numa página jurídica é uma dependência a mais para ela abrir"
        )

    @pytest.mark.parametrize("caminho", PAGINAS)
    def test_os_links_entre_elas_existem(self, client, caminho):
        corpo = client.get(caminho).text

        for destino in PAGINAS:
            if f'href="{destino}"' in corpo:
                assert client.get(destino).status_code == 200


class TestOTextoNaoRepeteOQueOProdutoAfirma:
    def test_o_aviso_cvm_nomeia_a_postura_em_vigor(self, client):
        corpo = client.get("/aviso-cvm").text

        assert "nível 2" in corpo, (
            "o nível de afirmação é configuração, e a página o lê do servidor — uma segunda "
            "cópia da frase envelheceria justamente onde ela é lida"
        )
        assert "Não é recomendação de compra ou venda" in corpo

    def test_a_minuta_se_declara_minuta(self, client):
        assert "Minuta" in client.get("/termos").text

    def test_a_privacidade_diz_como_apagar_a_conta(self, client):
        corpo = client.get("/privacidade").text

        assert "Apagar a conta" in corpo, (
            "a loja exige que a política diga como o dado é excluído, e a exclusão não fica "
            "atrás de plano"
        )
