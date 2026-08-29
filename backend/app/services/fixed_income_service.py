from __future__ import annotations

from datetime import UTC, date, datetime

from app.analysis.renda_fixa_analysis import DIAS_POR_MES, analyze_one
from app.collectors.rates import get_rates
from app.core.errors import NotFoundError
from app.core.pagination import clamp_limit, slice_after
from app.models.enums import AssetType, Liquidez, RendaFixaType, TaxType
from app.models.portfolio import PortfolioPosition
from app.models.renda_fixa import (
    FixedIncomeCreateRequest,
    FixedIncomeListResponse,
    FixedIncomePosition,
    FixedIncomeUpdateRequest,
    RendaFixaAsset,
)
from app.storage import portfolio_store

VENCIMENTO_PROXIMO_DIAS = 30

FIXED_INCOME_TICKER_PREFIX = "RF-"


def _today() -> date:
    return datetime.now(UTC).date()


def _parse_date(value: str | None) -> date | None:
    if not value:
        return None
    try:
        return date.fromisoformat(value[:10])
    except ValueError:
        return None


class FixedIncomeService:
    def list_positions(
        self, limit: int | None = None, cursor: str | None = None
    ) -> FixedIncomeListResponse:
        rates = get_rates()
        rows = portfolio_store.list_fixed_income()
        items = [self._mark_to_market(row, rates) for row in rows]

        page = slice_after(
            items,
            cursor,
            clamp_limit(limit),
            key=lambda i: i.data_aplicacao,
            identity=lambda i: i.id,
        )

        visiveis = [i for i in items if not i.oculto]
        total_investido = sum(i.valor_investido for i in visiveis)
        total_atual = sum(i.valor_atual for i in visiveis)
        total_rendimento = total_atual - total_investido

        if total_investido > 0:
            rendimento_pct = total_rendimento / total_investido * 100
            taxa_media = (
                sum(i.taxa_anual_efetiva_pct * i.valor_investido for i in visiveis)
                / total_investido
            )
        else:
            rendimento_pct = 0.0
            taxa_media = 0.0

        return FixedIncomeListResponse(
            items=page.items,
            next_cursor=page.next_cursor,
            has_more=page.has_more,
            total_count=len(items),
            total_investido=round(total_investido, 2),
            total_atual=round(total_atual, 2),
            total_rendimento=round(total_rendimento, 2),
            rendimento_pct=round(rendimento_pct, 2),
            taxa_media_aa=round(taxa_media, 2),
            cdi_referencia=rates["cdi_anual"],
            fonte_taxas=rates["source"],
        )

    def create(self, req: FixedIncomeCreateRequest) -> FixedIncomePosition:
        row = portfolio_store.create_fixed_income(**self._to_storage(req.model_dump()))
        return self._mark_to_market(row, get_rates())

    def update(self, position_id: int, req: FixedIncomeUpdateRequest) -> FixedIncomePosition:
        fields = self._to_storage(req.model_dump(exclude_unset=True))
        row = portfolio_store.update_fixed_income(position_id, **fields)
        if row is None:
            raise NotFoundError(f"Posição de renda fixa {position_id} não encontrada.")
        return self._mark_to_market(row, get_rates())

    def delete(self, position_id: int) -> dict:
        if not portfolio_store.delete_fixed_income(position_id):
            raise NotFoundError(f"Posição de renda fixa {position_id} não encontrada.")
        return {"deleted": position_id}

    @staticmethod
    def _to_storage(fields: dict) -> dict:
        out: dict = {}
        for key, value in fields.items():
            if isinstance(value, date):
                out[key] = value.isoformat()
            elif hasattr(value, "value"):
                out[key] = value.value
            else:
                out[key] = value
        return out

    @staticmethod
    def _as_asset(row: dict, prazo_meses: int) -> RendaFixaAsset:
        return RendaFixaAsset(
            tipo=RendaFixaType(row["tipo"]),
            valor_investido=row["valor_investido"],
            taxa=row["taxa"],
            prazo_meses=max(1, prazo_meses),
            tipo_taxa=TaxType(row["tipo_taxa"]),
            percentual_cdi=row["percentual_cdi"],
            liquidez=Liquidez(row["liquidez"]),
            nome=row["nome"],
            isento_ir=row["isento_ir"],
        )

    def _mark_to_market(self, row: dict, rates: dict) -> FixedIncomePosition:
        today = _today()
        aplicacao = _parse_date(row["data_aplicacao"]) or today
        vencimento = _parse_date(row["vencimento"])

        dias_decorridos = max((today - aplicacao).days, 0)
        meses_decorridos = dias_decorridos / DIAS_POR_MES

        prazo_total_meses = (
            max((vencimento - aplicacao).days, 1) / DIAS_POR_MES if vencimento else None
        )

        asset = self._as_asset(row, int(round(prazo_total_meses or meses_decorridos or 1)))

        atual = analyze_one(
            asset,
            cdi_anual=rates["cdi_anual"],
            selic_anual=rates["selic_anual"],
            ipca_anual=rates["ipca_anual"],
            prazo_meses_override=meses_decorridos,
        )

        no_vencimento = None
        if prazo_total_meses:
            no_vencimento = analyze_one(
                asset,
                cdi_anual=rates["cdi_anual"],
                selic_anual=rates["selic_anual"],
                ipca_anual=rates["ipca_anual"],
                prazo_meses_override=prazo_total_meses,
            )

        dias_para_vencimento = (vencimento - today).days if vencimento else None

        valor_investido = row["valor_investido"]
        rendimento = atual.valor_liquido - valor_investido

        return FixedIncomePosition(
            id=row["id"],
            nome=row["nome"],
            tipo=RendaFixaType(row["tipo"]),
            valor_investido=round(valor_investido, 2),
            taxa=row["taxa"],
            tipo_taxa=TaxType(row["tipo_taxa"]),
            percentual_cdi=row["percentual_cdi"],
            data_aplicacao=aplicacao,
            vencimento=vencimento,
            liquidez=Liquidez(row["liquidez"]),
            isento_ir=atual.isento_ir,
            oculto=row["oculto"],
            valor_atual=round(atual.valor_liquido, 2),
            rendimento_acumulado=round(rendimento, 2),
            rendimento_pct=round(rendimento / valor_investido * 100, 2)
            if valor_investido > 0
            else 0.0,
            meses_decorridos=round(meses_decorridos, 2),
            taxa_anual_efetiva_pct=atual.taxa_anual_efetiva_pct,
            yield_equivalente_pct=max(atual.taxa_liquida_aa, 0.0),
            pct_cdi_equivalente=atual.taxa_equivalente_cdi_pct,
            valor_no_vencimento=round(no_vencimento.valor_liquido, 2) if no_vencimento else None,
            rendimento_no_vencimento=round(no_vencimento.rendimento_liquido, 2)
            if no_vencimento
            else None,
            dias_para_vencimento=dias_para_vencimento,
            vencimento_proximo=(
                dias_para_vencimento is not None
                and 0 <= dias_para_vencimento <= VENCIMENTO_PROXIMO_DIAS
            ),
        )

    def as_portfolio_positions(self) -> list[PortfolioPosition]:
        listing = self.list_positions()
        return [_to_portfolio_position(item) for item in listing.items if not item.oculto]


