import { useMemo } from "react";
import { useParams } from "react-router-dom";
import { CartesianGrid, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { useApi } from "../api";
import { formatarData, formatarNumero } from "../formato";
import { NOME_DO_TIPO } from "./Caminho";
import Estado from "./Estado";

type DetalheDoFundo = {
  emissor: string;
  classe: string;
  tipo: string;
  nome: string | null;
  serie: { data: string; codigo: string; retorno_acumulado: number; salto_sem_evento: boolean | null }[];
  proventos: { data_com: string; tipo: string; valor: number; origem: string }[];
  eventos: { data_com: string; tipo: string; multiplicador: number | null; status: string }[];
};

const ORIGEM: Record<string, string> = {
  b3_historico: "B3",
  b3_recente: "B3",
  cvm_estimado: "estimado (CVM)",
};

export default function TelaFundo() {
  const { emissor, classe } = useParams();
  const estado = useApi<DetalheDoFundo>(`/api/fundos/${emissor}/${classe}`);
  return <Estado estado={estado}>{(d) => <Detalhe d={d} />}</Estado>;
}

function Detalhe({ d }: { d: DetalheDoFundo }) {
  const semanal = useMemo(
    () => d.serie.filter((_, i) => i % 5 === 0 || i === d.serie.length - 1),
    [d.serie],
  );
  const codigo = d.serie[d.serie.length - 1]?.codigo;
  const saltos = d.serie.filter((s) => s.salto_sem_evento).length;
  const estimados = d.proventos.filter((p) => p.origem === "cvm_estimado").length;

  return (
    <>
      <h1>
        {codigo} · {d.nome ?? d.emissor}
      </h1>
      <p className="nota">
        {NOME_DO_TIPO[d.tipo] ?? d.tipo} · emissor {d.emissor} · classe {d.classe}
        {saltos ? ` · ${saltos} dia(s) com salto sem evento, fora do retorno acumulado` : ""}
      </p>

      <h2>Retorno total acumulado (base 100)</h2>
      <div className="grafico">
        <ResponsiveContainer>
          <LineChart data={semanal}>
            <CartesianGrid stroke="var(--fio)" vertical={false} />
            <XAxis dataKey="data" tickFormatter={(v: string) => v.slice(0, 4)} minTickGap={40} stroke="var(--suave)" />
            <YAxis scale="log" domain={["auto", "auto"]} stroke="var(--suave)" tickFormatter={(v: number) => formatarNumero(v)} />
            <Tooltip formatter={(v: number) => formatarNumero(v)} labelFormatter={(v: string) => formatarData(v)} />
            <Line
              dataKey="retorno_acumulado"
              name="retorno acumulado"
              dot={false}
              stroke="var(--destaque)"
              strokeWidth={2}
              isAnimationActive={false}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>

      <h2>Proventos</h2>
      {estimados > 0 && (
        <p className="nota">
          Rendimento estimado é o yield do mês vezes o valor patrimonial da cota, do informe mensal da CVM. No mês
          em que a B3 dá o pago, o retorno usa o pago.
        </p>
      )}
      {d.proventos.length === 0 ? (
        <p className="nota">Nenhum provento na base. Antes de out/2026, ETF e BDR não têm histórico.</p>
      ) : (
        <div className="rolar">
          <table>
            <thead>
              <tr>
                <th className="esq">Data-com</th>
                <th className="esq">Tipo</th>
                <th>Valor por cota</th>
                <th className="esq">Origem</th>
              </tr>
            </thead>
            <tbody>
              {d.proventos.slice(0, 60).map((p, i) => (
                <tr key={`${p.data_com}-${p.origem}-${i}`}>
                  <td className="esq">{formatarData(p.data_com)}</td>
                  <td className="esq">{p.tipo}</td>
                  <td>R$ {formatarNumero(p.valor)}</td>
                  <td className={`esq ${p.origem === "cvm_estimado" ? "nota" : ""}`}>{ORIGEM[p.origem] ?? p.origem}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      <h2>Eventos de cota</h2>
      {d.eventos.length === 0 ? (
        <p className="nota">Nenhum.</p>
      ) : (
        <div className="rolar">
          <table>
            <thead>
              <tr>
                <th className="esq">Data-com</th>
                <th className="esq">Tipo</th>
                <th>Multiplicador</th>
                <th className="esq">Status</th>
              </tr>
            </thead>
            <tbody>
              {d.eventos.map((e, i) => (
                <tr key={`${e.data_com}-${i}`}>
                  <td className="esq">{formatarData(e.data_com)}</td>
                  <td className="esq">{e.tipo}</td>
                  <td>{formatarNumero(e.multiplicador)}</td>
                  <td className={`esq ${e.status === "divergente" ? "perde" : ""}`}>{e.status}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </>
  );
}
