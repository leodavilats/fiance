from __future__ import annotations

import unicodedata
from dataclasses import dataclass

from app.core.universe import search_universe
from app.storage import portfolio_store

GROUP_LIMIT = 5


def fold(texto: str) -> str:
    sem_acento = unicodedata.normalize("NFKD", texto)
    return "".join(c for c in sem_acento if not unicodedata.combining(c)).lower()


@dataclass(frozen=True)
class SearchHit:
    kind: str
    title: str
    subtitle: str
    ref: str

    def as_dict(self) -> dict:
        return {
            "kind": self.kind,
            "title": self.title,
            "subtitle": self.subtitle,
            "ref": self.ref,
        }


def _positions(termo: str, user_id: str | None) -> list[SearchHit]:
    achados = []
    for item in portfolio_store.list_positions(user_id):
        if termo in fold(item["ticker"]):
            achados.append(
                SearchHit(
                    kind="position",
                    title=item["ticker"],
                    subtitle=(
                        f"{item['quantity']:.0f} na carteira · "
                        f"preço médio R$ {item['avg_price']:.2f}"
                    ),
                    ref=item["ticker"],
                )
            )
    return achados[:GROUP_LIMIT]


def _fixed_income(termo: str, user_id: str | None) -> list[SearchHit]:
    achados = []
    for row in portfolio_store.list_fixed_income(user_id):
        if row["oculto"]:
            continue
        if termo in fold(row["nome"]) or termo in fold(row["tipo"]):
            achados.append(
                SearchHit(
                    kind="fixed_income",
                    title=row["nome"],
                    subtitle=(
                        f"{row['tipo'].replace('_', ' ').upper()} · "
                        f"aplicado em {row['data_aplicacao']}"
                    ),
                    ref=str(row["id"]),
                )
            )
    return achados[:GROUP_LIMIT]


def _assets(query: str, ja_na_carteira: set[str]) -> list[SearchHit]:
    achados = []
    for item in search_universe(query, limit=GROUP_LIMIT * 3):
        if item["ticker"] in ja_na_carteira:
            continue
        achados.append(
            SearchHit(
                kind="asset",
                title=item["ticker"],
                subtitle=item["name"],
                ref=item["ticker"],
            )
        )
    return achados[:GROUP_LIMIT]


def search(query: str, user_id: str | None = None) -> dict:
    termo = fold(query.strip())
    if not termo:
        return {"query": query, "groups": [], "total": 0}

    posicoes = _positions(termo, user_id)
    renda_fixa = _fixed_income(termo, user_id)
    ativos = _assets(query.strip(), {hit.title for hit in posicoes})

    grupos = [
        ("Na sua carteira", posicoes),
        ("Sua renda fixa", renda_fixa),
        ("Ativos", ativos),
    ]

    saida = [
        {"label": rotulo, "items": [hit.as_dict() for hit in itens]}
        for rotulo, itens in grupos
        if itens
    ]

    return {
        "query": query,
        "groups": saida,
        "total": sum(len(g["items"]) for g in saida),
    }
