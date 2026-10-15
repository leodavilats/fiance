from __future__ import annotations

from datetime import UTC, date, datetime

from api.alertas import avaliar

AGORA = datetime(2026, 10, 13, 12, 0, tzinfo=UTC)
HOJE = date(2026, 10, 13)


def _rodada(iniciada: datetime, terminada: datetime | None = None, falhas: dict | None = None):
    return {"iniciada_em": iniciada, "terminada_em": terminada, "falhas": falhas or {}}


def test_rodada_de_hoje_sem_falha_nao_alerta():
    rodada = _rodada(
        datetime(2026, 10, 13, 2, tzinfo=UTC), datetime(2026, 10, 13, 2, 30, tzinfo=UTC)
    )

    assert avaliar(rodada, date(2026, 10, 9), AGORA, HOJE) == [], "sexta, fim de semana e segunda"


def test_etapa_que_falhou_aparece_com_o_erro():
    rodada = _rodada(
        datetime(2026, 10, 13, 2, tzinfo=UTC),
        datetime(2026, 10, 13, 2, 30, tzinfo=UTC),
        {"FRE da CVM": "Indisponivel: 503"},
    )

    alertas = avaliar(rodada, date(2026, 10, 12), AGORA, HOJE)

    assert [a["mensagem"] for a in alertas] == [
        "FRE da CVM falhou na última rodada: Indisponivel: 503"
    ]


def test_rodada_parada_e_cotacao_velha_alertam():
    rodada = _rodada(datetime(2026, 10, 8, 2, tzinfo=UTC), datetime(2026, 10, 8, 3, tzinfo=UTC))

    tipos = [a["tipo"] for a in avaliar(rodada, date(2026, 10, 7), AGORA, HOJE)]

    assert tipos == ["rodada", "cotacao"]


def test_rodada_que_nao_terminou():
    rodada = _rodada(datetime(2026, 10, 13, 2, tzinfo=UTC))

    assert avaliar(rodada, date(2026, 10, 12), AGORA, HOJE)[0]["mensagem"].startswith(
        "A última rodada"
    )
