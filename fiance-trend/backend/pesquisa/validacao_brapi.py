from __future__ import annotations

import json
import time
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import httpx
import pandas as pd

# As réguas são as do protocolo (docs/pesquisas/validacao-brapi.md) e não mudam depois da execução.
INICIO = pd.Timestamp("2005-01-03")
EVENTOS = {"DESDOBRAMENTO", "GRUPAMENTO", "BONIFICACAO"}
DIAS_DE_FOLGA_DO_EVENTO = 5
FOLGA_DO_FATOR = 0.01
FOLGA_DA_CONFIRMACAO = 0.10
FOLGA_DO_DIA = 0.005
DIAS_QUE_BATEM = 0.98
DESVIO_MAXIMO = 0.05
FOLGA_DO_PROVENTO = 0.01
FOLGA_ABSOLUTA_DO_PROVENTO = 0.0001
TICKERS_POR_LOTE = 10
TETO_DE_REQUISICOES = 1000
URL = "https://brapi.dev/api/quote/"
REGISTRO = Path(__file__).resolve().parents[1] / "registro_validacao.jsonl"
_BRT = ZoneInfo("America/Sao_Paulo")


def ler_token(env: Path) -> str:
    for linha in env.read_text(encoding="utf-8").splitlines():
        if linha.startswith("BRAPI_TOKEN="):
            return linha.split("=", 1)[1].strip().strip('"')
    raise SystemExit(f"BRAPI_TOKEN não está em {env}")


@dataclass
class Coleta:
    requisicoes: int
    lotes_em_cache: int
    falhas: list[str]


def coletar(tickers: list[str], token: str, pasta: Path, teto: int = TETO_DE_REQUISICOES) -> Coleta:
    pasta.mkdir(parents=True, exist_ok=True)
    lotes = [tickers[i : i + TICKERS_POR_LOTE] for i in range(0, len(tickers), TICKERS_POR_LOTE)]
    feitas, em_cache, falhas = 0, 0, []
    with httpx.Client(headers={"Authorization": f"Bearer {token}"}, timeout=60) as cliente:
        for numero, lote in enumerate(lotes):
            arquivo = pasta / f"lote_{numero:04d}.json"
            if arquivo.exists():
                em_cache += 1
                continue
            if feitas >= teto:
                falhas.append(f"teto de {teto} requisições atingido no lote {numero}")
                break
            resposta = cliente.get(
                URL + ",".join(lote),
                params={"range": "1y", "interval": "1d", "dividends": "true"},
            )
            feitas += 1
            if resposta.status_code == 429:
                time.sleep(5)
                resposta = cliente.get(
                    URL + ",".join(lote),
                    params={"range": "1y", "interval": "1d", "dividends": "true"},
                )
                feitas += 1
            if resposta.is_error:
                falhas.append(f"lote {numero} ({','.join(lote)}): HTTP {resposta.status_code}")
                continue
            arquivo.write_text(resposta.text, encoding="utf-8")
    return Coleta(feitas, em_cache, falhas)


def _dia(texto: str | None) -> pd.Timestamp | None:
    return pd.Timestamp(texto[:10]) if texto else None


def ler_respostas(pasta: Path) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, list[str]]:
    precos, eventos, proventos, sem_resultado = [], [], [], []
    for arquivo in sorted(pasta.glob("lote_*.json")):
        for r in json.loads(arquivo.read_text(encoding="utf-8")).get("results") or []:
            codigo = r.get("symbol")
            if not codigo:
                continue
            historico = r.get("historicalDataPrice") or []
            if not historico:
                sem_resultado.append(codigo)
            for p in historico:
                if p.get("close") is None:
                    continue
                dia = datetime.fromtimestamp(p["date"], _BRT).date()
                precos.append((codigo, pd.Timestamp(dia), float(p["close"])))
            dividendos = r.get("dividendsData") or {}
            for e in dividendos.get("stockDividends") or []:
                eventos.append(
                    (
                        codigo,
                        e.get("label"),
                        _dia(e.get("lastDatePrior")),
                        e.get("factor"),
                        e.get("isinCode"),
                    )
                )
            for c in dividendos.get("cashDividends") or []:
                proventos.append(
                    (
                        codigo,
                        c.get("label"),
                        _dia(c.get("lastDatePrior")),
                        c.get("rate"),
                        c.get("isinCode"),
                    )
                )
    return (
        pd.DataFrame(precos, columns=["codigo", "data", "close"]),
        pd.DataFrame(eventos, columns=["codigo", "rotulo", "data_com", "fator", "isin"]),
        pd.DataFrame(proventos, columns=["codigo", "rotulo", "data_com", "valor", "isin"]),
        sem_resultado,
    )


