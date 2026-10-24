from __future__ import annotations

import asyncio
import logging
import re
import threading
from dataclasses import dataclass
from datetime import date, datetime
from datetime import time as hora
from zoneinfo import ZoneInfo

from app.collectors import circuit, mercado, plausibility
from app.core import cache
from app.core.brt import now_brt
from app.core.observability import record_external_call
from app.core.pregao import proxima_carga, ultimo_pregao_carregado
from app.core.universe import get_type_map
from app.models.enums import AssetType

logger = logging.getLogger(__name__)


class UnsupportedTickerError(ValueError):
    pass


REVALIDAR = 30 * 60

DIV_TTL = 24 * 3600


def validade(pregao: date | None, momento: datetime | None = None) -> int:
    agora = momento or now_brt()
    if pregao is None or pregao < ultimo_pregao_carregado(agora):
        return REVALIDAR
    return max(60, int((proxima_carga(agora) - agora).total_seconds()))


_FETCH_SEMAPHORE = asyncio.Semaphore(30)

KNOWN_UNITS = {
    "SANB11",
    "TAEE11",
    "BPAC11",
    "KLBN11",
    "SAPR11",
    "ALUP11",
    "ENGI11",
    "IGTI11",
    "RNEW11",
    "BRBI11",
}

KNOWN_ETFS = {
    "BOVA11",
    "BOVV11",
    "BOVB11",
    "BOAC11",
    "XBOV11",
    "PIBB11",
    "SMAL11",
    "SMAC11",
    "DIVO11",
    "BBSD11",
    "ECOO11",
    "GOVE11",
    "ISUS11",
    "MATB11",
    "XFIX11",
    "IVVB11",
    "NASD11",
    "SPXI11",
    "ACWI11",
    "WRLD11",
    "XINA11",
    "EURP11",
    "JAPN11",
    "BDRX11",
    "GOLD11",
    "IMAB11",
    "IB5M11",
    "B5P211",
    "IRFM11",
    "LFTS11",
    "FIXA11",
}

_ROOT = r"[A-Z][A-Z0-9]{3}"
_BDR = re.compile(rf"^{_ROOT}3\d$")
_ENDS_11 = re.compile(rf"^{_ROOT}11$")
_BR_STOCK = re.compile(rf"^{_ROOT}\d{{1,2}}$")

_SUBTYPE_TO_ASSET_TYPE = {
    "stock": AssetType.br_stock,
    "fii": AssetType.fii,
    "bdr": AssetType.bdr,
    "etf": AssetType.etf,
}


def detect_type(symbol: str) -> AssetType:
    s = symbol.strip().upper()
    base = s[:-3] if s.endswith(".SA") else s

    known_type = _SUBTYPE_TO_ASSET_TYPE.get(get_type_map().get(base))
    if known_type:
        return known_type

    if _BDR.match(base):
        return AssetType.bdr

    if _ENDS_11.match(base):
        if base in KNOWN_UNITS:
            return AssetType.br_stock
        if base in KNOWN_ETFS:
            return AssetType.etf
        return AssetType.fii

    if _BR_STOCK.match(base):
        return AssetType.br_stock

    raise UnsupportedTickerError(
        f"Tipo de ativo não suportado para {symbol!r} — este sistema cobre apenas "
        "ações BR, BDRs, FIIs e ETFs da B3."
    )


def _base_symbol(symbol: str) -> str:
    s = symbol.strip().upper()
    if s.endswith(".SA"):
        return s[:-3]
    return s


@dataclass
class AssetSnapshot:
    symbol: str
    asset_type: AssetType
    name: str | None
    sector: str | None
    currency: str | None
    price: float | None
    market_cap: float | None
    pe_ratio: float | None
    pb_ratio: float | None
    eps: float | None
    book_value: float | None
    roe: float | None
    dividend_yield: float | None
    debt_to_equity: float | None
    profit_margin: float | None
    revenue_growth: float | None
    fifty_two_week_high: float | None
    fifty_two_week_low: float | None

    change_percent_day: float | None = None
    as_of: float = 0.0
    source: str = "b3"
    net_income_history: list[float | None] | None = None
    equity_history: list[float | None] | None = None
    net_income_ttm: float | None = None

    def to_dict(self) -> dict:
        return self.__dict__.copy()


