import ReactMarkdown from "react-markdown";
import { Link } from "react-router-dom";
import remarkGfm from "remark-gfm";
import { useApi } from "../api";
import { formatarData, formatarNumero } from "../formato";
import Estado from "./Estado";

type Visao = {
  classes: { tipo: string; papeis: number; negociando: number; desde: string }[];
  proventos: { origem: string; linhas: number; desde: string }[];
  tesouro: { titulos: number; desde: string };
};

export const NOME_DO_TIPO: Record<string, string> = {
  acao: "Ações",
  fii: "FIIs",
  fundo: "ETFs e outros fundos",
  bdr: "BDRs",
};

const NOME_DA_ORIGEM: Record<string, string> = {
  b3_historico: "B3, histórico de companhia",
  b3_recente: "B3, recentes acumulados",
  cvm_estimado: "CVM, estimado pelo informe de FII",
};

export default function TelaCaminho() {
  const visao = useApi<Visao>("/api/visao");
  const plano = useApi<{ texto: string }>("/api/documentos/09-FUTURO.md");
  return (
    <>
      <h1>Caminho</h1>
      <p className="nota">
        O que a base tem hoje e o roadmap. <Link to="/coleta">Saúde da coleta</Link>.
      </p>
      <Estado estado={visao}>{(v) => <Numeros visao={v} />}</Estado>
      <Estado estado={plano}>
        {(documento) => (
          <article className="documento">
            <ReactMarkdown remarkPlugins={[remarkGfm]}>{documento.texto}</ReactMarkdown>
          </article>
        )}
      </Estado>
    </>
  );
}

function Numeros({ visao }: { visao: Visao }) {
  return (
    <>
      <div className="quadros">
        {visao.classes.map((c) => (
          <Link key={c.tipo} className="quadro" to={`/ativos?tipo=${c.tipo}`}>
            <span className="rotulo">{NOME_DO_TIPO[c.tipo] ?? c.tipo}</span>
            <strong>{formatarNumero(c.negociando)}</strong>
            <span className="nota">
              negociando · {formatarNumero(c.papeis)} na história, desde {formatarData(c.desde)}
            </span>
          </Link>
        ))}
        <Link className="quadro" to="/mercado">
          <span className="rotulo">Tesouro Direto</span>
          <strong>{formatarNumero(visao.tesouro.titulos)}</strong>
          <span className="nota">títulos, desde {formatarData(visao.tesouro.desde)}</span>
        </Link>
      </div>
      <div className="rolar">
        <table>
          <thead>
            <tr>
              <th className="esq">Proventos, por origem</th>
              <th>Linhas</th>
              <th>Desde</th>
            </tr>
          </thead>
          <tbody>
            {visao.proventos.map((p) => (
              <tr key={p.origem}>
                <td className="esq">{NOME_DA_ORIGEM[p.origem] ?? p.origem}</td>
                <td>{formatarNumero(p.linhas)}</td>
                <td>{formatarData(p.desde)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </>
  );
}
