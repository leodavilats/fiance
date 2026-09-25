from __future__ import annotations

import logging
import time
from datetime import timedelta

import httpx

from app.core import cache
from app.core.brt import now_brt

from . import circuit
from .plausibility import Range

logger = logging.getLogger(__name__)

PROVIDER = "bcb"

_BCB_URL = "https://api.bcb.gov.br/dados/serie/bcdata.sgs.{sid}/dados/ultimos/1?formato=json"

_BCB_RANGE_URL = (
    "https://api.bcb.gov.br/dados/serie/bcdata.sgs.{sid}/dados"
    "?formato=json&dataInicial={inicio}&dataFinal={fim}"
)

_SERIES = {"cdi": 4389, "selic": 432, "ipca": 13522, "selic_mensal": 4189}

SELIC_AVERAGE_MONTHS = 120

_CACHE_KEY = "reference_rates:bcb"
_TTL = 24 * 3600
_TIMEOUT = 6.0

DEFAULT_CDI_ANUAL = 14.40
DEFAULT_SELIC_ANUAL = 14.40
DEFAULT_IPCA_ANUAL = 5.0

FAIXAS: dict[str, Range] = {
    "cdi_anual": Range(
        0.0, 100.0, "Juro básico anual acima de 100% não é taxa, é erro de leitura."
    ),
    "selic_anual": Range(0.0, 100.0, "Idem para a Selic."),
    "ipca_anual": Range(-30.0, 200.0, "Deflação abaixo de -30% ou inflação acima de 200% ao ano."),
}

SOURCE_BCB = "bcb"
SOURCE_CACHE_VENCIDO = "bcb_cache_vencido"
SOURCE_ESTIMATIVA = "estimativa"


def _fetch_series(client: httpx.Client, sid: int) -> float | None:
    resp = client.get(_BCB_URL.format(sid=sid))
    resp.raise_for_status()
    data = resp.json()
    if not data:
        return None
    return float(str(data[-1]["valor"]).replace(",", "."))


def _selic_media(client: httpx.Client) -> float | None:
    hoje = now_brt()
    inicio = hoje - timedelta(days=SELIC_AVERAGE_MONTHS * 31)
    resp = client.get(
        _BCB_RANGE_URL.format(
            sid=_SERIES["selic_mensal"],
            inicio=inicio.strftime("%d/%m/%Y"),
            fim=hoje.strftime("%d/%m/%Y"),
        )
    )
    resp.raise_for_status()
    valores = [float(str(p["valor"]).replace(",", ".")) for p in resp.json() or []]
    valores = [v for v in valores[-SELIC_AVERAGE_MONTHS:] if FAIXAS["selic_anual"].accepts(v)]
    if len(valores) < SELIC_AVERAGE_MONTHS // 2:
        return None
    return round(sum(valores) / len(valores), 2)


def _dentro_da_faixa(campo: str, valor: float | None) -> float | None:
    if valor is None:
        return None
    faixa = FAIXAS.get(campo)
    if faixa is not None and not faixa.accepts(valor):
        logger.warning("BCB devolveu %s = %s, fora da faixa: %s", campo, valor, faixa.reason)
        return None
    return valor


def _estimativa() -> dict:
    return {
        "cdi_anual": DEFAULT_CDI_ANUAL,
        "selic_anual": DEFAULT_SELIC_ANUAL,
        "ipca_anual": DEFAULT_IPCA_ANUAL,
        "source": SOURCE_ESTIMATIVA,
    }


def _degradar(motivo: str) -> dict:
    vencido, _idade = cache.get_with_age(_CACHE_KEY)
    if vencido:
        logger.warning("BCB indisponível (%s); servindo cache vencido.", motivo)
        return {**vencido, "source": SOURCE_CACHE_VENCIDO}

    logger.warning("BCB indisponível (%s) e sem cache; caindo na estimativa.", motivo)
    return _estimativa()


def get_rates() -> dict:
    cached = cache.get(_CACHE_KEY)
    if cached:
        return cached

    if not circuit.allows(PROVIDER):
        return _degradar("circuito aberto")

    try:
        with httpx.Client(timeout=_TIMEOUT) as client:
            cdi = _fetch_series(client, _SERIES["cdi"])
            selic = _fetch_series(client, _SERIES["selic"])
            ipca = _fetch_series(client, _SERIES["ipca"])
    except Exception as exc:
        circuit.record_failure(PROVIDER, str(exc))
        return _degradar(str(exc))

    cdi = _dentro_da_faixa("cdi_anual", cdi)
    selic = _dentro_da_faixa("selic_anual", selic)
    ipca = _dentro_da_faixa("ipca_anual", ipca)

    if not cdi or not selic:
        return _degradar("BCB devolveu dados incompletos")

    circuit.record_success(PROVIDER)

    try:
        with httpx.Client(timeout=_TIMEOUT) as client:
            selic_media = _selic_media(client)
    except Exception as exc:
        logger.warning("BCB sem a série mensal da Selic (%s); a média fica ausente.", exc)
        selic_media = None

    rates = {
        "cdi_anual": round(cdi, 2),
        "selic_anual": round(selic, 2),
        "ipca_anual": round(ipca, 2) if ipca is not None else DEFAULT_IPCA_ANUAL,
        "selic_media_10a": selic_media,
        "source": SOURCE_BCB,
        "fetched_at": time.time(),
    }
    cache.set(_CACHE_KEY, rates, _TTL)
    return rates