def _to_portfolio_position(item: FixedIncomePosition) -> PortfolioPosition:
    label = f"{item.tipo.value.upper().replace('_', ' ')} · {item.taxa_anual_efetiva_pct:.2f}% a.a."
    reasons = [
        f"Rendimento líquido acumulado de {item.rendimento_pct:.2f}% "
        f"em {item.meses_decorridos:.1f} meses."
    ]
    if item.vencimento_proximo and item.dias_para_vencimento is not None:
        reasons.append(f"Vence em {item.dias_para_vencimento} dias — planeje a reaplicação.")

    return PortfolioPosition(
        ticker=f"{FIXED_INCOME_TICKER_PREFIX}{item.id}",
        name=item.nome,
        asset_type=AssetType.renda_fixa,
        quantity=1.0,
        avg_price=item.valor_investido,
        current_price=item.valor_atual,
        invested=item.valor_investido,
        current_value=item.valor_atual,
        pnl=item.rendimento_acumulado,
        pnl_pct=item.rendimento_pct,
        fair_price=None,
        margin_of_safety=None,
        verdict="HOLD",
        label=label,
        confidence=1.0,
        reasons=reasons,
        category="renda_fixa",
        category_resolved="renda_fixa",
        dividend_yield=item.yield_equivalente_pct,
        sector="Renda Fixa",
    )
