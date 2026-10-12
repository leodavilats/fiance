import { describe, expect, it } from "vitest";
import { formatarData, formatarPorcento, formatarReais } from "./formato";

describe("formato", () => {
  it("usa o padrão brasileiro", () => {
    expect(formatarData("2026-10-09")).toBe("09/10/2026");
    expect(formatarPorcento(0.0222)).toBe("2,2%");
    expect(formatarReais(36606000000)).toMatch(/^R\$ 36,6/);
    expect(formatarReais(null)).toBe("—");
  });
});
