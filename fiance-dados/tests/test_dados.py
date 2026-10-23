from __future__ import annotations

import re
from pathlib import Path

import sqlalchemy as sa
from fastapi.testclient import TestClient

from dadosapi import acesso
from dadosapi.app import criar
from dadosapi.config import carregar
from tests.conftest import TOKEN, criar_conta


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


def _essencial_pago(cliente, bancos) -> dict:
    criada = criar_conta(cliente, plano="essencial", email="pago@teste.com")
    with bancos.acesso.begin() as conn:
        conn.execute(
            sa.text("UPDATE acesso.conta SET pago_ate = current_date + 30 WHERE id = :id"),
            {"id": criada["conta"]["id"]},
        )
    return {"Authorization": f"Bearer {criada['chave']['chave']}"}


def test_essencial_ve_dois_anos_e_nao_a_serie_ajustada(cliente, bancos):
    chave = _essencial_pago(cliente, bancos)

    cotacoes = _dados(cliente, "/v1/ativos/TEST3/cotacoes", chave, de="2000-01-01")["dados"]
    serie = cliente.get("/v1/ativos/TEST3/serie", headers=chave)
    no_tempo = cliente.get(
        "/v1/empresas/00000000000001/demonstracoes",
        headers=chave,
        params={"sabido_em": "2025-04-01"},
    )

    assert "2005-01-03" not in [c["data"] for c in cotacoes], "o histórico longo é do Pro"
    assert serie.status_code == 403 and "série ajustada" in serie.json()["erro"]
    assert no_tempo.status_code == 403
    assert cliente.get("/v1/ativos/XPML11/informes", headers=chave).status_code == 403


def test_plano_pago_sem_pagamento_nao_entra(cliente):
    criada = criar_conta(cliente, plano="pro", email="devendo@teste.com")
    chave = {"Authorization": f"Bearer {criada['chave']['chave']}"}

    resposta = cliente.get("/v1/ativos", headers=chave)

    assert resposta.status_code == 402, "conta paga sem pagamento confirmado não usa a API"


def test_planos_publicos_sem_gratuito_nem_interno(cliente):
    planos = cliente.get("/v1/planos").json()

    assert [p["codigo"] for p in planos["dados"]] == ["essencial", "pro"]
    assert planos["cobranca_aberta"] is False
    assert all(p["preco_mensal_centavos"] for p in planos["dados"]), "nada gratuito (ADR-025)"


def test_planos_trazem_o_whatsapp_do_convite(bancos, url, monkeypatch):
    monkeypatch.setenv("DATABASE_URL", url)
    monkeypatch.setenv("DADOS_API_ADMIN_TOKEN", TOKEN)
    monkeypatch.setenv("CONTATO_WHATSAPP", "+55 31 99758-9889 ")

    planos = TestClient(criar(carregar(), bancos)).get("/v1/planos").json()

    assert planos["whatsapp"] == "5531997589889", "o link wa.me só aceita dígitos"
    assert planos["contato"] is None


def test_todo_recurso_de_plano_tem_rota_que_o_exige(cliente):
    planos = cliente.get("/admin/planos", headers={"X-Admin-Token": TOKEN}).json()
    oferecidos = {r for p in planos for r in p["recursos"]}
    fonte = (Path(acesso.__file__).parent / "app.py").read_text(encoding="utf-8")
    exigidos = set(re.findall(r'exigir\(a, "(\w+)"\)', fonte))

    assert oferecidos <= exigidos, (
        f"plano oferece {sorted(oferecidos - exigidos)} e nenhuma rota exige: o Quant prometeu "
        "uma exportação que não existia (ADR-030)"
    )
    assert exigidos <= set(acesso.NOME_DO_RECURSO), "recurso exigido sem nome para a recusa 403"


def test_vitrine_traz_os_numeros_da_base(cliente):
    vitrine = cliente.get("/v1/vitrine").json()

    assert vitrine["numeros"]["negociando"] == 2 and vitrine["numeros"]["acoes"] == 1
    assert vitrine["numeros"]["desde"] == "2005-01-03"


def test_retratos_em_lote_trazem_irmaos_e_todas_as_versoes(cliente, chave):
    retratos = _dados(cliente, "/v1/retratos", chave, codigos="test3, XPML11,XPTO3")["dados"]

    assert sorted(retratos) == ["TEST3", "XPML11"], "o que a base não tem fica de fora"
    acao = retratos["TEST3"]
    assert [i["codigo"] for i in acao["irmaos"]] == ["TEST3"]
    assert [(d["versao"], d["data_entrega"]) for d in acao["demonstracoes"]] == [
        (1, "2025-03-10"),
        (2, "2025-06-01"),
    ], "o app escolhe a versão; a API entrega todas"
    assert retratos["XPML11"]["demonstracoes"] == []
    muitos = ",".join(f"T{i:03d}3" for i in range(51))
    assert cliente.get("/v1/retratos", headers=chave, params={"codigos": muitos}).status_code == 422


def test_retratos_sem_o_recurso_trazem_so_a_ultima_versao(cliente, bancos):
    chave = _essencial_pago(cliente, bancos)

    acao = _dados(cliente, "/v1/retratos", chave, codigos="TEST3")["dados"]["TEST3"]

    assert [d["versao"] for d in acao["demonstracoes"]] == [2], (
        "todas as versões com a data de entrega são o balanço como se sabia na data, do Pro"
    )


def test_cursor_invalido_e_recusado_sem_erro_do_servidor(cliente, chave):
    resposta = cliente.get("/v1/ativos/TEST3/cotacoes", headers=chave, params={"cursor": "x"})

    assert resposta.status_code == 422 and "Cursor" in resposta.json()["erro"]