def _por_emissor(tabela: pd.DataFrame, ativos: pd.DataFrame) -> pd.DataFrame:
    chaves = ativos[["codigo", "emissor", "classe", "tipo"]]
    return tabela.merge(chaves, on="codigo", how="inner")


def comparar_eventos(
    brapi: pd.DataFrame, ativos: pd.DataFrame, nossos: pd.DataFrame, inferidos: pd.DataFrame
) -> pd.DataFrame:
    """`ativos`: só os tickers que a brapi respondeu. Uma linha por evento, de qualquer lado."""
    b = _por_emissor(brapi[brapi["rotulo"].isin(EVENTOS)], ativos)
    b = b[b["data_com"].notna() & (b["data_com"] >= INICIO)]
    b = b.drop_duplicates(["emissor", "classe", "data_com", "fator"])
    colunas = ["emissor", "classe", "data_com", "multiplicador", "status", "origem"]
    partes = [
        nossos.assign(origem="evento")[colunas],
        inferidos.assign(status="confirmado", origem="inferido")[colunas],
    ]
    cheias = [p for p in partes if not p.empty]
    lado_nosso = (
        pd.concat(cheias, ignore_index=True)
        if cheias
        else pd.DataFrame(columns=colunas).astype({"data_com": "datetime64[ns]"})
    )
    lado_nosso = lado_nosso[lado_nosso["data_com"] >= INICIO]
    emissores = set(zip(ativos["emissor"], ativos["classe"], strict=True))
    lado_nosso = lado_nosso[
        [
            (e, c) in emissores
            for e, c in zip(lado_nosso["emissor"], lado_nosso["classe"], strict=True)
        ]
    ]

    linhas, usados = [], set()
    for _, ev in b.iterrows():
        candidatos = lado_nosso[
            (lado_nosso["emissor"] == ev["emissor"])
            & (lado_nosso["classe"] == ev["classe"])
            & ((lado_nosso["data_com"] - ev["data_com"]).abs().dt.days <= DIAS_DE_FOLGA_DO_EVENTO)
        ]
        base = {
            "codigo": ev["codigo"], "tipo": ev["tipo"], "emissor": ev["emissor"], "classe": ev["classe"],
            "data_com": ev["data_com"], "rotulo": ev["rotulo"], "fator_brapi": ev["fator"],
        }  # fmt: skip
        if candidatos.empty:
            linhas.append({**base, "categoria": "so_brapi"})
            continue
        perto = candidatos.assign(
            erro=(candidatos["multiplicador"] / float(ev["fator"]) - 1).abs()
        ).sort_values("erro")
        melhor = perto.iloc[0]
        usados.add(melhor.name)
        if melhor["erro"] > FOLGA_DO_FATOR:
            categoria = "fator_difere"
        elif melhor["status"] != "confirmado":
            categoria = "nossa_recusou"
        else:
            categoria = "bate"
        linhas.append(
            {**base, "categoria": categoria, "multiplicador_nosso": melhor["multiplicador"],
             "status_nosso": melhor["status"], "origem_nossa": melhor["origem"]}
        )  # fmt: skip
    for indice, ev in lado_nosso.iterrows():
        if indice in usados or ev["status"] != "confirmado":
            continue
        linhas.append(
            {"emissor": ev["emissor"], "classe": ev["classe"], "data_com": ev["data_com"],
             "multiplicador_nosso": ev["multiplicador"], "origem_nossa": ev["origem"],
             "status_nosso": ev["status"], "categoria": "so_nossa"}
        )  # fmt: skip
    return pd.DataFrame(linhas)


