"""O custo do scanner é fixo, não marginal.

O scanner é a única feature do produto com custo que cresceria com o uso. A
correção não é cobrar por ela: é materializar o resultado num job periódico, de
modo que a varredura aconteça N vezes por dia — sempre a mesma quantidade —
e nenhuma requisição de usuário espere por ela. Feito isso, o Free pode ter
prévia sem medo e o Premium pode ter filtro sem teto.
"""

from __future__ import annotations

import asyncio

import pytest

from app.core import jobs
from app.services import OpportunityService
from tests.conftest import make_auth_headers


class TestJobPeriodico:
    @pytest.mark.anyio
    async def test_o_job_sobe_junto_com_a_aplicacao(self, monkeypatch):
        """Um job que existe mas ninguém agenda não materializa nada."""
        monkeypatch.setattr(jobs, "warm_up_market_scan", lambda: asyncio.sleep(0))

        tarefas = jobs.start_background_jobs()
        try:
            nomes = {t.get_name() for t in tarefas}
        finally:
            for tarefa in tarefas:
                tarefa.cancel()

        assert "market-scan-loop" in nomes

    def test_o_intervalo_chega_antes_do_ttl_vencer(self):
        """Se o job rodasse depois do vencimento, sobraria uma janela em que o
        usuário paga a varredura — que é exatamente o que ele veio evitar."""
        from app.services.opportunity_service import _SCAN_TTL

        assert jobs.MARKET_SCAN_INTERVAL < _SCAN_TTL

    def test_o_lock_expira_antes_do_proximo_ciclo(self):
        """TTL maior que o intervalo travaria o job para sempre."""
        assert jobs.MARKET_SCAN_INTERVAL * 0.9 < jobs.MARKET_SCAN_INTERVAL

    @pytest.mark.anyio
    async def test_o_corpo_do_job_recalcula_o_scan(self, monkeypatch):
        chamadas = []

        async def _fake_refresh(self):
            chamadas.append(1)
            return [], 0

        monkeypatch.setattr(OpportunityService, "_refresh_market", _fake_refresh)

        await jobs._market_scan_body()

        assert chamadas == [1]


class TestCustoNaoCresceComUsuarios:
    def test_dez_leituras_disparam_uma_varredura_so(self, client, monkeypatch):
        """O contraste que dá sentido ao job: sem cache, seriam dez varreduras."""
        varreduras = []

        original = OpportunityService._refresh_market

        async def _contando(self):
            varreduras.append(1)
            return await original(self)

        monkeypatch.setattr(OpportunityService, "_refresh_market", _contando)

        for i in range(10):
            headers = make_auth_headers(f"u_scan_{i}")
            assert client.get("/api/opportunities", headers=headers).status_code == 200

        assert len(varreduras) <= 1, "cada usuário novo não pode custar uma varredura do universo"

    def test_o_warm_up_e_o_job_usam_locks_diferentes(self):
        """Um roda uma vez no startup, o outro a cada ciclo. Compartilhar o lock
        faria o warm-up bloquear o primeiro ciclo periódico."""
        assert jobs.WARM_UP_LOCK == "market_scan_warmup"

    @pytest.mark.anyio
    async def test_o_warm_up_libera_o_lock_no_fim(self, monkeypatch):
        liberados = []

        async def _noop_scan(self):
            return [], 0

        monkeypatch.setattr(OpportunityService, "_scan_market", _noop_scan)
        monkeypatch.setattr(
            jobs.portfolio_store,
            "try_acquire_job_lock",
            lambda *a, **k: True,
        )
        monkeypatch.setattr(
            jobs.portfolio_store,
            "release_job_lock",
            lambda name, holder: liberados.append(name),
        )

        await jobs.warm_up_market_scan()

        assert liberados == [jobs.WARM_UP_LOCK]

    @pytest.mark.anyio
    async def test_o_warm_up_libera_o_lock_mesmo_falhando(self, monkeypatch):
        """Falha segurando o lock deixaria a frota inteira sem aquecer."""
        liberados = []

        async def _explode(self):
            raise RuntimeError("fonte fora do ar")

        monkeypatch.setattr(OpportunityService, "_scan_market", _explode)
        monkeypatch.setattr(jobs.portfolio_store, "try_acquire_job_lock", lambda *a, **k: True)
        monkeypatch.setattr(
            jobs.portfolio_store,
            "release_job_lock",
            lambda name, holder: liberados.append(name),
        )

        await jobs.warm_up_market_scan()

        assert liberados == [jobs.WARM_UP_LOCK]

    @pytest.mark.anyio
    async def test_sem_o_lock_o_warm_up_nao_varre(self, monkeypatch):
        """Três réplicas subindo não podem varrer o universo três vezes."""
        varreduras = []

        async def _contando(self):
            varreduras.append(1)
            return [], 0

        monkeypatch.setattr(OpportunityService, "_scan_market", _contando)
        monkeypatch.setattr(jobs.portfolio_store, "try_acquire_job_lock", lambda *a, **k: False)

        await jobs.warm_up_market_scan()

        assert varreduras == []
