"""Leitura de operações: tolerante com forma, intolerante com ambiguidade.

Adivinhar errado a forma custa uma mensagem de erro; adivinhar errado o valor
custa o preço médio, que é o IR. Os testes são organizados por essa assimetria.
"""

from __future__ import annotations

import pytest

from app.importing import parse_import
from app.importing.parser import MAX_ROWS, parse_day, parse_decimal

HOJE = "2026-08-27"


class TestNumero:
    @pytest.mark.parametrize(
        ("texto", "esperado"),
        [
            ("30,50", 30.50),
            ("30.50", 30.50),
            ("1.234,56", 1234.56),
            ("1,234.56", 1234.56),
            ("R$ 1.234,56", 1234.56),
            ("  42 ", 42.0),
            ("-15,25", -15.25),
        ],
    )
    def test_formatos_inequivocos_sao_aceitos(self, texto, esperado):
        assert parse_decimal(texto, 1, "preço") == pytest.approx(esperado)

    def test_ponto_com_tres_casas_e_recusado_por_ser_ambiguo(self):
        """`1.234` pode ser mil duzentos e trinta e quatro ou 1,234.

        Um fator de mil no preço médio é um extrato fiscal errado, então a
        resposta certa é perguntar, não escolher.
        """
        with pytest.raises(ValueError, match="ambíguo"):
            parse_decimal("1.234", 1, "preço")

    def test_texto_que_nao_e_numero_diz_o_que_veio(self):
        with pytest.raises(ValueError, match="trinta reais"):
            parse_decimal("trinta reais", 1, "preço")


class TestData:
    @pytest.mark.parametrize(
        ("texto", "esperado"),
        [
            ("10/01/2024", "2024-01-10"),
            ("1/1/2024", "2024-01-01"),
            ("2024-01-10", "2024-01-10"),
            ("10-01-2024", "2024-01-10"),
        ],
    )
    def test_formatos_reconhecidos(self, texto, esperado):
        assert parse_day(texto, 1) == esperado

    def test_formato_desconhecido_diz_qual_usar(self):
        with pytest.raises(ValueError, match="DD/MM/AAAA"):
            parse_day("Jan 10 2024", 1)


class TestListaColada:
    def test_o_formato_minimo_e_ativo_quantidade_preco(self):
        resultado = parse_import("PETR4 100 30,50", default_day=HOJE)

        assert resultado.ok
        assert len(resultado.rows) == 1
        entrada = resultado.rows[0].entry
        assert entrada.symbol == "PETR4"
        assert entrada.quantity == 100
        assert entrada.price == pytest.approx(30.50)
        assert entrada.kind.value == "buy"
        assert entrada.traded_on == HOJE

    def test_o_tipo_pode_vir_na_frente(self):
        resultado = parse_import("venda PETR4 50 35,00 10/01/2024", default_day=HOJE)

        assert resultado.ok
        assert resultado.rows[0].entry.kind.value == "sell"
        assert resultado.rows[0].entry.traded_on == "2024-01-10"

    def test_linhas_em_branco_e_comentarios_sao_ignorados(self):
        resultado = parse_import(
            "# minha carteira\n\nPETR4 100 30,50\n\n  \nVALE3 50 60,00\n", default_day=HOJE
        )

        assert resultado.ok
        assert [r.entry.symbol for r in resultado.rows] == ["PETR4", "VALE3"]

    def test_linha_incompleta_diz_a_linha_e_o_exemplo(self):
        resultado = parse_import("PETR4 100 30,50\nVALE3\n", default_day=HOJE)

        assert not resultado.ok
        problema = resultado.issues[0]
        assert problema.line == 2
        assert "PETR4 100 30,50" in problema.message
        assert problema.raw == "VALE3"

    def test_uma_linha_ruim_nao_descarta_as_boas_da_previa(self):
        """A prévia mostra tudo; é a gravação que é atômica."""
        resultado = parse_import("PETR4 100 30,50\nlixo\nVALE3 50 60,00", default_day=HOJE)

        assert len(resultado.rows) == 2
        assert len(resultado.issues) == 1


