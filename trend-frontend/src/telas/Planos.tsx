import { Link } from "react-router-dom";
import { useApi } from "../api";
import Estado from "./Estado";

export default function TelaPlanos() {
  const estado = useApi<{ nome: string; titulo: string }[]>("/api/documentos");
  return (
    <>
      <h1>Documentos</h1>
      <p className="nota">Os documentos de docs/ que dizem o que existe, o que vem depois e por quê.</p>
      <Estado estado={estado}>
        {(documentos) => (
          <ul>
            {documentos.map((d) => (
              <li key={d.nome}>
                <Link to={`/documentos/${d.nome}`}>{d.titulo}</Link> <span className="nota">{d.nome}</span>
              </li>
            ))}
          </ul>
        )}
      </Estado>
    </>
  );
}
