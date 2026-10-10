from __future__ import annotations

import time
from collections.abc import Callable

import httpx

ESPERAS = (10, 30, 90)


class Indisponivel(RuntimeError):
    pass


class Ausente(Indisponivel):
    pass


def _uma_vez(url: str, get: Callable[..., httpx.Response]) -> bytes:
    try:
        resposta = get(url, timeout=600, follow_redirects=True)
    except httpx.HTTPError as e:
        raise Indisponivel(f"{url} não respondeu: {type(e).__name__}.") from e
    if resposta.status_code == 404:
        raise Ausente(f"{url} não existe.")
    if resposta.status_code != 200:
        raise Indisponivel(f"{url} respondeu {resposta.status_code}.")
    if resposta.headers.get("content-type", "").startswith("text/html"):
        raise Indisponivel(f"{url} respondeu uma página HTML no lugar do arquivo.")
    return resposta.content


def baixar(
    url: str,
    get: Callable[..., httpx.Response] = httpx.get,
    dormir: Callable[[float], None] = time.sleep,
) -> bytes:
    for espera in ESPERAS:
        try:
            return _uma_vez(url, get)
        except Ausente:
            raise
        except Indisponivel as e:
            print(f"{e} Nova tentativa em {espera} s.", flush=True)
            dormir(espera)
    return _uma_vez(url, get)
