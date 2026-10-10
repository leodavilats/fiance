from __future__ import annotations

import io
import os
import zipfile
from pathlib import Path

import pytest
import sqlalchemy as sa
from alembic import command
from alembic.config import Config

from datajob.config import url_do_banco

URL = os.environ.get("DATAJOB_TEST_DATABASE_URL")

RAIZ = Path(__file__).resolve().parents[1]
TRECHO = Path(__file__).parent / "fixtures" / "COTAHIST_D08102026_trecho.TXT"


@pytest.fixture
def engine():
    if not URL:
        pytest.skip("DATAJOB_TEST_DATABASE_URL não definida: gravação precisa de Postgres")
    url = url_do_banco(URL)
    motor = sa.create_engine(url)
    with motor.begin() as conn:
        conn.execute(sa.text("DROP SCHEMA IF EXISTS mercado CASCADE"))
    config = Config(str(RAIZ / "alembic.ini"))
    config.set_main_option("script_location", str(RAIZ / "migrations"))
    config.set_main_option("sqlalchemy.url", url)
    command.upgrade(config, "head")
    yield motor
    motor.dispose()


def zipar(texto: str) -> bytes:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as arquivo:
        arquivo.writestr("COTAHIST.TXT", texto.encode("latin-1"))
    return buffer.getvalue()
