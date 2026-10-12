import { useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useApi } from "../api";
import { formatarData } from "../formato";
import Estado from "./Estado";

export type Papel = {
  cnpj: string;
  classe: string;
  codigo: string;
  ultimo_pregao: string;
  razao_social: string | null;
  setor: string | null;
};

export default function TelaEmpresas() {
  const estado = useApi<Papel[]>("/api/papeis");
  const [busca, setBusca] = useState("");
  const navegar = useNavigate();
  return (
    <>
      <h1>Empresas</h1>
      <p className="nota">
        Cada linha é um papel: a empresa e a classe da ação, atravessando as trocas de ticker.
      </p>
      <input
        type="search"
        placeholder="Ticker, nome ou setor"
        value={busca}
        onChange={(e) => setBusca(e.target.value)}
      />
      <Estado estado={estado}>
        {(papeis) => (
          <Lista papeis={papeis} busca={busca} abrir={(p) => navegar(`/empresa/${p.cnpj}/${p.classe}`)} />
        )}
      </Estado>
    </>
  );
}

function Lista({ papeis, busca, abrir }: { papeis: Papel[]; busca: string; abrir: (p: Papel) => void }) {
  const filtrados = useMemo(() => {
    const termo = busca.trim().toUpperCase();
    const lista = termo
      ? papeis.filter((p) => [p.codigo, p.razao_social, p.setor].some((v) => v?.toUpperCase().includes(termo)))
      : papeis;
    return [...lista].sort((a, b) => b.ultimo_pregao.localeCompare(a.ultimo_pregao)).slice(0, 200);
  }, [papeis, busca]);

  return (
    <div className="rolar">
      <table>
        <thead>
          <tr>
            <th className="esq">Ticker</th>
            <th className="esq">Empresa</th>
            <th className="esq">Setor</th>
            <th>Último pregão</th>
          </tr>
        </thead>
        <tbody>
          {filtrados.map((p) => (
            <tr key={`${p.cnpj}:${p.classe}`} className="clicavel" onClick={() => abrir(p)}>
              <td className="esq">{p.codigo}</td>
              <td className="esq">{p.razao_social ?? "—"}</td>
              <td className="esq">{p.setor ?? "—"}</td>
              <td>{formatarData(p.ultimo_pregao)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
