from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest
import sqlalchemy as sa
from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient

from dadosapi import banco
from dadosapi.app import criar
from dadosapi.config import Configuracao, url_do_banco

URL = os.environ.get("DADOS_API_TEST_DATABASE_URL")
RAIZ = Path(__file__).resolve().parents[1]
DATA_JOB = RAIZ.parent / "data-job"
TOKEN = "t" * 40


def _migrar(pasta: Path, url: str) -> None:
    config = Config(str(pasta / "alembic.ini"))
    config.set_main_option("script_location", str(pasta / "migrations"))
    config.set_main_option("sqlalchemy.url", url)
    command.upgrade(config, "head")


_DADOS = """
INSERT INTO mercado.coleta (id, fonte, arquivo, status, iniciada_em)
    VALUES (1, 'teste', 'teste', 'ok', now());
INSERT INTO mercado.ativo (isin, nome_resumido, especie, codbdi, primeiro_pregao, ultimo_pregao) VALUES
    ('BRTESTACNOR1', 'TESTE', 'ON NM', '02', '2005-01-03', '2026-10-09'),
    ('BRXPMLCTF000', 'FII XP MALLS', 'CI', '12', '2024-01-02', '2026-10-09');
INSERT INTO mercado.ticker (codigo, isin, primeiro_pregao, ultimo_pregao) VALUES
    ('TEST3', 'BRTESTACNOR1', '2005-01-03', '2026-10-09'),
    ('XPML11', 'BRXPMLCTF000', '2024-01-02', '2026-10-09');
INSERT INTO mercado.cotacao (isin, data, codigo, codbdi, abertura, maxima, minima, media,
    fechamento, negocios, quantidade, volume, fator_cotacao, coleta_id) VALUES
    ('BRTESTACNOR1', '2005-01-03', 'TEST3', '02', 1000, 1000, 1000, 1000, 1000, 1, 1, 1, 1000, 1),
    ('BRTESTACNOR1', '2026-10-08', 'TEST3', '02', 39, 40, 38, 39, 39, 10, 100, 3900, 1, 1),
    ('BRTESTACNOR1', '2026-10-09', 'TEST3', '02', 40, 41, 40, 41, 41, 10, 100, 4100, 1, 1),
    ('BRXPMLCTF000', '2026-10-09', 'XPML11', '12', 100, 100, 100, 100, 100, 1, 1, 100, 1, 1);
INSERT INTO mercado.empresa (cnpj, razao_social, nome_comercial, setor, coleta_id)
    VALUES ('00000000000001', 'TESTE SA', 'Teste', 'Energia', 1);
INSERT INTO mercado.emissor (codigo, cnpj, metodo) VALUES ('TEST', '00000000000001', 'fca');
INSERT INTO mercado.provento (emissor, classe, data_com, tipo, valor, origem, data_pagamento,
    coleta_id) VALUES
    ('TEST', 'ON', '2026-03-01', 'DIVIDENDO', 1.5, 'b3_historico', NULL, 1),
    ('XPML', 'CI', '2026-08-31', 'RENDIMENTO', 0.9, 'b3_recente', '2026-09-15', 1),
    ('XPML', 'CI', '2024-07-31', 'RENDIMENTO', 0.8, 'cvm_estimado', NULL, 1);
INSERT INTO mercado.fii_mensal (emissor, classe, referencia, cnpj, isin, nome, segmento,
    valor_patrimonial_cota, coleta_id) VALUES
    ('XPML', 'CI', '2026-08-01', '9', 'BRXPMLCTF000', 'XP MALLS', 'Shoppings', 110, 1);
INSERT INTO mercado.documento (id, cnpj, tipo, data_referencia, versao, data_entrega, coleta_id) VALUES
    (1, '00000000000001', 'DFP', '2024-12-31', 1, '2025-03-10', 1),
    (2, '00000000000001', 'DFP', '2024-12-31', 2, '2025-06-01', 1);
INSERT INTO mercado.demonstracao_linha (documento_id, demonstracao, inicio_exercicio, fim_exercicio,
    conta, consolidado, descricao, valor, conta_fixa, coleta_id) VALUES
    (1, 'DRE', '2024-01-01', '2024-12-31', '3.01', true, 'Receita de Venda de Bens e/ou Serviços', 1000, true, 1),
    (1, 'DRE', '2024-01-01', '2024-12-31', '3.11', true, 'Lucro/Prejuízo Consolidado do Período', 100, true, 1),
    (1, 'DRE', '2024-01-01', '2024-12-31', '3.11.01', true, 'Atribuído a Sócios da Empresa Controladora', 90, true, 1),
    (1, 'BPP', '2024-12-31', '2024-12-31', '2.03', true, 'Patrimônio Líquido Consolidado', 500, true, 1),
    (2, 'DRE', '2024-01-01', '2024-12-31', '3.01', true, 'Receita de Venda de Bens e/ou Serviços', 1000, true, 1),
    (2, 'DRE', '2024-01-01', '2024-12-31', '3.11', true, 'Lucro/Prejuízo Consolidado do Período', 80, true, 1),
    (2, 'DRE', '2024-01-01', '2024-12-31', '3.11.01', true, 'Atribuído a Sócios da Empresa Controladora', 70, true, 1),
    (2, 'BPP', '2024-12-31', '2024-12-31', '2.03', true, 'Patrimônio Líquido Consolidado', 500, true, 1);
INSERT INTO mercado.indicador (serie, data, valor, coleta_id) VALUES
    (12, '2026-10-08', 0.05, 1), (12, '2026-10-09', 0.05, 1), (1, '2026-10-09', 4.99, 1);
INSERT INTO mercado.tesouro (titulo, vencimento, data, taxa_compra, taxa_venda, pu_compra, pu_venda,
    pu_base, coleta_id) VALUES
    ('Tesouro Selic', '2029-03-01', '2026-10-08', 0.01, 0.02, 20000, 19990, 19990, 1),
    ('Tesouro Selic', '2029-03-01', '2026-10-09', 0.01, 0.02, 20010, 20000, 20000, 1);
INSERT INTO mercado.rodada (iniciada_em, terminada_em, falhas) VALUES (now(), now(), '{}');
REFRESH MATERIALIZED VIEW mercado.serie_papel;
REFRESH MATERIALIZED VIEW mercado.serie_fundo;
REFRESH MATERIALIZED VIEW mercado.ativo_hoje;
REFRESH MATERIALIZED VIEW mercado.fundamento_app;
"""


