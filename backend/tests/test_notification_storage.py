from app.storage import portfolio_store


def test_register_and_list_device_token():
    uid = "test_notif_register"
    portfolio_store.register_device_token("token-abc", "android", user_id=uid)

    all_tokens = portfolio_store.list_all_device_tokens()
    mine = [t for t in all_tokens if t["user_id"] == uid]
    assert len(mine) == 1
    assert mine[0]["token"] == "token-abc"


def test_register_same_token_reassigns_user():
    # Regression: se o mesmo token FCM aparecer para outro usuário (ex.: troca
    # de conta no aparelho), o registro deve realocar, não duplicar.
    portfolio_store.register_device_token("shared-token", "android", user_id="user_a")
    portfolio_store.register_device_token("shared-token", "android", user_id="user_b")

    all_tokens = portfolio_store.list_all_device_tokens()
    matching = [t for t in all_tokens if t["token"] == "shared-token"]
    assert len(matching) == 1
    assert matching[0]["user_id"] == "user_b"


def test_list_device_tokens_filters_by_user():
    portfolio_store.register_device_token("tok-user-x", "android", user_id="user_x")
    portfolio_store.register_device_token("tok-user-y", "android", user_id="user_y")

    mine = portfolio_store.list_device_tokens(user_id="user_x")
    assert [t["token"] for t in mine] == ["tok-user-x"]


def test_unregister_device_token():
    uid = "test_notif_unregister"
    portfolio_store.register_device_token("token-to-remove", "android", user_id=uid)
    portfolio_store.unregister_device_token("token-to-remove", user_id=uid)

    all_tokens = portfolio_store.list_all_device_tokens()
    assert not any(t["token"] == "token-to-remove" for t in all_tokens)


def test_notified_opportunities_roundtrip():
    uid = "test_notif_opportunities"
    assert portfolio_store.get_notified_opportunity_tickers(uid) == set()

    portfolio_store.mark_opportunities_notified(uid, ["PETR4", "VALE3"])
    assert portfolio_store.get_notified_opportunity_tickers(uid) == {"PETR4", "VALE3"}

    # Idempotente: marcar de novo não duplica nem quebra.
    portfolio_store.mark_opportunities_notified(uid, ["PETR4"])
    assert portfolio_store.get_notified_opportunity_tickers(uid) == {"PETR4", "VALE3"}


def test_preferences_notification_flags_default_true():
    uid = "test_notif_prefs_default"
    prefs = portfolio_store.get_preferences(user_id=uid)
    assert prefs["notify_price_alerts"] is True
    assert prefs["notify_new_opportunities"] is True


def test_preferences_notification_flags_can_be_disabled():
    uid = "test_notif_prefs_disable"
    portfolio_store.set_preferences(
        cash_available=100.0,
        notify_price_alerts=False,
        notify_new_opportunities=True,
        user_id=uid,
    )
    prefs = portfolio_store.get_preferences(user_id=uid)
    assert prefs["notify_price_alerts"] is False
    assert prefs["notify_new_opportunities"] is True
