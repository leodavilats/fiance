from __future__ import annotations

import os
import shutil
import subprocess
from datetime import date
from pathlib import Path

import pandas as pd
import sqlalchemy as sa

from pesquisa.dados import Base, montar
from pesquisa.fundamentos import preparar, preparar_acoes

PASTA = Path(__file__).resolve().parents[1] / ".retratos"

_SERIE = """
SELECT s.cnpj, s.classe, s.data, s.codigo, s.fechamento, s.fechamento_ajustado, s.retorno_total,
       s.volume, s.salto_sem_evento
FROM mercado.serie_papel s
"""
_CDI = "SELECT data, valor FROM mercado.indicador WHERE serie = 12"

_DISPONIVEL = """(SELECT min(x.data_entrega) FROM mercado.documento x
    WHERE x.cnpj = {t}.cnpj AND x.tipo = {t}.tipo AND x.data_referencia = {t}.data_referencia)"""

_RESULTADO = f"""
SELECT r.cnpj, r.tipo, r.data_referencia, r.versao, r.fim_exercicio, r.lucro_controladores,
       {_DISPONIVEL.format(t="r")} AS disponivel_em
FROM mercado.fundamento_resultado r
WHERE r.inicio_exercicio = make_date(extract(year FROM r.fim_exercicio)::int, 1, 1)
"""

_BALANCO = """
SELECT b.cnpj, b.tipo, b.data_referencia, b.versao, b.patrimonio_controladores
FROM mercado.fundamento_balanco b
WHERE b.data = b.data_referencia
"""

_ACOES = """
SELECT d.cnpj, d.tipo, d.data_referencia, d.versao, k.acoes_total, k.tesouraria_total
FROM mercado.composicao_capital k
JOIN mercado.documento d ON d.id = k.documento_id
"""

_CAPITAL = """
SELECT cnpj, data_referencia, versao, data_aprovacao, acoes_total
FROM mercado.capital_social
"""

CONSULTAS = {
    "serie": _SERIE,
    "cdi": _CDI,
    "resultado": _RESULTADO,
    "balanco": _BALANCO,
    "acoes": _ACOES,
    "capital": _CAPITAL,
}


class SemRetrato(RuntimeError):
    pass


def _url() -> str:
    url = (os.environ.get("PESQUISA_DATABASE_URL") or "").strip()
    if not url:
        raise SemRetrato("PESQUISA_DATABASE_URL não está definida: o retrato precisa ler a base.")
    for antigo in ("postgres://", "postgresql://"):
        if url.startswith(antigo):
            return "postgresql+psycopg://" + url[len(antigo) :]
    return url


def tirar(pasta: Path = PASTA) -> str:
    nome = date.today().isoformat()
    destino = pasta / nome
    destino.mkdir(parents=True, exist_ok=True)
    engine = sa.create_engine(_url())
    try:
        with engine.connect() as conn:
            for arquivo, consulta in CONSULTAS.items():
                tabela = pd.read_sql(sa.text(consulta), conn)
                tabela.to_parquet(destino / f"{arquivo}.parquet", index=False)
    finally:
        engine.dispose()
    return nome


def _copiar_pelo_railway(consulta: str, destino: Path, servico: str) -> None:
    comando = (
        f"psql -U postgres -d mercado -c "
        f'"\\copy ({" ".join(consulta.split())}) TO STDOUT WITH CSV HEADER"'
    )
    railway = shutil.which("railway")
    if railway is None:
        raise SemRetrato("A CLI do Railway não está instalada.")
    with destino.open("wb") as saida:
        processo = subprocess.run(
            [railway, "ssh", "--service", servico, "--", comando],
            stdin=subprocess.DEVNULL,
            stdout=saida,
            stderr=subprocess.PIPE,
            check=False,
        )
    if processo.returncode != 0:
        raise SemRetrato(f"A exportação pelo Railway falhou: {processo.stderr.decode()[-500:]}")


def tirar_pelo_railway(servico: str = "postgres-mercado", pasta: Path = PASTA) -> str:
    nome = date.today().isoformat()
    destino = pasta / nome
    destino.mkdir(parents=True, exist_ok=True)
    for arquivo, consulta in CONSULTAS.items():
        csv = destino / f"{arquivo}.csv"
        _copiar_pelo_railway(consulta, csv, servico)
        tabela = pd.read_csv(
            csv,
            skiprows=_linhas_antes_do_cabecalho(csv),
            dtype={"cnpj": str, "classe": str, "codigo": str},
        )
        if "salto_sem_evento" in tabela:
            tabela["salto_sem_evento"] = tabela["salto_sem_evento"].map({"t": True, "f": False})
        tabela.to_parquet(destino / f"{arquivo}.parquet", index=False)
        csv.unlink()
    return nome


def _linhas_antes_do_cabecalho(csv: Path) -> int:
    with csv.open(encoding="utf-8", errors="replace") as entrada:
        for numero, linha in enumerate(entrada):
            if linha.startswith(("cnpj,", "data,")):
                return numero
    raise SemRetrato(f"{csv.name} veio sem cabeçalho.")


def carregar(nome: str | None = None, pasta: Path = PASTA) -> Base:
    disponiveis = sorted(p.name for p in pasta.iterdir() if p.is_dir()) if pasta.exists() else []
    if not disponiveis:
        raise SemRetrato("Não há retrato da base: rode `python -m pesquisa retrato` antes.")
    nome = nome or disponiveis[-1]
    if nome not in disponiveis:
        raise SemRetrato(f"Não há retrato {nome}; há {', '.join(disponiveis)}.")
    tabelas = {
        arquivo: pd.read_parquet(caminho)
        for arquivo in CONSULTAS
        if (caminho := pasta / nome / f"{arquivo}.parquet").exists()
    }
    base = montar(tabelas["serie"], tabelas["cdi"], nome)
    if {"resultado", "balanco"} <= set(tabelas):
        base.fundamentos = preparar(tabelas["resultado"], tabelas["balanco"])
    if {"acoes", "capital"} <= set(tabelas):
        base.acoes = preparar_acoes(tabelas["acoes"], tabelas["capital"])
    return base
