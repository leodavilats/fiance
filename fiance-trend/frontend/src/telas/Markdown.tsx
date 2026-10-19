import { useMemo } from "react";
import ReactMarkdown from "react-markdown";
import { Link } from "react-router-dom";
import remarkGfm from "remark-gfm";
import { useApi } from "../api";
import { resolverLink } from "../links";

export default function Markdown({ documento, texto }: { documento: string; texto: string }) {
  const lista = useApi<{ nome: string }[]>("/api/documentos");
  const servidos = useMemo(
    () => new Set(lista.tipo === "pronto" ? lista.dados.map((d) => d.nome) : []),
    [lista],
  );
  return (
    <article className="documento">
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        components={{
          a: ({ href, children }) => {
            const alvo = href ? resolverLink(documento, href, servidos) : null;
            if (alvo === null) return <span title={href}>{children}</span>;
            if (alvo.startsWith("/")) return <Link to={alvo}>{children}</Link>;
            return <a href={alvo}>{children}</a>;
          },
        }}
      >
        {texto}
      </ReactMarkdown>
    </article>
  );
}
