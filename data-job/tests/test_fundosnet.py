from __future__ import annotations

import json
from datetime import date
from decimal import Decimal

import sqlalchemy as sa

from datajob import coleta, rotina
from datajob.fontes import b3_fundosnet
from datajob.rede import Ausente
from tests.test_proventos import _papel

ANTIGO = b"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<DadosEconomicoFinanceiros>
  <DadosGerais><CodISINCota>BREUROCTF011</CodISINCota><CodNegociacaoCota>EURO11</CodNegociacaoCota>
  </DadosGerais>
  <InformeRendimentos>
    <Rendimento>
      <DataAprovacao>2016-11-30</DataAprovacao><DataBase>2016-11-30</DataBase>
      <DataPagamento>2016-12-19</DataPagamento><ValorProventoCota>1.1</ValorProventoCota>
    </Rendimento>
    <Amortizacao tipo=""/>
  </InformeRendimentos>
</DadosEconomicoFinanceiros>"""

NOVO = b"""<?xml version="1.0" encoding="UTF-8"?>
<DadosEconomicoFinanceiros>
  <DadosGerais><CNPJFundo>1</CNPJFundo></DadosGerais>
  <InformeRendimentos>
    <Provento>
      <CodISIN>BRIDUACTF003</CodISIN>
      <Rendimento><DataBase>2026-10-23</DataBase><ValorProvento>0.026272891</ValorProvento>
        <DataPagamento>2026-10-30</DataPagamento></Rendimento>
      <Amortizacao tipo="Parcial"><DataBase>2026-10-23</DataBase>
        <ValorProvento>0.686141169</ValorProvento><DataPagamento>2026-10-30</DataPagamento>
      </Amortizacao>
    </Provento>
    <Provento>
      <CodISIN>BRIDUACTF011</CodISIN>
      <Rendimento><DataBase>2026-10-23</DataBase><ValorProvento>0</ValorProvento></Rendimento>
    </Provento>
  </InformeRendimentos>
