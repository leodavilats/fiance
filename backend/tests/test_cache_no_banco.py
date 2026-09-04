from __future__ import annotations

import time

import pytest
from sqlalchemy.dialects import postgresql, sqlite

from app.core.cache_backends import DatabaseBackend
from app.models.db_models import CacheEntryDb

pytestmark = pytest.mark.real_cache


def _upsert(dialeto):
    insert = postgresql.insert if dialeto.name == "postgresql" else sqlite.insert
    comando = insert(CacheEntryDb).values(k="uasset:PETR4", v="{}", expires_at=1.0)
    return comando.on_conflict_do_update(
        index_elements=[CacheEntryDb.k], set_={"v": "{}", "expires_at": 1.0}
    )


class TestOUpsertValeNosDoisBancos:
    @pytest.mark.parametrize("dialeto", [postgresql.dialect(), sqlite.dialect()])
    def test_o_sql_compila(self, dialeto):
        sql = str(_upsert(dialeto).compile(dialect=dialeto))

        assert "ON CONFLICT" in sql
        assert "cache_entries" in sql

    def test_o_conflito_e_resolvido_pela_chave(self):
        sql = str(_upsert(postgresql.dialect()).compile(dialect=postgresql.dialect()))

        assert "(k)" in sql, "o upsert precisa casar pela chave primária"


class TestOCacheNoBancoNaoPegaCaronaNaTransacaoDeQuemChama:
    def test_grava_sem_depender_de_commit_de_quem_chamou(self):
        backend = DatabaseBackend()
        backend.clear_all()

        backend.set_raw("do-cache", "{}", time.time() + 60)

        outro_no = DatabaseBackend()
        assert outro_no.get_raw("do-cache") is not None

    def test_ignora_a_sessao_ambiente_do_request(self):
        from app.core.context import reset_request_session, set_request_session
        from app.core.database import SessionLocal

        backend = DatabaseBackend()
        backend.clear_all()

        ambiente = SessionLocal()
        token = set_request_session(ambiente)
        try:
            backend.set_raw("fora-do-request", "{}", time.time() + 60)

            assert not ambiente.new, "o cache sujou a sessão do request"
            assert not ambiente.dirty
            ambiente.rollback()
        finally:
            reset_request_session(token)
            ambiente.close()

        assert backend.get_raw("fora-do-request") is not None

    def test_purgar_apaga_so_o_vencido(self):
        backend = DatabaseBackend()
        backend.clear_all()
        backend.set_raw("vencido", "x", time.time() - 10)
        backend.set_raw("vivo", "y", time.time() + 600)

        assert backend.purge_expired() == 1
        assert backend.get_raw("vivo") is not None
        assert backend.get_raw("vencido") is None

    def test_a_tabela_e_declarada_sem_dono(self):
        from app.storage.account_store import GLOBAL_TABLES

        assert CacheEntryDb.__tablename__ in GLOBAL_TABLES
