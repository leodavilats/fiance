import os
import tempfile

# Usa um arquivo SQLite temporário isolado para os testes, para nunca tocar
# o banco de desenvolvimento (.cache/fianceai.db). Precisa ser setado antes
# de qualquer import de app.core.database (que cria o engine no import).
_tmp_db = os.path.join(tempfile.mkdtemp(prefix="fianceai_test_"), "test.db")
os.environ["DATABASE_URL"] = f"sqlite:///{_tmp_db}"
