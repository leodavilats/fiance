import { useParams } from "react-router-dom";
import { useApi } from "../api";
import { formatarData, formatarNumero, formatarPorcento, formatarReais } from "../formato";
import type { Ponto } from "../serie";
import { Abas, ResumoDoAtivo, Voltar } from "./Detalhes";
import Estado from "./Estado";
import GraficoDaSerie from "./GraficoDaSerie";

type Dia = Ponto & { codigo: string };

type Fundamento = {
  data_referencia: string;
  receita: number | null;
  lucro_controladores: number | null;
  patrimonio_controladores: number | null;
  caixa: number | null;
  divida_bruta: number | null;
};

type Provento = { data_com: string; tipo: string; valor: number };
type Evento = { data_com: string; tipo: string; multiplicador: number | null; status: string; origem: string };

type DetalheDoPapel = {
  empresa: { razao_social?: string; setor?: string; data_cancelamento?: string | null };
  classe: string;
  serie: Dia[];
  proventos: Provento[];
  eventos: Evento[];
  fundamentos: Fundamento[];
};

export default function TelaEmpresa() {
  const { cnpj, classe } = useParams();
  const estado = useApi<DetalheDoPapel>(`/api/papeis/${cnpj}/${classe}`);
  return <Estado estado={estado}>{(d) => <Detalhe d={d} />}</Estado>;
}

function roe(f: Fundamento): string {
  if (f.lucro_controladores === null || !f.patrimonio_controladores) return "—";
  return formatarPorcento(Number(f.lucro_controladores) / Number(f.patrimonio_controladores));
}

function Detalhe({ d }: { d: DetalheDoPapel }) {
  const codigo = d.serie[d.serie.length - 1]?.codigo;
  return (
    <>
      <Voltar tipo="acao" />
      <h1>
        {codigo} · {d.empresa.razao_social ?? "Empresa sem cadastro na CVM"}
      </h1>
      <p className="nota">
        {d.empresa.setor ?? "Setor não informado"} · classe {d.classe}
        {d.empresa.data_cancelamento
          ? ` · registro cancelado em ${formatarData(d.empresa.data_cancelamento)}`
          : ""}
      </p>

      <ResumoDoAtivo serie={d.serie} proventos={d.proventos} unidade="ação" />

      <h2>Retorno total e preço</h2>
      <GraficoDaSerie serie={d.serie} />

      <h2>Detalhes</h2>
      <Abas
        abas={[
          { rotulo: "Resultado anual", total: d.fundamentos.length, conteudo: <Fundamentos f={d.fundamentos} /> },
          { rotulo: "Proventos", total: d.proventos.length, conteudo: <Proventos p={d.proventos} /> },
          { rotulo: "Eventos em ações", total: d.eventos.length, conteudo: <Eventos e={d.eventos} /> },
        ]}
      />
    </>
  );
}

function Fundamentos({ f }: { f: Fundamento[] }) {
  if (f.length === 0) return <p className="nota">Sem demonstrações ligadas a esta empresa.</p>;
  return (
    <div className="rolar">
      <table>
        <thead>
          <tr>
            <th className="esq">Ano</th>
            <th>Receita</th>
            <th>Lucro dos controladores</th>
            <th>Patrimônio</th>
            <th>ROE</th>
            <th>Caixa</th>
            <th>Dívida bruta</th>
          </tr>
        </thead>
        <tbody>
          {[...f].reverse().map((linha) => (
            <tr key={linha.data_referencia}>
              <td className="esq">{linha.data_referencia.slice(0, 4)}</td>
              <td>{formatarReais(linha.receita)}</td>
              <td className={Number(linha.lucro_controladores) < 0 ? "perde" : ""}>
                {formatarReais(linha.lucro_controladores)}
              </td>
              <td>{formatarReais(linha.patrimonio_controladores)}</td>
              <td>{roe(linha)}</td>
              <td>{formatarReais(linha.caixa)}</td>
              <td>{formatarReais(linha.divida_bruta)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function Proventos({ p }: { p: Provento[] }) {
  if (p.length === 0) return <p className="nota">Nenhum provento na base para esta classe.</p>;
  return (
    <div className="rolar">
      <table>
        <thead>
          <tr>
            <th className="esq">Data-com</th>
            <th className="esq">Tipo</th>
            <th>Valor por ação</th>
          </tr>
        </thead>
        <tbody>
          {p.slice(0, 40).map((linha, i) => (
            <tr key={`${linha.data_com}-${i}`}>
              <td className="esq">{formatarData(linha.data_com)}</td>
              <td className="esq">{linha.tipo}</td>
              <td>R$ {formatarNumero(linha.valor)}</td>
            </tr>
          ))}
        </tbody>
      </table>
      {p.length > 40 && <p className="nota">Os 40 mais recentes, de {formatarNumero(p.length)}.</p>}
    </div>
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
            <th className="esq">Origem</th>
          </tr>
        </thead>
        <tbody>
          {e.map((linha, i) => (
            <tr key={`${linha.data_com}-${i}`}>
              <td className="esq">{formatarData(linha.data_com)}</td>
              <td className="esq">{linha.tipo}</td>
              <td>{formatarNumero(linha.multiplicador)}</td>
              <td className={`esq ${linha.status === "divergente" ? "perde" : ""}`}>{linha.status}</td>
              <td className="esq">{linha.origem}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
