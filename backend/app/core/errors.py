from __future__ import annotations

# Exceções de domínio tipadas. Antes o mapeamento para status HTTP era feito
# por busca de substring na mensagem ("não encontrado" in msg), o que acoplava
# texto de erro em português a código de status.


class DomainError(ValueError):
    """Erro de regra de negócio. Vira HTTP 400 por padrão."""

    status_code = 400


class NotFoundError(DomainError):
    """Recurso inexistente para o usuário atual. Vira HTTP 404."""

    status_code = 404


class ConflictError(DomainError):
    """Estado atual do recurso impede a operação. Vira HTTP 409."""

    status_code = 409