def confirmar_pelo_preco(so_brapi: pd.DataFrame, vizinhos: pd.DataFrame) -> pd.DataFrame:
    """`vizinhos`: emissor, classe, data_com, antes (fechamento da véspera), depois (pregão seguinte)."""
    juntos = so_brapi.merge(vizinhos, on=["emissor", "classe", "data_com"], how="left")
    razao = juntos["antes"] / juntos["depois"]
    juntos["razao_observada"] = razao
    juntos["confirmado_pelo_preco"] = (
        razao / juntos["fator_brapi"].astype(float) - 1
    ).abs() <= FOLGA_DA_CONFIRMACAO
    return juntos


def comparar_precos(brapi: pd.DataFrame, nossos: pd.DataFrame) -> pd.DataFrame:
    """`nossos`: codigo, data, valor. Uma linha por ticker, com o veredito do protocolo."""
    janela = brapi.groupby("codigo")["data"].agg(["min", "max"])
    nossos = nossos.merge(janela, left_on="codigo", right_index=True)
    nossos = nossos[nossos["data"].between(nossos["min"], nossos["max"])].drop(
        columns=["min", "max"]
    )
    juntos = brapi.merge(nossos, on=["codigo", "data"], how="outer", indicator=True)
    linhas = []
    for codigo, grupo in juntos.groupby("codigo"):
        ambos = grupo[grupo["_merge"] == "both"]
        desvio = (ambos["close"] / ambos["valor"] - 1).abs()
        batem = float((desvio <= FOLGA_DO_DIA).mean()) if len(ambos) else float("nan")
        maior = float(desvio.max()) if len(ambos) else float("nan")
        linhas.append(
            {
                "codigo": codigo,
                "dias": len(ambos),
                "so_brapi": int((grupo["_merge"] == "left_only").sum()),
                "so_nossa": int((grupo["_merge"] == "right_only").sum()),
                "fracao_que_bate": batem,
                "maior_desvio": maior,
                "diverge": bool(len(ambos)) and (batem < DIAS_QUE_BATEM or maior > DESVIO_MAXIMO),
            }
        )
    return pd.DataFrame(linhas)


def comparar_proventos(
    brapi: pd.DataFrame, ativos: pd.DataFrame, nossos: pd.DataFrame
) -> pd.DataFrame:
    """Soma por data-com dos dois lados; `nossos` já sem `cvm_estimado`."""
    b = _por_emissor(brapi, ativos)
    b = b[b["tipo"].isin(["stock", "fii"]) & b["data_com"].notna() & (b["data_com"] >= INICIO)]
    b = b.drop_duplicates(["emissor", "classe", "data_com", "rotulo", "valor"])
    soma_b = b.groupby(["emissor", "classe", "data_com"], as_index=False)["valor"].sum()
    com_provento = ativos[ativos["tipo"].isin(["stock", "fii"])]
    alvo = set(zip(com_provento["emissor"], com_provento["classe"], strict=True))
    n = nossos[(nossos["data_com"] >= INICIO)]
    n = n[[(e, c) in alvo for e, c in zip(n["emissor"], n["classe"], strict=True)]]
    soma_n = n.groupby(["emissor", "classe", "data_com"], as_index=False)["valor"].sum()
    juntos = soma_b.merge(
        soma_n, on=["emissor", "classe", "data_com"], how="outer", suffixes=("_brapi", "_nosso")
    )
    diferenca = (juntos["valor_brapi"] - juntos["valor_nosso"]).abs()
    relativa = diferenca / juntos["valor_nosso"].abs()
    juntos["categoria"] = "valor_difere"
    juntos.loc[
        (relativa <= FOLGA_DO_PROVENTO) | (diferenca <= FOLGA_ABSOLUTA_DO_PROVENTO), "categoria"
    ] = "bate"
    juntos.loc[juntos["valor_nosso"].isna(), "categoria"] = "so_brapi"
    juntos.loc[juntos["valor_brapi"].isna(), "categoria"] = "so_nossa"
    return juntos


