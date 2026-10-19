import { Link, useParams } from "react-router-dom";
import { useApi } from "../api";
import Estado from "./Estado";
import Markdown from "./Markdown";

export default function TelaDocumento() {
  const nome = useParams()["*"] ?? "";
  const estado = useApi<{ nome: string; texto: string }>(`/api/documentos/${nome}`);
  return (
    <>
      <p className="nota">
        <Link to="/documentos">← Documentos</Link> · {nome}
      </p>
      <Estado estado={estado}>
        {(documento) => (
          <Markdown documento={nome} texto={documento.texto} />
        )}
      </Estado>
    </>
  );
}
