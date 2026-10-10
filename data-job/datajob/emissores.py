from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import date

import sqlalchemy as sa

from datajob.esquema import emissor
from datajob.fontes.cvm_comum import nome_normalizado

_BDI_DE_ACAO = ("02", "05", "06", "07", "08")
_ESPECIE_DE_ACAO = ("ON", "PN", "UN")


@dataclass(frozen=True)
class Acao:
    emissor: str
    nome_resumido: str
    primeiro_pregao: date
    ultimo_pregao: date


@dataclass(frozen=True)
class Empresa:
    cnpj: str
    nomes: frozenset[str]
    registro: date | None
    cancelamento: date | None


def ligar(
    acoes: list[Acao],
    por_fca: dict[str, set[str]],
    por_b3: dict[str, str],
    empresas: list[Empresa],
) -> dict[str, tuple[str, str]]:
    por_emissor: dict[str, list[Acao]] = defaultdict(list)
    for acao in acoes:
        por_emissor[acao.emissor].append(acao)

    ligados: dict[str, tuple[str, str]] = {}
    for codigo, lista in por_emissor.items():
        if len(por_fca.get(codigo, ())) == 1:
            ligados[codigo] = (next(iter(por_fca[codigo])), "fca")
            continue
        if codigo in por_b3:
            ligados[codigo] = (por_b3[codigo], "b3")
            continue
        inicio = min(a.primeiro_pregao for a in lista)
        fim = max(a.ultimo_pregao for a in lista)
        nome = nome_normalizado(max(lista, key=lambda a: a.ultimo_pregao).nome_resumido)
        if not nome:
            continue
        candidatos = {
            e.cnpj
            for e in empresas
            if any(n.startswith(nome) for n in e.nomes)
            and (e.registro is None or e.registro <= fim)
            and (e.cancelamento is None or e.cancelamento >= inicio)
        }
        if len(candidatos) == 1:
            ligados[codigo] = (candidatos.pop(), "nome")
    return ligados


def recalcular(conn: sa.Connection) -> Counter:
    acoes = [
        Acao(*linha)
        for linha in conn.execute(
            sa.text(
                "SELECT substr(isin, 3, 4), nome_resumido, primeiro_pregao, ultimo_pregao "
                "FROM mercado.ativo WHERE codbdi = ANY(:bdi) AND left(especie, 2) = ANY(:especie)"
            ),
            {"bdi": list(_BDI_DE_ACAO), "especie": list(_ESPECIE_DE_ACAO)},
        )
    ]
    por_fca: dict[str, set[str]] = defaultdict(set)
    for codigo, documento in conn.execute(
        sa.text(
            "SELECT DISTINCT left(codigo, 4), cnpj FROM mercado.valor_mobiliario "
            "WHERE length(codigo) >= 5 AND left(codigo, 4) <> '0000'"
        )
    ):
        por_fca[codigo].add(documento)
    por_b3 = dict(
        conn.execute(
            sa.text(
                "SELECT codigo, cnpj FROM mercado.emissor_b3 "
                "WHERE cnpj IS NOT NULL AND tipo IS DISTINCT FROM '4'"
            )
        ).all()
    )
    empresas = [
        Empresa(
            documento,
            frozenset(n for n in (nome_normalizado(r or ""), nome_normalizado(c or "")) if n),
            registro,
            cancelamento,
        )
        for documento, r, c, registro, cancelamento in conn.execute(
            sa.text(
                "SELECT cnpj, razao_social, nome_comercial, data_registro, data_cancelamento "
                "FROM mercado.empresa"
            )
        )
    ]

    ligados = ligar(acoes, por_fca, por_b3, empresas)
    conn.execute(sa.delete(emissor))
    if ligados:
        conn.execute(
            sa.insert(emissor),
            [{"codigo": c, "cnpj": d, "metodo": m} for c, (d, m) in sorted(ligados.items())],
        )
    contagem = Counter(m for _, m in ligados.values())
    contagem["sem_cnpj"] = len({a.emissor for a in acoes}) - len(ligados)
    return contagem
