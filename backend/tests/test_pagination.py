"""Paginação por cursor e versão da API.

As duas coisas andam juntas: paginar muda a forma da resposta, e mudar a forma
da resposta sem versionar o caminho só tem dois destinos ruins — quebrar cliente
publicado, ou nunca mais mudar nada.
"""

from __future__ import annotations

import pytest

from app.core.pagination import (
    DEFAULT_PAGE_SIZE,
    MAX_PAGE_SIZE,
    InvalidCursorError,
    clamp_limit,
    decode_cursor,
    encode_cursor,
    paginate,
    slice_after,
)
from app.main import API_VERSION
from tests.conftest import make_auth_headers


class TestCursor:
    def test_ida_e_volta_preserva_a_chave(self):
        assert decode_cursor(encode_cursor("2024-01-10", 42)) == ("2024-01-10", 42)

    def test_o_cursor_e_url_safe(self):
        cursor = encode_cursor("2024-01-10T00:00:00+00:00", 999999)

        assert "+" not in cursor
        assert "/" not in cursor
        assert "=" not in cursor

    @pytest.mark.parametrize("lixo", ["", "!!!", "YWJj", "nao-e-base64-valido!!"])
    def test_cursor_corrompido_e_400_e_nao_500(self, lixo):
        """Cliente que guardou um cursor antigo tem que receber instrução."""
        with pytest.raises(InvalidCursorError, match="Recomece a listagem"):
            decode_cursor(lixo)

    def test_o_limite_tem_teto_e_piso(self):
        assert clamp_limit(None) == DEFAULT_PAGE_SIZE
        assert clamp_limit(0) == 1
        assert clamp_limit(-5) == 1
        assert clamp_limit(999_999) == MAX_PAGE_SIZE


class TestFatiamento:
    ITENS = [(f"2024-01-{d:02d}", d) for d in range(20, 0, -1)]

    def _pagina(self, cursor, limite=5):
        return slice_after(
            list(self.ITENS),
            cursor,
            limite,
            key=lambda i: i[0],
            identity=lambda i: i[1],
        )

    def test_a_primeira_pagina_traz_o_limite_e_aponta_a_proxima(self):
        pagina = self._pagina(None)

        assert len(pagina.items) == 5
        assert pagina.has_more is True
        assert pagina.next_cursor is not None

    def test_as_paginas_cobrem_tudo_sem_repetir(self):
        vistos = []
        cursor = None

        for _ in range(10):
            pagina = self._pagina(cursor)
            vistos.extend(pagina.items)
            cursor = pagina.next_cursor
            if not pagina.has_more:
                break

        assert vistos == self.ITENS
        assert len(set(vistos)) == len(vistos), "nenhum item pode aparecer duas vezes"

    def test_a_ultima_pagina_nao_aponta_proxima(self):
        pagina = self._pagina(None, limite=100)

        assert pagina.has_more is False
        assert pagina.next_cursor is None

    def test_insercao_entre_paginas_nao_desloca_o_que_ja_foi_lido(self):
        """É o motivo de o cursor existir em vez de `OFFSET`.

        Com offset, inserir no topo empurra tudo para baixo e o item da borda
        aparece de novo na página seguinte. Com keyset, a âncora é o último item
        lido — o que entrou depois simplesmente não está atrás dele.
        """
        primeira = self._pagina(None)

        lista_crescida = [("2024-01-99", 999), *self.ITENS]
        segunda = slice_after(
            lista_crescida,
            primeira.next_cursor,
            5,
            key=lambda i: i[0],
            identity=lambda i: i[1],
        )

        assert not set(primeira.items) & set(segunda.items)
        assert ("2024-01-99", 999) not in segunda.items

    def test_dois_registros_do_mesmo_dia_nao_travam_a_paginacao(self):
        """Sem o `id` como desempate, a paginação repetiria a borda para sempre."""
        mesma_data = [("2024-01-10", i) for i in range(6, 0, -1)]
        pagina = slice_after(mesma_data, None, 3, key=lambda i: i[0], identity=lambda i: i[1])
        seguinte = slice_after(
            mesma_data, pagina.next_cursor, 3, key=lambda i: i[0], identity=lambda i: i[1]
        )

        assert pagina.items == mesma_data[:3]
        assert seguinte.items == mesma_data[3:]

    def test_a_linha_extra_e_o_que_revela_a_proxima_pagina(self):
        """`has_more` sai da linha a mais, não de um `COUNT(*)` na tabela."""
        pagina = paginate([1, 2, 3, 4], limit=3, key=lambda x: x, identity=lambda x: x)

        assert pagina.items == [1, 2, 3]
        assert pagina.has_more is True


def _semear_proventos(client, headers, quantidade: int) -> None:
    for dia in range(1, quantidade + 1):
        client.post(
            "/api/dividends/received",
            json={"ticker": "PETR4", "paid_at": f"2024-03-{dia:02d}", "amount": 10.0},
            headers=headers,
        )


