from __future__ import annotations

import httpx
import pytest
import sqlalchemy as sa
from fastapi.testclient import TestClient

from dadosapi import acesso, fumaca
from dadosapi.app import criar
from dadosapi.config import Configuracao
from tests.conftest import TOKEN

ADMIN = {"X-Admin-Token": TOKEN}
DEPENDEM_DO_DIA = {"a última cotação é recente"}


@pytest.fixture
def console(bancos, url, monkeypatch):
    monkeypatch.setattr(fumaca, "ACAO", "TEST3")
    monkeypatch.setattr(fumaca, "FII", "XPML11")
    app = criar(Configuracao(url, TOKEN), bancos, cliente_da_fumaca=lambda _: TestClient(app))
    return TestClient(app)


def _chaves_ativas(bancos) -> int:
    with bancos.acesso.connect() as conn:
        return conn.execute(
            sa.text("SELECT count(*) FROM acesso.chave WHERE revogada_em IS NULL")
        ).scalar_one()


def test_a_fumaca_confere_cada_plano_e_nao_deixa_chave(console, bancos):
    resposta = console.post("/admin/fumaca", headers=ADMIN)

    assert resposta.status_code == 200, resposta.text
    resultados = resposta.json()["resultados"]
    assert {r["grupo"] for r in resultados} == {
        "sem chave",
        "plano interno",
        "plano convidado",
        "plano essencial",
        "plano pro",
    }, "cada plano da tabela ganha a sua rodada"
    falhas = [r for r in resultados if not r["ok"] and r["nome"] not in DEPENDEM_DO_DIA]
    assert not falhas, falhas
    essencial = {r["nome"]: r for r in resultados if r["grupo"] == "plano essencial"}
    serie = essencial.get("GET /v1/ativos/TEST3/serie?limite=5 → 403")
    assert serie, "a fumaça espera o 403 do recurso que o plano não tem"
    assert serie["resposta"]["status"] == 403 and "não inclui" in serie["resposta"]["corpo"], (
        "o console mostra o corpo da resposta, não só o código"
    )
    assert all(r["resposta"] for r in resultados if r["nome"].startswith("GET ")), (
        "toda conferência de rota leva a resposta junto"
    )
    assert _chaves_ativas(bancos) == 0, "a chave da fumaça só vive enquanto ela roda"


def test_rodar_de_novo_reaproveita_as_contas(console, bancos):
    for _ in range(2):
        assert console.post("/admin/fumaca", headers=ADMIN).status_code == 200

    with bancos.acesso.connect() as conn:
        contas = conn.execute(
            sa.text("SELECT count(*) FROM acesso.conta WHERE email LIKE :d"),
            {"d": f"%{acesso.DOMINIO_DA_FUMACA}"},
        ).scalar_one()
        planos = conn.execute(sa.text("SELECT count(*) FROM acesso.plano")).scalar_one()
    assert contas == planos, "uma conta de fumaça por plano, não uma por rodada"


def test_a_fumaca_exige_o_token(console, bancos):
    assert console.post("/admin/fumaca").status_code == 401
    assert _chaves_ativas(bancos) == 0


def test_a_fumaca_nao_entra_nas_contas_nem_no_uso_do_console(console):
    assert console.post("/admin/fumaca", headers=ADMIN).status_code == 200

    contas = console.get("/admin/contas", headers=ADMIN).json()
    uso = console.get("/admin/uso", headers=ADMIN).json()
    assert not [c for c in contas if c["email"].endswith(acesso.DOMINIO_DA_FUMACA)], (
        "conta de fumaça sem chave apareceria em 'pede atenção'"
    )
    assert sum(d["requisicoes"] for d in uso) == 0, "o tráfego da fumaça não é uso de cliente"


def test_resposta_longa_e_cortada():
    corpo = "x" * (fumaca.LIMITE_DA_RESPOSTA + 5000)
    resposta = fumaca._resposta(httpx.Response(200, text=corpo))

    assert len(resposta["corpo"]) < len(corpo), "o portal inteiro não vai para o console"
    assert resposta["corpo"].endswith("mais 5000 caracteres")
