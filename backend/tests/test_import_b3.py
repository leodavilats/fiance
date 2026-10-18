from __future__ import annotations

import base64
import io
import re
import zipfile
from datetime import date, datetime

from openpyxl import Workbook

from app.core.pregao import deslocar_pregoes
from app.importing.b3 import parse_b3_movimentacao
from app.ledger import TransactionKind
from tests.conftest import make_auth_headers

CABECALHO = (
    "Entrada/Saída",
    "Data",
    "Movimentação",
    "Produto",
    "Instituição",
    "Quantidade",
    "Preço unitário",
    "Valor da Operação",
)
CORRETORA = "CORRETORA FICTICIA S.A. - CTVM"


def _linha(direcao, dia, movimento, produto, quantidade, preco, valor):
    return (direcao, dia, movimento, produto, CORRETORA, quantidade, preco, valor)


COMPRA_PETR4 = _linha(
    "Credito",
    "05/05/2026",
    "Transferência - Liquidação",
    "PETR4 - PETROLEO BRASILEIRO S/A",
    2,
    48.83,
    97.66,
)
COMPRA_ALLD3 = _linha(
    "Credito",
    "02/06/2026",
    "Transferência - Liquidação",
    "ALLD3 - ALLIED TECNOLOGIA S.A.",
    25,
    5.83,
    145.75,
)
VENDA_ALLD3 = _linha(
    "Debito",
    "14/10/2026",
    "Transferência - Liquidação",
    "ALLD3 - ALLIED TECNOLOGIA S.A.",
    25,
    6.02,
    150.5,
)
JCP_PETR4 = _linha(
    "Credito",
    "21/09/2026",
    "Juros Sobre Capital Próprio",
    "PETR4 - PETROLEO BRASILEIRO S/A",
    2,
    0.35,
    0.58,
)
RENDIMENTO_MXRF11 = _linha(
    "Credito", "15/10/2026", "Rendimento", "MXRF11 - MAXI RENDA FDO INV IMOB - FII", 22, 0.1, 2.2
)
ATUALIZACAO_PETR4 = _linha(
    "Credito", "24/07/2026", "Atualização", "PETR4 - PETROLEO BRASILEIRO S/A", 2, "-", "-"
)


def _xlsx(*linhas, cabecalho=CABECALHO) -> bytes:
    livro = Workbook()
    folha = livro.active
    folha.title = "Movimentação"
    folha.append(cabecalho)
    for linha in linhas:
        folha.append(linha)
    saida = io.BytesIO()
    livro.save(saida)
    return saida.getvalue()


def _dimensao_a1(conteudo: bytes) -> bytes:
    entrada = zipfile.ZipFile(io.BytesIO(conteudo))
    saida = io.BytesIO()
    with zipfile.ZipFile(saida, "w") as destino:
        for nome in entrada.namelist():
            dados = entrada.read(nome)
            if nome == "xl/worksheets/sheet1.xml":
                dados = re.sub(rb'<dimension ref="[^"]*"/>', b'<dimension ref="A1"/>', dados)
            destino.writestr(nome, dados)
    return saida.getvalue()


def _b64(conteudo: bytes) -> str:
    return base64.b64encode(conteudo).decode()


class TestCalendario:
    def test_recuar_dois_pregoes_pula_feriado_e_fim_de_semana(self):
        assert deslocar_pregoes(date(2026, 10, 14), -2) == date(2026, 10, 9), (
            "12/10 é feriado na B3 e 10–11/10 é fim de semana"
        )

    def test_avancar_e_recuar_se_desfazem(self):
        assert deslocar_pregoes(deslocar_pregoes(date(2026, 10, 9), 2), -2) == date(2026, 10, 9)