</DadosEconomicoFinanceiros>"""

_PRECOS = {"2016-11-30": ("100", "100"), "2016-12-01": ("100", "100")}


def _lista(avisos: list[tuple[int, str]], por_pagina: int = 200) -> dict[int, bytes]:
    return {
        inicio: json.dumps(
            {
                "recordsTotal": len(avisos),
                "data": [
                    {"id": i, "situacaoDocumento": s}
                    for i, s in avisos[inicio : inicio + por_pagina]
                ],
            }
        ).encode()
        for inicio in range(0, len(avisos), por_pagina)
    }


def test_aviso_antigo_traz_o_isin_nos_dados_gerais():
    proventos, rejeitados = b3_fundosnet.interpretar(ANTIGO)

    assert proventos == [
        {
            "isin": "BREUROCTF011",
            "data_com": date(2016, 11, 30),
            "tipo": "RENDIMENTO",
            "valor": Decimal("1.1"),
            "data_aprovacao": date(2016, 11, 30),
            "data_pagamento": date(2016, 12, 19),
        }
    ]
    assert rejeitados == []


def test_aviso_novo_traz_um_bloco_por_cota_com_amortizacao():
    proventos, _ = b3_fundosnet.interpretar(NOVO)

    assert [(p["isin"], p["tipo"], p["valor"]) for p in proventos] == [
        ("BRIDUACTF003", "RENDIMENTO", Decimal("0.026272891")),
        ("BRIDUACTF003", "AMORTIZACAO", Decimal("0.686141169")),
    ], "valor zero é a cota que não distribuiu, não um provento"


def test_lista_so_os_avisos_ativos_de_todas_as_paginas():
    paginas = _lista([(i, "I" if i % 3 == 0 else "A") for i in range(1, 451)])

    def baixar(url: str) -> bytes:
        return paginas[int(url.split("&s=")[1].split("&")[0])]

    ativos = b3_fundosnet.ativos(baixar)

    assert len(ativos) == 300, "versão inativa ou cancelada não conta"
    assert ativos[-1] == 449


def test_reprocessar_o_aviso_substitui_e_ignora_cota_desconhecida(engine, tmp_path):
    with engine.begin() as conn:
        _papel(conn, "BREUROCTF011", "CI", _PRECOS, codbdi="12")
    for _ in range(2):
        resultado = coleta.executar(
            engine,
            tmp_path,
            b3_fundosnet.FONTE,
            b3_fundosnet.nome(6960),
            ANTIGO,
            b3_fundosnet.processar,
            forcar=True,
        )
    coleta.executar(
        engine,
        tmp_path,
        b3_fundosnet.FONTE,
        b3_fundosnet.nome(1357698),
        NOVO,
        b3_fundosnet.processar,
    )

    with engine.connect() as conn:
        linhas = conn.execute(
            sa.text("SELECT emissor, classe, data_pagamento, origem FROM mercado.provento")
        ).all()
    assert resultado.gravadas == 1
    assert linhas == [("EURO", "CI", date(2016, 12, 19), "fundosnet")], (
        "o mesmo aviso regravado não duplica, e a cota que nunca negociou fica de fora"
    )


def test_conciliar_descarta_aviso_inativo_e_o_que_a_b3_ja_deu(engine, tmp_path):
    with engine.begin() as conn:
        _papel(conn, "BREUROCTF011", "CI", _PRECOS, codbdi="12")
    for documento_id in (1, 2, 3):
        coleta.executar(
            engine,
            tmp_path,
            b3_fundosnet.FONTE,
            b3_fundosnet.nome(documento_id),
            ANTIGO.replace(
                b"2016-11-30</DataBase>", f"2016-11-{20 + documento_id}</DataBase>".encode()
            )
            if documento_id != 3
            else ANTIGO,
            b3_fundosnet.processar,
            forcar=True,
        )
    with engine.begin() as conn:
        conn.execute(
            sa.text(
                "INSERT INTO mercado.provento (emissor, classe, data_com, tipo, valor, origem, "
                "coleta_id) VALUES ('EURO', 'CI', '2016-11-22', 'RENDIMENTO', 1.1000001, "
                "'b3_recente', (SELECT max(id) FROM mercado.coleta))"
            )
        )
        descartados = b3_fundosnet.conciliar(conn, [2, 3])
        restantes = conn.execute(
            sa.text("SELECT data_com, origem FROM mercado.provento ORDER BY data_com")
        ).all()

    assert descartados == 2
    assert restantes == [
        (date(2016, 11, 22), "b3_recente"),
        (date(2016, 11, 30), "fundosnet"),
    ], "o aviso 1 ficou inativo, e o do dia 22 a B3 já tinha"


def test_diario_coleta_os_avisos_que_faltam(engine, tmp_path, monkeypatch):
    with engine.begin() as conn:
        _papel(conn, "BREUROCTF011", "CI", _PRECOS, codbdi="12")
    paginas = _lista([(6959, "C"), (6960, "A")])
    baixados: list[str] = []

    def baixar(url: str) -> bytes:
        if "pesquisarGerenciadorDocumentosDados" in url:
            return paginas[0]
        if "downloadDocumento" in url:
            baixados.append(url)
            return ANTIGO
        raise Ausente(url)

    monkeypatch.setattr(rotina, "PAUSA_NO_FUNDOSNET", 0)
    for _ in range(2):
        falhas = rotina.diario(engine, tmp_path, baixar, lambda *_: None, hoje=date(2026, 10, 9))

    with engine.connect() as conn:
        origens = conn.execute(sa.text("SELECT origem FROM mercado.provento")).scalars().all()
    assert "avisos de rendimento do FundosNet" not in falhas
    assert baixados == [b3_fundosnet.url_do_documento(6960)], (
        "aviso já coletado não é baixado de novo"
    )
    assert origens == ["fundosnet"]
