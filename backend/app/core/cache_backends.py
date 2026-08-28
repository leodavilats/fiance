"""Onde o cache mora: um arquivo local, ou um Redis que todos os nós enxergam.

Com um nó só, cache em SQLite no disco é a escolha certa: sem operação, sem
dependência, sem rede. Com dois, ele deixa de ser um detalhe de desempenho e
vira um problema de correção — cada nó guarda a própria cópia, e a mesma pessoa
recarregando a página vê preços diferentes conforme o balanceador. "O ativo
subiu 2% ou caiu 1%?" passa a depender de qual máquina atendeu, e isso mina a
confiança no número muito além do que uma chamada externa a mais custaria.

Por isso a fronteira é esta interface, e não um `if` espalhado por quem
consulta. O padrão continua sendo o arquivo local; `REDIS_URL` troca a
implementação e mais nada.

**A entrada guarda o próprio vencimento**, mesmo no Redis, que sabe expirar
sozinho. É o que permite `get_with_age` devolver valor vencido com a idade ao
lado — o disjuntor da fonte de cotação depende disso: com a fonte fora do ar,
mostrar o preço de vinte minutos atrás dizendo que ele é de vinte minutos atrás
é melhor do que não mostrar nada. Um TTL nativo apagaria justamente o dado que
serve para isso.
"""

from __future__ import annotations

import json
import logging
import os
import sqlite3
import threading
import time
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Protocol

logger = logging.getLogger("fiance.cache")

#: Quanto tempo a entrada vencida ainda existe no Redis.
#:
#: No SQLite ela sobrevive até a faxina periódica passar — é o que faz
#: `get_with_age` conseguir devolver dado vencido para o disjuntor da fonte de
#: cotação. O Redis expira sozinho, então sem esta margem o mesmo código teria
#: comportamentos diferentes conforme o backend, que é o pior tipo de
#: divergência: a que só aparece em produção. A margem espelha o intervalo de
#: manutenção (`jobs.MAINTENANCE_INTERVAL`).
STALE_MARGIN_SECONDS = 6 * 3600


class CacheBackend(Protocol):
    """O contrato. `get_raw` devolve (texto, vencimento) sem julgar validade."""

    name: str

    def get_raw(self, key: str) -> tuple[str, float] | None: ...

    def set_raw(self, key: str, payload: str, expires_at: float) -> None: ...

    def delete(self, key: str) -> None: ...

    def delete_pattern(self, pattern: str) -> int: ...

    def clear_all(self) -> int: ...

    def purge_expired(self) -> int: ...


# --------------------------------------------------------------------- SQLite

_DEFAULT_DB_PATH = Path(__file__).resolve().parent.parent.parent / ".cache" / "http_cache.db"
DB_PATH = Path(os.environ.get("CACHE_DB_PATH") or _DEFAULT_DB_PATH)


class SqliteBackend:
    """Arquivo local. O padrão, e o certo enquanto houver um nó só."""

    name = "sqlite"

    _BUSY_TIMEOUT_MS = 5_000

    def __init__(self) -> None:
        self._local = threading.local()
        self._init_lock = threading.Lock()
        self._initialized = False
        self._path = DB_PATH

    def _ensure_db(self) -> None:
        # O caminho pode mudar entre chamadas (os testes trocam `DB_PATH`), e
        # nesse caso o esquema tem que ser criado de novo no arquivo novo.
        if self._initialized and self._path == DB_PATH:
            return

        with self._init_lock:
            if self._initialized and self._path == DB_PATH:
                return
            self._path = DB_PATH
            DB_PATH.parent.mkdir(parents=True, exist_ok=True)
            with sqlite3.connect(DB_PATH) as cx:
                cx.execute("PRAGMA journal_mode=WAL")
                cx.execute("PRAGMA synchronous=NORMAL")
                cx.execute(
                    "CREATE TABLE IF NOT EXISTS cache ("
                    "  k TEXT PRIMARY KEY,"
                    "  v TEXT NOT NULL,"
                    "  expires_at REAL NOT NULL"
                    ")"
                )
                cx.execute("CREATE INDEX IF NOT EXISTS ix_cache_expires ON cache(expires_at)")
            self._initialized = True

    def _connection(self) -> sqlite3.Connection:
        self._ensure_db()

        cx = getattr(self._local, "cx", None)
        if cx is None:
            cx = sqlite3.connect(DB_PATH, check_same_thread=False, isolation_level=None)
            cx.execute(f"PRAGMA busy_timeout={self._BUSY_TIMEOUT_MS}")
            cx.execute("PRAGMA journal_mode=WAL")
            cx.execute("PRAGMA synchronous=NORMAL")
            self._local.cx = cx
        return cx

    @contextmanager
    def _conn(self) -> Iterator[sqlite3.Connection]:
        cx = self._connection()
        try:
            yield cx
        except sqlite3.Error:
            self._local.cx = None
            try:
                cx.close()
            except sqlite3.Error:
                pass
            raise

    def reset_connection(self) -> None:
        cx = getattr(self._local, "cx", None)
        if cx is not None:
            try:
                cx.close()
            except sqlite3.Error:
                pass
            self._local.cx = None
        self._initialized = False

    def get_raw(self, key: str) -> tuple[str, float] | None:
        try:
            with self._conn() as cx:
                row = cx.execute("SELECT v, expires_at FROM cache WHERE k = ?", (key,)).fetchone()
        except sqlite3.Error as exc:
            logger.warning("Falha ao ler cache %s: %s", key, exc)
            return None
        return (row[0], row[1]) if row else None

    def set_raw(self, key: str, payload: str, expires_at: float) -> None:
        try:
            with self._conn() as cx:
                cx.execute(
                    "INSERT OR REPLACE INTO cache(k, v, expires_at) VALUES (?, ?, ?)",
                    (key, payload, expires_at),
                )
        except sqlite3.Error as exc:
            logger.warning("Falha ao gravar cache %s: %s", key, exc)

    def delete(self, key: str) -> None:
        try:
            with self._conn() as cx:
                cx.execute("DELETE FROM cache WHERE k = ?", (key,))
        except sqlite3.Error as exc:
            logger.warning("Falha ao apagar cache %s: %s", key, exc)

    def delete_pattern(self, pattern: str) -> int:
        with self._conn() as cx:
            return cx.execute("DELETE FROM cache WHERE k LIKE ?", (pattern,)).rowcount

    def clear_all(self) -> int:
        with self._conn() as cx:
            return cx.execute("DELETE FROM cache").rowcount

    def purge_expired(self) -> int:
        with self._conn() as cx:
            return cx.execute("DELETE FROM cache WHERE expires_at < ?", (time.time(),)).rowcount


