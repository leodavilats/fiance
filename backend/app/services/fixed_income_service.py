from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from app.analysis.renda_fixa_analysis import DIAS_POR_MES, RendaFixaAnalysisResult, analyze_one
from app.collectors.rates import get_rates
from app.core.brt import now_brt
from app.core.errors import NotFoundError
from app.core.money import quantize, sum_money, to_float
from app.core.pagination import clamp_limit, paginate
from app.models.enums import AssetType, Liquidez, RendaFixaType, TaxType
from app.models.portfolio import PortfolioPosition
from app.models.renda_fixa import (
    FixedIncomeCreateRequest,
    FixedIncomeListResponse,
    FixedIncomePosition,
    FixedIncomeUpdateRequest,
    RendaFixaAsset,
)
from app.services.milestones import record_holdings_milestones
from app.storage import portfolio_store

VENCIMENTO_PROXIMO_DIAS = 30

FIXED_INCOME_TICKER_PREFIX = "RF-"


def _today() -> date:
    return now_brt().date()


def _parse_date(value: str | None) -> date | None:
    if not value:
        return None
    try:
        return date.fromisoformat(value[:10])
    except ValueError:
        return None


@dataclass(frozen=True)
class _Marcacao:
    today: date
    aplicacao: date
    vencimento: date | None
    meses_decorridos: float
    prazo_total_meses: float | None
    asset: RendaFixaAsset
    atual: RendaFixaAnalysisResult


class FixedIncomeService:
    def list_positions(
        self, limit: int | None = None, cursor: str | None = None
    ) -> FixedIncomeListResponse:
        rates = get_rates()
        page_size = clamp_limit(limit)
        page = paginate(
            portfolio_store.list_fixed_income(limit=page_size, cursor=cursor),
            page_size,
            key=lambda row: row["data_aplicacao"],
            identity=lambda row: row["id"],
        )

        investido: list[Decimal] = []
        atual: list[Decimal] = []
        ponderada = 0.0
        for row in portfolio_store.list_visible_fixed_income_valuation():
            analise = self._analyze_today(row, rates).atual
            valor_investido = quantize(row["valor_investido"])
            investido.append(valor_investido)
            atual.append(quantize(analise.valor_liquido))
            ponderada += analise.taxa_anual_efetiva_pct * to_float(valor_investido)

        total_investido = sum_money(investido)
        total_atual = sum_money(atual)
        total_rendimento = total_atual - total_investido

        if total_investido > 0:
            rendimento_pct = to_float(total_rendimento) / to_float(total_investido) * 100
            taxa_media = ponderada / to_float(total_investido)
        else:
            rendimento_pct = 0.0
            taxa_media = 0.0

        return FixedIncomeListResponse(
            items=[self._mark_to_market(row, rates) for row in page.items],
            next_cursor=page.next_cursor,
            has_more=page.has_more,
            total_count=portfolio_store.count_fixed_income(),
            total_investido=to_float(total_investido),
            total_atual=to_float(total_atual),
            total_rendimento=to_float(total_rendimento),
            rendimento_pct=round(rendimento_pct, 2),
            taxa_media_aa=round(taxa_media, 2),
            cdi_referencia=rates["cdi_anual"],
            fonte_taxas=rates["source"],
        )

    def create(self, req: FixedIncomeCreateRequest) -> FixedIncomePosition:
        row = portfolio_store.create_fixed_income(**self._to_storage(req.model_dump()))
        record_holdings_milestones()
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
            valor_investido=to_float(row["valor_investido"]),
            taxa=row["taxa"],
            prazo_meses=max(1, prazo_meses),
            tipo_taxa=TaxType(row["tipo_taxa"]),
            percentual_cdi=row["percentual_cdi"],
            liquidez=Liquidez(row["liquidez"]),
            nome=row.get("nome"),
            isento_ir=row["isento_ir"],
        )

    def _analyze_today(self, row, rates: dict) -> _Marcacao:
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
            prazo_dias_override=dias_decorridos,
        )
        return _Marcacao(
            today=today,
            aplicacao=aplicacao,
            vencimento=vencimento,
            meses_decorridos=meses_decorridos,
            prazo_total_meses=prazo_total_meses,
            asset=asset,
            atual=atual,
        )

    def _mark_to_market(self, row: dict, rates: dict) -> FixedIncomePosition:
        marcacao = self._analyze_today(row, rates)
        today = marcacao.today
        aplicacao = marcacao.aplicacao
        vencimento = marcacao.vencimento
        meses_decorridos = marcacao.meses_decorridos
        prazo_total_meses = marcacao.prazo_total_meses
        asset = marcacao.asset
        atual = marcacao.atual

        no_vencimento = None
        if prazo_total_meses:
            no_vencimento = analyze_one(
                asset,
                cdi_anual=rates["cdi_anual"],
                selic_anual=rates["selic_anual"],
                ipca_anual=rates["ipca_anual"],
                prazo_meses_override=prazo_total_meses,
                prazo_dias_override=max((vencimento - aplicacao).days, 1),
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

    def liquidez_diaria_total(self) -> float:
        rates = get_rates()
        return round(
            sum(
                self._mark_to_market(row, rates).valor_atual
                for row in portfolio_store.list_fixed_income()
                if row.get("liquidez") == Liquidez.diaria.value
            ),
            2,
        )

    def as_portfolio_positions(self) -> list[PortfolioPosition]:
        rates = get_rates()
        return [
            _to_portfolio_position(self._mark_to_market(row, rates))
            for row in portfolio_store.list_fixed_income()
            if not row["oculto"]
        ]


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
