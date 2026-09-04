from __future__ import annotations

import json
import os
import time

import pytest

from app.core import cache as cache_mod
from app.core import cache_backends
from app.core.cache_backends import DatabaseBackend, RedisBackend, SqliteBackend

REDIS_URL = os.environ.get("REDIS_TEST_URL", "").strip()


def _redis_backend():
    if not REDIS_URL:
        pytest.skip(
            "REDIS_TEST_URL não configurado: o contrato do backend compartilhado "
            "não foi exercitado contra um Redis real neste ambiente."
        )
    try:
        backend = RedisBackend(REDIS_URL, prefix="fiance:test:")
        backend._client.ping()
    except Exception as exc:  # pragma: no cover - depende de infraestrutura
        pytest.skip(f"Redis inacessível em {REDIS_URL}: {exc}")
    backend.clear_all()
    return backend


@pytest.fixture(params=["sqlite", "database", "redis"])
def backend(request, tmp_path, monkeypatch):
    if request.param == "sqlite":
        monkeypatch.setattr(cache_backends, "DB_PATH", tmp_path / "contrato.db")
        cache_mod.reset_connection()
        yield SqliteBackend()
        cache_mod.reset_connection()
    elif request.param == "database":
        alvo = DatabaseBackend()
        alvo.clear_all()
        yield alvo
        alvo.clear_all()
    else:
        alvo = _redis_backend()
        yield alvo
        alvo.clear_all()


def _outro_no(backend):
    if backend.name == "sqlite":
        return SqliteBackend()
    if backend.name == "database":
        return DatabaseBackend()
    return RedisBackend(REDIS_URL, prefix="fiance:test:")


class TestContratoDoBackend:
    def test_o_que_foi_gravado_e_lido_de_volta(self, backend):
        backend.set_raw("k", '{"preco": 30.5}', time.time() + 60)

        assert backend.get_raw("k") == ('{"preco": 30.5}', pytest.approx(time.time() + 60, abs=2))

    def test_chave_inexistente_devolve_none_e_nao_estoura(self, backend):
        assert backend.get_raw("nunca-gravada") is None

    def test_gravar_de_novo_substitui(self, backend):
        backend.set_raw("k", "antigo", time.time() + 60)
        backend.set_raw("k", "novo", time.time() + 60)

        assert backend.get_raw("k")[0] == "novo"

    def test_o_vencido_continua_legivel(self, backend):
        backend.set_raw("velho", "valor", time.time() - 120)

        row = backend.get_raw("velho")

        assert row is not None
        assert row[1] < time.time()

    def test_apagar_apaga(self, backend):
        backend.set_raw("k", "v", time.time() + 60)
        backend.delete("k")

        assert backend.get_raw("k") is None

    def test_apagar_o_que_nao_existe_nao_estoura(self, backend):
        backend.delete("fantasma")

    def test_apagar_por_padrao_alcanca_o_prefixo(self, backend):
        backend.set_raw("uasset:PETR4", "a", time.time() + 60)
        backend.set_raw("uasset:VALE3", "b", time.time() + 60)
        backend.set_raw("rates:cdi", "c", time.time() + 60)

        apagadas = backend.delete_pattern("uasset:%")

        assert apagadas == 2
        assert backend.get_raw("rates:cdi") is not None

    def test_limpar_tudo_limpa_tudo(self, backend):
        backend.set_raw("a", "1", time.time() + 60)
        backend.set_raw("b", "2", time.time() + 60)

        backend.clear_all()

        assert backend.get_raw("a") is None
        assert backend.get_raw("b") is None

    def test_o_backend_se_identifica(self, backend):
        assert backend.name in {"sqlite", "database", "redis"}


class TestOQueSoOCompartilhadoResolve:
    def test_dois_nos_enxergam_a_mesma_gravacao(self, backend):
        outro_no = _outro_no(backend)

        backend.set_raw("preco:PETR4", '{"p": 30.5}', time.time() + 60)

        assert outro_no.get_raw("preco:PETR4")[0] == '{"p": 30.5}'

    def test_invalidar_num_no_invalida_no_outro(self, backend):
        outro_no = _outro_no(backend)

        backend.set_raw("preco:VALE3", "x", time.time() + 60)
        outro_no.delete("preco:VALE3")

        assert backend.get_raw("preco:VALE3") is None


