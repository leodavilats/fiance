"""Entitlement: quem pode o quê, decidido num lugar só.

A régua é dado (`plans`), a resolução é função pura de assinatura + trial + flag
(`resolve`), o contador reaproveita a primitiva do rate limiting (`meter`) e a
aplicação é uma dependência do FastAPI (`guard`).

Duas regras de arquitetura, ambas com teste:

* **Nenhum `if premium` fora daqui.** Cerca espalhada é impossível de mudar
  depois, e a composição do plano é a decisão mais provável de ser revista.
* **`analysis/` e `optimizer/` não importam nada deste módulo.** O cálculo de
  score, preço justo e ordenação não pode saber quem paga — se souber, a
  independência do algoritmo vira promessa em vez de propriedade.
"""

from .guard import PaymentRequired, peek, requires
from .plans import Feature, Plan, Rule, allows, limit_for, rule_for
from .resolve import TRIAL_DAYS, Decision, Entitlements, check, resolve

__all__ = [
    "Decision",
    "Entitlements",
    "Feature",
    "PaymentRequired",
    "Plan",
    "Rule",
    "TRIAL_DAYS",
    "allows",
    "check",
    "limit_for",
    "peek",
    "requires",
    "resolve",
    "rule_for",
]
