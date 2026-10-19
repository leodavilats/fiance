import { useParams } from "react-router-dom";
import { useApi } from "../api";
import { formatarData, formatarNumero } from "../formato";
import { NOME_DO_TIPO } from "./Caminho";
import Estado from "./Estado";
import GraficoDaSerie from "./GraficoDaSerie";
import type { Ponto } from "../serie";

type DetalheDoFundo = {
  emissor: string;
  classe: string;
  tipo: string;
  nome: string | null;
  serie: (Ponto & { codigo: string })[];
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
        {saltos ? ` · ${saltos} dia(s) com salto sem evento, fora do retorno acumulado e marcados no preço` : ""}
      </p>

      <h2>Retorno total e preço</h2>
      <GraficoDaSerie serie={d.serie} />

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
