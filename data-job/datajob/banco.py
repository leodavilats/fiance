from __future__ import annotations

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

_LOTE = 5000


def upsert(conn: sa.Connection, tabela: sa.Table, linhas: list[dict], chave: list[str]) -> int:
    if not linhas:
        return 0
    campos = [c for c in linhas[0] if c not in chave]
    gravadas = 0
    for inicio in range(0, len(linhas), _LOTE):
        insercao = postgresql.insert(tabela).values(linhas[inicio : inicio + _LOTE])
        if not campos:
            comando = insercao.on_conflict_do_nothing(index_elements=chave)
        else:
            comando = insercao.on_conflict_do_update(
                index_elements=chave,
                set_={c: insercao.excluded[c] for c in campos},
                where=sa.tuple_(
                    *(tabela.c[c] for c in campos if c != "coleta_id")
                ).is_distinct_from(
                    sa.tuple_(*(insercao.excluded[c] for c in campos if c != "coleta_id"))
                ),
            )
        # Em lote, o rowcount volta -1; o RETURNING conta só as linhas inseridas ou alteradas.
        gravadas += len(conn.execute(comando.returning(sa.literal(1))).all())
    return gravadas
