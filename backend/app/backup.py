from __future__ import annotations

import json
import logging
import sys
from decimal import Decimal

from sqlalchemy import inspect, select, text
from sqlalchemy.engine import Connection

from app.core.brt import now_brt
from app.core.money import ExactNumeric, money

logger = logging.getLogger("fiance.backup")

FORMATO = 1

TABELAS_EFEMERAS = frozenset({"cache_entries", "job_locks"})


class RestauracaoRecusada(RuntimeError):
    pass


def _tabelas():
    from app.core.database import Base
    from app.models import db_models  # noqa: F401

    return [t for t in Base.metadata.sorted_tables if t.name not in TABELAS_EFEMERAS]


def _revisao(conexao: Connection) -> list[str]:
    if "alembic_version" not in inspect(conexao).get_table_names():
        return []
    return sorted(r[0] for r in conexao.execute(text("SELECT version_num FROM alembic_version")))


def _para_json(valor):
    if isinstance(valor, Decimal):
        return str(valor)
    return valor


def exportar(conexao: Connection) -> dict:
    tabelas = {}
    for tabela in _tabelas():
        linhas = conexao.execute(select(tabela)).mappings().all()
        tabelas[tabela.name] = [{k: _para_json(v) for k, v in linha.items()} for linha in linhas]
    return {
        "formato": FORMATO,
        "revisao": _revisao(conexao),
        "gerado_em": now_brt().isoformat(),
        "tabelas": tabelas,
    }


def restaurar(conexao: Connection, copia: dict) -> dict[str, int]:
    if copia.get("formato") != FORMATO:
        raise RestauracaoRecusada(f"formato {copia.get('formato')} desconhecido")

    revisao_do_banco = _revisao(conexao)
    if copia.get("revisao") != revisao_do_banco:
        raise RestauracaoRecusada(
            f"a cópia é da revisão {copia.get('revisao')} e o banco está em {revisao_do_banco}: "
            "migre o banco para a revisão da cópia antes de restaurar"
        )

    tabelas = _tabelas()
    ocupadas = [t.name for t in tabelas if conexao.execute(select(t).limit(1)).first()]
    if ocupadas:
        raise RestauracaoRecusada(f"o banco de destino já tem dados em {ocupadas}")

    contagem: dict[str, int] = {}
    for tabela in tabelas:
        linhas = copia["tabelas"].get(tabela.name, [])
        exatas = {c.name for c in tabela.columns if isinstance(c.type, ExactNumeric)}
        convertidas = [
            {k: (money(v) if k in exatas and v is not None else v) for k, v in linha.items()}
            for linha in linhas
        ]
        if convertidas:
            conexao.execute(tabela.insert(), convertidas)
        contagem[tabela.name] = len(convertidas)
    return contagem


def reaplicar_exclusoes(conexao: Connection, copia_mais_nova: dict) -> list[str]:
    from app.models.db_models import User
    from app.storage.account_store import USER_SCOPED_MODELS

    lapides = [
        u for u in copia_mais_nova["tabelas"].get("users", []) if u.get("deleted_at") is not None
    ]
    usuarios = User.__table__
    reaplicadas = []
    for lapide in lapides:
        uid = lapide["id"]
        for _, modelo in USER_SCOPED_MODELS:
            tabela = modelo.__table__
            conexao.execute(tabela.delete().where(tabela.c.user_id == uid))
        conexao.execute(
            usuarios.update()
            .where(usuarios.c.id == uid)
            .values(
                email=f"apagado+{uid}@invalid",
                name="",
                picture="",
                onboarded_at=None,
                deleted_at=lapide["deleted_at"],
            )
        )
        reaplicadas.append(uid)
    return reaplicadas


def main(argv: list[str]) -> int:
    if len(argv) != 2 or argv[0] not in {"exportar", "restaurar", "reaplicar-exclusoes"}:
        print(
            "uso: python -m app.backup exportar|restaurar|reaplicar-exclusoes ARQUIVO",
            file=sys.stderr,
        )
        return 2

    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

    from app.core.config import get_settings
    from app.core.database import engine

    get_settings().validate_for_startup()
    acao, caminho = argv

    if acao == "exportar":
        with engine.connect() as conexao:
            copia = exportar(conexao)
        with open(caminho, "w", encoding="utf-8") as arquivo:
            json.dump(copia, arquivo, ensure_ascii=False)
        total = sum(len(v) for v in copia["tabelas"].values())
        logger.info("Cópia gravada em %s: %d linhas, revisão %s.", caminho, total, copia["revisao"])
        return 0

    with open(caminho, encoding="utf-8") as arquivo:
        copia = json.load(arquivo)

    if acao == "reaplicar-exclusoes":
        with engine.begin() as conexao:
            reaplicadas = reaplicar_exclusoes(conexao, copia)
        logger.info("Exclusões reaplicadas: %d contas.", len(reaplicadas))
        return 0

    try:
        with engine.begin() as conexao:
            contagem = restaurar(conexao, copia)
    except RestauracaoRecusada as motivo:
        logger.error("Restauração recusada: %s", motivo)
        return 1
    logger.info("Restaurado: %d linhas em %d tabelas.", sum(contagem.values()), len(contagem))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
