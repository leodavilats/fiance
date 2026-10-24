import { describe, expect, it } from "vitest";
import { amostrar, dentro, indicesDaJanela, paraOGrafico, recortar, resumir, variacao, type Ponto } from "./serie";

const ponto = (data: string, retorno_acumulado: number, extra: Partial<Ponto> = {}): Ponto => ({
  data,
  fechamento: retorno_acumulado / 10,
  retorno_acumulado,
  salto_sem_evento: false,
  ...extra,
});

describe("serie", () => {
  it("recorta pelo último pregão, não por hoje", () => {
    const serie = [ponto("2020-01-02", 100), ponto("2024-06-28", 150), ponto("2025-06-30", 180)];
    expect(recortar(serie, 12).map((p) => p.data)).toEqual(["2025-06-30"]);
    expect(recortar(serie, 13).map((p) => p.data)).toEqual(["2024-06-28", "2025-06-30"]);
    expect(recortar(serie, null)).toHaveLength(3);
  });

  it("a amostra guarda o último dia e todo salto sem evento", () => {
    const serie = Array.from({ length: 100 }, (_, i) =>
      ponto(`2020-01-${String(i).padStart(3, "0")}`, 100, { salto_sem_evento: i === 37 }),
    );
    const amostra = amostrar(serie, 10);
    expect(amostra.length).toBeLessThanOrEqual(12);
    expect(amostra[amostra.length - 1]).toBe(serie[99]);
    expect(amostra).toContain(serie[37]);
  });

  it("o retorno recomeça em 100 no início da janela", () => {
    const grafico = paraOGrafico([ponto("2024-01-02", 200), ponto("2024-01-03", 220)]);
    expect(grafico[0].retorno).toBe(100);
    expect(grafico[1].retorno).toBeCloseTo(110);
    expect(variacao(grafico, "retorno")).toBeCloseTo(0.1);
  });

  it("preço ausente ou não positivo some da linha, sem virar zero", () => {
    const grafico = paraOGrafico([
      ponto("2024-01-02", 100, { fechamento: null }),
      ponto("2024-01-03", 100, { fechamento: "0" }),
      ponto("2024-01-04", 100, { fechamento: "12.5" }),
    ]);
    expect(grafico.map((p) => p.preco)).toEqual([null, null, 12.5]);
    expect(variacao(grafico, "preco")).toBeNull();
  });

  it("o resumo de 12 meses só existe com um ano de série, e provento ausente não vira zero", () => {
    const serie = [ponto("2024-06-28", 100), ponto("2024-07-01", 105), ponto("2025-06-30", 120)];
    const resumo = resumir(serie, [
      { data_com: "2024-06-10", valor: 1 },
      { data_com: "2024-12-10", valor: "0.5" },
      { data_com: "2025-06-10", valor: 0.25 },
    ]);
    expect(resumo?.retorno12m).toBeCloseTo(0.2);
    expect(resumo?.proventos12m).toBeCloseTo(0.75);
    expect(resumo?.preco).toBe(12);
    expect(resumir(serie.slice(1), [])?.retorno12m).toBeNull();
    expect(resumir(serie, [])?.proventos12m).toBeNull();
  });

  it("a janela do zoom é por data, e cai nos pontos da amostra mais próximos por dentro", () => {
    const serie = [ponto("2024-01-02", 100), ponto("2024-01-05", 101), ponto("2024-01-09", 102), ponto("2024-01-12", 103)];
    expect(dentro(serie, ["2024-01-03", "2024-01-10"]).map((p) => p.data)).toEqual(["2024-01-05", "2024-01-09"]);
    expect(dentro(serie, null)).toBe(serie);
    expect(indicesDaJanela(serie, ["2024-01-03", "2024-01-10"])).toEqual([1, 2]);
    expect(indicesDaJanela(serie, ["2024-01-05", "2024-01-12"])).toEqual([1, 3]);
    expect(indicesDaJanela(serie, null), "sem zoom, a faixa cobre o período inteiro").toEqual([0, 3]);
    expect(indicesDaJanela(serie, ["2024-01-06", "2024-01-08"]), "janela sem ponto não some com a faixa").toEqual([0, 3]);
  });
});
