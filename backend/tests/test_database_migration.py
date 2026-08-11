from sqlalchemy import text

from app.core.database import _add_missing_columns, engine
from app.storage import portfolio_store


def test_add_missing_columns_backfills_existing_rows():
    # Regressão: Base.metadata.create_all() só cria tabelas ausentes, nunca
    # adiciona colunas novas a uma tabela que já existia (ex.: quando
    # PreferencesDb ganhou notify_price_alerts/notify_new_opportunities com
    # o banco de dev já em uso) — isso derrubava qualquer request tocando
    # preferências com 500 (coluna inexistente).
    uid = "test_migration_backfill"
    portfolio_store.set_preferences(cash_available=50.0, user_id=uid)

    with engine.begin() as conn:
        conn.execute(text("ALTER TABLE preferences DROP COLUMN notify_price_alerts"))

    # Sem a coluna, ler preferências deve falhar (confirma que o cenário do
    # bug foi reproduzido).
    try:
        portfolio_store.get_preferences(user_id=uid)
        raised = False
    except Exception:
        raised = True
    assert raised, "esperava falha com a coluna ausente, antes da migração"

    _add_missing_columns()

    # Depois da migração, a leitura funciona e a linha existente foi
    # preenchida com o default (True), não ficou NULL.
    prefs = portfolio_store.get_preferences(user_id=uid)
    assert prefs["notify_price_alerts"] is True


def test_add_missing_columns_is_idempotent():
    # Rodar de novo sem nada faltando não deve levantar erro.
    _add_missing_columns()
    _add_missing_columns()
