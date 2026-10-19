export type Ponto = {
  data: string;
  fechamento?: number | string | null;
  retorno_acumulado: number;
  salto_sem_evento: boolean | null;
};

export type PontoDoGrafico = { data: string; preco: number | null; retorno: number; salto: boolean };

export const PERIODOS: { rotulo: string; meses: number | null }[] = [
  { rotulo: "6M", meses: 6 },
  { rotulo: "1A", meses: 12 },
  { rotulo: "3A", meses: 36 },
  { rotulo: "5A", meses: 60 },
  { rotulo: "10A", meses: 120 },
  { rotulo: "Tudo", meses: null },
];

function mesesAntes(data: string, meses: number): string {
  const corte = new Date(`${data.slice(0, 10)}T00:00:00Z`);
  corte.setUTCMonth(corte.getUTCMonth() - meses);
  return corte.toISOString().slice(0, 10);
}

export function recortar<T extends { data: string }>(serie: T[], meses: number | null): T[] {
  if (meses === null || serie.length === 0) return serie;
  const limite = mesesAntes(serie[serie.length - 1].data, meses);
  return serie.filter((p) => p.data.slice(0, 10) >= limite);
}

export function amostrar<T extends { salto_sem_evento: boolean | null }>(serie: T[], maximo: number): T[] {
  if (serie.length <= maximo) return serie;
  const passo = Math.ceil(serie.length / maximo);
  return serie.filter((p, i) => i % passo === 0 || i === serie.length - 1 || p.salto_sem_evento);
}

export function paraOGrafico(serie: Ponto[]): PontoDoGrafico[] {
  const base = serie[0]?.retorno_acumulado;
  return serie.map((p) => {
    const preco = p.fechamento === null || p.fechamento === undefined ? null : Number(p.fechamento);
    return {
      data: p.data,
      preco: preco !== null && preco > 0 ? preco : null,
      retorno: base ? (p.retorno_acumulado / base) * 100 : p.retorno_acumulado,
      salto: Boolean(p.salto_sem_evento),
    };
  });
}

export function variacao(pontos: PontoDoGrafico[], chave: "preco" | "retorno"): number | null {
  const valores = pontos.map((p) => p[chave]).filter((v): v is number => v !== null);
  if (valores.length < 2) return null;
  return valores[valores.length - 1] / valores[0] - 1;
}

export type Resumo = {
  data: string;
  preco: number | null;
  retorno12m: number | null;
  proventos12m: number | null;
  saltos: number;
};

export function resumir(serie: Ponto[], proventos: { data_com: string; valor: number | string }[]): Resumo | null {
  const ultimo = serie[serie.length - 1];
  if (!ultimo) return null;
  const limite = mesesAntes(ultimo.data, 12);
  const inicio = [...serie].reverse().find((p) => p.data.slice(0, 10) <= limite);
  const preco = ultimo.fechamento === null || ultimo.fechamento === undefined ? null : Number(ultimo.fechamento);
  const doAno = proventos.filter((p) => p.data_com.slice(0, 10) > limite && p.data_com.slice(0, 10) <= ultimo.data);
  return {
    data: ultimo.data,
    preco: preco !== null && preco > 0 ? preco : null,
    retorno12m: inicio ? ultimo.retorno_acumulado / inicio.retorno_acumulado - 1 : null,
    proventos12m: proventos.length === 0 ? null : doAno.reduce((soma, p) => soma + Number(p.valor), 0),
    saltos: serie.filter((p) => p.salto_sem_evento).length,
  };
}
