"""Circuit breaker da fonte de cotação.

Todo o produto pago depende de um fornecedor. Quando ele cai, o comportamento
sem disjuntor é o pior possível: cada requisição de usuário espera o timeout
inteiro, a fila do servidor enche, e o app fica lento em vez de ficar honesto.

O disjuntor troca "lento e quebrado" por "rápido e explícito". Aberto, nem
tenta: devolve vazio na hora, e quem chama cai no cache vencido — que é dado
antigo, mas é dado, e a idade dele fica visível na tela.

É por processo, como o resto da instrumentação. Com mais de um worker cada um
descobre a queda por conta própria; isso custa algumas tentativas a mais e não
justifica coordenar por banco enquanto não houver mais de um nó.
"""

from __future__ import annotations

import logging
import threading
import time
from dataclasses import dataclass, field

logger = logging.getLogger("fiance.circuit")

#: Falhas seguidas para abrir. Baixo demais abre em soluço de rede; alto demais
#: faz o usuário esperar o timeout várias vezes antes de o disjuntor agir.
FAILURE_THRESHOLD = 5

#: Quanto fica aberto antes de deixar uma tentativa passar.
OPEN_SECONDS = 60.0

#: Sucessos necessários em meia-abertura para voltar ao normal. Mais de um
#: porque uma resposta boa isolada durante uma queda parcial reabriria a
#: torneira cedo demais.
RECOVERY_SUCCESSES = 2


@dataclass
class _State:
    failures: int = 0
    successes: int = 0
    opened_at: float | None = None
    last_failure: str = ""
    total_rejected: int = 0
    lock: threading.Lock = field(default_factory=threading.Lock)


_states: dict[str, _State] = {}
_registry_lock = threading.Lock()


def _state_for(provider: str) -> _State:
    with _registry_lock:
        if provider not in _states:
            _states[provider] = _State()
        return _states[provider]


def allows(provider: str, now: float | None = None) -> bool:
    """`False` quando o disjuntor está aberto e o descanso ainda não passou."""
    moment = now if now is not None else time.time()
    state = _state_for(provider)

    with state.lock:
        if state.opened_at is None:
            return True

        if moment - state.opened_at < OPEN_SECONDS:
            state.total_rejected += 1
            return False

        # Meia-abertura: deixa passar para descobrir se voltou.
        return True


def record_success(provider: str) -> None:
    state = _state_for(provider)
    with state.lock:
        if state.opened_at is not None:
            state.successes += 1
            if state.successes >= RECOVERY_SUCCESSES:
                logger.info("Circuito de %s fechado: fonte respondendo de novo.", provider)
                state.opened_at = None
                state.failures = 0
                state.successes = 0
            return

        state.failures = 0


def record_failure(provider: str, reason: str = "", now: float | None = None) -> None:
    moment = now if now is not None else time.time()
    state = _state_for(provider)

    with state.lock:
        state.last_failure = reason
        state.successes = 0

        if state.opened_at is not None:
            # Falhou na meia-abertura: recomeça o descanso.
            state.opened_at = moment
            return

        state.failures += 1
        if state.failures >= FAILURE_THRESHOLD:
            state.opened_at = moment
            logger.warning(
                "Circuito de %s aberto após %d falhas seguidas. Última: %s",
                provider,
                state.failures,
                reason or "sem detalhe",
            )


def status(provider: str, now: float | None = None) -> dict:
    """Estado legível — vai para `/data-quality`, não para o usuário final."""
    moment = now if now is not None else time.time()
    state = _state_for(provider)

    with state.lock:
        if state.opened_at is None:
            situacao = "fechado"
            retoma_em = None
        elif moment - state.opened_at < OPEN_SECONDS:
            situacao = "aberto"
            retoma_em = round(OPEN_SECONDS - (moment - state.opened_at), 1)
        else:
            situacao = "meia-abertura"
            retoma_em = 0.0

        return {
            "provider": provider,
            "state": situacao,
            "consecutive_failures": state.failures,
            "rejected_while_open": state.total_rejected,
            "last_failure": state.last_failure,
            "retry_in_seconds": retoma_em,
        }


def reset(provider: str | None = None) -> None:
    """Fecha o disjuntor. Existe para teste e para a rota de manutenção."""
    with _registry_lock:
        alvos = [provider] if provider else list(_states)
        for nome in alvos:
            _states[nome] = _State()
