import { useParams } from "react-router-dom";
import { useApi } from "../api";
import { formatarData, formatarNumero, formatarPorcento, formatarReais } from "../formato";
import Estado from "./Estado";
import GraficoDaSerie from "./GraficoDaSerie";
import type { Ponto } from "../serie";

type Dia = Ponto & { codigo: string };

type Fundamento = {
  data_referencia: string;
  receita: number | null;
  lucro_controladores: number | null;
  patrimonio_controladores: number | null;
  caixa: number | null;
  divida_bruta: number | null;
};

type DetalheDoPapel = {
  empresa: { razao_social?: string; setor?: string; data_cancelamento?: string | null };
  classe: string;
  serie: Dia[];
  proventos: { data_com: string; tipo: string; valor: number }[];
  eventos: { data_com: string; tipo: string; multiplicador: number | null; status: string; origem: string }[];
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
  const saltos = d.serie.filter((s) => s.salto_sem_evento).length;

  return (
    <>
      <h1>
        {codigo} · {d.empresa.razao_social ?? "Empresa sem cadastro na CVM"}
      </h1>
      <p className="nota">
        {d.empresa.setor ?? "Setor não informado"} · classe {d.classe}
        {d.empresa.data_cancelamento
          ? ` · registro cancelado em ${formatarData(d.empresa.data_cancelamento)}`
          : ""}
        {saltos ? ` · ${saltos} dia(s) com salto sem evento, fora do retorno acumulado e marcados no preço` : ""}
      </p>

      <h2>Retorno total e preço</h2>
      <GraficoDaSerie serie={d.serie} />

      <h2>Resultado anual (DFP)</h2>
      {d.fundamentos.length === 0 ? (
        <p className="nota">Sem demonstrações ligadas a esta empresa.</p>
      ) : (
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
              {[...d.fundamentos].reverse().map((f) => (
                <tr key={f.data_referencia}>
                  <td className="esq">{f.data_referencia.slice(0, 4)}</td>
                  <td>{formatarReais(f.receita)}</td>
                  <td className={Number(f.lucro_controladores) < 0 ? "perde" : ""}>
                    {formatarReais(f.lucro_controladores)}
                  </td>
                  <td>{formatarReais(f.patrimonio_controladores)}</td>
                  <td>{roe(f)}</td>
                  <td>{formatarReais(f.caixa)}</td>
                  <td>{formatarReais(f.divida_bruta)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      <h2>Proventos</h2>
      {d.proventos.length === 0 ? (
        <p className="nota">Nenhum provento na base para esta classe.</p>
      ) : (
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
              {d.proventos.slice(0, 40).map((p, i) => (
                <tr key={`${p.data_com}-${i}`}>
                  <td className="esq">{formatarData(p.data_com)}</td>
                  <td className="esq">{p.tipo}</td>
                  <td>R$ {formatarNumero(p.valor)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      <h2>Eventos em ações</h2>
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
                <th className="esq">Origem</th>
              </tr>
            </thead>
            <tbody>
              {d.eventos.map((e, i) => (
                <tr key={`${e.data_com}-${i}`}>
                  <td className="esq">{formatarData(e.data_com)}</td>
                  <td className="esq">{e.tipo}</td>
                  <td>{formatarNumero(e.multiplicador)}</td>
                  <td className={`esq ${e.status === "divergente" ? "perde" : ""}`}>{e.status}</td>
                  <td className="esq">{e.origem}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </>
  );
}
