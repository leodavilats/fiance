from __future__ import annotations

import json
import logging

from app.core.config import get_settings

logger = logging.getLogger("fianceai.push")

_firebase_app = None
_init_attempted = False


def _get_firebase_app():
    """Inicializa o Firebase Admin SDK sob demanda a partir da chave de conta
    de serviço em settings.firebase_service_account_json. Retorna None (e loga
    um aviso, uma única vez) se a credencial não estiver configurada — nesse
    caso send_push() apenas loga em vez de enviar de verdade."""
    global _firebase_app, _init_attempted
    if _firebase_app is not None or _init_attempted:
        return _firebase_app

    _init_attempted = True
    settings = get_settings()
    if not settings.firebase_service_account_json:
        logger.warning(
            "FIREBASE_SERVICE_ACCOUNT_JSON não configurado — notificações push "
            "serão apenas logadas, não enviadas de verdade."
        )
        return None

    try:
        import firebase_admin
        from firebase_admin import credentials

        cred_dict = json.loads(settings.firebase_service_account_json)
        cred = credentials.Certificate(cred_dict)
        _firebase_app = firebase_admin.initialize_app(cred)
    except Exception:
        logger.exception("Falha ao inicializar o Firebase Admin SDK")
        _firebase_app = None

    return _firebase_app


def send_push(
    tokens: list[str],
    title: str,
    body: str,
    data: dict[str, str] | None = None,
) -> list[str]:
    """Envia uma notificação push para os tokens informados.

    Retorna a lista de tokens que falharam por serem inválidos/não registrados
    (o chamador deve removê-los via portfolio_store.unregister_device_token).
    Se o Firebase não estiver configurado, apenas loga e retorna [] (nenhum
    token é considerado inválido nesse caso — é uma limitação de ambiente,
    não do token).
    """
    if not tokens:
        return []

    app = _get_firebase_app()
    if app is None:
        logger.info("[push simulado] '%s' — %s — destinos: %d", title, body, len(tokens))
        return []

    from firebase_admin import messaging

    invalid: list[str] = []
    for token in tokens:
        message = messaging.Message(
            token=token,
            notification=messaging.Notification(title=title, body=body),
            data=data or {},
        )
        try:
            messaging.send(message, app=app)
        except messaging.UnregisteredError:
            invalid.append(token)
        except Exception:
            logger.exception("Falha ao enviar push para token %s…", token[:12])

    return invalid
