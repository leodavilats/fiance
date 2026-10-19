import { useState, type ReactNode } from "react";
import { Link } from "react-router-dom";
import { formatarData, formatarNumero, formatarPorcento } from "../formato";
import { resumir, type Ponto } from "../serie";

export function Voltar({ tipo }: { tipo: string }) {
  return (
    <p className="nota">
      <Link to={`/ativos?tipo=${tipo}`}>← Ativos</Link>
    </p>
  );
}

export function ResumoDoAtivo({
  serie,
  proventos,
  unidade,
}: {
  serie: Ponto[];
  proventos: { data_com: string; valor: number | string }[];
  unidade: string;
}) {
  const r = resumir(serie, proventos);
  if (!r) return null;
  const sinal = r.retorno12m === null ? "" : r.retorno12m < 0 ? "perde" : "ganha";
  return (
    <div className="quadros">
      <div className="quadro">
        <span className="rotulo">Último fechamento</span>
        <strong>{r.preco === null ? "—" : `R$ ${formatarNumero(r.preco)}`}</strong>
        <span className="nota">em {formatarData(r.data)}</span>
      </div>
      <div className="quadro">
        <span className="rotulo">Retorno total em 12 meses</span>
        <strong className={sinal}>{formatarPorcento(r.retorno12m)}</strong>
        <span className="nota">{r.retorno12m === null ? "menos de um ano de série" : "com proventos"}</span>
      </div>
      <div className="quadro">
        <span className="rotulo">Proventos em 12 meses</span>
        <strong>{r.proventos12m === null ? "—" : `R$ ${formatarNumero(r.proventos12m)}`}</strong>
        <span className="nota">{r.proventos12m === null ? "nenhum provento na base" : `por ${unidade}, pela data-com`}</span>
      </div>
      <div className="quadro">
        <span className="rotulo">Salto sem evento</span>
        <strong className={r.saltos ? "perde" : ""}>{formatarNumero(r.saltos)}</strong>
        <span className="nota">{r.saltos ? "dia(s) fora do retorno, marcados no preço" : "nenhum dia"}</span>
      </div>
    </div>
  );
}

export function Abas({ abas }: { abas: { rotulo: string; total: number; conteudo: ReactNode }[] }) {
  const [ativa, setAtiva] = useState(0);
  return (
    <>
      <div className="abas" role="tablist">
        {abas.map((a, i) => (
          <button
            key={a.rotulo}
            role="tab"
            aria-selected={i === ativa}
            className={i === ativa ? "ativa" : ""}
            onClick={() => setAtiva(i)}
          >
            {a.rotulo} <span className="contagem">{formatarNumero(a.total)}</span>
          </button>
        ))}
      </div>
      <div role="tabpanel">{abas[ativa]?.conteudo}</div>
    </>
  );
}
