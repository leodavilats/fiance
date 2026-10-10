from __future__ import annotations

import io
import zipfile
from datetime import date
from decimal import Decimal
from pathlib import Path

import pytest

from datajob.fontes.b3_cotahist import (
    ArquivoInvalido,
    interpretar,
    linhas_do_zip,
    url_do_ano,
    url_do_dia,
)

TRECHO = Path(__file__).parent / "fixtures" / "COTAHIST_D08102026_trecho.TXT"


def _texto() -> str:
    return TRECHO.read_text(encoding="latin-1")


def _linhas() -> list[str]:
    return _texto().splitlines()


def _com_corpo(corpo: list[str]) -> str:
    linhas = _linhas()
    final = linhas[-1][:31] + f"{len(corpo):011d}" + linhas[-1][42:]
    return "\n".join([linhas[0], *corpo, final])


def _linha_de(codigo: str) -> str:
    return next(linha for linha in _linhas() if linha[12:24].strip() == codigo)


def _trocar(linha: str, inicio: int, valor: str) -> str:
    return linha[:inicio] + valor + linha[inicio + len(valor) :]


def test_a_cotacao_sai_como_a_b3_publicou():
    petr4 = next(c for c in interpretar(_texto()).cotacoes if c.codigo == "PETR4")

    assert petr4.isin == "BRPETRACNPR6"
    assert petr4.data == date(2026, 10, 8)
    assert petr4.codbdi == "02"
    assert petr4.nome_resumido == "PETROBRAS"
    assert petr4.especie == "PN      N2"
    assert (petr4.abertura, petr4.maxima, petr4.minima) == (
        Decimal("55.30"),
        Decimal("55.96"),
        Decimal("54.73"),
    )
    assert (petr4.media, petr4.fechamento) == (Decimal("55.43"), Decimal("55.48"))
    assert petr4.negocios == 82760
    assert petr4.quantidade == 51578400
    assert petr4.volume == Decimal("2859254537.00")
    assert petr4.fator_cotacao == 1


def test_so_o_mercado_a_vista_entra_e_todo_registro_conta():
    leitura = interpretar(_texto())

    codigos = {c.codigo for c in leitura.cotacoes}
    assert codigos == {"VALE3", "MXRF11", "PETR4", "BOVA11", "AAPL34"}, (
        "fracionário (PETR4F, mesmo ISIN da PETR4) e opção não são mercado à vista"
    )
    assert leitura.registros == 7
    assert leitura.rejeitadas == []


def test_arquivo_sem_registro_final_e_recusado_inteiro():
    with pytest.raises(ArquivoInvalido, match="cortado"):
        interpretar("\n".join(_linhas()[:-1]))


def test_contagem_do_registro_final_que_nao_bate_recusa_o_arquivo():
    linhas = _linhas()
    with pytest.raises(ArquivoInvalido, match="declara"):
        interpretar("\n".join(linhas[:-2] + [linhas[-1]]))


def test_linha_de_tamanho_errado_recusa_o_arquivo():
    with pytest.raises(ArquivoInvalido, match="posições"):
        interpretar(_com_corpo([_linha_de("PETR4")[:-1]]))


def test_preco_fora_da_faixa_do_dia_vai_para_quarentena():
    fechamento_acima_da_maxima = _trocar(_linha_de("PETR4"), 108, "0000000009999")

    leitura = interpretar(_com_corpo([fechamento_acima_da_maxima, _linha_de("VALE3")]))

    assert [c.codigo for c in leitura.cotacoes] == ["VALE3"]
    assert [(r.chave, r.motivo) for r in leitura.rejeitadas] == [
        ("PETR4 20261008", "preço fora da faixa do dia")
    ]


def test_media_fora_da_faixa_do_dia_e_aceita():
    media_acima_da_maxima = _trocar(_linha_de("PETR4"), 95, "0000000005700")

    leitura = interpretar(_com_corpo([media_acima_da_maxima]))

    assert leitura.rejeitadas == [], (
        "a B3 publica média fora da faixa (BMKS3 em 08/10/2026: tudo a 376,02, média 380,78)"
    )
    assert leitura.cotacoes[0].media == Decimal("57.00")


def test_preco_zero_vai_para_quarentena():
    sem_abertura = _trocar(_linha_de("PETR4"), 56, "0000000000000")

    leitura = interpretar(_com_corpo([sem_abertura]))

    assert leitura.cotacoes == []
    assert leitura.rejeitadas[0].motivo == "preço não positivo"


def test_isin_repetido_no_pregao_guarda_o_primeiro():
    petr4 = _linha_de("PETR4")

    leitura = interpretar(_com_corpo([petr4, petr4]))

    assert len(leitura.cotacoes) == 1
    assert leitura.rejeitadas[0].motivo == "ISIN repetido no mesmo pregão"


def test_conteudo_que_nao_e_zip_e_recusado():
    with pytest.raises(ArquivoInvalido, match="ZIP"):
        list(linhas_do_zip(b"<html>pregao sem arquivo</html>"))


def test_o_zip_da_b3_e_lido_em_latin1():
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as arquivo:
        arquivo.writestr("COTAHIST_D08102026.TXT", TRECHO.read_bytes())

    assert list(linhas_do_zip(buffer.getvalue())) == _linhas()


def test_endereco_dos_arquivos():
    assert url_do_ano(2025).endswith("/COTAHIST_A2025.ZIP")
    assert url_do_dia(date(2026, 10, 8)).endswith("/COTAHIST_D08102026.ZIP")