@pytest.fixture(scope="session")
def url():
    if not URL:
        pytest.skip("DADOS_API_TEST_DATABASE_URL não definida: a API precisa de Postgres")
    url = url_do_banco(URL)
    motor = sa.create_engine(url)
    with motor.begin() as conn:
        conn.execute(sa.text("DROP SCHEMA IF EXISTS acesso CASCADE"))
        conn.execute(sa.text("DROP SCHEMA IF EXISTS mercado CASCADE"))
    motor.dispose()
    sys.path.insert(0, str(DATA_JOB))
    _migrar(DATA_JOB, url)
    _migrar(RAIZ, url)
    motor = sa.create_engine(url)
    with motor.begin() as conn:
        conn.execute(sa.text(_DADOS))
    motor.dispose()
    return url


@pytest.fixture
def bancos(url):
    criados = banco.criar(url)
    with criados.acesso.begin() as conn:
        conn.execute(
            sa.text(
                "TRUNCATE acesso.evento_de_cobranca, acesso.assinatura, acesso.uso_diario, "
                "acesso.chave, acesso.conta CASCADE"
            )
        )
        conn.execute(
            sa.text("UPDATE acesso.plano SET limite_por_dia = 20000 WHERE codigo = 'convidado'")
        )
    yield criados
    criados.leitura.dispose()
    criados.acesso.dispose()


@pytest.fixture
def cliente(bancos, url):
    return TestClient(criar(Configuracao(url, TOKEN), bancos))


def criar_conta(cliente, plano: str = "convidado", email: str = "eu@teste.com") -> dict:
    resposta = cliente.post(
        "/admin/contas",
        json={"email": email, "nome": "Teste", "plano": plano},
        headers={"X-Admin-Token": TOKEN},
    )
    assert resposta.status_code == 201, resposta.text
    return resposta.json()


@pytest.fixture
def chave(cliente) -> dict:
    criada = criar_conta(cliente)
    return {"Authorization": f"Bearer {criada['chave']['chave']}"}