def _pct(numerador: float | None, denominador: float | None) -> float | None:
    if numerador is None or denominador is None or denominador <= 0:
        return None
    return round(numerador / denominador * 100.0, 4)


def _ultima_versao(linhas: list[dict]) -> dict[tuple[str, str], dict]:
    escolhidas: dict[tuple[str, str], dict] = {}
    for linha in sorted(linhas, key=lambda x: x["versao"]):
        escolhidas[(linha["tipo"], linha["data_referencia"])] = linha
    return escolhidas


def _acumulado_por_fim(resultados: list[dict]) -> dict[str, dict]:
    por_fim: dict[str, dict] = {}
    for linha in sorted(_ultima_versao(resultados).values(), key=lambda x: x["tipo"] != "DFP"):
        por_fim.setdefault(linha["fim_exercicio"], linha)
    return por_fim


def _doze_meses(por_fim: dict[str, dict], campo: str) -> float | None:
    if not por_fim:
        return None
    fim = max(por_fim)
    atual = por_fim[fim].get(campo)
    if atual is None:
        return None
    if fim[5:] == "12-31":
        return atual
    ano = int(fim[:4])
    anual = (por_fim.get(f"{ano - 1}-12-31") or {}).get(campo)
    mesmo_ponto = (por_fim.get(f"{ano - 1}{fim[4:]}") or {}).get(campo)
    if anual is None or mesmo_ponto is None:
        return None
    return atual + anual - mesmo_ponto


_EXERCICIOS_NA_SERIE = 5
_MERCADO_MINIMO_SOBRE_PATRIMONIO = 0.02


def _mais_negociado(irmaos: list[dict], prefixo: str) -> float | None:
    candidatos = [i for i in irmaos if (i["classe"] or "").startswith(prefixo) and i["preco"]]
    if not candidatos:
        return None
    return max(candidatos, key=lambda i: i["volume_medio"] or 0)["preco"]


