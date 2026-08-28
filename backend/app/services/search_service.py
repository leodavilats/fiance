"""Busca global: uma caixa que atravessa a carteira, o universo e a navegação.

O produto já tinha busca de ticker, e ela resolvia uma pergunta só — "existe um
papel com este código?". As perguntas que sobravam eram as que a pessoa
realmente faz: "cadê aquele CDB do Banco Inter?", "onde eu lanço um provento?",
"quanto eu tenho de Vale?". Todas as três terminavam em navegação manual pela
arquitetura de informação, que é pedir para a pessoa aprender o mapa antes de
poder perguntar o caminho.

Três decisões estruturam o resultado:

* **O que é da pessoa vem primeiro.** Quem digita "PETR" e tem PETR4 na carteira
  quer a própria posição, não a página do ativo. Ordenar por relevância textual
  colocaria as duas no mesmo balaio; ordenar por origem resolve sem heurística.
* **Navegação não passa por aqui.** Destinos de tela ("proventos", "importar",
  "metas") também são resultado de busca, mas a lista deles vive em cada
  cliente: rota é assunto de cliente, as árvores do web e do app diferem, e um
  catálogo de rotas no servidor seria uma segunda verdade sobre a arquitetura de
  informação — que diverge no dia em que alguém renomeia uma tela. O servidor
  devolve **o que só ele sabe**: a carteira, a renda fixa e o universo. O
  cliente junta com os próprios destinos.
* **Nada de correspondência aproximada.** Só subsequência, ignorando caixa e
  acento — "tesouro selic" tem que achar "Tesouro Selic". Um algoritmo de
  distância traria resultados que a pessoa não pediu e não saberia explicar, e
  numa busca que mistura dinheiro com navegação isso custa confiança.
"""

from __future__ import annotations

import unicodedata
from dataclasses import dataclass

from app.core.universe import search_universe
from app.storage import portfolio_store

#: Teto por grupo. A busca é um atalho, não uma listagem — devolver trinta
#: posições obriga a pessoa a procurar de novo dentro do resultado.
GROUP_LIMIT = 5


def fold(texto: str) -> str:
    """Minúsculas sem acento.

    Em português isso não é refinamento: "Tesouro Selic" e "tesouro selic" são a
    mesma coisa para quem digita com pressa, e casar só o exato faria a busca
    parecer quebrada justamente com os nomes mais comuns.
    """
    sem_acento = unicodedata.normalize("NFKD", texto)
    return "".join(c for c in sem_acento if not unicodedata.combining(c)).lower()


@dataclass(frozen=True)
class SearchHit:
    kind: str
    title: str
    subtitle: str
    #: O identificador do que foi achado — o cliente decide para onde ele leva.
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
                    # O tipo vem do enum (`tesouro_ipca`); a pessoa lê "TESOURO
                    # IPCA", não o identificador.
                    subtitle=(
                        f"{row['tipo'].replace('_', ' ').upper()} · "
                        f"aplicado em {row['data_aplicacao']}"
                    ),
                    ref=str(row["id"]),
                )
            )
    return achados[:GROUP_LIMIT]


def _assets(query: str, ja_na_carteira: set[str]) -> list[SearchHit]:
    """O universo recebe a consulta **crua**.

    `search_universe` compara contra o nome em maiúsculas, com acento. Passar o
    termo já dobrado faria "são" deixar de achar "SÃO" — o dobramento ajuda na
    carteira, onde a comparação é nossa, e atrapalha aqui.
    """
    achados = []
    for item in search_universe(query, limit=GROUP_LIMIT * 3):
        if item["ticker"] in ja_na_carteira:
            # Já apareceu como posição, e repetir o mesmo papel em dois grupos
            # faz a lista parecer maior do que é.
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
    """Busca em tudo que a pessoa pode querer alcançar pelo nome.

    Consulta vazia devolve vazio, não o catálogo: uma caixa que despeja o
    produto inteiro ao ganhar foco ensina a pessoa a fechá-la.
    """
    termo = fold(query.strip())
    if not termo:
        return {"query": query, "groups": [], "total": 0}

    posicoes = _positions(termo, user_id)
    renda_fixa = _fixed_income(termo, user_id)
    ativos = _assets(query.strip(), {hit.title for hit in posicoes})

    # A ordem é a resposta: o que é da pessoa, depois o que ela pode fazer,
    # depois o que existe no mercado.
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
