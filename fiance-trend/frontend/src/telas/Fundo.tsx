import { useParams } from "react-router-dom";
import { useApi } from "../api";
import { formatarData, formatarNumero } from "../formato";
import type { Ponto } from "../serie";
import { NOME_DO_TIPO } from "./Caminho";
import { Abas, ResumoDoAtivo, Voltar } from "./Detalhes";
import Estado from "./Estado";
import GraficoDaSerie from "./GraficoDaSerie";

type Provento = { data_com: string; tipo: string; valor: number; origem: string };
type Evento = { data_com: string; tipo: string; multiplicador: number | null; status: string };

type DetalheDoFundo = {
  emissor: string;
  classe: string;
  tipo: string;
  nome: string | null;
  serie: (Ponto & { codigo: string })[];
  proventos: Provento[];
  eventos: Evento[];
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
  return (
    <>
      <Voltar tipo={d.tipo} />
      <h1>
        {codigo} · {d.nome ?? d.emissor}
      </h1>
      <p className="nota">
        {NOME_DO_TIPO[d.tipo] ?? d.tipo} · emissor {d.emissor} · classe {d.classe}
      </p>

      <ResumoDoAtivo
        serie={d.serie}
        proventos={d.proventos.filter((p) => p.origem !== "cvm_estimado")}
        unidade="cota"
      />

      <h2>Retorno total e preço</h2>
      <GraficoDaSerie serie={d.serie} />

      <h2>Detalhes</h2>
      <Abas
        abas={[
          { rotulo: "Proventos", total: d.proventos.length, conteudo: <Proventos p={d.proventos} /> },
          { rotulo: "Eventos de cota", total: d.eventos.length, conteudo: <Eventos e={d.eventos} /> },
        ]}
      />
    </>
  );
}

function Proventos({ p }: { p: Provento[] }) {
  if (p.length === 0) {
    return <p className="nota">Nenhum provento na base. Antes de out/2026, ETF e BDR não têm histórico.</p>;
  }
  const estimados = p.filter((linha) => linha.origem === "cvm_estimado").length;
  return (
    <>
      {estimados > 0 && (
        <p className="nota">
          Rendimento estimado é o yield do mês vezes o valor patrimonial da cota, do informe mensal da CVM. No mês
          em que a B3 dá o pago, o retorno usa o pago.
        </p>
      )}
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
            {p.slice(0, 60).map((linha, i) => (
              <tr key={`${linha.data_com}-${linha.origem}-${i}`}>
                <td className="esq">{formatarData(linha.data_com)}</td>
                <td className="esq">{linha.tipo}</td>
                <td>R$ {formatarNumero(linha.valor)}</td>
                <td className={`esq ${linha.origem === "cvm_estimado" ? "nota" : ""}`}>
                  {ORIGEM[linha.origem] ?? linha.origem}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        {p.length > 60 && <p className="nota">Os 60 mais recentes, de {formatarNumero(p.length)}.</p>}
      </div>
    </>
  );
}

function Eventos({ e }: { e: Evento[] }) {
  if (e.length === 0) return <p className="nota">Nenhum.</p>;
  return (
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
          {e.map((linha, i) => (
            <tr key={`${linha.data_com}-${i}`}>
              <td className="esq">{formatarData(linha.data_com)}</td>
              <td className="esq">{linha.tipo}</td>
              <td>{formatarNumero(linha.multiplicador)}</td>
              <td className={`esq ${linha.status === "divergente" ? "perde" : ""}`}>{linha.status}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