def _fundamentos(pacote: dict) -> dict:
    ativo = pacote["ativo"]
    por_fim = _acumulado_por_fim(pacote["resultados"])
    balancos = {
        linha["data_referencia"]: linha for linha in _ultima_versao(pacote["balancos"]).values()
    }
    ultimo_balanco = balancos[max(balancos)] if balancos else {}
    patrimonio = ultimo_balanco.get("patrimonio_controladores")

    lucro_12m = _doze_meses(por_fim, "lucro_controladores")
    receita_12m = _doze_meses(por_fim, "receita")
    anuais = sorted((f for f in por_fim if f[5:] == "12-31"), reverse=True)
    lucros = [por_fim[f].get("lucro_controladores") for f in anuais[:_EXERCICIOS_NA_SERIE]]
    patrimonios = [
        (balancos.get(f) or {}).get("patrimonio_controladores")
        for f in anuais[:_EXERCICIOS_NA_SERIE]
    ]
    receitas = [por_fim[f].get("receita") for f in anuais[:2]]
    crescimento = None
    if len(receitas) == 2 and receitas[0] is not None and receitas[1] and receitas[1] > 0:
        crescimento = round((receitas[0] / receitas[1] - 1) * 100.0, 4)

    ordinarias = ativo.get("acoes_ordinarias") or 0
    preferenciais = ativo.get("acoes_preferenciais") or 0
    irmaos = pacote["irmaos"]
    preco_on = _mais_negociado(irmaos, "ON")
    preco_pn = _mais_negociado(irmaos, "PN")
    referencia = (
        preco_on
        if preferenciais == 0 or (preco_on and ordinarias >= preferenciais)
        else preco_pn or preco_on
    )
    preco_on = preco_on or referencia
    preco_pn = preco_pn or referencia
    valor_de_mercado = None
    if referencia and ordinarias + preferenciais > 0:
        valor_de_mercado = (preco_on or 0) * ordinarias + (preco_pn or 0) * preferenciais
        if (
            patrimonio
            and patrimonio > 0
            and valor_de_mercado / patrimonio < (_MERCADO_MINIMO_SOBRE_PATRIMONIO)
        ):
            ordinarias, preferenciais = ordinarias * 1000, preferenciais * 1000
            valor_de_mercado *= 1000

    acoes = ordinarias + preferenciais
    por_papel = None
    if acoes > 0 and referencia:
        por_papel = 1.0 if ativo["classe"] != "UNT" else round(ativo["preco"] / referencia)
    lpa = lucro_12m / acoes * por_papel if lucro_12m is not None and por_papel else None
    vpa = patrimonio / acoes * por_papel if patrimonio is not None and por_papel else None

    return {
        "market_cap": valor_de_mercado,
        "pe_ratio": round(ativo["preco"] / lpa, 4) if lpa else None,
        "pb_ratio": round(ativo["preco"] / vpa, 4) if vpa and vpa > 0 else None,
        "eps": lpa,
        "book_value": vpa,
        "roe": _pct(lucro_12m, patrimonio),
        "debt_to_equity": _pct(ultimo_balanco.get("divida_bruta"), patrimonio),
        "profit_margin": _pct(lucro_12m, receita_12m) if receita_12m else None,
        "revenue_growth": crescimento,
        "net_income_history": lucros or None,
        "equity_history": patrimonios or None,
        "net_income_ttm": lucro_12m,
    }


_BRT = ZoneInfo("America/Sao_Paulo")
_FECHAMENTO = hora(18, 0)


def _instante_do_fechamento(dia: str) -> float:
    return datetime.combine(datetime.fromisoformat(dia).date(), _FECHAMENTO, _BRT).timestamp()


def snapshot_do_pacote(pacote: dict, symbol: str, asset_type: AssetType) -> AssetSnapshot | None:
    ativo = pacote["ativo"]
    preco = ativo.get("preco")
    if not preco:
        return None

    numeros = {
        "price": preco,
        "market_cap": None,
        "pe_ratio": None,
        "pb_ratio": None,
        "eps": None,
        "book_value": None,
        "roe": None,
        "dividend_yield": (
            round(ativo["proventos_12m"] / preco * 100, 2) if ativo.get("proventos_12m") else None
        ),
        "debt_to_equity": None,
        "profit_margin": None,
        "revenue_growth": None,
        "fifty_two_week_high": ativo.get("maxima_52s"),
        "fifty_two_week_low": ativo.get("minima_52s"),
        "change_percent_day": (
            round((preco / ativo["preco_anterior"] - 1) * 100, 4)
            if ativo.get("preco_anterior")
            else None
        ),
    }
    series = {"net_income_history": None, "equity_history": None, "net_income_ttm": None}
    if ativo["tipo"] == "stock":
        fundamentos = _fundamentos(pacote)
        for chave in series:
            series[chave] = fundamentos.pop(chave)
        numeros.update(fundamentos)
    elif ativo["tipo"] == "fii" and ativo.get("valor_patrimonial_cota"):
        numeros["book_value"] = ativo["valor_patrimonial_cota"]
        numeros["pb_ratio"] = round(preco / ativo["valor_patrimonial_cota"], 4)

    numeros, veredito = plausibility.screen(numeros, symbol=symbol.upper())
    if not veredito.accepted:
        record_external_call("mercado.plausibility", ok=False)
        return None

    return AssetSnapshot(
        symbol=symbol.upper(),
        as_of=_instante_do_fechamento(ativo["data"]),
        source="b3",
        asset_type=asset_type,
        name=ativo.get("nome") or symbol.upper(),
        sector=ativo.get("setor"),
        currency="BRL",
        **series,
        **numeros,
    )


