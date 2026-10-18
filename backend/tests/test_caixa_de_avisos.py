from __future__ import annotations

from datetime import date
from types import SimpleNamespace

import pytest

from app.core.context import reset_current_user_id, set_current_user_id
from app.models.whats_new import WhatsNewItem, WhatsNewResponse
from app.services import inbox_service, notification_job
from app.services.whats_new_service import WhatsNewService
from app.storage import inbox_store, portfolio_store
from tests.conftest import make_auth_headers


def _item(kind: str, topic: str, title: str = "Aviso") -> WhatsNewItem:
    return WhatsNewItem(
        kind=kind,
        severity="warning",
        title=title,
        detail="Detalhe.",
        action="rebalance",
        action_label="Ver",
        topic=topic,
    )


@pytest.fixture()
def avisos(monkeypatch):
    atuais: list[WhatsNewItem] = []

    async def build(self):
        return WhatsNewResponse(items=list(atuais), generated_at=0.0)

    monkeypatch.setattr(WhatsNewService, "build", build)
    return atuais


class TestIdentidade:
    def test_o_mesmo_assunto_na_mesma_semana_e_um_aviso_so(self):
        segunda = inbox_service.notices_from_whats_new(
            [_item("patrimony", "patrimony:subiu")], date(2026, 10, 12)
        )
        sexta = inbox_service.notices_from_whats_new(
            [_item("patrimony", "patrimony:subiu")], date(2026, 10, 16)
        )
        seguinte = inbox_service.notices_from_whats_new(
            [_item("patrimony", "patrimony:subiu")], date(2026, 10, 19)
        )

        assert segunda[0].dedup_key == sexta[0].dedup_key
        assert seguinte[0].dedup_key != segunda[0].dedup_key

    def test_desvio_de_meta_volta_no_maximo_uma_vez_por_mes(self):
        outubro = inbox_service.notices_from_whats_new(
            [_item("allocation", "allocation:acoes:acima")], date(2026, 10, 1)
        )
        fim = inbox_service.notices_from_whats_new(
            [_item("allocation", "allocation:acoes:acima")], date(2026, 10, 31)
        )

        assert outubro[0].dedup_key == fim[0].dedup_key

    def test_vencimento_e_um_aviso_por_aplicacao_sem_periodo(self):
        (aviso,) = inbox_service.notices_from_whats_new(
            [_item("maturity", "maturity:7")], date(2026, 10, 1)
        )

        assert aviso.dedup_key == "maturity:7@"

    def test_linha_vazia_e_item_sem_assunto_nao_entram(self):
        vazio = WhatsNewItem(kind="empty", severity="info", title="Nada", detail="")
        sem_assunto = WhatsNewItem(kind="patrimony", severity="info", title="X", detail="")

        assert inbox_service.notices_from_whats_new([vazio, sem_assunto], date.today()) == []


