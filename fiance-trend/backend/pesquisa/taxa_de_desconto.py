from __future__ import annotations

import json
from collections import Counter
from dataclasses import replace
from datetime import UTC, date, datetime
from pathlib import Path
from statistics import median

import pandas as pd

from pesquisa import preco_justo
from pesquisa.dados import Base
from pesquisa.motor import fins_de_mes
from pesquisa.periodos import Periodo
from pesquisa.universo import elegiveis

modelo = preco_justo.modelo

ARQUIVO = Path(__file__).resolve().parents[1] / "registro_taxa.jsonl"
PERIODO = Periodo("distribuicao", date(2011, 1, 1), date(2025, 9, 30))
LIMITE_DE_UM_LADO = 0.80

PREFIXADO = "Tesouro Prefixado"
IPCA = "Tesouro IPCA+"

CANDIDATAS = {
    0: "Selic média de 10 anos + 5 pontos",
    1: "Selic média de 10 anos + 3 pontos",
    2: "Tesouro Prefixado mais longo à venda + 5 pontos",
    3: "Tesouro IPCA+ mais longo à venda + meta de inflação + 5 pontos",
}


class Recusado(RuntimeError):
    pass


def ler(arquivo: Path = ARQUIVO) -> list[dict]:
    if not arquivo.exists():
        return []
    return [json.loads(x) for x in arquivo.read_text(encoding="utf-8").splitlines() if x]


def conferir(forcar: bool, arquivo: Path = ARQUIVO) -> None:
    if ler(arquivo) and not forcar:
        raise Recusado("A distribuição já rodou: o protocolo não repete sem --forcar.")


def titulo_de_referencia(
    tesouro: pd.DataFrame, titulo: str, dia: pd.Timestamp
) -> tuple[str, float] | None:
    do_mes = tesouro[
        (tesouro["titulo"] == titulo)
        & (tesouro["data"] <= dia)
        & (tesouro["data"].dt.to_period("M") == dia.to_period("M"))
    ]
    if do_mes.empty:
        return None
    ultimo = do_mes[do_mes["data"] == do_mes["data"].max()]
    a_venda = ultimo[ultimo["taxa_compra"].notna() & ultimo["taxa_venda"].notna()]
    if a_venda.empty:
        return None
    mais_longo = a_venda.loc[a_venda["vencimento"].idxmax()]
    return mais_longo["vencimento"].date().isoformat(), float(mais_longo["taxa_venda"])


def _com_taxa(juro, taxa: float) -> modelo.ValuationRates:
    if juro is None:
        return modelo.ValuationRates(
            discount_rate=round(taxa, 4), fii_yield=0.0, rate_base="tesouro", selic_pct=0.0
        )
    return replace(juro, discount_rate=round(taxa, 4))


def juros_do_mes(selic: pd.Series, tesouro: pd.DataFrame, dia: pd.Timestamp) -> tuple[dict, dict]:
    premio = modelo.EQUITY_RISK_PREMIUM
    atual = preco_justo.juro_na_data(selic, dia)
    juros: dict[int, modelo.ValuationRates | None] = {0: atual, 1: None, 2: None, 3: None}
    referencias: dict[int, str | None] = dict.fromkeys(CANDIDATAS)
    if atual is not None:
        juros[1] = _com_taxa(atual, atual.discount_rate - premio + 0.03)
    prefixado = titulo_de_referencia(tesouro, PREFIXADO, dia)
    if prefixado:
        referencias[2] = prefixado[0]
        juros[2] = _com_taxa(atual, prefixado[1] / 100 + premio)
    ipca = titulo_de_referencia(tesouro, IPCA, dia)
    if ipca:
        referencias[3] = ipca[0]
        juros[3] = _com_taxa(atual, ipca[1] / 100 + modelo.INFLATION_TARGET + premio)
    return juros, referencias


def _tesouro(base: Base) -> pd.DataFrame:
    tabela = base.extras.get("tesouro")
    if tabela is None:
        raise Recusado("O retrato não tem o Tesouro: tire um retrato novo.")
    return tabela.assign(
        data=pd.to_datetime(tabela["data"]),
        vencimento=pd.to_datetime(tabela["vencimento"]),
        taxa_compra=pd.to_numeric(tabela["taxa_compra"]),
        taxa_venda=pd.to_numeric(tabela["taxa_venda"]),
    )


