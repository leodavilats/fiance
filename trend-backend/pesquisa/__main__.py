from __future__ import annotations

import argparse
import json
import sys

from pesquisa import registro, relatorio, retrato
from pesquisa.hipoteses import todas
from pesquisa.metricas import resumir
from pesquisa.motor import simular
from pesquisa.periodos import PERIODOS


def _rodar(args) -> int:
    hipotese = todas()[args.hipotese]
    if args.periodo == "prova":
        registro.conferir_prova(hipotese, args.forcar)

    base = retrato.carregar(args.retrato)
    resultado = simular(
        base, PERIODOS[args.periodo], lambda dia: hipotese.escolher(base, dia, hipotese.parametros)
    )
    resumo = resumir(resultado)
    registro.anotar(hipotese, args.periodo, base.retrato, resumo, forcado=args.forcar)
    relatorio.guardar(
        resultado, hipotese.nome, registro.assinatura(hipotese), args.periodo, base.nomes
    )
    print(json.dumps(resumo, ensure_ascii=False, indent=2))
    print(
        f"variações já testadas de {hipotese.nome}: {registro.tentativas(hipotese.nome)}",
        file=sys.stderr,
    )
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m pesquisa")
    comandos = parser.add_subparsers(dest="comando", required=True)
    tirar = comandos.add_parser(
        "retrato", help="Exporta a base para arquivos locais com a data de hoje"
    )
    tirar.add_argument(
        "--pelo-railway", action="store_true", help="Exporta pela CLI do Railway, sem expor o banco"
    )
    rodar = comandos.add_parser("rodar", help="Simula uma hipótese num período")
    rodar.add_argument("--hipotese", choices=sorted(todas()), required=True)
    rodar.add_argument("--periodo", choices=sorted(PERIODOS), required=True)
    rodar.add_argument("--retrato", help="Data do retrato; sem ela, o mais recente")
    rodar.add_argument("--forcar", action="store_true", help="Reabre a prova, e fica no registro")
    comandos.add_parser("relatorio", help="Gera relatorio.html a partir do registro")
    args = parser.parse_args(sys.argv[1:] if argv is None else argv)

    try:
        if args.comando == "relatorio":
            destino = relatorio.PASTA.parent / "relatorio.html"
            destino.write_text(relatorio.gerar(), encoding="utf-8")
            print(f"relatório em {destino}")
            return 0
        if args.comando == "retrato":
            nome = retrato.tirar_pelo_railway() if args.pelo_railway else retrato.tirar()
            print(f"retrato {nome} gravado.")
            return 0
        return _rodar(args)
    except (registro.ProvaLacrada, retrato.SemRetrato) as e:
        print(f"Recusado: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
