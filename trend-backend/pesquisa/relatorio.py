from __future__ import annotations

import html
import json
from pathlib import Path

import pandas as pd

from pesquisa import registro
from pesquisa.motor import Resultado

PASTA = Path(__file__).resolve().parents[1] / "resultados"


def _arquivo(hipotese: str, assinatura: str, periodo: str, pasta: Path) -> Path:
    return pasta / f"{hipotese}_{assinatura}_{periodo}.json"


def guardar(
    resultado: Resultado,
    hipotese: str,
    assinatura: str,
    periodo: str,
    nomes: pd.Series,
    pasta: Path = PASTA,
) -> Path:
    pasta.mkdir(parents=True, exist_ok=True)
    mensal = pd.DataFrame({"carteira": resultado.patrimonio, "cdi": resultado.cdi})
    mensal = mensal.resample("ME").last().dropna()
    carteiras = {
        str(dia.date()): [str(nomes.get(p, p)) for p in papeis]
        for dia, papeis in sorted(resultado.carteiras.items())
    }
    destino = _arquivo(hipotese, assinatura, periodo, pasta)
    destino.write_text(
        json.dumps(
            {
                "datas": [str(d.date()) for d in mensal.index],
                "carteira": [round(v, 2) for v in mensal["carteira"]],
                "cdi": [round(v, 2) for v in mensal["cdi"]],
                "carteiras": carteiras,
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    return destino


def _pct(valor) -> str:
    return "—" if valor is None else f"{valor * 100:.1f}%".replace(".", ",")


def _grafico(datas: list[str], carteira: list[float], cdi: list[float]) -> str:
    largura, altura, margem = 640, 220, 36
    todos = carteira + cdi
    menor, maior = min(todos), max(todos)
    faixa = (maior - menor) or 1

    def pontos(valores: list[float]) -> str:
        passo = (largura - 2 * margem) / max(len(valores) - 1, 1)
        return " ".join(
            f"{margem + i * passo:.1f},{altura - margem - (v - menor) / faixa * (altura - 2 * margem):.1f}"
            for i, v in enumerate(valores)
        )

    rotulo = lambda v: f"R$ {v / 1000:,.0f} mil".replace(",", ".")  # noqa: E731
    return f"""
<svg viewBox="0 0 {largura} {altura}" role="img" aria-label="Carteira contra o CDI">
  <line x1="{margem}" y1="{altura - margem}" x2="{largura - margem}" y2="{altura - margem}" class="eixo"/>
  <text x="{margem}" y="{margem - 10}" class="rotulo">{rotulo(maior)}</text>
  <text x="{margem}" y="{altura - 8}" class="rotulo">{datas[0][:7]}</text>
  <text x="{largura - margem}" y="{altura - 8}" class="rotulo" text-anchor="end">{datas[-1][:7]}</text>
  <polyline points="{pontos(cdi)}" class="linha cdi"/>
  <polyline points="{pontos(carteira)}" class="linha carteira"/>
</svg>"""


_ESTILO = """
:root { --fundo:#fbfaf7; --texto:#1d1d1b; --suave:#6b6a65; --fio:#e3e1da; --carteira:#1f5fa8; --cdi:#9a8f78;
        --perde:#a33a2a; --ganha:#2f6f3e; }
@media (prefers-color-scheme: dark) { :root:not([data-theme="light"]) {
  --fundo:#161615; --texto:#ecebe6; --suave:#a3a199; --fio:#2c2b28; --carteira:#7fb0ea; --cdi:#b9ae95;
  --perde:#e58a7a; --ganha:#86c795; } }
body { background:var(--fundo); color:var(--texto); font:15px/1.5 system-ui, sans-serif; margin:0; }
main { max-width:880px; margin:0 auto; padding:24px 16px 64px; }
h1 { font:600 26px/1.2 Georgia, serif; margin:0 0 4px; } h2 { font:600 19px Georgia, serif; margin:36px 0 8px; }
p.nota { color:var(--suave); margin:4px 0 16px; }
table { border-collapse:collapse; width:100%; font-variant-numeric:tabular-nums; font-size:13px; }
th, td { border-bottom:1px solid var(--fio); padding:6px 8px; text-align:right; white-space:nowrap; }
th:first-child, td:first-child, th:nth-child(2), td:nth-child(2) { text-align:left; }
.rolar { overflow-x:auto; } .perde { color:var(--perde); } .ganha { color:var(--ganha); }
svg { width:100%; height:auto; } .eixo { stroke:var(--fio); } .rotulo { fill:var(--suave); font-size:11px; }
.linha { fill:none; stroke-width:2; } .carteira { stroke:var(--carteira); } .cdi { stroke:var(--cdi); stroke-dasharray:4 3; }
.legenda span { display:inline-block; margin-right:16px; color:var(--suave); font-size:13px; }
.legenda i { display:inline-block; width:18px; height:3px; vertical-align:middle; margin-right:6px; }
ul.papeis { columns:4 120px; color:var(--suave); font-size:13px; padding-left:18px; }
"""


def gerar(arquivo_registro: Path = registro.ARQUIVO, pasta: Path = PASTA) -> str:
    execucoes = registro.ler(arquivo_registro)
    linhas = []
    for r in reversed(execucoes):
        resumo = r["resumo"]
        excesso = resumo.get("excesso_anual")
        classe = "ganha" if excesso and excesso > 0 else "perde"
        linhas.append(
            f"<tr><td>{html.escape(r['hipotese'])}</td><td>{r['periodo']}</td>"
            f"<td>{_pct(resumo.get('retorno_anual'))}</td><td>{_pct(resumo.get('cdi_anual'))}</td>"
            f"<td class='{classe}'>{_pct(excesso)}</td><td>{_pct(resumo.get('volatilidade_anual'))}</td>"
            f"<td>{_pct(resumo.get('pior_queda'))}</td><td>{_pct(resumo.get('meses_acima_do_cdi'))}</td>"
            f"<td>{_pct(resumo.get('giro_mensal_medio'))}</td><td>{r['quando'][:10]}</td></tr>"
        )

    secoes, vistos = [], set()
    for r in reversed(execucoes):
        chave = (r["hipotese"], r["assinatura"], r["periodo"])
        caminho = _arquivo(*chave, pasta)
        if chave in vistos or not caminho.exists():
            continue
        vistos.add(chave)
        curva = json.loads(caminho.read_text(encoding="utf-8"))
        ultimo_mes, papeis = sorted(curva["carteiras"].items())[-1]
        tentativas = registro.tentativas(r["hipotese"], arquivo_registro)
        secoes.append(
            f"<h2>{html.escape(r['hipotese'])} · {r['periodo']}</h2>"
            f"<p class='nota'>{html.escape(json.dumps(r['parametros'], ensure_ascii=False))} · "
            f"{tentativas} variação(ões) desta hipótese no registro · retrato {r['retrato']}</p>"
            "<p class='legenda'><span><i style='background:var(--carteira)'></i>carteira</span>"
            "<span><i style='background:var(--cdi)'></i>CDI</span></p>"
            + _grafico(curva["datas"], curva["carteira"], curva["cdi"])
            + f"<p class='nota'>Carteira escolhida em {ultimo_mes} ({len(papeis)} papéis):</p>"
            + "<ul class='papeis'>"
            + "".join(f"<li>{html.escape(p)}</li>" for p in papeis)
            + "</ul>"
        )

    return f"""<!doctype html><html lang="pt-BR"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1"><title>Pesquisa de carteira</title>
<style>{_ESTILO}</style></head><body><main>
<h1>Pesquisa de carteira</h1>
<p class="nota">Cada linha é uma execução do registro, mais recente primeiro. Retornos ao ano, depois de custo de
0,25% por lado e imposto de 15% sobre ganho realizado. Estudo 2005–2018, validação 2019–2022, prova
lacrada de 2023 em diante.</p>
<div class="rolar"><table><thead><tr><th>Hipótese</th><th>Período</th><th>Retorno</th><th>CDI</th>
<th>Diferença</th><th>Volatilidade</th><th>Pior queda</th><th>Meses &gt; CDI</th><th>Giro/mês</th>
<th>Quando</th></tr></thead><tbody>{"".join(linhas)}</tbody></table></div>
{"".join(secoes)}
</main></body></html>"""