class TestCsv:
    def test_cabecalho_em_portugues_com_ponto_e_virgula(self):
        texto = (
            "Data;Ativo;Tipo;Quantidade;Preço;Taxas\n"
            "10/01/2024;PETR4;Compra;100;30,50;9,90\n"
            "15/03/2024;VALE3;Venda;50;62,10;9,90\n"
        )

        resultado = parse_import(texto, default_day=HOJE)

        assert resultado.ok, resultado.issues
        assert "csv" in resultado.detected_format
        assert [r.entry.kind.value for r in resultado.rows] == ["buy", "sell"]
        assert resultado.rows[0].entry.fees == pytest.approx(9.90)

    def test_cabecalho_em_ingles_com_virgula(self):
        texto = "date,ticker,type,quantity,price\n2024-01-10,PETR4,buy,100,30.50\n"

        resultado = parse_import(texto, default_day=HOJE)

        assert resultado.ok, resultado.issues
        assert resultado.rows[0].entry.symbol == "PETR4"

    def test_sem_coluna_de_ativo_o_erro_diz_quais_nomes_servem(self):
        texto = "Data;Quantidade;Preço\n10/01/2024;100;30,50\n"

        resultado = parse_import(texto, default_day=HOJE)

        assert not resultado.ok
        assert "Ticker" in resultado.issues[0].message

    def test_a_linha_do_erro_e_a_do_arquivo_e_nao_a_do_registro(self):
        """Linha 1 é o cabeçalho — o usuário conta linhas no editor dele."""
        texto = "Data;Ativo;Quantidade;Preço\n10/01/2024;PETR4;100;30,50\n10/01/2024;XX;10;1,00\n"

        resultado = parse_import(texto, default_day=HOJE)

        assert resultado.issues[0].line == 3

    def test_amortizacao_le_o_valor_devolvido_da_coluna_de_preco(self):
        texto = "Data;Ativo;Tipo;Quantidade;Preço\n10/07/2024;MXRF11;Amortização;0;150,00\n"

        resultado = parse_import(texto, default_day=HOJE)

        assert resultado.ok, resultado.issues
        entrada = resultado.rows[0].entry
        assert entrada.kind.value == "amortization"
        assert entrada.amount == pytest.approx(150.0)
        assert entrada.quantity == 0


class TestRecusas:
    def test_ticker_que_nao_e_da_b3_e_recusado(self):
        resultado = parse_import("BANANA 100 30,50", default_day=HOJE)

        assert not resultado.ok
        assert "B3" in resultado.issues[0].message

    def test_tipo_desconhecido_lista_os_conhecidos(self):
        texto = "Data;Ativo;Tipo;Quantidade;Preço\n10/01/2024;PETR4;Doação;100;30,50\n"

        resultado = parse_import(texto, default_day=HOJE)

        assert "compra" in resultado.issues[0].message

    def test_compra_sem_preco_e_recusada_pela_regra_do_razao(self):
        """A validação do lançamento vale também na importação."""
        texto = "Data;Ativo;Tipo;Quantidade;Preço\n10/01/2024;PETR4;Compra;100;0\n"

        resultado = parse_import(texto, default_day=HOJE)

        assert not resultado.ok
        assert "preço positivo" in resultado.issues[0].message

    def test_arquivo_vazio_nao_e_sucesso_silencioso(self):
        assert not parse_import("   \n\n", default_day=HOJE).ok

    def test_arquivo_grande_demais_sugere_o_que_fazer(self):
        texto = "\n".join(["PETR4 1 1,00"] * (MAX_ROWS + 1))

        resultado = parse_import(texto, default_day=HOJE)

        assert not resultado.ok
        assert "por ano" in resultado.issues[0].message
