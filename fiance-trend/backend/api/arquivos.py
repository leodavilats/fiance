from __future__ import annotations

import json
import re
from pathlib import Path


def registro(pasta: Path) -> list[dict]:
    arquivo = pasta / "registro.jsonl"
    if not arquivo.exists():
        return []
    linhas = arquivo.read_text(encoding="utf-8").splitlines()
    return [json.loads(linha) for linha in linhas if linha]


def curva(pasta: Path, hipotese: str, assinatura: str, periodo: str) -> dict | None:
    if not all(re.fullmatch(r"[a-z0-9_]+", parte) for parte in (hipotese, assinatura, periodo)):
        return None
    arquivo = pasta / "resultados" / f"{hipotese}_{assinatura}_{periodo}.json"
    return json.loads(arquivo.read_text(encoding="utf-8")) if arquivo.exists() else None


def ranking(pasta: Path) -> list[dict]:
    arquivo = pasta / "registro_ranking.jsonl"
    if not arquivo.exists():
        return []
    linhas = arquivo.read_text(encoding="utf-8").splitlines()
    return [json.loads(linha) for linha in linhas if linha]


def ranking_meses(pasta: Path, classe: str, sinal: str, assinatura: str, periodo: str):
    partes = (classe, sinal, assinatura, periodo)
    if not all(re.fullmatch(r"[a-z0-9_]+", parte) for parte in partes):
        return None
    arquivo = pasta / "resultados" / f"ranking_{classe}_{sinal}_{assinatura}_{periodo}.json"
    return json.loads(arquivo.read_text(encoding="utf-8")) if arquivo.exists() else None


def _titulo(texto: str, padrao: str) -> str:
    for linha in texto.splitlines():
        if linha.startswith("# "):
            return linha[2:].strip()
    return padrao


def documentos(docs: Path) -> list[dict]:
    caminhos = [
        docs / "05-FUTURO.md",
        docs / "03-ESTADO.md",
        docs / "04-PROBLEMAS.md",
        docs / "01-VISAO.md",
        docs / "02-ARQUITETURA.md",
        *sorted((docs / "base").glob("*.md")),
        docs / "dados" / "README.md",
        docs / "pesquisa" / "README.md",
        *sorted((docs / "pesquisa" / "estudos").glob("*.md")),
        docs / "decisoes" / "ADR-022-dados-de-mercado-coletados-em-lote.md",
        docs / "decisoes" / "ADR-023-fase-pessoal-primeiro.md",
        docs / "decisoes" / "ADR-024-api-de-dados.md",
        docs / "decisoes" / "ADR-029-documentacao-por-parte.md",
    ]
    lista = []
    for caminho in caminhos:
        if caminho.exists():
            nome = caminho.relative_to(docs).as_posix()
            lista.append(
                {"nome": nome, "titulo": _titulo(caminho.read_text(encoding="utf-8"), nome)}
            )
    return lista


def documento(docs: Path, nome: str) -> str | None:
    permitidos = {d["nome"] for d in documentos(docs)}
    if nome not in permitidos:
        return None
    return (docs / nome).read_text(encoding="utf-8")
