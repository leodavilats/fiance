import { Link } from "react-router-dom";
import { useApi } from "../api";

type Alerta = { tipo: string; mensagem: string };

export default function Alertas() {
  const estado = useApi<Alerta[]>("/api/alertas");
  if (estado.tipo === "erro") {
    return <div className="alerta">Não foi possível conferir a coleta: {estado.mensagem}</div>;
  }
  if (estado.tipo !== "pronto" || estado.dados.length === 0) return null;
  return (
    <div className="alerta">
      <strong>A coleta precisa de atenção.</strong>
      <ul>
        {estado.dados.map((a) => (
          <li key={a.mensagem}>{a.mensagem}</li>
        ))}
      </ul>
      <Link to="/coleta">Ver a coleta</Link>
    </div>
  );
}