_PROVEDOR = "mercado"

_AUSENTE_TTL = 6 * 3600

_AUSENTE = {"__ausente__": True}

_prefetch_lock = threading.Lock()

_PREFETCH_ESPERA = 5.0

_LOTE = 50


def _raw_key(base: str) -> str:
    return f"mercado_raw:{base}"


_PREGAO_KEY = "mercado_pregao_da_base"


def pregao_da_base() -> date | None:
    cached = cache.get(_PREGAO_KEY)
    if cached:
        return date.fromisoformat(cached)
    if not circuit.allows(_PROVEDOR):
        return None
    try:
        pregao = mercado.ler_pregao_da_base()
    except Exception as e:
        logger.warning("A base de mercado não disse até que pregão vai: %s", e)
        return None
    if pregao is not None:
        cache.set(_PREGAO_KEY, pregao.isoformat(), validade(pregao))
    return pregao


def validade_do_mercado() -> int:
    return validade(pregao_da_base())


def _guardar_raw(base: str, pacote: dict | None, prazo: int) -> None:
    cache.set(_raw_key(base), pacote if pacote else _AUSENTE, prazo if pacote else _AUSENTE_TTL)


def _ler_raw(base: str) -> dict | None:
    cached = cache.get(_raw_key(base))
    if cached is None:
        return None
    return {} if cached.get("__ausente__") else cached


def _buscar(bases: list[str]) -> bool:
    try:
        pacotes = mercado.ler_pacotes(bases)
        record_external_call(_PROVEDOR, ok=True)
        circuit.record_success(_PROVEDOR)
    except Exception as e:
        record_external_call(_PROVEDOR, ok=False)
        circuit.record_failure(_PROVEDOR, type(e).__name__)
        logger.warning("A base de mercado falhou para %d tickers: %s", len(bases), e)
        return False
    prazo = validade_do_mercado()
    for base in bases:
        _guardar_raw(base, pacotes.get(base), prazo)
    return True


def prefetch(symbols: list[str]) -> int:
    bases = list(dict.fromkeys(_base_symbol(s) for s in symbols if s))
    faltantes = [b for b in bases if _ler_raw(b) is None]
    if not faltantes or not circuit.allows(_PROVEDOR):
        return 0

    exclusivo = _prefetch_lock.acquire(timeout=_PREFETCH_ESPERA)
    pedidos = 0
    try:
        for inicio in range(0, len(faltantes), _LOTE):
            lote = [b for b in faltantes[inicio : inicio + _LOTE] if _ler_raw(b) is None]
            if not lote:
                continue
            if not circuit.allows(_PROVEDOR):
                break
            pedidos += 1
            if not _buscar(lote):
                break
    finally:
        if exclusivo:
            _prefetch_lock.release()
    return pedidos


def _pacote(base: str) -> dict:
    cached = _ler_raw(base)
    if cached is not None:
        return cached
    if not circuit.allows(_PROVEDOR) or not _buscar([base]):
        return {}
    return _ler_raw(base) or {}


def _fetch_sync(symbol: str, asset_type: AssetType | None = None) -> AssetSnapshot | None:
    t = asset_type or detect_type(symbol)
    pacote = _pacote(_base_symbol(symbol))
    if not pacote:
        return None
    return snapshot_do_pacote(pacote, symbol, t)


_DIAS_DO_PERIODO = {
    "1d": 1,
    "5d": 7,
    "1mo": 31,
    "3mo": 92,
    "6mo": 183,
    "1y": 366,
    "2y": 731,
    "max": 10_000,
}


