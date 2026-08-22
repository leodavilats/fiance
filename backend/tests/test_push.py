from app.notifications import push


def _reset_firebase_app_cache():
    push._firebase_app = None
    push._init_attempted = False


def test_send_push_without_credentials_is_noop(monkeypatch):
    class _FakeSettings:
        firebase_service_account_json = ""

    monkeypatch.setattr(push, "get_settings", lambda: _FakeSettings())
    _reset_firebase_app_cache()
    try:
        invalid = push.send_push(["fake-token-1", "fake-token-2"], "Título", "Corpo")
        assert invalid == []
    finally:
        _reset_firebase_app_cache()


def test_send_push_with_no_tokens_is_noop():
    assert push.send_push([], "Título", "Corpo") == []


def test_is_configured_false_without_credentials(monkeypatch):
    class _FakeSettings:
        firebase_service_account_json = ""

    monkeypatch.setattr(push, "get_settings", lambda: _FakeSettings())
    _reset_firebase_app_cache()
    try:
        assert push.is_configured() is False
    finally:
        _reset_firebase_app_cache()
