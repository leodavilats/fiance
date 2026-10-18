from __future__ import annotations

import json

import pandas as pd

from pesquisa import validacao_brapi as v

D = pd.Timestamp
ATIVOS = pd.DataFrame(
    [
        ("MGLU3", "MGLU", "ON", "stock"),
        ("XPML11", "XPML", "CI", "fii"),
        ("BOVA11", "BOVA", "CI", "etf"),
    ],
    columns=["codigo", "emissor", "classe", "tipo"],
)


def _evento_brapi(data, rotulo, fator, codigo="MGLU3"):
    return (codigo, rotulo, D(data), fator, "BRMGLUACNOR2")


def _eventos_brapi(*linhas):
    return pd.DataFrame(list(linhas), columns=["codigo", "rotulo", "data_com", "fator", "isin"])


def _nossos(*linhas):
    return pd.DataFrame(
        [("MGLU", "ON", D(d), m, s) for d, m, s in linhas],
        columns=["emissor", "classe", "data_com", "multiplicador", "status"],
    )


SEM_INFERIDOS = pd.DataFrame(columns=["emissor", "classe", "data_com", "multiplicador"])


def test_eventos_seguem_as_categorias_do_protocolo():
    brapi = _eventos_brapi(
        _evento_brapi("2020-10-13", "DESDOBRAMENTO", 4),
        _evento_brapi("2019-08-05", "DESDOBRAMENTO", 8),
        _evento_brapi("2024-05-24", "GRUPAMENTO", 0.1),
        _evento_brapi("2023-01-02", "BONIFICACAO", 1.1),
        _evento_brapi("2004-06-01", "DESDOBRAMENTO", 2),
        _evento_brapi("2022-01-01", "RESG TOTAL RV", 100),
    )
    nossos = _nossos(
        ("2020-10-15", 4.0, "confirmado"),
        ("2024-05-24", 0.2, "confirmado"),
        ("2023-01-02", 1.1, "refutado"),
        ("2012-03-01", 2.0, "confirmado"),
    )

    r = v.comparar_eventos(brapi, ATIVOS, nossos, SEM_INFERIDOS).set_index("data_com")["categoria"]

    assert r[D("2020-10-13")] == "bate", "dois dias de diferença e o mesmo fator ainda batem"
    assert r[D("2019-08-05")] == "so_brapi"
    assert r[D("2024-05-24")] == "fator_difere"
    assert r[D("2023-01-02")] == "nossa_recusou"
    assert r[D("2012-03-01")] == "so_nossa"
    assert D("2004-06-01") not in r.index, "o protocolo começa em 03/01/2005"
    assert len(r) == 5, "rótulo fora de desdobramento, grupamento e bonificação não entra"


def test_evento_inferido_conta_como_nosso():
    brapi = _eventos_brapi(_evento_brapi("2017-09-04", "DESDOBRAMENTO", 8))
    inferidos = pd.DataFrame([("MGLU", "ON", D("2017-09-05"), 8.0)], columns=SEM_INFERIDOS.columns)

    r = v.comparar_eventos(brapi, ATIVOS, _nossos(), inferidos)

    assert r["categoria"].tolist() == ["bate"] and r["origem_nossa"].tolist() == ["inferido"]


def test_so_nossa_so_vale_para_ticker_que_a_brapi_respondeu():
    outro = pd.DataFrame(
        [("PETR", "PN", D("2008-04-25"), 2.0, "confirmado")],
        columns=["emissor", "classe", "data_com", "multiplicador", "status"],
    )

    r = v.comparar_eventos(_eventos_brapi(), ATIVOS, outro, SEM_INFERIDOS)

    assert r.empty


def test_confirmacao_pelo_preco_usa_a_folga_de_dez_por_cento():
    so_brapi = pd.DataFrame(
        [("MGLU", "ON", D("2019-08-05"), 8.0), ("MGLU", "ON", D("2017-09-04"), 8.0)],
        columns=["emissor", "classe", "data_com", "fator_brapi"],
    )
    vizinhos = pd.DataFrame(
        [
            ("MGLU", "ON", D("2019-08-05"), 160.0, 20.5),
            ("MGLU", "ON", D("2017-09-04"), 100.0, 98.0),
        ],
        columns=["emissor", "classe", "data_com", "antes", "depois"],
    )

    r = v.confirmar_pelo_preco(so_brapi, vizinhos)

    assert r["confirmado_pelo_preco"].tolist() == [True, False]


def test_preco_diverge_por_fracao_de_dias_ou_por_um_dia_grande():
    dias = pd.date_range("2026-01-02", periods=100, freq="B")
    brapi = pd.DataFrame({"codigo": "MGLU3", "data": dias, "close": 10.0})
    nossos = pd.DataFrame({"codigo": "MGLU3", "data": dias, "valor": 10.02})
    um_dia_ruim = nossos.copy()
    um_dia_ruim.loc[50, "valor"] = 10.6

    bom = v.comparar_precos(brapi, nossos).iloc[0]
    ruim = v.comparar_precos(brapi, um_dia_ruim).iloc[0]

    assert not bom["diverge"] and bom["fracao_que_bate"] == 1.0
    assert ruim["diverge"], "um dia acima de 5% basta para o ticker divergir"


