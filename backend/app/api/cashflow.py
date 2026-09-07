from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException

from app.cashflow import CashEntry, CashKind, Debt
from app.collectors import rates
from app.models.cashflow import (
    CascadeResponse,
    CashEntryRequest,
    CashEntryResponse,
    CashVocabularyResponse,
    DebtRequest,
    DebtResponse,
    MarkPaidRequest,
    MonthResponse,
    SurplusResponse,
)
from app.services import cashflow_service
from app.services.benchmark_service import BenchmarkService
from app.storage import portfolio_store

logger = logging.getLogger("fiance.api.cashflow")

router = APIRouter()


async def _referencia_de_rendimento() -> tuple[float | None, bool, float | None]:
    """O que a carteira da pessoa rende ao mês, e o CDI como segunda opção."""
    tem_carteira = portfolio_store.has_holdings()

    cdi_anual: float | None = None
    try:
        cdi_anual = rates.get_rates().get("cdi_anual")
    except Exception as exc:
        logger.warning("CDI indisponível para a régua de dívida: %s", exc)

    if not tem_carteira:
        return None, False, cdi_anual

    try:
        benchmark = await BenchmarkService().get_benchmark()
        total_pct = benchmark.portfolio_return_pct
    except Exception as exc:
        logger.warning("Retorno da carteira indisponível: %s", exc)
        return None, False, cdi_anual

    if not benchmark.points:
        return None, False, cdi_anual

    # O retorno vem acumulado na série. Mensalizar por composto, e não dividir pelo número de
    # pontos: a série não tem passo mensal garantido.
    meses = max(1.0, len(benchmark.points) / 21.0)
    mensal = ((1.0 + total_pct / 100.0) ** (1.0 / meses) - 1.0) * 100.0
    return mensal, True, cdi_anual


def _entry_do_request(req: CashEntryRequest) -> CashEntry:
    try:
        return CashEntry(
            kind=CashKind(req.kind),
            category=req.category,
            description=req.description,
            amount=req.amount,
            due_on=req.due_on,
            paid_on=req.paid_on,
        )
    except Exception as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.get("/cashflow/vocabulary", response_model=CashVocabularyResponse)
async def vocabulario() -> CashVocabularyResponse:
    return CashVocabularyResponse()


@router.get("/cashflow/month", response_model=MonthResponse)
async def mes(month: str | None = None) -> MonthResponse:
    projecao = cashflow_service.mes(referencia=month)
    return MonthResponse(**projecao.as_dict())


@router.get("/cashflow/entries", response_model=list[CashEntryResponse])
async def lancamentos() -> list[CashEntryResponse]:
    return [
        CashEntryResponse(
            id=e.id or 0,
            kind=e.kind.value,
            category=e.category,
            description=e.description,
            amount=e.amount,
            due_on=e.due_on,
            paid_on=e.paid_on,
            derived=e.derived,
        )
        for e in cashflow_service.entradas()
    ]


@router.post("/cashflow/entries", response_model=CashEntryResponse, status_code=201)
async def lancar(req: CashEntryRequest) -> CashEntryResponse:
    entry = _entry_do_request(req)
    novo_id = cashflow_service.registrar(entry)

    return CashEntryResponse(
        id=novo_id,
        kind=entry.kind.value,
        category=entry.category,
        description=entry.description,
        amount=entry.amount,
        due_on=entry.due_on,
        paid_on=entry.paid_on,
        derived=False,
    )


@router.post("/cashflow/entries/{entry_id}/paid", status_code=204)
async def marcar_paga(entry_id: int, req: MarkPaidRequest) -> None:
    cashflow_service.marcar_paga(entry_id, req.paid_on)


@router.delete("/cashflow/entries/{entry_id}", status_code=204)
async def apagar(entry_id: int) -> None:
    cashflow_service.apagar(entry_id)


@router.get("/cashflow/debts", response_model=list[DebtResponse])
async def dividas() -> list[DebtResponse]:
    mensal, tem_carteira, cdi_anual = await _referencia_de_rendimento()
    lidas = cashflow_service.dividas(
        referencia_mensal=mensal, tem_carteira=tem_carteira, cdi_anual=cdi_anual
    )
    return [DebtResponse(**d) for d in lidas]


@router.post("/cashflow/debts", response_model=DebtResponse, status_code=201)
async def cadastrar_divida(req: DebtRequest) -> DebtResponse:
    try:
        debt = Debt(
            kind=req.kind,
            description=req.description,
            balance=req.balance,
            monthly_rate=req.monthly_rate,
        )
    except Exception as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    cashflow_service.cadastrar_divida(debt)

    mensal, tem_carteira, cdi_anual = await _referencia_de_rendimento()
    lidas = cashflow_service.dividas(
        referencia_mensal=mensal, tem_carteira=tem_carteira, cdi_anual=cdi_anual
    )
    nova = next((d for d in lidas if d["description"] == debt.description.strip()), lidas[-1])
    return DebtResponse(**nova)


@router.post("/cashflow/debts/{debt_id}/settled", status_code=204)
async def quitar_divida(debt_id: int) -> None:
    cashflow_service.quitar_divida(debt_id)


@router.get("/surplus", response_model=SurplusResponse)
async def sobra(month: str | None = None) -> SurplusResponse:
    """A ponte: o mês projetado e a ordem do que fazer com o piso da sobra."""
    mensal, tem_carteira, cdi_anual = await _referencia_de_rendimento()

    projecao, cascata = cashflow_service.sobra(
        referencia_mensal=mensal,
        tem_carteira=tem_carteira,
        cdi_anual=cdi_anual,
        mes_referencia=month,
    )

    return SurplusResponse(
        month=MonthResponse(**projecao.as_dict()),
        cascade=CascadeResponse(**cascata.as_dict()),
        has_cash=cashflow_service.tem_caixa(),
    )
