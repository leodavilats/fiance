import { describe, expect, it } from "vitest";
import { resolverLink } from "./links";

const servidos = new Set(["09-FUTURO.md", "pesquisas/README.md", "pesquisas/ranking.md"]);

describe("links", () => {
  it("resolve o caminho relativo ao documento que cita", () => {
    expect(resolverLink("pesquisas/README.md", "ranking.md", servidos)).toBe("/documentos/pesquisas/ranking.md");
    expect(resolverLink("pesquisas/ranking.md", "../09-FUTURO.md#planejado", servidos)).toBe(
      "/documentos/09-FUTURO.md#planejado",
    );
  });

  it("documento que o painel não serve vira texto, não 404", () => {
    expect(resolverLink("pesquisas/README.md", "../10-PROBLEMAS.md", servidos)).toBeNull();
    expect(resolverLink("09-FUTURO.md", "../../backend/app/x.py", servidos)).toBeNull();
  });

  it("link externo e âncora passam como estão", () => {
    expect(resolverLink("09-FUTURO.md", "https://www.b3.com.br", servidos)).toBe("https://www.b3.com.br");
    expect(resolverLink("09-FUTURO.md", "#riscos", servidos)).toBe("#riscos");
  });
});