class TestLeitura:
    def test_liquidacao_a_credito_e_compra_no_pregao_de_dois_dias_antes(self):
        lido = parse_b3_movimentacao(_xlsx(COMPRA_PETR4))

        assert lido.issues == []
        (op,) = lido.operations
        assert op.line == 2
        assert op.entry.kind is TransactionKind.BUY
        assert op.entry.symbol == "PETR4"
        assert op.entry.traded_on == "2026-04-30", (
            "05/05 liquida o pregão de 30/04; 01/05 é feriado"
        )
        assert op.settled_on == "2026-05-05"
        assert op.entry.quantity == 2
        assert op.entry.price == 48.83

    def test_liquidacao_a_debito_e_venda(self):
        (op,) = parse_b3_movimentacao(_xlsx(VENDA_ALLD3)).operations

        assert op.entry.kind is TransactionKind.SELL
        assert op.entry.traded_on == "2026-10-09"

    def test_jcp_entra_como_provento_com_o_valor_liquido(self):
        lido = parse_b3_movimentacao(_xlsx(JCP_PETR4))

        assert lido.operations == []
        (provento,) = lido.dividends
        assert provento.kind == "jcp"
        assert provento.paid_at == "2026-09-21"
        assert provento.amount == 0.58, "o valor da operação já vem descontado do IR"
        assert provento.price == 0.35

    def test_rendimento_entra_como_provento(self):
        (provento,) = parse_b3_movimentacao(_xlsx(RENDIMENTO_MXRF11)).dividends

        assert provento.kind == "rendimento"
        assert provento.ticker == "MXRF11"

    def test_atualizacao_e_conferencia_e_nao_lancamento(self):
        lido = parse_b3_movimentacao(_xlsx(ATUALIZACAO_PETR4))

        assert lido.issues == []
        assert lido.operations == [] and lido.dividends == []
        (custodia,) = lido.custody
        assert (custodia.symbol, custodia.on, custodia.quantity) == ("PETR4", "2026-07-24", 2)

    def test_movimentacao_desconhecida_fica_de_fora_com_aviso_e_sem_bloquear(self):
        desdobro = _linha("Credito", "10/06/2026", "Desdobro", "ITSA4 - ITAUSA S/A", 10, "-", "-")

        lido = parse_b3_movimentacao(_xlsx(COMPRA_PETR4, desdobro))

        assert lido.issues == []
        assert len(lido.operations) == 1
        assert [w.line for w in lido.warnings] == [3]
        assert "à mão" in lido.warnings[0].message

    def test_produto_sem_codigo_de_negociacao_fica_de_fora_com_aviso(self):
        tesouro = _linha(
            "Credito",
            "10/06/2026",
            "Transferência - Liquidação",
            "Tesouro Selic 2029",
            1,
            15000.0,
            15000.0,
        )

        lido = parse_b3_movimentacao(_xlsx(tesouro))

        assert lido.issues == [] and lido.operations == []
        assert "Renda fixa" in lido.warnings[0].message

    def test_fracionario_vira_o_codigo_do_lote(self):
        fracionario = _linha(
            "Credito",
            "05/05/2026",
            "Transferência - Liquidação",
            "PETR4F - PETROLEO",
            3,
            48.0,
            144.0,
        )

        (op,) = parse_b3_movimentacao(_xlsx(fracionario)).operations

        assert op.entry.symbol == "PETR4"

    def test_data_como_celula_de_data_tambem_vale(self):
        linha = list(COMPRA_PETR4)
        linha[1] = datetime(2026, 5, 5)

        (op,) = parse_b3_movimentacao(_xlsx(tuple(linha))).operations

        assert op.settled_on == "2026-05-05"

    def test_planilha_que_declara_so_a1_e_lida_inteira(self):
        lido = parse_b3_movimentacao(_dimensao_a1(_xlsx(COMPRA_PETR4, JCP_PETR4)))

        assert lido.issues == [], "o Excel da B3 sai com <dimension ref='A1'/>"
        assert len(lido.operations) == 1 and len(lido.dividends) == 1

    def test_cabecalho_de_outro_extrato_e_recusado_na_linha_1(self):
        lido = parse_b3_movimentacao(_xlsx(cabecalho=("Ativo", "Quantidade")))

        assert [i.line for i in lido.issues] == [1]

    def test_arquivo_que_nao_e_excel_e_recusado(self):
        lido = parse_b3_movimentacao(b"Data;Ativo\n01/01/2026;PETR4")

        assert [i.line for i in lido.issues] == [0]
        assert ".xlsx" in lido.issues[0].message

    def test_data_ilegivel_aponta_a_linha(self):
        linha = list(COMPRA_PETR4)
        linha[1] = "ontem"

        lido = parse_b3_movimentacao(_xlsx(COMPRA_ALLD3, tuple(linha)))

        assert [i.line for i in lido.issues] == [3]


def _preview(client, headers, conteudo: bytes):
    return client.post(
        "/api/v1/transactions/import/b3/preview",
        json={"content_base64": _b64(conteudo)},
        headers=headers,
    )


def _commit(client, headers, conteudo: bytes, include_lines=()):
    return client.post(
        "/api/v1/transactions/import/b3",
        json={"content_base64": _b64(conteudo), "include_lines": list(include_lines)},
        headers=headers,
    )


EXTRATO = _xlsx(VENDA_ALLD3, JCP_PETR4, ATUALIZACAO_PETR4, COMPRA_ALLD3, COMPRA_PETR4)


