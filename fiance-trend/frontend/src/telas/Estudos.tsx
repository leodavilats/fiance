import { Link } from "react-router-dom";
import { useApi } from "../api";
import Estado from "./Estado";
import Markdown from "./Markdown";

const INDICE = "pesquisas/README.md";

export default function TelaEstudos() {
  const estado = useApi<{ texto: string }>(`/api/documentos/${INDICE}`);
  return (
    <>
      <h1>Estudos</h1>
      <p className="nota">
        Cada estudo tem protocolo escrito antes de rodar. Os resultados estão em{" "}
        <Link to="/ranking">Ranking</Link> e <Link to="/pesquisa">Pesquisa de carteira</Link>; o proposto só roda
        depois do aceite.
      </p>
      <Estado estado={estado}>{(d) => <Markdown documento={INDICE} texto={d.texto} />}</Estado>
    </>
  );
}
