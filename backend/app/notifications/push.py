from __future__ import annotations

import json
import logging

from app.core.config import get_settings

logger = logging.getLogger("fiance.push")

_firebase_app = None
_init_attempted = False


def _get_firebase_app():
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


def is_configured() -> bool:
    return _get_firebase_app() is not None


def send_push(
    tokens: list[str],
    title: str,
    body: str,
    data: dict[str, str] | None = None,
) -> list[str]:
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
