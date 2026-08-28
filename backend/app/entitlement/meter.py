"""Contador de uso de feature — a mesma primitiva do teto de abuso.

`app/core/usage.py` já contava por usuário, recurso e janela para o rate
limiting. Teto de plano é o mesmo problema com outra janela, então não ganha
tabela nova: a granularidade mora no formato de `window_key`, e o mês é o
brasileiro, pelo mesmo motivo que a isenção de IR é.

Duas janelas, e a diferença é semântica:

* **Mensal** para consumo que reinicia — cinco páginas de ativo por mês.
* **Permanente** para posse — três alertas são três alertas, não três por mês.
  Apagar um alerta libera a vaga; virar o mês não.
"""

from __future__ import annotations

from app.core import usage

from .plans import Feature

#: Janela dos tetos permanentes. Uma chave fixa mantém tudo na mesma tabela sem
#: fingir que existe recorte de tempo onde não existe.
LIFETIME_WINDOW = "lifetime"

#: TTL do contador mensal: dois meses, para a janela anterior ainda existir
#: quando alguém consulta o histórico de uso perto da virada.
MONTHLY_TTL = usage.DAY * 62
LIFETIME_TTL = usage.DAY * 3650


def _resource(feature: Feature) -> str:
    return f"feature:{feature.value}"


def _window(monthly: bool) -> str:
    return usage.month_window() if monthly else LIFETIME_WINDOW


def used(user_id: str, feature: Feature, monthly: bool = True) -> int:
    return usage.current(user_id, _resource(feature), _window(monthly))


def consume(user_id: str, feature: Feature, amount: int = 1, monthly: bool = True) -> int:
    return usage.increment(
        user_id,
        _resource(feature),
        _window(monthly),
        ttl_seconds=MONTHLY_TTL if monthly else LIFETIME_TTL,
        amount=amount,
    )


def release(user_id: str, feature: Feature, amount: int = 1) -> int:
    """Devolve uma vaga de teto permanente.

    Existe porque posse é reversível: apagar um alerta tem que liberar o lugar.
    Consumo mensal **não** usa isto — devolver cota de página de ativo já
    visitada seria dar acesso ilimitado a quem sabe recarregar.
    """
    atual = used(user_id, feature, monthly=False)
    if atual <= 0:
        return 0
    return consume(user_id, feature, amount=-min(amount, atual), monthly=False)


def reset(user_id: str, feature: Feature, monthly: bool = True) -> int:
    """Zera o contador — cortesia manual e manutenção."""
    return usage.reset(user_id, _resource(feature), _window(monthly))