class TestCaixa:
    def test_abrir_a_caixa_guarda_os_avisos_e_conta_os_nao_lidos(self, client, avisos):
        headers = make_auth_headers("u_caixa_abre")
        avisos.append(_item("allocation", "allocation:acoes:acima", "Ações acima da meta"))

        corpo = client.get("/api/v1/inbox", headers=headers).json()

        assert [i["title"] for i in corpo["items"]] == ["Ações acima da meta"]
        assert corpo["items"][0]["read_at"] is None
        assert corpo["unread"] == 1
        assert client.get("/api/v1/inbox/unread", headers=headers).json() == {"unread": 1}

    def test_reabrir_nao_repete_o_aviso(self, client, avisos):
        headers = make_auth_headers("u_caixa_repete")
        avisos.append(_item("tax", "tax"))

        client.get("/api/v1/inbox", headers=headers)
        corpo = client.get("/api/v1/inbox", headers=headers).json()

        assert len(corpo["items"]) == 1, "o assunto já está na caixa; reler não o duplica"

    def test_o_aviso_fica_mesmo_quando_o_assunto_some(self, client, avisos):
        headers = make_auth_headers("u_caixa_historico")
        avisos.append(_item("maturity", "maturity:3", "CDB vence em 10 dias"))
        client.get("/api/v1/inbox", headers=headers)
        avisos.clear()

        corpo = client.get("/api/v1/inbox", headers=headers).json()

        assert [i["title"] for i in corpo["items"]] == ["CDB vence em 10 dias"]

    def test_marcar_um_e_marcar_todos(self, client, avisos):
        headers = make_auth_headers("u_caixa_lido")
        avisos.extend([_item("tax", "tax"), _item("maturity", "maturity:1")])
        ids = [i["id"] for i in client.get("/api/v1/inbox", headers=headers).json()["items"]]

        um = client.post("/api/v1/inbox/read", json={"ids": ids[:1]}, headers=headers).json()
        todos = client.post("/api/v1/inbox/read", json={}, headers=headers).json()

        assert um == {"unread": 1}
        assert todos == {"unread": 0}

    def test_filtro_por_tipo(self, client, avisos):
        headers = make_auth_headers("u_caixa_filtro")
        avisos.extend([_item("tax", "tax"), _item("maturity", "maturity:1")])
        client.get("/api/v1/inbox", headers=headers)

        corpo = client.get("/api/v1/inbox?kind=maturity", headers=headers).json()

        assert {i["kind"] for i in corpo["items"]} == {"maturity"}

    def test_pagina_por_cursor(self, client, avisos):
        headers = make_auth_headers("u_caixa_pagina")
        avisos.extend(_item("maturity", f"maturity:{n}") for n in range(5))
        client.get("/api/v1/inbox", headers=headers)

        primeira = client.get("/api/v1/inbox?limit=3", headers=headers).json()
        segunda = client.get(
            f"/api/v1/inbox?limit=3&cursor={primeira['next_cursor']}", headers=headers
        ).json()

        assert primeira["has_more"] is True
        ids = [i["id"] for i in primeira["items"] + segunda["items"]]
        assert len(ids) == len(set(ids)) == 5

    def test_a_caixa_nao_atravessa_usuarios(self, client, avisos):
        dono = make_auth_headers("u_caixa_dono")
        vizinho = make_auth_headers("u_caixa_vizinho")
        avisos.append(_item("tax", "tax"))
        client.get("/api/v1/inbox", headers=dono)
        avisos.clear()

        assert client.get("/api/v1/inbox", headers=vizinho).json()["items"] == []

    def test_falha_ao_calcular_nao_esconde_o_que_ja_esta_guardado(
        self, client, avisos, monkeypatch
    ):
        headers = make_auth_headers("u_caixa_falha")
        avisos.append(_item("tax", "tax"))
        client.get("/api/v1/inbox", headers=headers)

        async def quebra(self):
            raise RuntimeError("fonte fora do ar")

        monkeypatch.setattr(WhatsNewService, "build", quebra)
        resposta = client.get("/api/v1/inbox", headers=headers)

        assert resposta.status_code == 200
        assert len(resposta.json()["items"]) == 1


class TestAlertaDePreco:
    @pytest.mark.anyio
    async def test_alerta_disparado_entra_na_caixa_mesmo_sem_push(self, client, monkeypatch):
        client.get("/api/v1/inbox/unread", headers=make_auth_headers("u_caixa_alerta"))
        token = set_current_user_id("u_caixa_alerta")
        try:
            portfolio_store.create_price_alert("PETR4", "below", 30.0)
        finally:
            reset_current_user_id(token)

        async def universo(tickers):
            return [SimpleNamespace(symbol="PETR4", price=29.5)]

        monkeypatch.setattr(notification_job.AssetRepository, "get_universe", universo)
        enviados = []
        monkeypatch.setattr(notification_job, "send_push", lambda *a, **k: enviados.append(a) or [])

        await notification_job.run_notification_cycle()

        assert enviados == [], "sem aparelho cadastrado não há push"
        assert inbox_store.unread_count(user_id="u_caixa_alerta") == 1
        assert portfolio_store.list_price_alerts(user_id="u_caixa_alerta")[0]["triggered_at"]
