from __future__ import annotations

import io
import zipfile
from datetime import date
from decimal import Decimal

import sqlalchemy as sa

from datajob import coleta, rotina
from datajob.fontes import cvm_fii
from datajob.rede import Ausente
from tests.test_proventos import _papel

_GERAL = "Tipo_Fundo_Classe;CNPJ_Fundo_Classe;Data_Referencia;Versao;Codigo_ISIN\n"
_COMPLEMENTO = (
    "CNPJ_Fundo_Classe;Data_Referencia;Versao;Valor_Patrimonial_Cotas;"
    "Percentual_Dividend_Yield_Mes\n"
)


def _informe(geral: list[str], complemento: list[str]) -> bytes:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as arquivo:
        arquivo.writestr(
            "inf_mensal_fii_geral_2024.csv", (_GERAL + "\n".join(geral)).encode("latin-1")
        )
        arquivo.writestr(
            "inf_mensal_fii_complemento_2024.csv",
            (_COMPLEMENTO + "\n".join(complemento)).encode("latin-1"),
        )
        arquivo.writestr("inf_mensal_fii_ativo_passivo_2024.csv", b"x\n")
    return buffer.getvalue()


HGLG = _informe(
    [
        "Fundo;11.728.688/0001-47;2024-01-01;1;BRHGLGCTF004",
        "Fundo;11.728.688/0001-47;2024-02-01;1;BRHGLGCTF004",
        "Fundo;22.222.222/0001-22;2024-01-01;1;BRRUIMCTF000",
    ],
    [
        "11.728.688/0001-47;2024-01-01;1;158.10;0.006952",
        "11.728.688/0001-47;2024-02-01;1;157.80;0.001",
        "11.728.688/0001-47;2024-02-01;2;157.80;0.006958",
        "22.222.222/0001-22;2024-01-01;1;10;-0.01",
    ],
)


def test_rendimento_estimado_pelo_yield_e_pela_cota():
    proventos, mensal, rejeitados = cvm_fii.interpretar(HGLG)

    assert [(p["emissor"], p["data_com"], p["valor"]) for p in proventos] == [
        ("HGLG", date(2024, 1, 31), Decimal("1.099111")),
        ("HGLG", date(2024, 2, 29), Decimal("1.097972")),
    ], "o HGLG pagou R$ 1,10 por cota em cada mês de 2024; a versão 2 corrige a 1"
    assert len(rejeitados) == 1, "yield negativo não é rendimento"
    assert {(m["emissor"], m["referencia"], m["valor_patrimonial_cota"]) for m in mensal} == {
        ("HGLG", date(2024, 1, 1), Decimal("158.10")),
        ("HGLG", date(2024, 2, 1), Decimal("157.80")),
        ("RUIM", date(2024, 1, 1), Decimal("10")),
    }, "o valor da cota fica guardado mesmo no mês sem rendimento, para o P/VP"


def test_informe_ate_2022_chama_o_cnpj_de_cnpj_fundo():
    antigo = _informe(
        ["Fundo;11.728.688/0001-47;2020-01-01;1;BRHGLGCTF004"],
        ["11.728.688/0001-47;2020-01-01;1;150;0.006"],
    )
    with zipfile.ZipFile(io.BytesIO(antigo)) as original:
        membros = {
            n: original.read(n).replace(b"CNPJ_Fundo_Classe", b"CNPJ_Fundo")
            for n in original.namelist()
        }
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as arquivo:
        for nome, texto in membros.items():
            arquivo.writestr(nome, texto)

    proventos, _, _ = cvm_fii.interpretar(buffer.getvalue())

    assert [p["valor"] for p in proventos] == [Decimal("0.900000")]


def test_fii_inteiro_so_na_primeira_vez():
    assert rotina.anos_do_fii(False, date(2026, 10, 12))[0] == cvm_fii.PRIMEIRO_ANO
    assert rotina.anos_do_fii(True, date(2026, 10, 12)) == [2025, 2026]


def test_pago_pela_b3_vence_o_estimado_no_mesmo_mes(engine, tmp_path):
    with engine.begin() as conn:
        _papel(
            conn,
            "BRHGLGCTF004",
            "CI",
            {
                "2024-01-31": ("100", "100"),
                "2024-02-01": ("100", "100"),
                "2024-02-29": ("100", "100"),
                "2024-03-01": ("100", "100"),
            },
            codbdi="12",
        )
    coleta.executar(
        engine, tmp_path, cvm_fii.FONTE, "inf_mensal_fii_2024.zip", HGLG, cvm_fii.processar
    )
    with engine.begin() as conn:
        coleta_id = conn.execute(sa.text("SELECT max(id) FROM mercado.coleta")).scalar_one()
        conn.execute(
            sa.text(
                "INSERT INTO mercado.provento (emissor, classe, data_com, tipo, valor, origem, "
                "coleta_id) VALUES ('HGLG', 'CI', '2024-02-29', 'RENDIMENTO', 1.10, 'b3_recente', :c)"
            ),
            {"c": coleta_id},
        )
        conn.execute(sa.text("REFRESH MATERIALIZED VIEW mercado.serie_fundo"))
        serie = {
            str(r.data): r
            for r in conn.execute(
                sa.text("SELECT * FROM mercado.serie_fundo WHERE emissor = 'HGLG'")
            )
        }

    assert round(serie["2024-02-01"].provento, 6) == Decimal("1.099111")
    assert serie["2024-02-01"].provento_estimado
    assert serie["2024-03-01"].provento == Decimal("1.10"), "o pago substitui o estimado, não soma"
    assert not serie["2024-03-01"].provento_estimado


def test_informe_ja_guardado_e_reprocessado_quando_a_tabela_nova_esta_vazia(engine, tmp_path):
    from datajob import armazenamento

    armazenamento.guardar(tmp_path, cvm_fii.FONTE, "inf_mensal_fii_2024.zip", HGLG)

    def baixar(url: str) -> bytes:
        raise Ausente(url)

    rotina.diario(engine, tmp_path, baixar, lambda *_: None, hoje=date(2026, 10, 12))

    with engine.connect() as conn:
        meses = conn.execute(sa.text("SELECT count(*) FROM mercado.fii_mensal")).scalar_one()
    assert meses == 3, "o bruto guardado antes da tabela existir também entra"
