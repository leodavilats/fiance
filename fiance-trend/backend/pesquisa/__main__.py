from __future__ import annotations

import argparse
import json
import sys

from pesquisa import (
    calibracao,
    calibracao_taxa_nova,
    custo_de_troca,
    filtro_de_risco,
    registro,
    relatorio,
    retrato,
    taxa_de_desconto,
)
from pesquisa.hipoteses import todas
from pesquisa.metricas import resumir
from pesquisa.motor import simular
from pesquisa.periodos import PERIODOS
from pesquisa.ranking import CLASSES, SINAIS
from pesquisa.ranking import registro as registro_ranking
from pesquisa.ranking.medida import avaliar


def _rodar(args) -> int:
    hipotese = todas()[args.hipotese]
    if args.periodo == "prova":
        registro.conferir_prova(hipotese, args.forcar)
    if args.periodo == "estudo":
        registro.conferir_teto(hipotese, args.forcar)

    base = retrato.carregar(args.retrato)
    resultado = simular(
        base,
        PERIODOS[args.periodo],
        lambda dia: hipotese.escolher(base, dia, hipotese.parametros),
        meses_entre_rebalanceamentos=hipotese.parametros.get("meses_entre_rebalanceamentos", 1),
    )
    resumo = resumir(resultado)
    registro.anotar(hipotese, args.periodo, base.retrato, resumo, forcado=args.forcar)
    relatorio.guardar(
        resultado, hipotese.nome, registro.assinatura(hipotese), args.periodo, base.nomes
    )
    print(json.dumps(resumo, ensure_ascii=False, indent=2))
    print(
        f"variações no estudo: {len(registro.variacoes_no_estudo())} de {registro.TETO_DO_ESTUDO}",
        file=sys.stderr,
    )
    return 0


def _ranking(args) -> int:
    sinal, classe = SINAIS[args.sinal], CLASSES[args.classe]
    registro_ranking.conferir(sinal, classe, args.periodo, args.forcar)
    base = retrato.carregar(args.retrato)
    dados = base.fii if classe.nome == "fii" else base
    if dados is None:
        raise retrato.SemRetrato("O retrato não tem FIIs: tire um retrato novo.")
    resumo, meses = avaliar(dados, classe.periodos[args.periodo], sinal, classe)
    anotado = registro_ranking.anotar(
        sinal, classe, args.periodo, base.retrato, resumo, forcado=args.forcar
    )
    destino = relatorio.PASTA / (
        f"ranking_{classe.nome}_{sinal.nome}_{anotado['assinatura']}_{args.periodo}.json"
    )
    destino.write_text(
        json.dumps({"resumo": resumo, "meses": meses}, ensure_ascii=False), encoding="utf-8"
    )
    print(json.dumps(resumo, ensure_ascii=False, indent=2))
    print(
        f"variações no estudo: {registro_ranking.variacoes_no_estudo()} de "
        f"{registro_ranking.TETO_DO_ESTUDO}",
        file=sys.stderr,
    )
    return 0


def _calibracao(args) -> int:
    calibracao.conferir(args.variacao, args.periodo, args.forcar)
    base = retrato.carregar(args.retrato)
    resumo, meses = calibracao.rodar(base, args.variacao, args.periodo)
    calibracao.anotar(args.variacao, args.periodo, base.retrato, resumo, args.forcar)
    destino = relatorio.PASTA / f"calibracao_{args.variacao}_{args.periodo}.json"
    destino.write_text(
        json.dumps({"resumo": resumo, "meses": meses}, ensure_ascii=False), encoding="utf-8"
    )
    print(json.dumps(resumo, ensure_ascii=False, indent=2))
    return 0


def _calibracao_taxa_nova(args) -> int:
    calibracao_taxa_nova.conferir(args.periodo, args.forcar)
    base = retrato.carregar(args.retrato)
    resumo, meses = calibracao_taxa_nova.rodar(base, args.periodo)
    calibracao_taxa_nova.anotar(args.periodo, base.retrato, resumo, args.forcar)
    destino = relatorio.PASTA / f"calibracao_taxa_nova_{args.periodo}.json"
    destino.write_text(
        json.dumps({"resumo": resumo, "meses": meses}, ensure_ascii=False), encoding="utf-8"
    )
    print(json.dumps(resumo, ensure_ascii=False, indent=2))
    return 0


