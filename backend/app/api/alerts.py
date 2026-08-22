from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, field_validator

from app.collectors.universal import fetch_many
from app.storage import portfolio_store

router = APIRouter()


class AlertCreate(BaseModel):
    ticker: str
    condition: str
    target_price: float
    note: str | None = None

    @field_validator("condition")
    @classmethod
    def validate_condition(cls, v: str) -> str:
        if v not in ("above", "below"):
            raise ValueError("condition must be 'above' or 'below'")
        return v

    @field_validator("target_price")
    @classmethod
    def validate_price(cls, v: float) -> float:
        if v <= 0:
            raise ValueError("target_price must be positive")
        return v


class AlertResponse(BaseModel):
    id: int
    ticker: str
    condition: str
    target_price: float
    note: str | None
    created_at: float
    triggered_at: float | None


class AlertTriggered(BaseModel):
    id: int
    ticker: str
    condition: str
    target_price: float
    note: str | None
    current_price: float


@router.get("/alerts", response_model=list[AlertResponse])
async def list_alerts() -> list[AlertResponse]:
    return [AlertResponse(**a) for a in portfolio_store.list_price_alerts()]


@router.post("/alerts/check", response_model=list[AlertTriggered])
@router.get("/alerts/check", response_model=list[AlertTriggered])
async def check_alerts() -> list[AlertTriggered]:
    """Verifica alertas e marca os disparados, igual ao job de notificação."""
    alerts = portfolio_store.list_price_alerts()
    active = [a for a in alerts if a["triggered_at"] is None]
    if not active:
        return []

    tickers = list({a["ticker"] for a in active})
    snapshots = await fetch_many(tickers)
    price_map: dict[str, float] = {
        s.symbol.upper(): s.price for s in snapshots if s.price is not None
    }

    triggered: list[AlertTriggered] = []
    for alert in active:
        price = price_map.get(alert["ticker"].upper())
        if price is None:
            continue
        hit = (alert["condition"] == "below" and price <= alert["target_price"]) or (
            alert["condition"] == "above" and price >= alert["target_price"]
        )
        if hit:
            triggered.append(
                AlertTriggered(
                    id=alert["id"],
                    ticker=alert["ticker"],
                    condition=alert["condition"],
                    target_price=alert["target_price"],
                    note=alert["note"],
                    current_price=round(price, 2),
                )
            )
            portfolio_store.mark_alert_triggered(alert["id"])

    return triggered


@router.post("/alerts", response_model=AlertResponse, status_code=201)
async def create_alert(body: AlertCreate) -> AlertResponse:
    alert_id = portfolio_store.create_price_alert(
        ticker=body.ticker,
        condition=body.condition,
        target_price=body.target_price,
        note=body.note,
    )
    alerts = portfolio_store.list_price_alerts()
    created = next((a for a in alerts if a["id"] == alert_id), None)
    if not created:
        raise HTTPException(status_code=500, detail="Falha ao criar alerta")
    return AlertResponse(**created)


@router.delete("/alerts/{alert_id}")
async def delete_alert(alert_id: int) -> dict:
    deleted = portfolio_store.delete_price_alert(alert_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Alerta não encontrado")
    return {"deleted": alert_id}