class TestListasNaApi:
    def test_o_total_cobre_tudo_mesmo_com_a_lista_cortada(self, client):
        """O número no topo da tela não pode encolher conforme a rolagem.

        É o critério que separa paginar de truncar: `items` é a página,
        `total_received` é o extrato.
        """
        headers = make_auth_headers("u_pag_totais")
        _semear_proventos(client, headers, 8)

        corpo = client.get("/api/dividends/received?limit=3", headers=headers).json()

        assert len(corpo["items"]) == 3
        assert corpo["has_more"] is True
        assert corpo["total_count"] == 8
        assert corpo["total_received"] == 80.0, "o total é do conjunto, não da página"

    def test_folhear_ate_o_fim_devolve_cada_item_uma_vez(self, client):
        headers = make_auth_headers("u_pag_folhear")
        _semear_proventos(client, headers, 7)

        vistos: list[int] = []
        url = "/api/dividends/received?limit=2"
        for _ in range(10):
            corpo = client.get(url, headers=headers).json()
            vistos.extend(i["id"] for i in corpo["items"])
            if not corpo["has_more"]:
                break
            url = f"/api/dividends/received?limit=2&cursor={corpo['next_cursor']}"

        assert len(vistos) == 7
        assert len(set(vistos)) == 7

    def test_cursor_invalido_devolve_400_com_instrucao(self, client):
        headers = make_auth_headers("u_pag_cursor_ruim")

        resposta = client.get("/api/dividends/received?cursor=lixo!!", headers=headers)

        assert resposta.status_code == 400
        assert "Recomece" in resposta.json()["detail"]

    def test_o_limite_pedido_alto_demais_e_recusado_pelo_contrato(self, client):
        headers = make_auth_headers("u_pag_teto")

        resposta = client.get(f"/api/dividends/received?limit={MAX_PAGE_SIZE + 1}", headers=headers)

        assert resposta.status_code == 422

    def test_operacoes_encerradas_paginam_no_banco(self, client):
        headers = make_auth_headers("u_pag_trades")
        client.post(
            "/api/portfolio/position",
            json={"ticker": "PETR4", "quantity": 500, "avg_price": 30.0},
            headers=headers,
        )
        for _ in range(4):
            client.post(
                "/api/portfolio/sell",
                json={"ticker": "PETR4", "quantity": 10, "sell_price": 35.0},
                headers=headers,
            )

        corpo = client.get("/api/portfolio/trades?limit=2", headers=headers).json()

        assert len(corpo["trades"]) == 2
        assert corpo["total_count"] == 4
        assert corpo["has_more"] is True
        # Os totais vêm de SUM sobre a tabela, não da soma da página.
        assert corpo["total_realized_pnl"] > 0

    def test_lancamentos_paginam_e_vem_em_ordem_de_leitura(self, client):
        headers = make_auth_headers("u_pag_ledger")
        for dia in range(1, 6):
            client.post(
                "/api/transactions",
                json={
                    "kind": "buy",
                    "symbol": "PETR4",
                    "traded_on": f"2024-02-{dia:02d}",
                    "quantity": 10,
                    "price": 30.0,
                },
                headers=headers,
            )

        corpo = client.get("/api/transactions?limit=2", headers=headers).json()

        assert [i["traded_on"] for i in corpo["items"]] == ["2024-02-05", "2024-02-04"]
        assert corpo["has_more"] is True

    def test_sem_limite_a_resposta_continua_completa_para_carteira_normal(self, client):
        """O padrão não pode truncar quem cabe numa página."""
        headers = make_auth_headers("u_pag_pequena")
        _semear_proventos(client, headers, 3)

        corpo = client.get("/api/dividends/received", headers=headers).json()

        assert len(corpo["items"]) == 3
        assert corpo["has_more"] is False
        assert corpo["next_cursor"] is None


class TestVersaoDaApi:
    def test_o_caminho_com_versao_responde(self, client):
        headers = make_auth_headers("u_ver_v1")

        resposta = client.get(f"/api/{API_VERSION}/portfolio", headers=headers)

        assert resposta.status_code == 200

    def test_o_caminho_sem_versao_continua_respondendo(self, client):
        """Derrubar os apps instalados num deploy seria trocar um problema por outro."""
        headers = make_auth_headers("u_ver_legado")

        assert client.get("/api/portfolio", headers=headers).status_code == 200

    def test_toda_resposta_carimba_a_versao(self, client):
        headers = make_auth_headers("u_ver_header")

        resposta = client.get(f"/api/{API_VERSION}/portfolio", headers=headers)

        assert resposta.headers["X-API-Version"] == API_VERSION

    def test_o_caminho_sem_versao_se_declara_em_transicao(self, client):
        """O aviso existe para ser medido: é o que dirá quando o alias pode sair."""
        headers = make_auth_headers("u_ver_aviso")

        legado = client.get("/api/portfolio", headers=headers)
        versionado = client.get(f"/api/{API_VERSION}/portfolio", headers=headers)

        assert "X-API-Deprecation" in legado.headers
        assert f"/api/{API_VERSION}/portfolio" in legado.headers["X-API-Deprecation"]
        assert "X-API-Deprecation" not in versionado.headers

    def test_o_cabecalho_e_ascii(self, client):
        """Header HTTP é latin-1: um acento aqui derruba a resposta inteira."""
        headers = make_auth_headers("u_ver_ascii")

        aviso = client.get("/api/portfolio", headers=headers).headers["X-API-Deprecation"]

        aviso.encode("ascii")

    def test_as_duas_montagens_sao_o_mesmo_router(self, client):
        """Duas cópias da API divergiriam na primeira mudança."""
        headers = make_auth_headers("u_ver_mesmo")
        client.post(
            "/api/portfolio/position",
            json={"ticker": "PETR4", "quantity": 10, "avg_price": 30.0},
            headers=headers,
        )

        legado = client.get("/api/portfolio", headers=headers).json()
        versionado = client.get(f"/api/{API_VERSION}/portfolio", headers=headers).json()

        assert legado["items"] == versionado["items"]
