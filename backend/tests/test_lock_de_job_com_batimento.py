"""Um worker que morre não pode travar o snapshot diário por horas.

O lock não era liberado ao terminar — só vencia —, e o TTL era o próprio intervalo do job. Isso
é o certo para *espaçar* ciclos e o errado para *exclusão mútua*: um worker que morresse logo
após adquirir deixava `daily_snapshot` bloqueado por até 5,4h (0,9 × 6h), em silêncio.

O batimento separa os dois prazos: curto enquanto o corpo roda, longo depois que ele termina.
"""

from __future__ import annotations

import asyncio
import time

import pytest

from app.core import jobs
from app.storage import portfolio_store

NOME = "job_de_teste"


@pytest.fixture(autouse=True)
def _limpa_lock():
    yield
    portfolio_store.release_job_lock(NOME, jobs.WORKER_ID)
    portfolio_store.release_job_lock(NOME, "outro_worker")


def _expira_em() -> float | None:
    from app.core.database import db_session
    from app.models.db_models import JobLockDb

    with db_session() as session:
        row = session.get(JobLockDb, NOME)
        return None if row is None else row.expires_at


class TestRenovacao:
    def test_renova_o_prazo_de_quem_tem_o_lock(self):
        portfolio_store.try_acquire_job_lock(NOME, jobs.WORKER_ID, 10)
        antes = _expira_em()

        assert portfolio_store.renew_job_lock(NOME, jobs.WORKER_ID, 600) is True
        assert _expira_em() > antes + 500

    def test_nao_renova_lock_de_outro(self):
        portfolio_store.try_acquire_job_lock(NOME, "outro_worker", 600)

        assert portfolio_store.renew_job_lock(NOME, jobs.WORKER_ID, 600) is False, (
            "renovar lock alheio seria roubá-lo, que é o oposto do que o lock faz"
        )

    def test_nao_renova_lock_que_nao_existe(self):
        assert portfolio_store.renew_job_lock(NOME, jobs.WORKER_ID, 600) is False


class TestPrazoCurtoEnquantoRoda:
    def test_o_lock_nasce_com_o_prazo_do_batimento_e_nao_com_o_do_intervalo(self):
        """É este prazo que decide em quanto tempo um worker morto é substituído."""
        assert jobs.HEARTBEAT_TTL <= 300, (
            "o prazo enquanto o corpo roda tem de ser curto — era o intervalo do job, "
            "e por isso a recuperação levava horas"
        )
        assert jobs.HEARTBEAT_TTL > jobs.HEARTBEAT_INTERVAL * 2, (
            "e folgado o bastante para uma batida atrasada não liberar um lock vivo"
        )

    def test_corpo_curto_deixa_o_prazo_longo_ao_terminar(self, monkeypatch):
        monkeypatch.setattr(jobs, "HEARTBEAT_INTERVAL", 0.01)

        async def corpo() -> None:
            return None

        asyncio.run(jobs._run_guarded(NOME, interval_seconds=0, lock_ttl_seconds=3600, body=corpo))

        restante = _expira_em() - time.time()
        assert restante > 3000, (
            "terminado o corpo, o lock vira espaçamento: liberá-lo faria o worker seguinte "
            "repetir o trabalho segundos depois"
        )

    def test_enquanto_o_corpo_roda_o_prazo_e_curto(self, monkeypatch):
        monkeypatch.setattr(jobs, "HEARTBEAT_INTERVAL", 3600)
        visto: list[float] = []

        async def corpo() -> None:
            visto.append(_expira_em() - time.time())

        asyncio.run(jobs._run_guarded(NOME, interval_seconds=0, lock_ttl_seconds=3600, body=corpo))

        assert visto, "o corpo não rodou"
        assert visto[0] <= jobs.HEARTBEAT_TTL + 1, (
            "durante o ciclo o prazo é o do batimento — é o que limita o estrago de um worker "
            "que morre no meio"
        )

    def test_o_batimento_estende_um_corpo_mais_longo_que_o_prazo(self, monkeypatch):
        """O corpo dura mais que o TTL, e mesmo assim o lock continua nosso no fim."""
        monkeypatch.setattr(jobs, "HEARTBEAT_INTERVAL", 0.02)
        monkeypatch.setattr(jobs, "HEARTBEAT_TTL", 0.2)

        async def corpo() -> None:
            await asyncio.sleep(0.5)

        asyncio.run(jobs._run_guarded(NOME, interval_seconds=0, lock_ttl_seconds=3600, body=corpo))

        restante = _expira_em() - time.time()
        assert restante > 3000, (
            "sem renovar, o lock teria vencido no meio do corpo e outro worker o tomaria"
        )

    def test_corpo_que_estoura_ainda_solta_o_batimento(self, monkeypatch):
        monkeypatch.setattr(jobs, "HEARTBEAT_INTERVAL", 0.01)
        sobraram: list[int] = []

        async def corpo() -> None:
            raise RuntimeError("falha no meio do ciclo")

        async def cenario() -> None:
            await jobs._run_guarded(NOME, interval_seconds=0, lock_ttl_seconds=3600, body=corpo)
            await asyncio.sleep(0.05)
            sobraram.append(
                sum(1 for t in asyncio.all_tasks() if (t.get_name() or "").startswith("heartbeat-"))
            )

        asyncio.run(cenario())

        assert sobraram == [0], "o batimento vazou depois da exceção do corpo"
