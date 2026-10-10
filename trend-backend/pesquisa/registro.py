from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path

from pesquisa.hipoteses import Hipotese

ARQUIVO = Path(__file__).resolve().parents[1] / "registro.jsonl"


class ProvaLacrada(RuntimeError):
    pass


def assinatura(hipotese: Hipotese) -> str:
    texto = json.dumps({"nome": hipotese.nome, "parametros": hipotese.parametros}, sort_keys=True)
    return hashlib.sha256(texto.encode()).hexdigest()[:12]


def ler(arquivo: Path = ARQUIVO) -> list[dict]:
    if not arquivo.exists():
        return []
    return [
        json.loads(linha) for linha in arquivo.read_text(encoding="utf-8").splitlines() if linha
    ]


def conferir_prova(hipotese: Hipotese, forcar: bool, arquivo: Path = ARQUIVO) -> None:
    if not hipotese.congelada:
        raise ProvaLacrada(
            f"{hipotese.nome} não está congelada: a prova só abre para hipótese com parâmetros fixos."
        )
    aberturas = [
        r
        for r in ler(arquivo)
        if r["periodo"] == "prova" and r["assinatura"] == assinatura(hipotese)
    ]
    if aberturas and not forcar:
        raise ProvaLacrada(
            f"A prova de {hipotese.nome} já foi aberta em {aberturas[0]['quando']}. "
            "Abrir de novo exige --forcar, e fica no registro."
        )


def anotar(
    hipotese: Hipotese,
    periodo: str,
    retrato: str,
    resumo: dict,
    forcado: bool = False,
    arquivo: Path = ARQUIVO,
) -> dict:
    registro = {
        "quando": datetime.now(UTC).isoformat(timespec="seconds"),
        "hipotese": hipotese.nome,
        "assinatura": assinatura(hipotese),
        "parametros": hipotese.parametros,
        "periodo": periodo,
        "retrato": retrato,
        "forcado": forcado,
        "resumo": resumo,
    }
    with arquivo.open("a", encoding="utf-8") as saida:
        saida.write(json.dumps(registro, ensure_ascii=False) + "\n")
    return registro


def tentativas(hipotese_nome: str, arquivo: Path = ARQUIVO) -> int:
    return len({r["assinatura"] for r in ler(arquivo) if r["hipotese"] == hipotese_nome})
