from __future__ import annotations

import httpx


class Indisponivel(RuntimeError):
    pass


class Ausente(Indisponivel):
    pass


def baixar(url: str) -> bytes:
    try:
        resposta = httpx.get(url, timeout=600, follow_redirects=True)
    except httpx.HTTPError as e:
        raise Indisponivel(f"{url} não respondeu: {type(e).__name__}.") from e
    if resposta.status_code == 404:
        raise Ausente(f"{url} não existe.")
    if resposta.status_code != 200:
        raise Indisponivel(f"{url} respondeu {resposta.status_code}.")
    return resposta.content
