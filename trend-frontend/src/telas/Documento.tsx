import ReactMarkdown from "react-markdown";
import { Link, useParams } from "react-router-dom";
import remarkGfm from "remark-gfm";
import { useApi } from "../api";
import Estado from "./Estado";

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
          <article className="documento">
            <ReactMarkdown remarkPlugins={[remarkGfm]}>{documento.texto}</ReactMarkdown>
          </article>
        )}
      </Estado>
    </>
  );
}
