from __future__ import annotations

from app.services.dip_service import drop_from_high_pct
from tests.conftest import make_auth_headers

ROTA = "/api/v1/dip-scanner"


def _varrer(client, **params):
    headers = make_auth_headers("quedas_user")
    params.setdefault("universe", "PETR4,VALE3")
    resposta = client.get(ROTA, headers=headers, params=params)
    assert resposta.status_code == 200, resposta.text
    return resposta.json()


def test_a_queda_e_medida_contra_a_maxima_de_52_semanas():
    assert drop_from_high_pct(35.0, 50.0) == 30.0
    assert drop_from_high_pct(55.0, 50.0) == 0.0, "preço acima da máxima não é queda negativa"
    assert drop_from_high_pct(35.0, None) is None, "sem máxima não há como medir a queda"


def test_so_entra_quem_caiu_o_minimo_pedido(client):
    assert _varrer(client)["items"] == [], (
        "PETR4 caiu 9,5% e VALE3 14,3% da máxima: abaixo dos 15% padrão, nenhum está em queda"
    )
    corte = _varrer(client, min_drop=10)
    assert [i["symbol"] for i in corte["items"]] == ["VALE3"]
    assert corte["min_drop_pct"] == 10


def test_o_recorte_mostra_a_mesma_leitura_da_folha_do_ativo(client):
    headers = make_auth_headers("quedas_user")
    itens = {i["symbol"]: i for i in _varrer(client, min_drop=5)["items"]}

    for simbolo, item in itens.items():
        folha = client.get(f"/api/v1/asset/{simbolo}", headers=headers).json()
        assert item["label"] == folha["decision"]["label"], (
            "a varredura tinha veredito próprio, e MXRF11 saía 'Abaixo do preço justo' na folha e "
            "'Armadilha' na lista: a queda é recorte, e a leitura é uma só"
        )
        assert item["verdict"] == folha["decision"]["verdict"]


def test_a_ordem_segue_a_margem_de_seguranca(client):
    itens = _varrer(client, min_drop=5)["items"]
    margens = [i["margin_of_safety"] for i in itens if i["margin_of_safety"] is not None]

    assert margens == sorted(margens, reverse=True), (
        "quem decide é a leitura de valor: a queda filtra, e a margem ordena"
    )


def test_nao_ha_nota_nem_etiqueta_propria_de_queda(client):
    item = _varrer(client, min_drop=5)["items"][0]

    for campo in ("dip_score", "breakdown", "verdict_label", "rsi_14"):
        assert campo not in item, (
            f"{campo} era do veredito próprio da varredura, em que RSI e média de 200 dias somavam "
            "pontos: o técnico não decide"
        )
