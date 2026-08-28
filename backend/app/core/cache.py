"""Cache de respostas externas.

A serialização, o TTL e a contabilidade de acerto vivem aqui; **onde o dado
mora** vive em `cache_backends`. A separação existe porque a resposta certa
muda com o número de nós: com um, arquivo local é o certo — sem operação, sem
dependência; com dois, cada nó guardaria a própria cópia e a mesma pessoa
recarregando a página veria preços diferentes conforme o balanceador.

Quem chama não sabe de nada disso, e é esse o ponto: trocar de backend é
configurar `REDIS_URL`, não reescrever quem consulta.
"""

from __future__ import annotations

import json
import logging
import time
from typing import Any

from app.core.cache_backends import DB_PATH, CacheBackend, SqliteBackend, build_backend

logger = logging.getLogger("fiance.cache")

__all__ = [
    "DB_PATH",
    "backend",
    "clear_all",
    "delete",
    "delete_pattern",
    "get",
    "get_with_age",
    "purge_expired",
    "reset_connection",
    "set",
    "set_backend",
]

_backend: CacheBackend | None = None


def backend() -> CacheBackend:
    global _backend
    if _backend is None:
        _backend = build_backend()
    return _backend


def set_backend(novo: CacheBackend | None) -> None:
    """Troca o backend. Usado na inicialização e nos testes."""
    global _backend
    _backend = novo


def _record_lookup(hit: bool) -> None:
    try:
        from app.core.observability import record_cache_lookup

        record_cache_lookup(hit)
    except Exception:
        pass


def reset_connection() -> None:
    """Fecha a conexão desta thread (usado em testes e após trocar DB_PATH)."""
    atual = _backend
    if atual is not None and hasattr(atual, "reset_connection"):
        atual.reset_connection()
    # O backend é reconstruído na próxima chamada: `DB_PATH` pode ter mudado, e
    # o de disco guarda o caminho com que foi criado.
    set_backend(None)


def get(key: str) -> Any | None:
    row = backend().get_raw(key)

    if not row:
        _record_lookup(hit=False)
        return None

    value, expires_at = row

    if expires_at < time.time():
        _record_lookup(hit=False)
        delete(key)
        return None

    _record_lookup(hit=True)
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        return None


def get_with_age(key: str) -> tuple[Any | None, float | None]:
    """Valor e segundos desde o vencimento, **mesmo vencido**.

    É o que sustenta a degradação do disjuntor: com a fonte fora do ar, mostrar
    o preço de vinte minutos atrás **dizendo** que ele é de vinte minutos atrás
    é melhor do que não mostrar nada.
    """
    row = backend().get_raw(key)
    if not row:
        return None, None

    value, expires_at = row
    try:
        parsed = json.loads(value)
    except json.JSONDecodeError:
        return None, None

    return parsed, max(0.0, time.time() - expires_at)


def set(key: str, value: Any, ttl_seconds: int) -> None:
    backend().set_raw(key, json.dumps(value, default=str), time.time() + ttl_seconds)


def delete(key: str) -> None:
    backend().delete(key)


def delete_pattern(pattern: str) -> int:
    return backend().delete_pattern(pattern)


def clear_all() -> int:
    return backend().clear_all()


def purge_expired() -> int:
    """Remove entradas vencidas. Chamado pelo ciclo de manutenção."""
    return backend().purge_expired()


def describe() -> dict:
    """Onde o cache está morando agora.

    Existe para a rota de diagnóstico: descobrir que os nós não compartilham
    cache olhando gráfico de latência é caro, e a resposta é uma palavra.
    """
    atual = backend()
    return {
        "backend": atual.name,
        "shared": atual.name != "sqlite",
        "note": (
            "Cache por nó. Com mais de um nó, a mesma pessoa pode ver preços "
            "diferentes conforme o balanceador — configure REDIS_URL."
            if atual.name == "sqlite"
            else "Cache compartilhado entre os nós."
        ),
    }


def _sqlite_backend_for_tests() -> SqliteBackend:
    """Backend de disco explícito, para o teste que inspeciona o arquivo."""
    novo = SqliteBackend()
    set_backend(novo)
    return novo