def _taxa_de_desconto(args) -> int:
    taxa_de_desconto.conferir(args.forcar)
    base = retrato.carregar(args.retrato)
    resumo, meses = taxa_de_desconto.avaliar(base)
    taxa_de_desconto.anotar(base.retrato, resumo, args.forcar)
    destino = relatorio.PASTA / "taxa_de_desconto.json"
    destino.write_text(
        json.dumps({"resumo": resumo, "meses": meses}, ensure_ascii=False), encoding="utf-8"
    )
    print(json.dumps(resumo, ensure_ascii=False, indent=2))
    return 0


def _custo_de_troca(args) -> int:
    custo_de_troca.conferir(args.forcar)
    base = retrato.carregar(args.retrato)
    resumo, _ = custo_de_troca.rodar(base)
    custo_de_troca.anotar(base.retrato, resumo, args.forcar)
    destino = relatorio.PASTA / "custo_de_troca.json"
    destino.write_text(json.dumps(resumo, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(resumo, ensure_ascii=False, indent=2))
    return 0


def _filtro_de_risco(args) -> int:
    filtro_de_risco.conferir(args.forcar)
    base = retrato.carregar(args.retrato)
    resumo = filtro_de_risco.rodar(base)
    filtro_de_risco.anotar(base.retrato, resumo, args.forcar)
    destino = relatorio.PASTA / "filtro_de_risco.json"
    destino.write_text(json.dumps(resumo, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(resumo, ensure_ascii=False, indent=2))
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
    ranking = comandos.add_parser("ranking", help="Mede o acerto de um sinal de tendência")
    ranking.add_argument("--sinal", choices=sorted(SINAIS), required=True)
    ranking.add_argument("--classe", choices=sorted(CLASSES), required=True)
    ranking.add_argument("--periodo", choices=sorted(PERIODOS), required=True)
    ranking.add_argument("--retrato", help="Data do retrato; sem ela, o mais recente")
    ranking.add_argument("--forcar", action="store_true", help="Passa por cima do protocolo")
    calibrar = comandos.add_parser("calibracao", help="Mede o preço justo do app no passado")
    calibrar.add_argument(
        "--variacao", type=int, choices=sorted(calibracao.VARIACOES), required=True
    )
    calibrar.add_argument("--periodo", choices=sorted(calibracao.PERIODOS), required=True)
    calibrar.add_argument("--retrato", help="Data do retrato; sem ela, o mais recente")
    calibrar.add_argument("--forcar", action="store_true", help="Passa por cima do protocolo")
    nova = comandos.add_parser(
        "calibracao-taxa-nova", help="Mede o veredito com a taxa da ADR-028 contra o retorno"
    )
    nova.add_argument("--periodo", choices=sorted(calibracao.PERIODOS), required=True)
    nova.add_argument("--retrato", help="Data do retrato; sem ela, o mais recente")
    nova.add_argument("--forcar", action="store_true", help="Passa por cima do protocolo")
    for nome, ajuda in (
        ("taxa-de-desconto", "Distribui o veredito por taxa candidata, sem olhar retorno"),
        ("custo-de-troca", "Estima o spread por faixa de liquidez"),
        ("filtro-de-risco", "Mede o filtro de tendência na validação, uma vez"),
    ):
        estudo = comandos.add_parser(nome, help=ajuda)
        estudo.add_argument("--retrato", help="Data do retrato; sem ela, o mais recente")
        estudo.add_argument("--forcar", action="store_true", help="Passa por cima do protocolo")
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
        if args.comando == "ranking":
            return _ranking(args)
        if args.comando == "calibracao":
            return _calibracao(args)
        if args.comando == "calibracao-taxa-nova":
            return _calibracao_taxa_nova(args)
        if args.comando == "taxa-de-desconto":
            return _taxa_de_desconto(args)
        if args.comando == "custo-de-troca":
            return _custo_de_troca(args)
        if args.comando == "filtro-de-risco":
            return _filtro_de_risco(args)
        return _rodar(args)
    except (
        registro.ProvaLacrada,
        registro.TetoAtingido,
        registro_ranking.Recusado,
        calibracao.Recusado,
        calibracao_taxa_nova.Recusado,
        taxa_de_desconto.Recusado,
        custo_de_troca.Recusado,
        filtro_de_risco.Recusado,
        retrato.SemRetrato,
    ) as e:
        print(f"Recusado: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
