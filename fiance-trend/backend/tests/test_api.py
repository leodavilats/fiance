from __future__ import annotations

import base64
import json
from pathlib import Path

import pytest
import sqlalchemy as sa
from fastapi.testclient import TestClient

from api.app import criar
from api.config import Configuracao


@pytest.fixture
def pastas(tmp_path: Path):
    docs = tmp_path / "docs"
    (docs / "pesquisas").mkdir(parents=True)
    (docs / "pesquisas" / "pesquisa.md").write_text("# Plano — pesquisa\n\ntexto", encoding="utf-8")
    (docs / "09-FUTURO.md").write_text("# Futuro\n", encoding="utf-8")
    (tmp_path / "segredo.md").write_text("não", encoding="utf-8")
    pesquisa = tmp_path / "fiance-trend-backend"
    (pesquisa / "resultados").mkdir(parents=True)
    (pesquisa / "registro.jsonl").write_text(
        json.dumps({"hipotese": "h", "assinatura": "abc", "periodo": "estudo", "resumo": {}})
        + "\n",
        encoding="utf-8",
    )
    (pesquisa / "resultados" / "h_abc_estudo.json").write_text('{"datas": []}', encoding="utf-8")
    (pesquisa / "registro_ranking.jsonl").write_text(
        json.dumps({"sinal": "s", "classe": "acoes", "assinatura": "abc", "periodo": "estudo"})
        + "\n",
        encoding="utf-8",
    )
    (pesquisa / "resultados" / "ranking_acoes_s_abc_estudo.json").write_text(
        json.dumps({"meses": []}), encoding="utf-8"
    )
    front = tmp_path / "dist"
    front.mkdir()
    (front / "index.html").write_text("<div id=root></div>", encoding="utf-8")
    (front / "app.js").write_text("console.log(1)", encoding="utf-8")
    return docs, pesquisa, front


@pytest.fixture
def cliente(pastas):
    docs, pesquisa, front = pastas
    config = Configuracao("sqlite://", "eu", "s3nha", docs, pesquisa, front)
    return TestClient(criar(config, engine=sa.create_engine("sqlite://")))


def _com_senha(senha: str = "s3nha") -> dict:
    return {"Authorization": "Basic " + base64.b64encode(f"eu:{senha}".encode()).decode()}


def test_tudo_pede_senha_menos_a_saude(cliente):
    assert cliente.get("/saude").status_code == 200
    assert cliente.get("/").status_code == 401
    assert cliente.get("/api/pesquisa").status_code == 401
    assert cliente.get("/api/pesquisa", headers=_com_senha("errada")).status_code == 401


def test_registro_e_curva_da_pesquisa(cliente):
    execucoes = cliente.get("/api/pesquisa", headers=_com_senha()).json()["execucoes"]
    curva = cliente.get("/api/pesquisa/curva/h/abc/estudo", headers=_com_senha())

    assert execucoes[0]["hipotese"] == "h"
    assert curva.json() == {"datas": []}
    assert cliente.get("/api/pesquisa/curva/..%2F/x/y", headers=_com_senha()).status_code == 404


def test_registro_e_meses_do_ranking(cliente):
    execucoes = cliente.get("/api/ranking", headers=_com_senha()).json()["execucoes"]
    meses = cliente.get("/api/ranking/acoes/s/abc/estudo", headers=_com_senha())

    assert execucoes[0]["sinal"] == "s"
    assert meses.json() == {"meses": []}
    assert cliente.get("/api/ranking/acoes/s/..%2F/estudo", headers=_com_senha()).status_code == 404


def test_documentos_so_da_lista(cliente):
    lista = cliente.get("/api/documentos", headers=_com_senha()).json()
    texto = cliente.get("/api/documentos/pesquisas/pesquisa.md", headers=_com_senha()).json()

    assert {d["nome"] for d in lista} == {"pesquisas/pesquisa.md", "09-FUTURO.md"}
    assert texto["texto"].startswith("# Plano")
    assert cliente.get("/api/documentos/../segredo.md", headers=_com_senha()).status_code == 404


def test_front_entrega_o_arquivo_ou_o_indice(cliente):
    assert cliente.get("/app.js", headers=_com_senha()).text == "console.log(1)"
    assert "root" in cliente.get("/empresa/123/ON", headers=_com_senha()).text, (
        "rota do front sem arquivo cai no index.html"
    )
    assert cliente.get("/api/nao-existe", headers=_com_senha()).status_code == 404