def avaliar(base: Base, periodo: Periodo = PERIODO) -> tuple[dict, list[dict]]:
    dados = preco_justo.Dados(base)
    tesouro = _tesouro(base)
    fins = sorted(d for d in fins_de_mes(base.pregoes) if periodo.contem(d.date()))
    meses = []
    for dia in fins:
        juros, referencias = juros_do_mes(dados.selic, tesouro, dia)
        contagem = {c: Counter() for c in CANDIDATAS}
        larguras: dict[int, list[float]] = {c: [] for c in CANDIDATAS}
        for papel in elegiveis(base, dia):
            com_juro = {c: j for c, j in juros.items() if j is not None}
            for c, (grupo, motivo, largura) in preco_justo.faixas(
                base, dados, papel, dia, com_juro
            ).items():
                contagem[c][grupo or motivo] += 1
                if largura is not None:
                    larguras[c].append(largura)
            for c in CANDIDATAS:
                if juros[c] is None:
                    contagem[c]["sem_titulo_a_venda" if c in (2, 3) else "sem_juro"] += 1
        mes = {"mes": dia.date().isoformat()}
        for c in CANDIDATAS:
            mes[str(c)] = {
                "taxa": juros[c].discount_rate if juros[c] else None,
                "referencia": referencias[c],
                "contagem": dict(contagem[c]),
                "largura_mediana": round(median(larguras[c]), 4) if larguras[c] else None,
            }
        meses.append(mes)
    return resumir(meses), meses


def _fracoes(contagem: dict) -> dict[str, float] | None:
    com_faixa = sum(contagem.get(g, 0) for g in preco_justo.GRUPOS)
    if com_faixa == 0:
        return None
    return {g: contagem.get(g, 0) / com_faixa for g in preco_justo.GRUPOS}


def resumir(meses: list[dict]) -> dict:
    resumo = {"meses": len(meses), "de": meses[0]["mes"] if meses else None,
              "ate": meses[-1]["mes"] if meses else None, "candidatas": {}}  # fmt: skip
    for c, descricao in CANDIDATAS.items():
        linhas = [(m["mes"], m[str(c)]) for m in meses]
        com_fracao = [(mes, v, f) for mes, v in linhas if (f := _fracoes(v["contagem"]))]
        if not com_fracao:
            resumo["candidatas"][str(c)] = {"descricao": descricao, "meses_com_faixa": 0}
            continue
        mediana = {g: round(median(f[g] for _, _, f in com_fracao), 3) for g in preco_justo.GRUPOS}
        alto = max(com_fracao, key=lambda x: x[1]["taxa"])
        baixo = min(com_fracao, key=lambda x: x[1]["taxa"])
        motivos = Counter()
        for _, v in linhas:
            motivos.update({k: n for k, n in v["contagem"].items() if k not in preco_justo.GRUPOS})
        trocas = sum(
            1
            for (_, a), (_, b) in zip(linhas, linhas[1:], strict=False)
            if a["referencia"] and b["referencia"] and a["referencia"] != b["referencia"]
        )
        larguras = [v["largura_mediana"] for _, v in linhas if v["largura_mediana"] is not None]
        resumo["candidatas"][str(c)] = {
            "descricao": descricao,
            "meses_com_faixa": len(com_fracao),
            "com_faixa_medio": round(
                sum(
                    sum(v["contagem"].get(g, 0) for g in preco_justo.GRUPOS)
                    for _, v, _ in com_fracao
                )
                / len(com_fracao),
                1,
            ),
            "mediana": mediana,
            "juro_mais_alto": {
                "mes": alto[0],
                "taxa": alto[1]["taxa"],
                **{g: round(alto[2][g], 3) for g in preco_justo.GRUPOS},
            },  # fmt: skip
            "juro_mais_baixo": {
                "mes": baixo[0],
                "taxa": baixo[1]["taxa"],
                **{g: round(baixo[2][g], 3) for g in preco_justo.GRUPOS},
            },  # fmt: skip
            "sem_faixa_por_motivo": dict(motivos.most_common()),
            "trocas_de_titulo": trocas,
            "largura_mediana": round(median(larguras), 3) if larguras else None,
            "compativel": mediana["acima"] <= LIMITE_DE_UM_LADO
            and mediana["abaixo"] <= LIMITE_DE_UM_LADO,
        }
    return resumo


def anotar(retrato: str, resumo: dict, forcado: bool, arquivo: Path = ARQUIVO) -> dict:
    registro = {
        "quando": datetime.now(UTC).isoformat(timespec="seconds"),
        "periodo": PERIODO.nome,
        "retrato": retrato,
        "forcado": forcado,
        "resumo": resumo,
    }
    with arquivo.open("a", encoding="utf-8") as saida:
        saida.write(json.dumps(registro, ensure_ascii=False) + "\n")
    return registro