def erro_da_estimativa(brapi: pd.DataFrame, ativos: pd.DataFrame, estimados: pd.DataFrame) -> dict:
    """Rendimento de FII estimado pela CVM contra o da brapi, por mês de data-com. Só descreve."""
    b = _por_emissor(brapi, ativos)
    b = b[(b["tipo"] == "fii") & b["data_com"].notna()].drop_duplicates(
        ["emissor", "classe", "data_com", "valor"]
    )
    b = (
        b.assign(mes=b["data_com"].dt.to_period("M"))
        .groupby(["emissor", "classe", "mes"], as_index=False)["valor"]
        .sum()
    )
    e = estimados.assign(mes=estimados["data_com"].dt.to_period("M"))
    e = e.groupby(["emissor", "classe", "mes"], as_index=False)["valor"].sum()
    juntos = e.merge(b, on=["emissor", "classe", "mes"], suffixes=("_estimado", "_brapi"))
    juntos = juntos[juntos["valor_brapi"] > 0]
    erro = (juntos["valor_estimado"] / juntos["valor_brapi"] - 1).abs()
    if erro.empty:
        return {"meses": 0}
    return {
        "meses": int(len(erro)),
        "fiis": int(juntos[["emissor", "classe"]].drop_duplicates().shape[0]),
        "mediana": round(float(erro.median()), 4),
        "p90": round(float(erro.quantile(0.9)), 4),
        "ate_10_por_cento": round(float((erro <= 0.10).mean()), 4),
    }


def resumo(eventos: pd.DataFrame, precos: pd.DataFrame, proventos: pd.DataFrame, fii: dict) -> dict:
    so_brapi = eventos[eventos["categoria"] == "so_brapi"]
    confirmados = so_brapi.get("confirmado_pelo_preco", pd.Series(dtype=bool))
    return {
        "data": date.today().isoformat(),
        "eventos": {k: int(v) for k, v in eventos["categoria"].value_counts().items()},
        "eventos_so_brapi_confirmados_pelo_preco": int(confirmados.fillna(False).sum()),
        "precos": {
            "tickers": int(len(precos)),
            "divergem": int(precos["diverge"].sum()),
            "sem_dia_comparado": int((precos["dias"] == 0).sum()),
            "dias_so_brapi": int(precos["so_brapi"].sum()),
            "dias_so_nossa": int(precos["so_nossa"].sum()),
        },
        "proventos": {k: int(v) for k, v in proventos["categoria"].value_counts().items()},
        "estimativa_fii": fii,
    }


def _ler_base(pasta: Path) -> dict[str, pd.DataFrame]:
    datas = {
        "eventos": ["data_com"],
        "inferidos": ["data_com"],
        "proventos": ["data_com"],
        "precos": ["data"],
    }
    return {
        nome: pd.read_csv(pasta / f"{nome}.csv", parse_dates=datas.get(nome, []))
        for nome in ("ativos", "eventos", "inferidos", "proventos", "precos")
    }


