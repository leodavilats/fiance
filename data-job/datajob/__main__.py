from __future__ import annotations

import argparse
import sys
from datetime import date
from pathlib import Path

import httpx
import sqlalchemy as sa

from datajob import armazenamento, coleta
from datajob.config import carregar
from datajob.fontes import b3_cotahist

_FONTES = {b3_cotahist.FONTE: b3_cotahist.processar}


class Indisponivel(RuntimeError):
    pass


def _baixar(url: str) -> bytes:
    resposta = httpx.get(url, timeout=300, follow_redirects=True)
    if resposta.status_code != 200:
        raise Indisponivel(f"{url} respondeu {resposta.status_code}.")
    return resposta.content


def _relatar(arquivo: str, resultado: coleta.Resultado) -> None:
    if resultado.status == "pulada":
        print(
            f"{arquivo}: já coletado com o mesmo conteúdo, pulado (coleta {resultado.coleta_id})."
        )
        return
    print(
        f"{arquivo}: {resultado.lidas} registros lidos, {resultado.gravadas} cotações gravadas "
        f"ou alteradas, {resultado.quarentena} em quarentena (coleta {resultado.coleta_id})."
    )


def _cotahist(args, engine: sa.Engine, raiz: Path) -> None:
    if args.arquivo:
        caminho = Path(args.arquivo)
        nome, conteudo = caminho.name, caminho.read_bytes()
    else:
        url = b3_cotahist.url_do_ano(args.ano) if args.ano else b3_cotahist.url_do_dia(args.dia)
        nome, conteudo = url.rsplit("/", 1)[1], _baixar(url)

    resultado = coleta.executar(
        engine, raiz, b3_cotahist.FONTE, nome, conteudo, b3_cotahist.processar, args.forcar
    )
    _relatar(nome, resultado)


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

    reprocessar = comandos.add_parser("reprocessar", help="Regrava a partir do bruto guardado")
    reprocessar.add_argument("--fonte", choices=sorted(_FONTES), required=True)

    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _argumentos(sys.argv[1:] if argv is None else argv)
    config = carregar()
    engine = sa.create_engine(config.database_url)
    comandos = {"cotahist": _cotahist, "reprocessar": _reprocessar}
    try:
        comandos[args.comando](args, engine, config.bruto_dir)
    except (Indisponivel, b3_cotahist.ArquivoInvalido) as e:
        print(f"Falhou: {e}", file=sys.stderr)
        return 1
    finally:
        engine.dispose()
    return 0


if __name__ == "__main__":
    sys.exit(main())