class TestEscolhaDoBackend:
    def test_sem_redis_url_o_padrao_e_o_arquivo_local(self, monkeypatch):
        monkeypatch.delenv("REDIS_URL", raising=False)
        monkeypatch.delenv("CACHE_BACKEND", raising=False)
        monkeypatch.setattr(cache_backends, "_url_do_banco_e_compartilhada", lambda: False)

        assert cache_backends.build_backend().name == "sqlite"

    def test_com_banco_compartilhado_o_padrao_e_o_banco(self, monkeypatch):
        monkeypatch.delenv("REDIS_URL", raising=False)
        monkeypatch.delenv("CACHE_BACKEND", raising=False)
        monkeypatch.setattr(cache_backends, "_url_do_banco_e_compartilhada", lambda: True)

        assert cache_backends.build_backend().name == "database"

    def test_escolha_explicita_vence_o_padrao(self, monkeypatch):
        monkeypatch.delenv("REDIS_URL", raising=False)
        monkeypatch.setattr(cache_backends, "_url_do_banco_e_compartilhada", lambda: True)
        monkeypatch.setenv("CACHE_BACKEND", "sqlite")

        assert cache_backends.build_backend().name == "sqlite"

    def test_nome_de_backend_errado_falha_alto(self, monkeypatch):
        monkeypatch.setenv("CACHE_BACKEND", "postgress")

        with pytest.raises(RuntimeError, match="CACHE_BACKEND"):
            cache_backends.build_backend()

    def test_redis_pedido_sem_url_falha_alto(self, monkeypatch):
        monkeypatch.delenv("REDIS_URL", raising=False)
        monkeypatch.setenv("CACHE_BACKEND", "redis")

        with pytest.raises(RuntimeError, match="REDIS_URL"):
            cache_backends.build_backend()

    def test_com_redis_url_o_backend_e_compartilhado(self, monkeypatch):
        monkeypatch.setenv("REDIS_URL", REDIS_URL or "redis://localhost:6379/0")

        try:
            escolhido = cache_backends.build_backend()
        except RuntimeError as erro:
            assert "redis" in str(erro).lower()
            return

        assert escolhido.name == "redis"

    def test_a_fachada_diz_se_o_cache_e_compartilhado(self, monkeypatch):
        monkeypatch.delenv("REDIS_URL", raising=False)
        monkeypatch.setenv("CACHE_BACKEND", "sqlite")
        cache_mod.set_backend(None)

        estado = cache_mod.describe()

        assert estado["shared"] is False
        assert "CACHE_BACKEND=database" in estado["note"]
        cache_mod.set_backend(None)

    def test_o_cache_no_banco_se_declara_compartilhado(self, monkeypatch):
        monkeypatch.setenv("CACHE_BACKEND", "database")
        monkeypatch.setattr(cache_backends, "_url_do_banco_e_compartilhada", lambda: True)
        cache_mod.set_backend(None)

        estado = cache_mod.describe()

        assert estado["backend"] == "database"
        assert estado["shared"] is True
        cache_mod.set_backend(None)

    def test_cache_no_banco_sobre_sqlite_nao_promete_compartilhamento(self, monkeypatch):
        monkeypatch.setenv("CACHE_BACKEND", "database")
        monkeypatch.setattr(cache_backends, "_url_do_banco_e_compartilhada", lambda: False)
        cache_mod.set_backend(None)

        estado = cache_mod.describe()

        assert estado["shared"] is False
        cache_mod.set_backend(None)


class _ClienteFalso:
    def __init__(self) -> None:
        self.data: dict[str, str] = {}
        self.ttls: dict[str, int] = {}

    def get(self, key):
        return self.data.get(key)

    def set(self, key, value, ex=None):
        self.data[key] = value
        self.ttls[key] = ex

    def delete(self, *keys):
        return sum(1 for k in keys if self.data.pop(k, None) is not None)

    def scan_iter(self, match, count=None):
        import fnmatch

        return [k for k in list(self.data) if fnmatch.fnmatch(k, match)]


@pytest.fixture()
def redis_falso():
    cliente = _ClienteFalso()
    return RedisBackend("redis://ignorado", prefix="p:", client=cliente), cliente


class TestTraducaoDoAdaptadorRedis:
    def test_a_chave_vai_prefixada(self, redis_falso):
        backend, cliente = redis_falso
        backend.set_raw("uasset:PETR4", "v", time.time() + 60)

        assert "p:uasset:PETR4" in cliente.data

    def test_o_vencimento_viaja_no_valor(self, redis_falso):
        backend, cliente = redis_falso
        vence = time.time() + 60
        backend.set_raw("k", "conteudo", vence)

        envelope = json.loads(cliente.data["p:k"])
        assert envelope["v"] == "conteudo"
        assert envelope["e"] == pytest.approx(vence)

    def test_o_ttl_nativo_e_maior_que_o_vencimento(self, redis_falso):
        backend, cliente = redis_falso
        backend.set_raw("k", "v", time.time() + 60)

        assert cliente.ttls["p:k"] > 60

    def test_entrada_ja_vencida_ainda_recebe_ttl_positivo(self, redis_falso):
        backend, cliente = redis_falso
        backend.set_raw("k", "v", time.time() - 120)

        assert cliente.ttls["p:k"] >= 1

    def test_o_padrao_sql_vira_glob(self, redis_falso):
        backend, _ = redis_falso
        backend.set_raw("uasset:PETR4", "a", time.time() + 60)
        backend.set_raw("uasset:VALE3", "b", time.time() + 60)
        backend.set_raw("rates:cdi", "c", time.time() + 60)

        assert backend.delete_pattern("uasset:%") == 2
        assert backend.get_raw("rates:cdi") is not None

    def test_limpar_tudo_nao_alcanca_chave_de_fora(self, redis_falso):
        backend, cliente = redis_falso
        backend.set_raw("k", "v", time.time() + 60)
        cliente.data["outra-coisa"] = "nao mexer"

        backend.clear_all()

        assert cliente.data == {"outra-coisa": "nao mexer"}

    def test_valor_corrompido_vira_none_em_vez_de_estourar(self, redis_falso):
        backend, cliente = redis_falso
        cliente.data["p:k"] = "isto nao e json"

        assert backend.get_raw("k") is None

    def test_purgar_nao_varre_a_base(self, redis_falso):
        backend, _ = redis_falso

        assert backend.purge_expired() == 0
