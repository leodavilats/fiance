from __future__ import annotations

import argparse
import sys
from datetime import date
from pathlib import Path

import sqlalchemy as sa

from datajob import armazenamento, coleta, rotina
from datajob.config import carregar
from datajob.erros import ArquivoInvalido
from datajob.fontes import (
    b3_cotahist,
    b3_emissores,
    b3_proventos,
    cvm_cadastro,
    cvm_demonstracoes,
    cvm_fca,
    cvm_fre,
    cvm_ipe,
)
from datajob.rede import Indisponivel, baixar

_FONTES = {
    b3_cotahist.FONTE: b3_cotahist.processar,
    cvm_cadastro.FONTE: cvm_cadastro.processar,
    cvm_fca.FONTE: cvm_fca.processar,
    b3_emissores.FONTE: b3_emissores.processar,
    b3_proventos.FONTE: b3_proventos.processar,
    cvm_ipe.FONTE: cvm_ipe.processar,
    cvm_fre.FONTE: cvm_fre.processar,
    **{cvm_demonstracoes.FONTE[t]: cvm_demonstracoes.processador(t) for t in ("DFP", "ITR")},
}


def _relatar(arquivo: str, resultado: coleta.Resultado | None) -> None:
    if resultado is None:
        print(f"{arquivo}: não publicado (sem pregão, ou ainda não saiu).", flush=True)
    elif resultado.status == "pulada":
        print(f"{arquivo}: já coletado com o mesmo conteúdo, pulado.", flush=True)
    else:
        print(
            f"{arquivo}: {resultado.lidas} registros lidos, {resultado.gravadas} linhas "
            f"gravadas ou alteradas, {resultado.quarentena} em quarentena "
            f"(coleta {resultado.coleta_id}).",
            flush=True,
        )


def _cotahist(args, engine: sa.Engine, raiz: Path) -> None:
    if args.arquivo:
        caminho = Path(args.arquivo)
        nome, conteudo = caminho.name, caminho.read_bytes()
    else:
        url = b3_cotahist.url_do_ano(args.ano) if args.ano else b3_cotahist.url_do_dia(args.dia)
        nome, conteudo = url.rsplit("/", 1)[1], baixar(url)

    resultado = coleta.executar(
        engine, raiz, b3_cotahist.FONTE, nome, conteudo, b3_cotahist.processar, args.forcar
    )
    _relatar(nome, resultado)


def _diario(args, engine: sa.Engine, raiz: Path) -> int:
    falhas = rotina.diario(engine, raiz, baixar, _relatar)
    return 1 if falhas else 0


def _reprocessar(args, engine: sa.Engine, raiz: Path) -> None:
    for caminho in armazenamento.guardados(raiz, args.fonte):
        nome = caminho.name.split("__", 1)[1]
        resultado = coleta.executar(
            engine, raiz, args.fonte, nome, caminho.read_bytes(), _FONTES[args.fonte], forcar=True
        )
        _relatar(nome, resultado)


def _argumentos(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(prog="python -m datajob")
    comandos = parser.add_subparsers(dest="comando", required=True)

    cotahist = comandos.add_parser("cotahist", help="Cotações diárias da B3")
    origem = cotahist.add_mutually_exclusive_group(required=True)
    origem.add_argument("--ano", type=int)
    origem.add_argument("--dia", type=date.fromisoformat)
    origem.add_argument("--arquivo", help="ZIP já baixado, em vez de buscar na B3")
    cotahist.add_argument("--forcar", action="store_true", help="Grava mesmo se o hash já entrou")

    comandos.add_parser("diario", help="Busca o que falta desde o último pregão gravado")

    reprocessar = comandos.add_parser("reprocessar", help="Regrava a partir do bruto guardado")
    reprocessar.add_argument("--fonte", choices=sorted(_FONTES), required=True)

    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _argumentos(sys.argv[1:] if argv is None else argv)
    config = carregar()
    engine = sa.create_engine(config.database_url)
    comandos = {"cotahist": _cotahist, "diario": _diario, "reprocessar": _reprocessar}
    try:
        return comandos[args.comando](args, engine, config.bruto_dir) or 0
    except (Indisponivel, ArquivoInvalido) as e:
        print(f"Falhou: {e}", file=sys.stderr)
        return 1
    finally:
        engine.dispose()


if __name__ == "__main__":
    sys.exit(main())
