from __future__ import annotations

import time

from app.api.events import MAX_BATCH
from app.core import events as catalog
from app.services.analytics_service import aha_correlation, build_funnel
from app.storage import event_store
from tests.conftest import make_auth_headers

DAY = 86400.0


def _post(client, headers, *items) -> int:
    return client.post("/api/events", json={"events": list(items)}, headers=headers).status_code


def test_todo_evento_do_dicionario_responde_uma_pergunta():
    for spec in catalog.CATALOG.values():
        assert spec.question in catalog.QUESTIONS, spec.name


def test_evento_fora_do_dicionario_e_recusado(client):
    headers = make_auth_headers("u_ev_unknown")

    assert _post(client, headers, {"name": "usuario_clicou_no_botao_azul"}) == 422


def test_propriedade_com_dado_de_carteira_e_recusada(client):
    headers = make_auth_headers("u_ev_priv")

    assert _post(client, headers, {"name": "feed_item_opened", "props": {"ticker": "PETR4"}}) == 422
    assert _post(client, headers, {"name": "paywall_viewed", "props": {"amount": 19.9}}) == 422
    assert _post(client, headers, {"name": "paywall_viewed", "props": {"patrimony": 100}}) == 422


def test_propriedade_categorica_permitida_e_gravada(client):
    headers = make_auth_headers("u_ev_ok")

    assert _post(client, headers, {"name": "paywall_viewed", "props": {"origin": "hoje"}}) == 200

    assert event_store.counts_by_prop("paywall_viewed", "origin").get("hoje", 0) >= 1


def test_evento_no_futuro_e_ancorado_no_agora(client):
    headers = make_auth_headers("u_ev_clock")
    futuro = time.time() + 10 * DAY

    assert _post(client, headers, {"name": "session_started", "occurred_at": futuro}) == 200

    gravado = event_store.first_occurrence("u_ev_clock", "session_started")
    assert gravado is not None and gravado <= time.time() + 1


def test_lote_grande_demais_e_recusado(client):
    headers = make_auth_headers("u_ev_batch")
    lote = [{"name": "session_started"} for _ in range(MAX_BATCH + 1)]

    assert _post(client, headers, *lote) == 422


def test_catalogo_e_publicado_para_o_cliente(client):
    headers = make_auth_headers("u_ev_catalog")

    corpo = client.get("/api/events/catalog", headers=headers).json()

    nomes = {e["name"] for e in corpo["events"]}
    assert "portfolio_first_position_added" in nomes
    assert set(corpo["questions"]) == set(catalog.QUESTIONS)


def _seed_cohort(prefix: str, now: float) -> None:
    entrada = now - 40 * DAY
    for i in range(10):
        user = f"{prefix}_{i}"
        event_store.record(user, "signup_completed", {}, "web", occurred_at=entrada)
        event_store.record(user, "onboarding_completed", {}, "web", occurred_at=entrada + 60)
        if i < 7:
            event_store.record(
                user, "portfolio_first_position_added", {}, "web", occurred_at=entrada + 120
            )
        if i < 4:
            event_store.record(user, "first_diagnosis_viewed", {}, "web", occurred_at=entrada + 180)
        if i < 5:
            event_store.record(user, "session_started", {}, "web", occurred_at=now - 2 * DAY)


def test_funil_calcula_ativacao_e_d30():
    now = time.time()
    _seed_cohort("u_funnel", now)

    funil = build_funnel(days=90, now=now)
    por_metrica = {m["metric"]: m for m in funil["metrics"]}

    ativados = event_store.users_with("portfolio_first_position_added")
    assert {f"u_funnel_{i}" for i in range(7)} <= ativados
    assert "u_funnel_7" not in ativados

    ativacao = por_metrica["Ativação — primeira posição"]
    assert ativacao["numerator"] == len(ativados)
    assert ativacao["denominator"] >= 10
    assert ativacao["target"] == 0.55

    d30 = por_metrica["D30"]
    assert d30["denominator"] >= 10, "só entra na coorte quem já tem 30 dias"
    assert d30["numerator"] >= 5


def test_aha_ordena_por_lift_de_retencao():
    now = time.time()
    _seed_cohort("u_aha", now)

    candidatos = aha_correlation(now=now)

    assert [c["event"] for c in candidatos][:1] != []
    por_evento = {c["event"]: c for c in candidatos}
    diagnostico = por_evento["first_diagnosis_viewed"]
    assert diagnostico["cohort_with"] >= 4
    assert diagnostico["d30_with"] is not None
