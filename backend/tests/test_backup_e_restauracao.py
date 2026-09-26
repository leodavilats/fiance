from __future__ import annotations

import json
from decimal import Decimal

import pytest
from sqlalchemy import create_engine, select, text

from app.backup import (
    TABELAS_EFEMERAS,
    RestauracaoRecusada,
    exportar,
    reaplicar_exclusoes,
    restaurar,
)
from app.core.database import Base
from app.models import db_models  # noqa: F401


def _banco(tmp_path, nome: str, revisao: str = "abc123"):
    engine = create_engine(f"sqlite:///{tmp_path / nome}")
    Base.metadata.create_all(engine)
    with engine.begin() as cx:
        cx.execute(text("CREATE TABLE alembic_version (version_num VARCHAR(32) NOT NULL)"))
        cx.execute(text("INSERT INTO alembic_version VALUES (:r)"), {"r": revisao})
    return engine


def _povoar(engine):
    tabelas = Base.metadata.tables
    with engine.begin() as cx:
        cx.execute(tabelas["users"].insert(), [{"id": "u1", "email": "a@b.c", "created_at": 1.0}])
        cx.execute(
            tabelas["portfolio"].insert(),
            [
                {
                    "user_id": "u1",
                    "ticker": "PETR4",
                    "quantity": Decimal("100"),
                    "avg_price": Decimal("31.23456789"),
                    "category": "acoes_br",
                    "created_at": 1.0,
                    "updated_at": 2.0,
                }
            ],
        )
        cx.execute(
            tabelas["transactions"].insert(),
            [
                {
                    "user_id": "u1",
                    "symbol": "PETR4",
                    "kind": "buy",
                    "quantity": Decimal("100"),
                    "price": Decimal("31.23456789"),
                    "fees": Decimal("4.90"),
                    "amount": Decimal("0"),
                    "traded_on": "2026-09-01",
                    "created_at": 1.0,
                }
            ],
        )
        cx.execute(tabelas["cache_entries"].insert(), [{"k": "x", "v": "1", "expires_at": 1.0}])


def test_a_copia_restaurada_e_igual_a_original(tmp_path):
    origem = _banco(tmp_path, "origem.db")
    _povoar(origem)
    with origem.connect() as cx:
        copia = json.loads(json.dumps(exportar(cx), ensure_ascii=False))

    destino = _banco(tmp_path, "destino.db")
    with destino.begin() as cx:
        contagem = restaurar(cx, copia)

    assert contagem["transactions"] == 1 and contagem["portfolio"] == 1
    with destino.connect() as cx:
        preco = cx.execute(select(Base.metadata.tables["transactions"].c.price)).scalar_one()
        media = cx.execute(select(Base.metadata.tables["portfolio"].c.avg_price)).scalar_one()

    assert preco == Decimal("31.23456789") and media == Decimal("31.23456789"), (
        "dinheiro fiscal é Decimal: a cópia passa por texto e volta exata, sem arredondar por float"
    )


def test_o_que_e_efemero_nao_entra_na_copia(tmp_path):
    origem = _banco(tmp_path, "origem.db")
    _povoar(origem)
    with origem.connect() as cx:
        copia = exportar(cx)

    assert not TABELAS_EFEMERAS & set(copia["tabelas"]), (
        "cache e trava de job são estado de operação: restaurá-los traria preço vencido como válido"
    )


def test_nao_restaura_por_cima_de_dados(tmp_path):
    origem = _banco(tmp_path, "origem.db")
    _povoar(origem)
    with origem.connect() as cx:
        copia = exportar(cx)

    with origem.begin() as cx, pytest.raises(RestauracaoRecusada, match="já tem dados"):
        restaurar(cx, copia)


def test_nao_restaura_em_outra_revisao_do_esquema(tmp_path):
    origem = _banco(tmp_path, "origem.db", revisao="velha")
    _povoar(origem)
    with origem.connect() as cx:
        copia = exportar(cx)

    destino = _banco(tmp_path, "destino.db", revisao="nova")
    with destino.begin() as cx, pytest.raises(RestauracaoRecusada, match="revisão"):
        restaurar(cx, copia)


def test_a_exclusao_posterior_a_copia_e_reaplicada(tmp_path):
    origem = _banco(tmp_path, "origem.db")
    _povoar(origem)
    with origem.connect() as cx:
        copia_antiga = exportar(cx)

    tabelas = Base.metadata.tables
    with origem.begin() as cx:
        cx.execute(tabelas["transactions"].delete())
        cx.execute(tabelas["portfolio"].delete())
        cx.execute(tabelas["users"].update().values(email="apagado+u1@invalid", deleted_at=9.0))
        copia_nova = exportar(cx)

    destino = _banco(tmp_path, "destino.db")
    with destino.begin() as cx:
        restaurar(cx, copia_antiga)
        reaplicadas = reaplicar_exclusoes(cx, copia_nova)

    assert reaplicadas == ["u1"]
    with destino.connect() as cx:
        assert cx.execute(select(tabelas["transactions"])).first() is None, (
            "a cópia é anterior à exclusão da conta: restaurá-la sem reaplicar a exclusão traria "
            "de volta dados que a pessoa pediu para apagar"
        )
        assert cx.execute(select(tabelas["users"].c.deleted_at)).scalar_one() == 9.0