def test_preco_conta_os_pregoes_de_um_lado_so():
    brapi = pd.DataFrame(
        {
            "codigo": "XPML11",
            "data": [D("2026-01-02"), D("2026-01-05"), D("2026-01-07")],
            "close": [100.0, 101.0, 103.0],
        }
    )
    nossos = pd.DataFrame(
        {
            "codigo": "XPML11",
            "data": [D("2026-01-05"), D("2026-01-06"), D("2026-01-07")],
            "valor": [101.0, 102.0, 103.0],
        }
    )

    r = v.comparar_precos(brapi, nossos).iloc[0]

    assert (r["dias"], r["so_brapi"], r["so_nossa"]) == (2, 1, 1)


def test_preco_so_compara_dentro_da_janela_que_a_brapi_devolveu():
    brapi = pd.DataFrame(
        {"codigo": "XPML11", "data": [D("2026-01-05"), D("2026-01-06")], "close": [101.0, 102.0]}
    )
    nossos = pd.DataFrame(
        {
            "codigo": "XPML11",
            "data": [D("2025-06-02"), D("2026-01-05"), D("2026-01-06")],
            "valor": [90.0, 101.0, 102.0],
        }
    )

    r = v.comparar_precos(brapi, nossos).iloc[0]

    assert r["so_nossa"] == 0, "o plano da brapi dá um ano; o que vem antes não é dia faltando nela"


def test_proventos_somam_por_data_com_e_respeitam_a_folga():
    brapi = pd.DataFrame(
        [
            ("XPML11", "RENDIMENTO", D("2024-01-31"), 0.92, "x"),
            ("MGLU3", "DIVIDENDO", D("2025-04-25"), 0.20, "x"),
            ("MGLU3", "JCP", D("2025-04-25"), 0.10, "x"),
            ("MGLU3", "JCP", D("2021-07-05"), 0.0155, "x"),
            ("BOVA11", "RENDIMENTO", D("2025-01-01"), 1.0, "x"),
        ],
        columns=["codigo", "rotulo", "data_com", "valor", "isin"],
    )
    nossos = pd.DataFrame(
        [
            ("XPML", "CI", D("2024-01-31"), 0.92),
            ("MGLU", "ON", D("2025-04-25"), 0.302),
            ("MGLU", "ON", D("2023-04-28"), 0.05),
        ],
        columns=["emissor", "classe", "data_com", "valor"],
    )

    r = v.comparar_proventos(brapi, ATIVOS, nossos).set_index("data_com")["categoria"]

    assert r[D("2024-01-31")] == "bate"
    assert r[D("2025-04-25")] == "bate", (
        "dividendo e JCP do mesmo dia somam 0,30; 0,302 está a menos de 1%"
    )
    assert r[D("2021-07-05")] == "so_brapi"
    assert r[D("2023-04-28")] == "so_nossa"
    assert D("2025-01-01") not in r.index, "ETF fica fora da comparação de proventos"


def test_estimativa_de_fii_so_descreve_o_erro():
    brapi = pd.DataFrame(
        [
            ("XPML11", "RENDIMENTO", D("2024-01-31"), 1.00, "x"),
            ("XPML11", "RENDIMENTO", D("2024-02-29"), 1.00, "x"),
        ],
        columns=["codigo", "rotulo", "data_com", "valor", "isin"],
    )
    estimados = pd.DataFrame(
        [("XPML", "CI", D("2024-01-31"), 1.05), ("XPML", "CI", D("2024-02-29"), 1.30)],
        columns=["emissor", "classe", "data_com", "valor"],
    )

    r = v.erro_da_estimativa(brapi, ATIVOS, estimados)

    assert (r["meses"], r["fiis"], r["ate_10_por_cento"]) == (2, 1, 0.5)


def test_resposta_da_brapi_vira_tabela_com_a_data_de_brasilia(tmp_path):
    resposta = {
        "results": [
            {
                "symbol": "MGLU3",
                "historicalDataPrice": [{"date": 1760929200, "close": 7.9429}],
                "dividendsData": {
                    "stockDividends": [{"label": "BONIFICACAO", "factor": 1.05, "lastDatePrior": "2025-12-29T03:00:00.000Z", "isinCode": "X"}],
                    "cashDividends": [{"label": "JCP", "rate": 0.0155, "lastDatePrior": "2021-07-05T03:00:00.000Z", "isinCode": "X"}],
                },
            },
            {"symbol": "SEMDADO3"},
        ]
    }  # fmt: skip
    (tmp_path / "lote_0000.json").write_text(json.dumps(resposta), encoding="utf-8")

    precos, eventos, proventos, sem_resultado = v.ler_respostas(tmp_path)

    assert precos.iloc[0]["data"] == D("2025-10-20"), "meia-noite de Brasília é 03h UTC"
    assert eventos.iloc[0]["data_com"] == D("2025-12-29") and proventos.iloc[0]["valor"] == 0.0155
    assert sem_resultado == ["SEMDADO3"]
