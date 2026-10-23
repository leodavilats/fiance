import type { ReactNode } from "react";
import type { Estado as EstadoApi } from "../api";

export default function Estado<T>({
  estado,
  children,
}: {
  estado: EstadoApi<T>;
  children: (dados: T) => ReactNode;
}) {
  if (estado.tipo === "carregando") {
    return (
      <div className="esqueleto" role="status" aria-label="Carregando">
        <span />
        <span />
        <span />
      </div>
    );
  }
  if (estado.tipo === "erro") return <p className="erro">Não foi possível carregar: {estado.mensagem}</p>;
  return <>{children(estado.dados)}</>;
}