# ---------------------------------------------------------------------- Redis


class RedisBackend:
    """Um cache que todos os nós enxergam.

    O vencimento vai **no valor**, não só no TTL do Redis: `get_with_age`
    precisa do dado vencido para o disjuntor, e um TTL nativo o apagaria no
    instante em que ele começa a servir. O TTL nativo existe mesmo assim, com
    uma margem — é faxina, não regra de negócio.
    """

    name = "redis"

    def __init__(self, url: str, prefix: str = "fiance:cache:", client: Any = None) -> None:
        self._prefix = prefix

        if client is not None:
            # Costura para testar a **tradução** sem servidor: prefixo de chave,
            # envelope com o vencimento, padrão SQL virando glob. Não substitui
            # o teste de contrato contra um Redis real — aquele responde outra
            # pergunta, a de dois nós enxergarem a mesma gravação.
            self._client = client
            return

        try:
            import redis  # noqa: PLC0415
        except ModuleNotFoundError as exc:  # pragma: no cover - depende do ambiente
            raise RuntimeError(
                "REDIS_URL está configurado mas o pacote `redis` não está instalado. "
                "Sem ele o cache voltaria a ser por nó, e nós diferentes mostrariam "
                "preços diferentes para a mesma pessoa — falhar aqui é melhor do que "
                "descobrir isso em produção."
            ) from exc

        self._client = redis.Redis.from_url(url, decode_responses=True)

    def _k(self, key: str) -> str:
        return f"{self._prefix}{key}"

    def get_raw(self, key: str) -> tuple[str, float] | None:
        try:
            bruto = self._client.get(self._k(key))
        except Exception as exc:  # pragma: no cover - depende de servidor
            # Redis fora do ar não pode derrubar a requisição: cache é
            # aceleração, e um erro aqui vira "sem cache", não erro 500.
            logger.warning("Falha ao ler cache %s: %s", key, exc)
            return None

        if not bruto:
            return None
        try:
            envelope = json.loads(bruto)
            return envelope["v"], float(envelope["e"])
        except (json.JSONDecodeError, KeyError, TypeError, ValueError):
            return None

    def set_raw(self, key: str, payload: str, expires_at: float) -> None:
        envelope = json.dumps({"v": payload, "e": expires_at})
        sobrevida = max(1, int(expires_at - time.time()) + STALE_MARGIN_SECONDS)
        try:
            self._client.set(self._k(key), envelope, ex=sobrevida)
        except Exception as exc:  # pragma: no cover - depende de servidor
            logger.warning("Falha ao gravar cache %s: %s", key, exc)

    def delete(self, key: str) -> None:
        try:
            self._client.delete(self._k(key))
        except Exception as exc:  # pragma: no cover - depende de servidor
            logger.warning("Falha ao apagar cache %s: %s", key, exc)

    def _scan(self, match: str) -> list[str]:
        # `scan_iter` e não `keys`: `keys` trava o Redis inteiro enquanto varre,
        # e numa base de produção isso é uma pausa visível para todos os nós.
        return list(self._client.scan_iter(match=match, count=500))

    def delete_pattern(self, pattern: str) -> int:
        # O padrão chega no dialeto SQL (`%`); aqui ele é glob.
        glob = self._prefix + pattern.replace("%", "*")
        chaves = self._scan(glob)
        return int(self._client.delete(*chaves)) if chaves else 0

    def clear_all(self) -> int:
        chaves = self._scan(f"{self._prefix}*")
        return int(self._client.delete(*chaves)) if chaves else 0

    def purge_expired(self) -> int:
        # O Redis já expira sozinho pela sobrevida gravada em `set_raw`. Varrer
        # a base inteira para antecipar isso seria trabalho por trabalho.
        return 0


# --------------------------------------------------------------------- Seleção


def build_backend() -> CacheBackend:
    """O de disco por padrão; Redis quando `REDIS_URL` estiver configurado."""
    url = os.environ.get("REDIS_URL", "").strip()
    if url:
        logger.info("Cache compartilhado via Redis.")
        return RedisBackend(url)
    return SqliteBackend()
