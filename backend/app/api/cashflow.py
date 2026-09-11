from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException

from app.cashflow import CashEntry, CashKind, Debt
from app.models.cashflow import (
    CascadeResponse,
    CashEntryBatchRequest,
    CashEntryRequest,
    CashEntryResponse,
    CashVocabularyResponse,
    DebtRequest,
    DebtResponse,
    MarkPaidRequest,
    MonthResponse,
    MonthTemplateResponse,
    SurplusResponse,
)
from app.services import GoalService, cashflow_service
from app.services.rendimento_referencia import referencia_de_rendimento

logger = logging.getLogger("fiance.api.cashflow")

router = APIRouter()

goal_service = GoalService()


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
    return _resposta(entry, cashflow_service.registrar(entry))


def _resposta(entry: CashEntry, entry_id: int | None = None) -> CashEntryResponse:
    return CashEntryResponse(
        id=entry_id if entry_id is not None else (entry.id or 0),
        kind=entry.kind.value,
        category=entry.category,
        description=entry.description,
        amount=entry.amount,
        due_on=entry.due_on,
        paid_on=entry.paid_on,
        derived=entry.derived,
    )


@router.post("/cashflow/entries/batch", response_model=list[CashEntryResponse], status_code=201)
async def lancar_em_lote(req: CashEntryBatchRequest) -> list[CashEntryResponse]:
    """Grava o lote inteiro ou nenhum: meio molde de mês é pior que molde nenhum."""
    entries = [_entry_do_request(e) for e in req.entries]
    ids = cashflow_service.registrar_varias(entries)
    return [_resposta(e, i) for e, i in zip(entries, ids, strict=True)]


@router.put("/cashflow/entries/{entry_id}", response_model=CashEntryResponse)
async def editar(entry_id: int, req: CashEntryRequest) -> CashEntryResponse:
    entry = _entry_do_request(req)
    return _resposta(cashflow_service.editar(entry_id, entry))


@router.get("/cashflow/month/template", response_model=MonthTemplateResponse)
async def molde_do_mes(target: str, source: str | None = None) -> MonthTemplateResponse:
    """O mês anterior lido como molde do destino, sem gravar nada."""
    origem = source or cashflow_service.mes_anterior(target)
    try:
        candidatos = cashflow_service.molde(origem, target)
    except Exception as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    return MonthTemplateResponse(
        source=origem,
        target=target,
        candidates=[c.as_dict() for c in candidatos],
    )


@router.post("/cashflow/entries/{entry_id}/paid", status_code=204)
async def marcar_paga(entry_id: int, req: MarkPaidRequest) -> None:
    cashflow_service.marcar_paga(entry_id, req.paid_on)


@router.delete("/cashflow/entries/{entry_id}", status_code=204)
async def apagar(entry_id: int) -> None:
    cashflow_service.apagar(entry_id)


@router.get("/cashflow/debts", response_model=list[DebtResponse])
async def dividas() -> list[DebtResponse]:
    mensal, tem_carteira, cdi_anual = await referencia_de_rendimento()
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

    mensal, tem_carteira, cdi_anual = await referencia_de_rendimento()
    lidas = cashflow_service.dividas(
        referencia_mensal=mensal, tem_carteira=tem_carteira, cdi_anual=cdi_anual
    )
    nova = next((d for d in lidas if d["description"] == debt.description.strip()), lidas[-1])
    return DebtResponse(**nova)


@router.post("/cashflow/debts/{debt_id}/settled", status_code=204)
async def quitar_divida(debt_id: int) -> None:
    cashflow_service.quitar_divida(debt_id)


# A alocação-alvo decide a ordem do aporte, e a cascata precisa saber se ela é da pessoa: com o
# padrão do produto (30/35/15/15/5), dizer "o alvo que você declarou" seria inventar objetivo
# alheio. A distância em p.p. de cada classe não entra aqui de propósito — ela exige avaliar a
# carteira a preço de mercado, que é a chamada mais cara do produto, e é o que `/quick-invest`
# responde quando a tela pergunta o destino.
_ORDEM_POR_META = (
    "O destino sai da sua alocação-alvo: entra primeiro a classe que está mais abaixo do alvo "
    "que você declarou."
)


@router.get("/surplus", response_model=SurplusResponse)
async def sobra(month: str | None = None) -> SurplusResponse:
    """A ponte: o mês projetado e a ordem do que fazer com o piso da sobra."""
    mensal, tem_carteira, cdi_anual = await referencia_de_rendimento()

    projecao, cascata = cashflow_service.sobra(
        referencia_mensal=mensal,
        tem_carteira=tem_carteira,
        cdi_anual=cdi_anual,
        mes_referencia=month,
        desvio_de_meta=_ORDEM_POR_META if goal_service.has_declared_goals() else None,
    )

    return SurplusResponse(
        month=MonthResponse(**projecao.as_dict()),
        cascade=CascadeResponse(**cascata.as_dict()),
        has_cash=cashflow_service.tem_caixa(),
    )