def _sql_dos_vizinhos(so_brapi: pd.DataFrame) -> str:
    valores = ",\n".join(
        f"('{e}', '{c}', DATE '{d:%Y-%m-%d}')"
        for e, c, d in so_brapi[["emissor", "classe", "data_com"]]
        .drop_duplicates()
        .itertuples(index=False)
    )
    return f"""COPY (WITH alvo(emissor, classe, data_com) AS (VALUES
{valores}
), serie AS (
    SELECT m.codigo AS emissor, s.classe, s.data, s.fechamento FROM mercado.serie_papel s
    JOIN mercado.emissor m ON m.cnpj = s.cnpj
    UNION ALL SELECT emissor, classe, data, fechamento FROM mercado.serie_fundo
)
SELECT a.emissor, a.classe, a.data_com,
    (SELECT s.fechamento FROM serie s WHERE s.emissor = a.emissor AND s.classe = a.classe
        AND s.data <= a.data_com ORDER BY s.data DESC LIMIT 1) AS antes,
    (SELECT s.fechamento FROM serie s WHERE s.emissor = a.emissor AND s.classe = a.classe
        AND s.data > a.data_com ORDER BY s.data LIMIT 1) AS depois
FROM alvo a) TO STDOUT WITH CSV HEADER;
"""


def principal(argv: list[str] | None = None) -> int:
    import argparse

    raiz = Path(__file__).resolve().parents[1] / ".brapi"
    analise = argparse.ArgumentParser(prog="python -m pesquisa.validacao_brapi")
    analise.add_argument("acao", choices=["coletar", "comparar"])
    analise.add_argument(
        "--env", type=Path, default=Path(__file__).resolve().parents[3] / "backend" / ".env"
    )
    args = analise.parse_args(argv)
    base = _ler_base(raiz / "base")

    if args.acao == "coletar":
        tickers = sorted(base["ativos"]["codigo"].unique())
        coleta = coletar(tickers, ler_token(args.env), raiz / "respostas")
        print(
            f"{len(tickers)} tickers; {coleta.requisicoes} requisições; {coleta.lotes_em_cache} lotes em cache"
        )
        for falha in coleta.falhas:
            print("falha:", falha)
        return 1 if coleta.falhas else 0

    precos_b, eventos_b, proventos_b, sem_resultado = ler_respostas(raiz / "respostas")
    respondidos = base["ativos"][
        base["ativos"]["codigo"].isin(
            set(precos_b["codigo"]) | set(eventos_b["codigo"]) | set(proventos_b["codigo"])
        )
    ]
    eventos = comparar_eventos(eventos_b, respondidos, base["eventos"], base["inferidos"])
    vizinhos = raiz / "base" / "vizinhos.csv"
    so_brapi = eventos[eventos["categoria"] == "so_brapi"]
    if not vizinhos.exists():
        (raiz / "vizinhos.sql").write_text(_sql_dos_vizinhos(so_brapi), encoding="utf-8")
        print(
            f"{len(so_brapi)} eventos só na brapi: rode {raiz / 'vizinhos.sql'} e salve em {vizinhos}"
        )
        return 2
    confirmados = confirmar_pelo_preco(so_brapi, pd.read_csv(vizinhos, parse_dates=["data_com"]))
    eventos = pd.concat(
        [eventos[eventos["categoria"] != "so_brapi"], confirmados], ignore_index=True
    )
    precos = comparar_precos(
        precos_b, base["precos"][base["precos"]["codigo"].isin(respondidos["codigo"])]
    )
    nossos = base["proventos"]
    proventos = comparar_proventos(
        proventos_b, respondidos, nossos[nossos["origem"] != "cvm_estimado"]
    )
    fii = erro_da_estimativa(proventos_b, respondidos, nossos[nossos["origem"] == "cvm_estimado"])
    saida = raiz / "resultado"
    saida.mkdir(exist_ok=True)
    eventos.to_csv(saida / "eventos.csv", index=False)
    precos.to_csv(saida / "precos.csv", index=False)
    proventos.to_csv(saida / "proventos.csv", index=False)
    final = {**resumo(eventos, precos, proventos, fii), "tickers_sem_resposta": len(sem_resultado)}
    with REGISTRO.open("a", encoding="utf-8", newline="\n") as arquivo:
        arquivo.write(json.dumps(final, ensure_ascii=False) + "\n")
    print(json.dumps(final, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(principal())
