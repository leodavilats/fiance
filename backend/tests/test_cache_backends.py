"""O contrato do cache, cobrado igual de cada backend.

Com um nó, cache local é o certo. Com dois, ele deixa de ser desempenho e vira
correção: cada nó guarda a própria cópia, e a mesma pessoa recarregando a página
vê preços diferentes conforme o balanceador. "Subiu 2% ou caiu 1%?" passa a
depender de qual máquina atendeu.

O contrato é escrito **uma vez** e rodado contra cada implementação. O de disco
roda sempre; o do Redis roda onde houver um Redis e é **pulado com motivo** onde
não houver — declarar a lacuna vale mais do que um teste contra um dublê que
concorda comigo por construção.
"""

from __future__ import annotations

import json
import os
import time

import pytest

from app.core import cache as cache_mod
from app.core import cache_backends
from app.core.cache_backends import RedisBackend, SqliteBackend

REDIS_URL = os.environ.get("REDIS_TEST_URL", "").strip()


def _redis_backend():
    """Um Redis de verdade, ou o motivo pelo qual o teste não rodou."""
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


@pytest.fixture(params=["sqlite", "redis"])
def backend(request, tmp_path, monkeypatch):
    if request.param == "sqlite":
        monkeypatch.setattr(cache_backends, "DB_PATH", tmp_path / "contrato.db")
        cache_mod.reset_connection()
        yield SqliteBackend()
        cache_mod.reset_connection()
    else:
        alvo = _redis_backend()
        yield alvo
        alvo.clear_all()


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
        """É o que sustenta a degradação do disjuntor.

        Com a fonte fora do ar, mostrar o preço de vinte minutos atrás dizendo
        que ele é de vinte minutos atrás é melhor que não mostrar nada — e um
        TTL nativo apagaria justamente esse dado.
        """
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
        """A rota de diagnóstico responde com isto: descobrir que os nós não
        compartilham cache por gráfico de latência é caro."""
        assert backend.name in {"sqlite", "redis"}


class TestOQueSoOCompartilhadoResolve:
    def test_dois_nos_enxergam_a_mesma_gravacao(self, backend):
        """A razão de o backend existir.

        Dois processos, um cache. No de disco isto vale porque o arquivo é o
        mesmo; no Redis, porque o servidor é o mesmo. Se um dia um backend novo
        guardar estado em memória de processo, é aqui que ele falha.
        """
        if backend.name == "sqlite":
            outro_no = SqliteBackend()
        else:
            outro_no = RedisBackend(REDIS_URL, prefix="fiance:test:")

        backend.set_raw("preco:PETR4", '{"p": 30.5}', time.time() + 60)

        assert outro_no.get_raw("preco:PETR4")[0] == '{"p": 30.5}'

    def test_invalidar_num_no_invalida_no_outro(self, backend):
        """Senão limpar o cache viraria uma operação por máquina, e alguém
        sempre esqueceria uma."""
        if backend.name == "sqlite":
            outro_no = SqliteBackend()
        else:
            outro_no = RedisBackend(REDIS_URL, prefix="fiance:test:")

        backend.set_raw("preco:VALE3", "x", time.time() + 60)
        outro_no.delete("preco:VALE3")

        assert backend.get_raw("preco:VALE3") is None


class TestEscolhaDoBackend:
    def test_sem_redis_url_o_padrao_e_o_arquivo_local(self, monkeypatch):
        """Com um nó só, é a escolha certa: sem operação e sem dependência."""
        monkeypatch.delenv("REDIS_URL", raising=False)

        assert cache_backends.build_backend().name == "sqlite"

    def test_com_redis_url_o_backend_e_compartilhado(self, monkeypatch):
        monkeypatch.setenv("REDIS_URL", REDIS_URL or "redis://localhost:6379/0")

        try:
            escolhido = cache_backends.build_backend()
        except RuntimeError as erro:
            # Sem o pacote instalado, a falha é **alta e explicada** em vez de
            # silenciosa: cair para cache por nó em produção seria o pior
            # resultado possível, e é justamente o que ninguém notaria.
            assert "redis" in str(erro).lower()
            return

        assert escolhido.name == "redis"

    def test_a_fachada_diz_se_o_cache_e_compartilhado(self, monkeypatch):
        monkeypatch.delenv("REDIS_URL", raising=False)
        cache_mod.set_backend(None)

        estado = cache_mod.describe()

        assert estado["shared"] is False
        assert "REDIS_URL" in estado["note"]
        cache_mod.set_backend(None)


class _ClienteFalso:
    """Um Redis mínimo, só para conferir o que o adaptador **fala**.

    Ele não prova nada sobre compartilhamento entre nós — isso é o teste de
    contrato, que precisa de servidor. O que ele pega é a classe de erro que um
    servidor real também pegaria, mas tarde: chave sem prefixo, padrão SQL
    enviado como se fosse glob, vencimento perdido no caminho.
    """

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
        """Sem prefixo, o cache dividiria espaço com qualquer outra coisa no
        mesmo Redis."""
        backend, cliente = redis_falso
        backend.set_raw("uasset:PETR4", "v", time.time() + 60)

        assert "p:uasset:PETR4" in cliente.data

    def test_o_vencimento_viaja_no_valor(self, redis_falso):
        """O TTL nativo apagaria o dado vencido, que é justamente o que o
        disjuntor usa para degradar."""
        backend, cliente = redis_falso
        vence = time.time() + 60
        backend.set_raw("k", "conteudo", vence)

        envelope = json.loads(cliente.data["p:k"])
        assert envelope["v"] == "conteudo"
        assert envelope["e"] == pytest.approx(vence)

    def test_o_ttl_nativo_e_maior_que_o_vencimento(self, redis_falso):
        """A margem espelha o SQLite, onde a linha sobrevive até a faxina.
        Sem ela, o mesmo código degradaria diferente conforme o backend."""
        backend, cliente = redis_falso
        backend.set_raw("k", "v", time.time() + 60)

        assert cliente.ttls["p:k"] > 60

    def test_entrada_ja_vencida_ainda_recebe_ttl_positivo(self, redis_falso):
        """`set_raw` com TTL negativo acontece: é como o teste de degradação
        fabrica dado velho. TTL zero ou negativo seria recusado pelo Redis."""
        backend, cliente = redis_falso
        backend.set_raw("k", "v", time.time() - 120)

        assert cliente.ttls["p:k"] >= 1

    def test_o_padrao_sql_vira_glob(self, redis_falso):
        """O resto do produto fala `%` porque nasceu no SQLite. Mandar `%` para
        o Redis não apagaria nada — e não apagar cache é uma falha silenciosa."""
        backend, _ = redis_falso
        backend.set_raw("uasset:PETR4", "a", time.time() + 60)
        backend.set_raw("uasset:VALE3", "b", time.time() + 60)
        backend.set_raw("rates:cdi", "c", time.time() + 60)

        assert backend.delete_pattern("uasset:%") == 2
        assert backend.get_raw("rates:cdi") is not None

    def test_limpar_tudo_nao_alcanca_chave_de_fora(self, redis_falso):
        """O Redis pode ser compartilhado com outra coisa; `clear_all` limpa o
        cache, não o servidor."""
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
        """O Redis já expira sozinho; varrer tudo para antecipar isso seria
        trabalho por trabalho, e `keys` numa base grande trava o servidor."""
        backend, _ = redis_falso

        assert backend.purge_expired() == 0
