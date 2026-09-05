from __future__ import annotations

import pytest

from app.core import database


class TestQuemMigra:
    def test_banco_local_ainda_se_cria_sozinho(self):
        assert database.banco_e_local() is True

    def test_postgres_nao_migra_no_startup(self, monkeypatch):
        monkeypatch.setattr(database, "banco_e_local", lambda: False)

        chamou = []
        monkeypatch.setattr(database, "migrate", lambda: chamou.append("migrou"))
        monkeypatch.setattr(database, "conferir_revisao", lambda: chamou.append("conferiu"))

        database.init_db()

        assert chamou == ["conferiu"], "startup contra banco compartilhado só confere, não migra"


class TestOQueOStartupConfere:
    def test_revisao_em_dia_passa_calada(self):
        database.ensure_initialized()

        database.conferir_revisao()

    def test_banco_atrasado_falha_alto(self, monkeypatch):
        monkeypatch.setattr(database, "_revisoes_do_banco", lambda: {"revisao_velha"})

        with pytest.raises(database.BancoAtrasado) as erro:
            database.conferir_revisao()

        assert "python -m app.release" in str(erro.value), (
            "a mensagem precisa dizer o comando que resolve — erro de coluna ausente no meio de "
            "um request aparece longe da causa"
        )

    def test_banco_sem_carimbo_nenhum_tambem_falha(self, monkeypatch):
        monkeypatch.setattr(database, "_revisoes_do_banco", set)

        with pytest.raises(database.BancoAtrasado):
            database.conferir_revisao()


class TestOProcfile:
    def test_declara_o_release_e_nao_manda_mais_fixar_um_worker(self):
        from pathlib import Path

        procfile = (Path(database.BACKEND_ROOT) / "Procfile").read_text(encoding="utf-8")

        assert "release: python -m app.release" in procfile

        linha_web = next(linha for linha in procfile.splitlines() if linha.startswith("web:"))
        assert "--workers 1" not in linha_web, (
            "o comentário justificava --workers 1 com cache em SQLite local, que deixou de ser "
            "verdade quando o cache passou a morar no banco da aplicação"
        )