def _history_sync(symbol: str, period: str = "1y") -> dict[str, float]:
    detect_type(symbol)
    try:
        serie = mercado.ler_historico(_base_symbol(symbol), _DIAS_DO_PERIODO.get(period, 366))
        record_external_call(_PROVEDOR, ok=True)
        return serie
    except Exception as e:
        record_external_call(_PROVEDOR, ok=False)
        logger.warning("Histórico de %s não saiu da base de mercado: %s", symbol, e)
        return {}


def _dividends_sync(symbol: str) -> list[dict] | None:
    detect_type(symbol)
    try:
        linhas = mercado.ler_proventos(_base_symbol(symbol))
        record_external_call(_PROVEDOR, ok=True)
    except Exception as e:
        record_external_call(_PROVEDOR, ok=False)
        logger.warning("Proventos de %s não saíram da base de mercado: %s", symbol, e)
        return None
    return proventos_do_app(linhas)


def proventos_do_app(linhas: list[dict]) -> list[dict]:
    return sorted(
        (
            {
                "date": linha["data_pagamento"] or linha["data_com"],
                "value": linha["valor"],
                "ex_date": linha["data_com"],
            }
            for linha in linhas
            if linha["valor"] is not None
        ),
        key=lambda d: d["date"],
    )


async def fetch_asset(symbol: str, asset_type: AssetType | None = None) -> AssetSnapshot | None:
    ck = f"uasset:{symbol.upper()}"
    cached = cache.get(ck)
    if cached:
        try:
            return AssetSnapshot(**cached)
        except Exception:
            pass

    async with _FETCH_SEMAPHORE:
        cached = cache.get(ck)
        if cached:
            try:
                return AssetSnapshot(**cached)
            except Exception:
                pass

        snap = await asyncio.to_thread(_fetch_sync, symbol, asset_type)

    if snap:
        cache.set(ck, snap.to_dict(), await asyncio.to_thread(validade_do_mercado))

    return snap


async def fetch_many(symbols: list[str]) -> list[AssetSnapshot]:
    frios = [s for s in symbols if cache.get(f"uasset:{s.upper()}") is None]
    if frios:
        await asyncio.to_thread(prefetch, frios)

    tasks = [fetch_asset(s) for s in symbols]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    out: list[AssetSnapshot] = []
    for r in results:
        if isinstance(r, AssetSnapshot):
            out.append(r)
        elif isinstance(r, Exception):
            logger.debug("fetch_many: erro ignorado — %s", r)

    return out


async def fetch_history_universal(symbol: str, period: str = "1y") -> dict[str, float]:
    ck = f"uhist:{symbol.upper()}:{period}"
    cached = cache.get(ck)
    if cached:
        return cached

    series = await asyncio.to_thread(_history_sync, symbol, period)

    if series:
        cache.set(ck, series, await asyncio.to_thread(validade_do_mercado))

    return series


_IBOV_PROXY = "BOVA11"


async def fetch_ibov_history(days: int = 365) -> dict[str, float]:
    ck = f"uhist:ibov:{days}"
    cached = cache.get(ck)
    if cached is not None:
        return cached

    try:
        series = await asyncio.to_thread(mercado.ler_historico, _IBOV_PROXY, days)
    except Exception as e:
        logger.warning("Histórico do Ibovespa não saiu da base de mercado: %s", e)
        return {}
    cache.set(ck, series, await asyncio.to_thread(validade_do_mercado))
    return series


async def fetch_dividends(symbol: str) -> list[dict] | None:
    ck = f"udiv:{symbol.upper()}"
    cached = cache.get(ck)
    if cached is not None:
        return cached

    data = await asyncio.to_thread(_dividends_sync, symbol)

    if data is None:
        vencido, idade = cache.get_with_age(ck)
        if vencido is not None:
            logger.warning("Proventos de %s não chegaram; servindo cache de %.0fs.", symbol, idade)
            return vencido
        logger.warning("Proventos de %s não chegaram e não há cache.", symbol)
        return None

    cache.set(ck, data, DIV_TTL)
    return data
