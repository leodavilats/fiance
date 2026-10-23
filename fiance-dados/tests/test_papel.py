from __future__ import annotations

import pytest
import sqlalchemy as sa
from fastapi.testclient import TestClient

from dadosapi import banco
from dadosapi.app import criar
from dadosapi.config import Configuracao
from tests.conftest import RAIZ, TOKEN, _migrar, criar_conta

SENHA = "papel-de-teste"


@pytest.fixture
def url_do_papel(url, bancos):
    motor = sa.create_engine(url)
    with motor.begin() as conn:
        conn.exec_driver_sql((RAIZ / "papel.sql").read_text(encoding="utf-8"))
        conn.exec_driver_sql(f"ALTER ROLE dados_api PASSWORD '{SENHA}'")
    yield sa.make_url(url).set(username="dados_api", password=SENHA).render_as_string(False)
    with motor.begin() as conn:
        conn.exec_driver_sql("REASSIGN OWNED BY dados_api TO CURRENT_USER")
        conn.exec_driver_sql("DROP OWNED BY dados_api")
        conn.exec_driver_sql("DROP ROLE dados_api")
    motor.dispose()


def test_a_api_e_as_migracoes_rodam_com_o_papel_proprio(url_do_papel):
    _migrar(RAIZ, url_do_papel)
    bancos = banco.criar(url_do_papel)
    try:
        cliente = TestClient(criar(Configuracao(url_do_papel, TOKEN), bancos))
        criada = criar_conta(cliente, email="papel@teste.com")
        chave = {"Authorization": f"Bearer {criada['chave']['chave']}"}

        assert cliente.get("/v1/ativos/TEST3/cotacoes", headers=chave).status_code == 200
        with bancos.acesso.begin() as conn, pytest.raises(sa.exc.ProgrammingError):
            conn.execute(sa.text("DELETE FROM mercado.cotacao"))
        with bancos.acesso.begin() as conn, pytest.raises(sa.exc.ProgrammingError):
            conn.execute(sa.text("CREATE SCHEMA invasor"))
    finally:
        bancos.leitura.dispose()
        bancos.acesso.dispose()
