from __future__ import annotations

from decimal import Decimal

import pytest
from sqlalchemy import Float, create_engine, inspect, select, text
from sqlalchemy.orm import Session

from app.core.database import Base
from app.core.money import ExactNumeric
from app.models import db_models  # noqa: F401
from app.models.db_models import ClosedTradeDb, PortfolioPosition

CAMPOS_DE_DINHEIRO = frozenset(
    {
        "amount",
        "avg_price",
        "cash_available",
        "fees",
        "gross_profit",
        "ir_amount",
        "loss_offset_used",
        "net_profit",
        "passive_income_goal",
        "price",
        "sell_price",
        "target_price",
        "target_value",
        "taxable_profit",
        "total_current",
        "total_invested",
        "total_pnl",
        "valor_investido",
    }
)

CAMPOS_DE_QUANTIDADE = frozenset({"quantity"})

FLOAT_PERMITIDO = frozenset(
    {
        "acquired_at",
        "cancelled_at",
        "captured_at",
        "created_at",
        "credited_until",
        "current_period_end",
        "cut_at",
        "deleted_at",
        "desired_yield_bdr",
        "desired_yield_etf",
        "desired_yield_fii",
        "desired_yield_stock",
        "expires_at",
        "from",
        "granted_at",
        "ir_rate",
        "last_digest_sent_at",
        "notified_at",
        "occurred_at",
        "onboarded_at",
        "percentual_cdi",
        "processed_at",
        "qualified_at",
        "revoked_at",
        "rewarded_at",
        "score_at_suggestion",
        "ratio_from",
        "ratio_to",
        "sold_at",
        "target_pct",
        "taxa",
        "total_pnl_pct",
        "triggered_at",
        "trial_ends_at",
        "trial_started_at",
        "updated_at",
    }
)


def _colunas():
    for tabela in Base.metadata.sorted_tables:
        for coluna in tabela.columns:
            yield tabela.name, coluna


class TestNenhumFloatEmCampoMonetario:
    def test_todo_campo_de_dinheiro_usa_o_tipo_exato(self):
        errados = [
            f"{tabela}.{coluna.name}"
            for tabela, coluna in _colunas()
            if coluna.name in CAMPOS_DE_DINHEIRO and not isinstance(coluna.type, ExactNumeric)
        ]

        assert errados == []

    def test_toda_quantidade_usa_o_tipo_exato(self):
        errados = [
            f"{tabela}.{coluna.name}"
            for tabela, coluna in _colunas()
            if coluna.name in CAMPOS_DE_QUANTIDADE and not isinstance(coluna.type, ExactNumeric)
        ]

        assert errados == []

    def test_todo_float_restante_esta_declarado_como_nao_monetario(self):
        indevidos = [
            f"{tabela}.{coluna.name}"
            for tabela, coluna in _colunas()
            if isinstance(coluna.type, Float) and coluna.name not in FLOAT_PERMITIDO
        ]

        assert indevidos == [], (
            "campo Float novo: se for dinheiro, use Money; "
            "se for carimbo de tempo ou percentual, declare em FLOAT_PERMITIDO"
        )


class TestExatidaoNoArmazenamento:
    @pytest.fixture()
    def sessao(self, tmp_path):
        engine = create_engine(f"sqlite:///{tmp_path / 'exatidao.db'}")
        Base.metadata.create_all(engine)
        with Session(engine) as sessao:
            yield sessao

    def test_o_valor_volta_identico(self, sessao):
        sessao.add(
            PortfolioPosition(
                user_id="u",
                ticker="PETR4",
                quantity=Decimal("1"),
                avg_price=Decimal("0.07"),
                created_at=0.0,
                updated_at=0.0,
            )
        )
        sessao.flush()
        sessao.expire_all()

        lido = sessao.scalar(select(PortfolioPosition.avg_price))

        assert lido == Decimal("0.07")
        assert isinstance(lido, Decimal)

    def test_mil_lancamentos_de_sete_centavos_somam_setenta_reais(self, sessao):
        for i in range(1000):
            sessao.add(
                ClosedTradeDb(
                    id=i + 1,
                    user_id="u",
                    ticker="PETR4",
                    category="acoes_br",
                    quantity=Decimal("1"),
                    avg_price=Decimal("0"),
                    sell_price=Decimal("0.07"),
                    gross_profit=Decimal("0.07"),
                    ir_rate=0.0,
                    ir_amount=Decimal("0"),
                    net_profit=Decimal("0.07"),
                    sold_at=0.0,
                    created_at=0.0,
                )
            )
        sessao.flush()

        total = sum(sessao.scalars(select(ClosedTradeDb.net_profit)).all())

        assert total == Decimal("70.00")

    def test_a_soma_no_proprio_banco_tambem_fecha(self, sessao):
        for i in range(1000):
            sessao.add(
                ClosedTradeDb(
                    id=i + 1,
                    user_id="u",
                    ticker="PETR4",
                    category="acoes_br",
                    quantity=Decimal("1"),
                    avg_price=Decimal("0"),
                    sell_price=Decimal("0.07"),
                    gross_profit=Decimal("0.07"),
                    ir_rate=0.0,
                    ir_amount=Decimal("0.07"),
                    net_profit=Decimal("0"),
                    sold_at=0.0,
                    created_at=0.0,
                )
            )
        sessao.flush()

        bruto = sessao.execute(text("SELECT SUM(ir_amount) FROM closed_trades")).scalar()

        assert Decimal(bruto) / Decimal(10) ** 8 == Decimal("70.00000000")

    def test_no_sqlite_o_armazenamento_e_inteiro(self, sessao):
        sessao.add(
            PortfolioPosition(
                user_id="u",
                ticker="VALE3",
                quantity=Decimal("1"),
                avg_price=Decimal("0.07"),
                created_at=0.0,
                updated_at=0.0,
            )
        )
        sessao.flush()

        tipo = sessao.execute(
            text("SELECT typeof(avg_price) FROM portfolio WHERE ticker = 'VALE3'")
        ).scalar()

        assert tipo == "integer"


class TestOEsquemaFoiEmitido:
    def test_a_coluna_nasce_inteira_no_sqlite(self, tmp_path):
        engine = create_engine(f"sqlite:///{tmp_path / 'esquema.db'}")
        Base.metadata.create_all(engine)

        colunas = {c["name"]: c["type"] for c in inspect(engine).get_columns("portfolio")}

        assert "BIGINT" in str(colunas["avg_price"]).upper()
