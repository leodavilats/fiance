from app.notifications.push import send_push


def test_send_push_without_credentials_is_noop():
    # Sem FIREBASE_SERVICE_ACCOUNT_JSON configurado (padrão nos testes), o
    # envio deve apenas logar e retornar sem erro — nunca derrubar o chamador.
    invalid = send_push(["fake-token-1", "fake-token-2"], "Título", "Corpo")
    assert invalid == []


def test_send_push_with_no_tokens_is_noop():
    assert send_push([], "Título", "Corpo") == []
