from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path

from pesquisa.ranking import Classe, Sinal

ARQUIVO = Path(__file__).resolve().parents[2] / "registro_ranking.jsonl"

TETO_DO_ESTUDO = 6
_ANTERIOR = {"validacao": "estudo", "prova": "validacao"}


class Recusado(RuntimeError):
    pass


def assinatura(sinal: Sinal, classe: Classe) -> str:
    texto = json.dumps(
        {"sinal": sinal.nome, "parametros": sinal.parametros, "classe": classe.nome},
        sort_keys=True,
    )
    return hashlib.sha256(texto.encode()).hexdigest()[:12]


def ler(arquivo: Path = ARQUIVO) -> list[dict]:
    if not arquivo.exists():
        return []
    return [
        json.loads(linha) for linha in arquivo.read_text(encoding="utf-8").splitlines() if linha
    ]


def conferir(sinal: Sinal, classe: Classe, periodo: str, forcar: bool, arquivo: Path = ARQUIVO):
    if forcar:
        return
    registros = ler(arquivo)
    minha = assinatura(sinal, classe)
    if periodo == "estudo":
        feitas = {r["assinatura"] for r in registros if r["periodo"] == "estudo"}
        if minha not in feitas and len(feitas) >= TETO_DO_ESTUDO:
            raise Recusado(
                f"O estudo já tem {len(feitas)} variações, o teto do protocolo. A conclusão é "
                '"o ranking não informa"; rodar mais exige --forcar, e fica no registro.'
            )
        return
    anterior = [
        r for r in registros if r["assinatura"] == minha and r["periodo"] == _ANTERIOR[periodo]
    ]
    if not any(r["resumo"].get("passou") for r in anterior):
        raise Recusado(
            f"{sinal.nome} em {classe.nome} não passou em {_ANTERIOR[periodo]}: "
            f"{periodo} continua lacrada."
        )
    abertas = [r for r in registros if r["assinatura"] == minha and r["periodo"] == periodo]
    if abertas:
        raise Recusado(
            f"{periodo} de {sinal.nome} em {classe.nome} já foi aberta em {abertas[0]['quando']}."
        )


def anotar(
    sinal: Sinal,
    classe: Classe,
    periodo: str,
    retrato: str,
    resumo: dict,
    forcado: bool = False,
    arquivo: Path = ARQUIVO,
) -> dict:
    registro = {
        "quando": datetime.now(UTC).isoformat(timespec="seconds"),
        "sinal": sinal.nome,
        "classe": classe.nome,
        "assinatura": assinatura(sinal, classe),
        "parametros": sinal.parametros,
        "periodo": periodo,
        "retrato": retrato,
        "forcado": forcado,
        "resumo": resumo,
    }
    with arquivo.open("a", encoding="utf-8") as saida:
        saida.write(json.dumps(registro, ensure_ascii=False) + "\n")
    return registro


def variacoes_no_estudo(arquivo: Path = ARQUIVO) -> int:
    return len({r["assinatura"] for r in ler(arquivo) if r["periodo"] == "estudo"})
