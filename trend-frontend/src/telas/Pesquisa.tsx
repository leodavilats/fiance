import { useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { CartesianGrid, Legend, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { useApi } from "../api";
import { formatarData, formatarNumero, formatarPorcento } from "../formato";
import Estado from "./Estado";

type Execucao = {
  quando: string;
  hipotese: string;
  assinatura: string;
  periodo: string;
  parametros: Record<string, unknown>;
  resumo: {
    retorno_anual?: number;
    cdi_anual?: number;
    excesso_anual?: number;
    pior_queda?: number;
    giro_mensal_medio?: number;
  };
};

type Curva = { datas: string[]; carteira: number[]; cdi: number[]; carteiras: Record<string, string[]> };

const REGUA = 0.02;

export default function TelaPesquisa() {
  const estado = useApi<{ execucoes: Execucao[] }>("/api/pesquisa");
  const [escolhida, setEscolhida] = useState<Execucao | null>(null);
  return (
    <>
      <h1>Pesquisa</h1>
      <p className="nota">
        Busca encerrada em 12/10/2026, no teto de 8 variações: não achei vantagem investível. Régua: 2
        pontos ao ano acima do CDI, depois de custo e imposto. <Link to="/planos/planos/pesquisa.md">Ler o protocolo</Link>.
      </p>
      <Estado estado={estado}>
        {(dados) => (
          <>
            <Tabela execucoes={dados.execucoes} escolher={setEscolhida} />
            {escolhida && <Grafico execucao={escolhida} />}
          </>
        )}
      </Estado>
    </>
  );
}

function Tabela({ execucoes, escolher }: { execucoes: Execucao[]; escolher: (e: Execucao) => void }) {
  const unicas = useMemo(() => {
    const vistas = new Map<string, Execucao>();
    for (const e of execucoes) vistas.set(`${e.assinatura}:${e.periodo}`, e);
    return [...vistas.values()];
  }, [execucoes]);

  return (
    <div className="rolar">
      <table>
        <thead>
          <tr>
            <th className="esq">Hipótese</th>
            <th className="esq">Período</th>
            <th>Retorno</th>
            <th>CDI</th>
            <th>Diferença</th>
            <th>Pior queda</th>
            <th>Giro/mês</th>
            <th>Quando</th>
          </tr>
        </thead>
        <tbody>
          {unicas.map((e) => {
            const excesso = e.resumo.excesso_anual ?? 0;
            return (
              <tr key={`${e.assinatura}:${e.periodo}`} className="clicavel" onClick={() => escolher(e)}>
                <td className="esq">{e.hipotese}</td>
                <td className="esq">{e.periodo}</td>
                <td>{formatarPorcento(e.resumo.retorno_anual)}</td>
                <td>{formatarPorcento(e.resumo.cdi_anual)}</td>
                <td className={excesso >= REGUA ? "ganha" : "perde"}>{formatarPorcento(e.resumo.excesso_anual)}</td>
                <td>{formatarPorcento(e.resumo.pior_queda)}</td>
                <td>{formatarPorcento(e.resumo.giro_mensal_medio)}</td>
                <td>{formatarData(e.quando)}</td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}

function Grafico({ execucao }: { execucao: Execucao }) {
  const estado = useApi<Curva>(
    `/api/pesquisa/curva/${execucao.hipotese}/${execucao.assinatura}/${execucao.periodo}`,
  );
  return (
    <>
      <h2>
        {execucao.hipotese} · {execucao.periodo}
      </h2>
      <p className="nota">{JSON.stringify(execucao.parametros)}</p>
      <Estado estado={estado}>
        {(curva) => {
          const pontos = curva.datas.map((data, i) => ({ data, carteira: curva.carteira[i], cdi: curva.cdi[i] }));
          const [ultimoMes, papeis] = Object.entries(curva.carteiras).sort().at(-1) ?? ["", []];
          return (
            <>
              <div className="grafico">
                <ResponsiveContainer>
                  <LineChart data={pontos}>
                    <CartesianGrid stroke="var(--fio)" vertical={false} />
                    <XAxis dataKey="data" tickFormatter={(v: string) => v.slice(0, 4)} minTickGap={40} stroke="var(--suave)" />
                    <YAxis scale="log" domain={["auto", "auto"]} stroke="var(--suave)" tickFormatter={(v: number) => formatarNumero(v / 1000) + " mil"} />
                    <Tooltip formatter={(v: number) => `R$ ${formatarNumero(v)}`} labelFormatter={(v: string) => formatarData(v)} />
                    <Legend />
                    <Line dataKey="carteira" dot={false} stroke="var(--destaque)" strokeWidth={2} isAnimationActive={false} />
                    <Line dataKey="cdi" name="CDI" dot={false} stroke="var(--referencia)" strokeDasharray="4 3" isAnimationActive={false} />
                  </LineChart>
                </ResponsiveContainer>
              </div>
              <p className="nota">
                Carteira em {formatarData(ultimoMes)}: {papeis.length ? papeis.join(", ") : "toda em CDI"}
              </p>
            </>
          );
        }}
      </Estado>
    </>
  );
}
