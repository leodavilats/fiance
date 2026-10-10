from __future__ import annotations

import io
import zipfile
from datetime import date
from decimal import Decimal

import sqlalchemy as sa

from datajob import inferencia
from datajob.fontes import cvm_demonstracoes, cvm_ipe
from tests.test_proventos import _coleta, _papel


def test_kepler_e_meliuz_passam_e_a_gafisa_nao():
    kepler = inferencia.fator_comum(Decimal("55.15") / Decimal("18.42"), Decimal(89860) / 29953)
    meliuz = inferencia.fator_comum(Decimal("32.82") / Decimal("5.90"), Decimal(803598) / 126433)
    gafisa = inferencia.fator_comum(Decimal("1.19") / Decimal("10.00"), Decimal(37884) / 337445)

    assert (kepler, meliuz) == (3, 6)
    assert gafisa is None, "10 para 1 com aumento de capital: preço e ações apontam para 1/8 e 1/9"


def test_queda_de_preco_sem_mudar_o_numero_de_acoes_nao_e_evento():
    assert inferencia.fator_comum(Decimal(3), Decimal("1.0")) is None, "Americanas, jan/2023"


def test_documento_precisa_falar_no_sentido_certo_e_perto_do_salto():
    dia = date(2022, 5, 6)
    desdobramento = [(date(2022, 4, 4), "Desdobramento KEPL3", "p1")]
    grupamento = [(date(2022, 4, 4), "Grupamento de ações", "p2")]
    antigo = [(date(2021, 1, 4), "Desdobramento KEPL3", "p3")]

    assert inferencia.evidencia(Decimal(3), desdobramento, dia) == ("p1", "Desdobramento KEPL3")
    assert inferencia.evidencia(Decimal(3), grupamento, dia) is None
    assert inferencia.evidencia(Decimal(3), antigo, dia) is None


def _zip(nome: str, csv: str) -> bytes:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as arquivo:
        arquivo.writestr(nome, csv.encode("latin-1"))
    return buffer.getvalue()


IPE = (
    "CNPJ_Companhia;Nome_Companhia;Codigo_CVM;Data_Referencia;Categoria;Tipo;Especie;Assunto;"
    "Data_Entrega;Tipo_Apresentacao;Protocolo_Entrega;Versao;Link_Download\n"
    "91.983.056/0001-69;KEPLER WEBER S.A.;14460;2022-04-04;Fato Relevante;;;"
    "Desdobramento KEPL3;2022-04-04;AP - Apresentação;P1;1;https://rad\n"
    "91.983.056/0001-69;KEPLER WEBER S.A.;14460;2022-04-04;Fato Relevante;;;"
    "Resultado do 1T22;2022-04-28;AP - Apresentação;P2;1;https://rad\n"
)


def test_ipe_guarda_so_o_que_fala_de_evento_em_acoes():
    documentos = cvm_ipe.interpretar(_zip("ipe_cia_aberta_2022.csv", IPE))

    assert [(d["cnpj"], d["assunto"]) for d in documentos] == [
        ("91983056000169", "Desdobramento KEPL3")
    ]


COMPOSICAO = (
    "CNPJ_CIA;DT_REFER;VERSAO;DENOM_CIA;QT_ACAO_ORDIN_CAP_INTEGR;QT_ACAO_PREF_CAP_INTEGR;"
    "QT_ACAO_TOTAL_CAP_INTEGR;QT_ACAO_ORDIN_TESOURO;QT_ACAO_PREF_TESOURO;QT_ACAO_TOTAL_TESOURO\n"
    "91.983.056/0001-69;2022-03-31;1;KEPLER WEBER S.A.;29953;0;29953;65;0;65\n"
    "91.983.056/0001-69;2022-06-30;1;KEPLER WEBER S.A.;89860;0;89860;196;0;196\n"
)


def test_composicao_do_capital():
    linhas = cvm_demonstracoes.interpretar_composicao(
        _zip("itr_cia_aberta_composicao_capital_2022.csv", COMPOSICAO), "ITR"
    )

    assert [(r["data_referencia"], r["acoes_total"]) for r in linhas] == [
        (date(2022, 3, 31), 29953),
        (date(2022, 6, 30), 89860),
    ]


def test_salto_da_kepler_vira_evento_inferido_e_a_serie_fica_continua(engine, tmp_path):
    kepler = "91983056000169"
    with engine.begin() as conn:
        _papel(
            conn,
            "BRKEPLACNOR1",
            "ON NM",
            {"2022-05-05": ("55", "55.15"), "2022-05-06": ("18.42", "19.04")},
        )
        coleta_id = _coleta(conn)
        conn.execute(
            sa.text(
                "INSERT INTO mercado.emissor (codigo, cnpj, metodo) VALUES ('KEPL', :c, 'fca')"
            ),
            {"c": kepler},
        )
        for referencia in ("2022-03-31", "2022-06-30"):
            conn.execute(
                sa.text(
                    "INSERT INTO mercado.documento (cnpj, tipo, data_referencia, versao, coleta_id) "
                    "VALUES (:c, 'ITR', :r, 1, :k)"
                ),
                {"c": kepler, "r": referencia, "k": coleta_id},
            )
        cvm_demonstracoes.gravar_composicao(
            conn, _zip("itr_cia_aberta_composicao_capital_2022.csv", COMPOSICAO), "ITR"
        )
        for documento in cvm_ipe.interpretar(_zip("ipe_cia_aberta_2022.csv", IPE)):
            conn.execute(
                sa.text(
                    "INSERT INTO mercado.ipe_documento (protocolo, versao, cnpj, data_entrega, "
                    "categoria, assunto, coleta_id) VALUES (:protocolo, :versao, :cnpj, "
                    ":data_entrega, :categoria, :assunto, :k)"
                ),
                {**documento, "k": coleta_id},
            )
        conn.execute(sa.text("REFRESH MATERIALIZED VIEW mercado.serie_papel"))

        assert inferencia.inferir(conn) == 1
        assert inferencia.inferir(conn) == 0, "rodar de novo não duplica"
        conn.execute(sa.text("REFRESH MATERIALIZED VIEW mercado.serie_papel"))
        dia = conn.execute(
            sa.text("SELECT * FROM mercado.serie_papel WHERE cnpj = :c AND data = '2022-05-06'"),
            {"c": kepler},
        ).one()

    assert not dia.salto_sem_evento
    assert abs(dia.retorno_total - Decimal("0.0357")) < Decimal("0.001"), "19,04 × 3 / 55,15 − 1"
