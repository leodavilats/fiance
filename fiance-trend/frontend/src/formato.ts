const numero = new Intl.NumberFormat("pt-BR", { maximumFractionDigits: 2 });
const compacto = new Intl.NumberFormat("pt-BR", { notation: "compact", maximumFractionDigits: 1 });
const porcento = new Intl.NumberFormat("pt-BR", { style: "percent", maximumFractionDigits: 1 });

export function formatarNumero(valor: number | string | null | undefined): string {
  return valor === null || valor === undefined ? "—" : numero.format(Number(valor));
}

export function formatarReais(valor: number | string | null | undefined): string {
  return valor === null || valor === undefined ? "—" : `R$ ${compacto.format(Number(valor))}`;
}

export function formatarPorcento(valor: number | string | null | undefined): string {
  return valor === null || valor === undefined ? "—" : porcento.format(Number(valor));
}

export function formatarData(valor: string | null | undefined): string {
  if (!valor) return "—";
  const [ano, mes, dia] = valor.slice(0, 10).split("-");
  return `${dia}/${mes}/${ano}`;
}
