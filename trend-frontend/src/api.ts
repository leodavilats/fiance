import { useEffect, useState } from "react";

export type Estado<T> =
  | { tipo: "carregando" }
  | { tipo: "erro"; mensagem: string }
  | { tipo: "pronto"; dados: T };

export function useApi<T>(caminho: string | null): Estado<T> {
  const [estado, setEstado] = useState<Estado<T>>({ tipo: "carregando" });
  useEffect(() => {
    if (!caminho) return;
    let ativo = true;
    setEstado({ tipo: "carregando" });
    fetch(caminho)
      .then(async (resposta) => {
        if (!resposta.ok) throw new Error(`${resposta.status} em ${caminho}`);
        return (await resposta.json()) as T;
      })
      .then((dados) => ativo && setEstado({ tipo: "pronto", dados }))
      .catch((erro: Error) => ativo && setEstado({ tipo: "erro", mensagem: erro.message }));
    return () => {
      ativo = false;
    };
  }, [caminho]);
  return estado;
}
