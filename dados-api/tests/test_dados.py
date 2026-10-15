from __future__ import annotations

from tests.conftest import criar_conta


def _dados(cliente, rota: str, chave: dict, **parametros):
    resposta = cliente.get(rota, headers=chave, params=parametros)
    assert resposta.status_code == 200, resposta.text
    return resposta.json()


def test_lista_de_ativos_pagina_por_cursor(cliente, chave):
    primeira = _dados(cliente, "/v1/ativos", chave, limite=1)
    segunda = _dados(cliente, "/v1/ativos", chave, limite=1, cursor=primeira["proximo"])

    assert [a["codigo"] for a in primeira["dados"]] == ["TEST3"]
    assert [a["codigo"] for a in segunda["dados"]] == ["XPML11"] and segunda["proximo"] is None
    assert [a["codigo"] for a in _dados(cliente, "/v1/ativos", chave, tipo="fii")["dados"]] == [
        "XPML11"
    ]


def test_retrato_do_ativo(cliente, chave):
    acao = _dados(cliente, "/v1/ativos/test3", chave)["dados"]

    assert (acao["codigo"], acao["tipo"], acao["preco"], acao["negociando"]) == (
        "TEST3",
        "stock",
        41.0,
        True,
    )
    assert acao["nome"] == "Teste" and acao["setor"] == "Energia"
    inexistente = cliente.get("/v1/ativos/XPTO3", headers=chave)
    assert inexistente.status_code == 404
    assert inexistente.json() == {"erro": "Ativo XPTO3 não encontrado na base."}, (
        "todo erro sai como {'erro': ...}, o de acesso e o de rota"
    )


def test_cotacao_sai_por_acao_mesmo_cotada_por_lote(cliente, chave):
    cotacoes = _dados(cliente, "/v1/ativos/TEST3/cotacoes", chave)["dados"]

    assert cotacoes[0]["data"] == "2005-01-03"
    assert cotacoes[0]["fechamento"] == 1.0, "2005: cotado por lote de mil, fator 1000"
    assert cotacoes[-1]["fechamento"] == 41.0


def test_serie_ajustada_com_retorno_total(cliente, chave):
    serie = _dados(cliente, "/v1/ativos/TEST3/serie", chave, de="2026-10-01")["dados"]

    assert [d["data"] for d in serie] == ["2026-10-08", "2026-10-09"]
    assert round(serie[-1]["retorno_total"], 6) == round(41 / 39 - 1, 6)


def test_proventos_sem_estimado_por_padrao(cliente, chave):
    padrao = _dados(cliente, "/v1/ativos/XPML11/proventos", chave)["dados"]
    com_estimado = _dados(cliente, "/v1/ativos/XPML11/proventos", chave, incluir_estimados=True)

    assert [(p["valor"], p["data_pagamento"]) for p in padrao] == [(0.9, "2026-09-15")]
    assert [p["estimado"] for p in com_estimado["dados"]] == [True, False]


def test_demonstracao_como_se_sabia_na_data(cliente, chave):
    rota = "/v1/empresas/00000000000001/demonstracoes"
    hoje = _dados(cliente, rota, chave)["dados"]
    na_epoca = _dados(cliente, rota, chave, sabido_em="2025-04-01")["dados"]

    assert [(d["versao"], d["lucro_controladores"]) for d in hoje] == [(2, 70.0)]
    assert [(d["versao"], d["lucro_controladores"]) for d in na_epoca] == [(1, 90.0)], (
        "a reapresentação de junho não existia em abril"
    )


def test_empresa_com_os_tickers(cliente, chave):
    empresa = _dados(cliente, "/v1/empresas/00000000000001", chave)["dados"]

    assert empresa["razao_social"] == "TESTE SA"
    assert [t["codigo"] for t in empresa["tickers"]] == ["TEST3"]


def test_informe_de_fii_e_recusa_para_acao(cliente, chave):
    informes = _dados(cliente, "/v1/ativos/XPML11/informes", chave)["dados"]

    assert informes[0]["valor_patrimonial_cota"] == 110.0
    assert cliente.get("/v1/ativos/TEST3/informes", headers=chave).status_code == 422


def test_macro(cliente, chave):
    cdi = _dados(cliente, "/v1/indicadores/cdi", chave)["dados"]
    tesouro = _dados(cliente, "/v1/tesouro", chave)["dados"]
    historico = _dados(
        cliente, "/v1/tesouro/historico", chave, titulo="Tesouro Selic", vencimento="2029-03-01"
    )["dados"]

    assert [d["data"] for d in cdi] == ["2026-10-08", "2026-10-09"]
    assert tesouro[0]["data"] == "2026-10-09" and len(historico) == 2
    assert cliente.get("/v1/indicadores/bitcoin", headers=chave).status_code == 404


def test_atualidade(cliente, chave):
    atual = _dados(cliente, "/v1/atualidade", chave)["dados"]

    assert atual["ate"]["cotacao"] == "2026-10-09"
    assert atual["ultima_coleta"]["falhas"] == {}


def test_plano_gratuito_ve_so_o_ultimo_ano(cliente):
    gratis = criar_conta(cliente, plano="gratuito", email="gratis@teste.com")
    chave = {"Authorization": f"Bearer {gratis['chave']['chave']}"}

    cotacoes = _dados(cliente, "/v1/ativos/TEST3/cotacoes", chave, de="2000-01-01")["dados"]

    assert "2005-01-03" not in [c["data"] for c in cotacoes], "o histórico longo é de plano pago"
