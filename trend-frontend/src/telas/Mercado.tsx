import { CartesianGrid, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { useApi } from "../api";
import { formatarData, formatarNumero } from "../formato";
import Estado from "./Estado";

type Titulo = {
  titulo: string;
  vencimento: string;
  data: string;
  taxa_compra: number | null;
  taxa_venda: number | null;
  pu_compra: number | null;
  pu_venda: number | null;
  pu_base: number | null;
};

type Macro = {
  ptax: { data: string; valor: number }[];
  selic_meta: { data: string; valor: number }[];
  tesouro: Titulo[];
};

export default function TelaMercado() {
  const estado = useApi<Macro>("/api/macro");
  return (
    <>
      <h1>Dólar e Tesouro</h1>
      <Estado estado={estado}>{(m) => <Conteudo m={m} />}</Estado>
    </>
  );
}

function Conteudo({ m }: { m: Macro }) {
  const ptax = m.ptax.map((p) => ({ data: p.data, valor: Number(p.valor) }));
  const ultima = ptax[ptax.length - 1];
  const selic = m.selic_meta[0];
  const data = m.tesouro[0]?.data;
  return (
    <>
      <p className="nota">
        PTAX de venda em {formatarData(ultima?.data)}: R$ {formatarNumero(ultima?.valor)}
        {selic ? ` · meta da Selic em ${formatarData(selic.data)}: ${formatarNumero(selic.valor)}% ao ano` : ""}
      </p>

      <h2>Dólar PTAX, último dia de cada mês</h2>
      <div className="grafico">
        <ResponsiveContainer>
          <LineChart data={ptax}>
            <CartesianGrid stroke="var(--fio)" vertical={false} />
            <XAxis dataKey="data" tickFormatter={(v: string) => v.slice(0, 4)} minTickGap={40} stroke="var(--suave)" />
            <YAxis domain={["auto", "auto"]} stroke="var(--suave)" tickFormatter={(v: number) => formatarNumero(v)} />
            <Tooltip formatter={(v: number) => `R$ ${formatarNumero(v)}`} labelFormatter={(v: string) => formatarData(v)} />
            <Line dataKey="valor" name="PTAX" dot={false} stroke="var(--destaque)" strokeWidth={2} isAnimationActive={false} />
          </LineChart>
        </ResponsiveContainer>
      </div>

      <h2>Tesouro Direto em {formatarData(data)}</h2>
      <p className="nota">Taxa em % ao ano. Título fora de venda fica sem taxa e preço de compra.</p>
      <div className="rolar">
        <table>
          <thead>
            <tr>
              <th className="esq">Título</th>
              <th>Vencimento</th>
              <th>Taxa de compra</th>
              <th>Taxa de venda</th>
              <th>Preço de compra</th>
              <th>Preço de venda</th>
            </tr>
          </thead>
          <tbody>
            {m.tesouro.map((t) => (
              <tr key={`${t.titulo}:${t.vencimento}`}>
                <td className="esq">{t.titulo}</td>
                <td>{formatarData(t.vencimento)}</td>
                <td>{t.taxa_compra === null ? "—" : `${formatarNumero(t.taxa_compra)}%`}</td>
                <td>{t.taxa_venda === null ? "—" : `${formatarNumero(t.taxa_venda)}%`}</td>
                <td>{t.pu_compra === null ? "—" : `R$ ${formatarNumero(t.pu_compra)}`}</td>
                <td>{t.pu_venda === null ? "—" : `R$ ${formatarNumero(t.pu_venda)}`}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </>
  );
}
