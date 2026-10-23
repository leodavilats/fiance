import { useEffect, useMemo, useRef, useState } from "react";
import { Link } from "react-router-dom";
import { Bar, CartesianGrid, ComposedChart, Line, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { useApi } from "../api";
import { formatarData, formatarNumero, formatarPorcento } from "../formato";
import Estado from "./Estado";

type Resumo = {
  meses: number;
  ativos_medio?: number;
  ic?: number;
  t?: number;
  acerto_topo?: number;
  diferenca_liquida_ano?: number;
  giro_medio?: number;
  passou: boolean;
};

type Execucao = {
  quando: string;
  sinal: string;
  classe: string;
  assinatura: string;
  periodo: string;
  parametros: Record<string, unknown>;
  resumo: Resumo;
};

type Mes = { mes: string; ativos: number; ic: number; topo: number; fundo: number; liquida: number; topo_nomes: string[] };

export default function TelaRanking() {
  const estado = useApi<{ execucoes: Execucao[] }>("/api/ranking");
  const [escolhida, setEscolhida] = useState<Execucao | null>(null);
  const detalhe = useRef<HTMLElement>(null);
  useEffect(() => {
    detalhe.current?.scrollIntoView({ behavior: "smooth", block: "start" });
  }, [escolhida]);
  return (
    <>
      <h1>Ranking de tendência</h1>
      <p className="nota">
        A pergunta: ordenar pela força da tendência diz quem rende mais no mês seguinte? Passa quem tiver
        correlação de postos ≥ 0,03 com t ≥ 2, topo vencendo o fundo em ≥ 55% dos meses e diferença positiva
        depois da troca. Teto de 6 variações. <Link to="/documentos/pesquisa/estudos/ranking.md">Ler o protocolo</Link>.
      </p>
      <Estado estado={estado}>
        {(dados) => (
          <>
            <Tabela execucoes={dados.execucoes} escolhida={escolhida} escolher={setEscolhida} />
            <section ref={detalhe}>{escolhida && <Meses execucao={escolhida} />}</section>
          </>
        )}
      </Estado>
    </>
  );
}

function Tabela({
  execucoes,
  escolhida,
  escolher,
}: {
  execucoes: Execucao[];
  escolhida: Execucao | null;
  escolher: (e: Execucao) => void;
}) {
  const unicas = useMemo(() => {
    const vistas = new Map<string, Execucao>();
    for (const e of execucoes) vistas.set(`${e.assinatura}:${e.periodo}`, e);
    return [...vistas.values()];
  }, [execucoes]);

  if (unicas.length === 0) return <p className="nota">Nenhuma execução registrada.</p>;
  return (
    <div className="rolar">
      <table>
        <thead>
          <tr>
            <th className="esq">Sinal</th>
            <th className="esq">Classe</th>
            <th className="esq">Período</th>
            <th>Meses</th>
            <th>Correlação</th>
            <th>t</th>
            <th>Topo vence</th>
            <th>Diferença líquida/ano</th>
            <th className="esq">Resultado</th>
            <th>Quando</th>
          </tr>
        </thead>
        <tbody>
          {unicas.map((e) => (
            <tr key={`${e.assinatura}:${e.periodo}`} className={`clicavel ${escolhida?.assinatura === e.assinatura && escolhida?.periodo === e.periodo ? "escolhida" : ""}`}
              onClick={() => escolher(e)}
            >
              <td className="esq">{e.sinal}</td>
              <td className="esq">{e.classe}</td>
              <td className="esq">{e.periodo}</td>
              <td>{e.resumo.meses}</td>
              <td>{formatarNumero(e.resumo.ic)}</td>
              <td>{formatarNumero(e.resumo.t)}</td>
              <td>{formatarPorcento(e.resumo.acerto_topo)}</td>
              <td>{formatarPorcento(e.resumo.diferenca_liquida_ano)}</td>
              <td className={`esq ${e.resumo.passou ? "ganha" : "perde"}`}>{e.resumo.passou ? "passou" : "não passou"}</td>
              <td>{formatarData(e.quando)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function Meses({ execucao }: { execucao: Execucao }) {
  const estado = useApi<{ meses: Mes[] }>(
    `/api/ranking/${execucao.classe}/${execucao.sinal}/${execucao.assinatura}/${execucao.periodo}`,
  );
  return (
    <>
      <h2>
        {execucao.sinal} · {execucao.classe} · {execucao.periodo}
      </h2>
      <p className="nota">{JSON.stringify(execucao.parametros)}</p>
      <Estado estado={estado}>
        {(dados) => {
          let acumulado = 1;
          const pontos = dados.meses.map((m) => {
            acumulado *= 1 + m.liquida;
            return { mes: m.mes, ic: m.ic, acumulado };
          });
          const ultimo = dados.meses[dados.meses.length - 1];
          return (
            <>
              <p className="nota">
                Barras: correlação de postos de cada mês. Linha: topo menos fundo, líquido da troca, acumulado.
              </p>
              <div className="grafico">
                <ResponsiveContainer>
                  <ComposedChart data={pontos}>
                    <CartesianGrid stroke="var(--fio)" vertical={false} />
                    <XAxis dataKey="mes" tickFormatter={(v: string) => v.slice(0, 4)} minTickGap={40} stroke="var(--suave)" />
                    <YAxis yAxisId="ic" stroke="var(--suave)" tickFormatter={(v: number) => formatarNumero(v)} />
                    <YAxis yAxisId="acumulado" orientation="right" stroke="var(--suave)" tickFormatter={(v: number) => formatarNumero(v)} />
                    <Tooltip formatter={(v: number) => formatarNumero(v)} labelFormatter={(v: string) => formatarData(v)} />
                    <Bar yAxisId="ic" dataKey="ic" name="correlação" fill="var(--referencia)" isAnimationActive={false} />
                    <Line yAxisId="acumulado" dataKey="acumulado" name="topo − fundo, acumulado" dot={false} stroke="var(--destaque)" strokeWidth={2} isAnimationActive={false} />
                  </ComposedChart>
                </ResponsiveContainer>
              </div>
              {ultimo && (
                <p className="nota">
                  Topo em {formatarData(ultimo.mes)}, entre {ultimo.ativos}: {ultimo.topo_nomes.join(", ")}
                </p>
              )}
            </>
          );
        }}
      </Estado>
    </>
  );
}
