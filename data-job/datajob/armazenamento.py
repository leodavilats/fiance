from __future__ import annotations

import hashlib
from pathlib import Path


def hash_de(conteudo: bytes) -> str:
    return hashlib.sha256(conteudo).hexdigest()


def guardar(raiz: Path, fonte: str, nome: str, conteudo: bytes) -> Path:
    destino = raiz / fonte / f"{hash_de(conteudo)[:16]}__{nome}"
    if not destino.exists():
        destino.parent.mkdir(parents=True, exist_ok=True)
        temporario = destino.with_suffix(destino.suffix + ".parcial")
        temporario.write_bytes(conteudo)
        temporario.replace(destino)
    return destino


def guardados(raiz: Path, fonte: str) -> list[Path]:
    pasta = raiz / fonte
    if not pasta.exists():
        return []
    return sorted(p for p in pasta.iterdir() if p.is_file() and not p.name.endswith(".parcial"))