class TestPrevia:
    def test_a_previa_nao_grava_nada(self, client):
        headers = make_auth_headers("u_b3_previa")

        corpo = _preview(client, headers, EXTRATO).json()

        assert corpo["ok"] is True, corpo["issues"]
        assert [r["line"] for r in corpo["rows"]] == [2, 3, 5, 6]
        assert {r["target"] for r in corpo["rows"]} == {"operacao", "provento"}
        assert corpo["warnings"] == [], "a Atualização de PETR4 bate com o extrato"
        assert client.get("/api/v1/transactions", headers=headers).json()["count"] == 0

    def test_venda_sem_posicao_bloqueia_na_linha_da_venda(self, client):
        headers = make_auth_headers("u_b3_venda_sem_posicao")

        corpo = _preview(client, headers, _xlsx(VENDA_ALLD3)).json()

        assert corpo["ok"] is False
        assert [i["line"] for i in corpo["issues"]] == [2]

    def test_atualizacao_que_nao_bate_vira_aviso(self, client):
        headers = make_auth_headers("u_b3_custodia")
        a_mais = list(ATUALIZACAO_PETR4)
        a_mais[5] = 5

        corpo = _preview(client, headers, _xlsx(COMPRA_PETR4, tuple(a_mais))).json()

        assert corpo["ok"] is True
        (aviso,) = corpo["warnings"]
        assert aviso["line"] == 3
        assert "A B3 tinha 5 PETR4 em 24/07/2026" in aviso["message"]


class TestGravacao:
    def test_grava_operacoes_e_proventos_juntos(self, client):
        headers = make_auth_headers("u_b3_grava")

        corpo = _commit(client, headers, EXTRATO).json()

        assert corpo["operations"] == 3
        assert corpo["dividends"] == 1
        assert corpo["skipped_duplicates"] == 0
        tickers = {
            p["ticker"] for p in client.get("/api/v1/portfolio", headers=headers).json()["items"]
        }
        assert tickers == {"PETR4"}, "ALLD3 foi comprada e vendida inteira"
        recebidos = client.get("/api/v1/dividends/received", headers=headers).json()["items"]
        assert [(d["ticker"], d["kind"], d["amount"]) for d in recebidos] == [
            ("PETR4", "jcp", 0.58)
        ]

    def test_uma_linha_ruim_recusa_tudo(self, client):
        headers = make_auth_headers("u_b3_atomico")

        resposta = _commit(client, headers, _xlsx(JCP_PETR4, VENDA_ALLD3))

        assert resposta.status_code == 422
        assert "linha 3" in resposta.json()["detail"]
        assert client.get("/api/v1/dividends/received", headers=headers).json()["items"] == []

    def test_base64_quebrado_e_recusado(self, client):
        headers = make_auth_headers("u_b3_base64")

        resposta = client.post(
            "/api/v1/transactions/import/b3/preview",
            json={"content_base64": "isto não é base64"},
            headers=headers,
        )

        assert resposta.status_code == 422


class TestDuplicidade:
    def test_reimportar_o_mesmo_extrato_casa_tudo_e_nao_grava_nada(self, client):
        headers = make_auth_headers("u_b3_reimporta")
        _commit(client, headers, EXTRATO)

        previa = _preview(client, headers, EXTRATO).json()
        corpo = _commit(client, headers, EXTRATO).json()

        assert previa["duplicates"] == 4
        assert (corpo["operations"], corpo["dividends"], corpo["skipped_duplicates"]) == (0, 0, 4)

    def test_lancamento_manual_no_dia_da_liquidacao_e_preco_arredondado_casa(self, client):
        headers = make_auth_headers("u_b3_manual")
        client.post(
            "/api/v1/transactions",
            json={
                "kind": "buy",
                "symbol": "PETR4",
                "traded_on": "2026-05-05",
                "quantity": 2,
                "price": 48.8,
            },
            headers=headers,
        )

        (linha,) = _preview(client, headers, _xlsx(COMPRA_PETR4)).json()["rows"]

        assert linha["duplicate"] is not None
        assert linha["duplicate"]["day"] == "2026-05-05"
        assert linha["duplicate"]["price"] == 48.8

    def test_preco_muito_diferente_nao_e_a_mesma_operacao(self, client):
        headers = make_auth_headers("u_b3_outro_preco")
        client.post(
            "/api/v1/transactions",
            json={
                "kind": "buy",
                "symbol": "PETR4",
                "traded_on": "2026-04-30",
                "quantity": 2,
                "price": 40.0,
            },
            headers=headers,
        )

        (linha,) = _preview(client, headers, _xlsx(COMPRA_PETR4)).json()["rows"]

        assert linha["duplicate"] is None

    def test_repetida_so_entra_quando_a_linha_e_escolhida(self, client):
        headers = make_auth_headers("u_b3_escolhe")
        _commit(client, headers, _xlsx(COMPRA_PETR4))

        corpo = _commit(client, headers, _xlsx(COMPRA_PETR4), include_lines=[2]).json()

        assert corpo["operations"] == 1
        assert client.get("/api/v1/transactions", headers=headers).json()["count"] == 2

    def test_duplicidade_nao_atravessa_usuarios(self, client):
        dono = make_auth_headers("u_b3_tenant_a")
        vizinho = make_auth_headers("u_b3_tenant_b")
        _commit(client, dono, EXTRATO)

        assert _preview(client, vizinho, EXTRATO).json()["duplicates"] == 0
