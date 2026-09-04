from __future__ import annotations

from tests.conftest import make_auth_headers

CSV_BOM = (
    "Data;Ativo;Tipo;Quantidade;Preço;Taxas\n"
    "10/01/2024;PETR4;Compra;100;30,50;9,90\n"
    "15/03/2024;VALE3;Compra;50;62,10;9,90\n"
)


def _preview(client, headers, content: str):
    return client.post(
        "/api/transactions/import/preview", json={"content": content}, headers=headers
    )


def _commit(client, headers, content: str, **extra):
    return client.post(
        "/api/transactions/import", json={"content": content, **extra}, headers=headers
    )


class TestPrevia:
    def test_a_previa_nao_grava_nada(self, client):
        headers = make_auth_headers("u_import_preview")

        corpo = _preview(client, headers, CSV_BOM).json()

        assert corpo["ok"] is True
        assert len(corpo["rows"]) == 2
        assert client.get("/api/transactions", headers=headers).json()["count"] == 0

    def test_a_previa_mostra_boas_e_ruins_ao_mesmo_tempo(self, client):
        headers = make_auth_headers("u_import_mixed")
        texto = CSV_BOM + "40/13/2024;PETR4;Compra;10;1,00;0\n"

        corpo = _preview(client, headers, texto).json()

        assert len(corpo["rows"]) == 2
        assert len(corpo["issues"]) == 1
        assert corpo["issues"][0]["line"] == 4
        assert corpo["ok"] is False


class TestAtomicidade:
    def test_uma_linha_ruim_recusa_o_lote_inteiro(self, client):
        headers = make_auth_headers("u_import_atomic")
        texto = CSV_BOM + "sem_data;PETR4;Compra;10;1,00;0\n"

        resposta = _commit(client, headers, texto)

        assert resposta.status_code == 422
        assert client.get("/api/transactions", headers=headers).json()["count"] == 0

    def test_o_erro_da_recusa_aponta_a_linha(self, client):
        headers = make_auth_headers("u_import_msg")

        detalhe = _commit(client, headers, "PETR4 100 30,50\nlixo total aqui").json()["detail"]

        assert "linha 2" in detalhe

    def test_lote_valido_grava_tudo(self, client):
        headers = make_auth_headers("u_import_ok")

        corpo = _commit(client, headers, CSV_BOM).json()

        assert corpo["imported"] == 2
        assert client.get("/api/transactions", headers=headers).json()["count"] == 2


class TestDuplicidade:
    def test_reimportar_a_mesma_nota_e_apresentado_e_nao_silenciado(self, client):
        headers = make_auth_headers("u_import_dup")
        _commit(client, headers, CSV_BOM)

        corpo = _preview(client, headers, CSV_BOM).json()

        assert corpo["duplicates"] == 2
        assert all(row["duplicate_of"] is not None for row in corpo["rows"])

    def test_por_padrao_a_repetida_fica_de_fora(self, client):
        headers = make_auth_headers("u_import_dup_skip")
        _commit(client, headers, CSV_BOM)

        corpo = _commit(client, headers, CSV_BOM).json()

        assert corpo["imported"] == 0
        assert corpo["skipped_duplicates"] == 2
        assert client.get("/api/transactions", headers=headers).json()["count"] == 2

    def test_o_usuario_pode_dizer_que_sao_duas_operacoes_de_verdade(self, client):
        headers = make_auth_headers("u_import_dup_keep")
        _commit(client, headers, CSV_BOM)

        corpo = _commit(client, headers, CSV_BOM, include_duplicates=True).json()

        assert corpo["imported"] == 2
        assert client.get("/api/transactions", headers=headers).json()["count"] == 4

    def test_duplicidade_nao_atravessa_usuarios(self, client):
        dono = make_auth_headers("u_import_tenant_a")
        vizinho = make_auth_headers("u_import_tenant_b")
        _commit(client, dono, CSV_BOM)

        corpo = _preview(client, vizinho, CSV_BOM).json()

        assert corpo["duplicates"] == 0


class TestReconciliacaoAposImportar:
    def test_a_carteira_importada_aparece_na_projecao(self, client):
        """Importar tem que mudar a Carteira, não só o razão.

        Antes, a importação gravava com perfeição num lugar que a tela
        principal não lê: o usuário colava o extrato, o produto respondia
        `{"imported": 2}`, e nada mudava.
        """
        headers = make_auth_headers("u_import_projection")

        _commit(client, headers, CSV_BOM)

        posicoes = client.get("/api/portfolio", headers=headers).json()
        tickers = {p["ticker"] for p in posicoes["items"]}

        assert {"PETR4", "VALE3"} <= tickers

    def test_apos_importar_a_projecao_nao_diverge_da_posicao(self, client):
        headers = make_auth_headers("u_import_sem_divergencia")

        _commit(client, headers, CSV_BOM)

        resultado = client.get("/api/transactions/reconciliation", headers=headers).json()

        assert resultado["in_sync"] is True, resultado["differences"]

    def test_o_preco_medio_importado_bate_com_a_nota(self, client):
        headers = make_auth_headers("u_import_avg")
        _commit(client, headers, CSV_BOM)

        corpo = client.get("/api/transactions/derivation/PETR4", headers=headers).json()

        assert corpo["position"]["total_cost"] == 3059.90
        assert corpo["position"]["avg_price"] == 30.599
