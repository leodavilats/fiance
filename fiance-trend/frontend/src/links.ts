export function resolverLink(documento: string, href: string, servidos: Set<string>): string | null {
  if (/^[a-z]+:/i.test(href) || href.startsWith("#")) return href;
  const [caminho, ancora] = href.split("#");
  const partes = documento.split("/").slice(0, -1);
  for (const parte of caminho.split("/")) {
    if (parte === "" || parte === ".") continue;
    if (parte === "..") {
      if (partes.length === 0) return null;
      partes.pop();
    } else {
      partes.push(parte);
    }
  }
  const alvo = partes.join("/");
  if (!servidos.has(alvo)) return null;
  return `/documentos/${alvo}${ancora ? `#${ancora}` : ""}`;
}
