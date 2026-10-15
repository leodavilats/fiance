import { useMemo, useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { useApi } from "../api";
import { formatarData } from "../formato";
import { NOME_DO_TIPO } from "./Caminho";
import Estado from "./Estado";

export type Ativo = {
  tipo: string;
  chave: string;
  classe: string;
  codigo: string;
  ultimo_pregao: string;
  nome: string | null;
  setor: string | null;
};

const TIPOS = ["acao", "fii", "fundo", "bdr"];

export function rotaDoAtivo(a: Ativo): string {
  return a.tipo === "acao" ? `/empresa/${a.chave}/${a.classe}` : `/fundo/${a.chave}/${a.classe}`;
}

export default function TelaAtivos() {
  const estado = useApi<Ativo[]>("/api/ativos");
  const [parametros, setParametros] = useSearchParams();
  const tipo = parametros.get("tipo") ?? "acao";
  const [busca, setBusca] = useState("");
  const navegar = useNavigate();
  return (
    <>
      <h1>Ativos</h1>
      <p className="nota">
        Cada linha é um papel, atravessando as trocas de ticker. Ação pela empresa e classe; fundo e BDR pelo
        emissor e classe da cota.
      </p>
      <nav className="abas">
        {TIPOS.map((t) => (
          <button key={t} className={t === tipo ? "ativa" : ""} onClick={() => setParametros({ tipo: t })}>
            {NOME_DO_TIPO[t]}
          </button>
        ))}
      </nav>
      <input
        type="search"
        placeholder="Ticker, nome ou setor"
        value={busca}
        onChange={(e) => setBusca(e.target.value)}
      />
      <Estado estado={estado}>
        {(ativos) => <Lista ativos={ativos} tipo={tipo} busca={busca} abrir={(a) => navegar(rotaDoAtivo(a))} />}
      </Estado>
    </>
  );
}

function Lista({
  ativos,
  tipo,
  busca,
  abrir,
}: {
  ativos: Ativo[];
  tipo: string;
  busca: string;
  abrir: (a: Ativo) => void;
}) {
  const filtrados = useMemo(() => {
    const termo = busca.trim().toUpperCase();
    const daClasse = ativos.filter((a) => a.tipo === tipo);
    const lista = termo
      ? daClasse.filter((a) => [a.codigo, a.nome, a.setor].some((v) => v?.toUpperCase().includes(termo)))
      : daClasse;
    return [...lista].sort((a, b) => b.ultimo_pregao.localeCompare(a.ultimo_pregao)).slice(0, 200);
  }, [ativos, tipo, busca]);

  return (
    <div className="rolar">
      <table>
        <thead>
          <tr>
            <th className="esq">Ticker</th>
            <th className="esq">Nome</th>
            {tipo === "acao" && <th className="esq">Setor</th>}
            <th>Último pregão</th>
          </tr>
        </thead>
        <tbody>
          {filtrados.map((a) => (
            <tr key={`${a.tipo}:${a.chave}:${a.classe}`} className="clicavel" onClick={() => abrir(a)}>
              <td className="esq">{a.codigo}</td>
              <td className="esq">{a.nome ?? "—"}</td>
              {tipo === "acao" && <td className="esq">{a.setor ?? "—"}</td>}
              <td>{formatarData(a.ultimo_pregao)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
