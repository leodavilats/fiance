import { describe, expect, it } from "vitest";
import { resolverLink } from "./links";

const servidos = new Set(["05-FUTURO.md", "pesquisa/README.md", "pesquisa/estudos/ranking.md"]);

describe("links", () => {
  it("resolve o caminho relativo ao documento que cita", () => {
    expect(resolverLink("pesquisa/README.md", "estudos/ranking.md", servidos)).toBe("/documentos/pesquisa/estudos/ranking.md");
    expect(resolverLink("pesquisa/estudos/ranking.md", "../../05-FUTURO.md#planejado", servidos)).toBe(
      "/documentos/05-FUTURO.md#planejado",
    );
  });

  it("documento que o painel não serve vira texto, não 404", () => {
    expect(resolverLink("pesquisa/README.md", "../06-DESENVOLVIMENTO.md", servidos)).toBeNull();
    expect(resolverLink("05-FUTURO.md", "../../backend/app/x.py", servidos)).toBeNull();
  });

  it("link externo e âncora passam como estão", () => {
    expect(resolverLink("05-FUTURO.md", "https://www.b3.com.br", servidos)).toBe("https://www.b3.com.br");
    expect(resolverLink("05-FUTURO.md", "#riscos", servidos)).toBe("#riscos");
  });
});
