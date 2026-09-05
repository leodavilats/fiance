from __future__ import annotations

import logging

from app.analysis.classify import auto_category, resolve_category
from app.collectors.universal import UnsupportedTickerError, detect_type
from app.core.brt import day_timestamp
from app.core.money import ZERO, quantize, to_float
from app.ledger.apuracao import CATEGORIA_PADRAO, Apuracao, VendaApurada, apurar
from app.storage import ledger_store, portfolio_store

logger = logging.getLogger("fiance.apuracao")


def _categoria_por_ticker(ticker: str) -> str:
    try:
        return auto_category(detect_type(ticker))
    except UnsupportedTickerError:
        logger.debug("Ticker %s sem classificação; apurando como %s.", ticker, CATEGORIA_PADRAO)
        return CATEGORIA_PADRAO


def mapa_de_categorias(user_id: str | None = None) -> dict[str, str]:
    mapa: dict[str, str] = {}

    for item in portfolio_store.list_positions(user_id):
        ticker = item["ticker"].strip().upper()
        mapa[ticker] = resolve_category(item["category"], _categoria_por_ticker(ticker))

    for simbolo in ledger_store.symbols(user_id=user_id):
        ticker = simbolo.strip().upper()
        if ticker not in mapa:
            mapa[ticker] = _categoria_por_ticker(ticker)

    return mapa


def apuracao(user_id: str | None = None) -> Apuracao:
    return apurar(
        ledger_store.list_entries(user_id=user_id),
        mapa_de_categorias(user_id=user_id),
    )


def _linha(apuracao_completa: Apuracao, venda: VendaApurada) -> dict:
    mes = apuracao_completa.mes(venda.mes, venda.categoria)
    imposto = apuracao_completa.ir_da_venda(venda)

    return {
        "id": venda.entry_id or 0,
        "ticker": venda.ticker,
        "category": venda.categoria,
        "quantity": venda.quantity,
        "avg_price": venda.avg_price,
        "sell_price": venda.sell_price,
        "gross_profit": to_float(quantize(venda.result)),
        "ir_rate": to_float(mes.ir_rate) if mes else 0.0,
        "ir_amount": to_float(quantize(imposto)),
        "net_profit": to_float(quantize(venda.result - imposto)),
        "loss_offset_used": 0.0,
        "taxable_profit": to_float(quantize(max(venda.result - imposto, ZERO))),
        "loss_compensable": bool(mes.loss_compensable) if mes else True,
        "sold_at": day_timestamp(venda.traded_on),
        "month": venda.mes,
        "ir_is_prorated": bool(mes and mes.ir_amount > ZERO),
    }


def vendas_apuradas(user_id: str | None = None) -> tuple[list[dict], Apuracao]:
    completa = apuracao(user_id=user_id)
    linhas = [_linha(completa, venda) for venda in completa.vendas]
    linhas.sort(key=lambda linha: (linha["sold_at"], linha["id"]), reverse=True)
    return linhas, completa


def saldos_de_prejuizo(completa: Apuracao) -> list[dict]:
    por_categoria: dict[str, dict] = {}

    for mes in completa.meses:
        bucket = por_categoria.setdefault(
            mes.categoria, {"realized_loss": ZERO, "offset_used": ZERO}
        )
        bucket["realized_loss"] += mes.loss_generated
        bucket["offset_used"] += mes.loss_offset_used

    return [
        {
            "category": categoria,
            "realized_loss": to_float(quantize(valores["realized_loss"])),
            "offset_used": to_float(quantize(valores["offset_used"])),
            "available": to_float(
                quantize(max(valores["realized_loss"] - valores["offset_used"], ZERO))
            ),
        }
        for categoria, valores in sorted(por_categoria.items())
        if valores["realized_loss"] > ZERO or valores["offset_used"] > ZERO
    ]


def resultado_bruto_entre(inicio: float, fim: float, user_id: str | None = None) -> float:
    completa = apuracao(user_id=user_id)
    total = ZERO
    for venda in completa.vendas:
        quando = day_timestamp(venda.traded_on)
        if inicio <= quando < fim:
            total += venda.result
    return to_float(quantize(total))
