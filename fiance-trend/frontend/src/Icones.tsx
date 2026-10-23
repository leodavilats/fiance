const TRACOS: Record<string, string> = {
  caminho: "M3 13.5c0-3.5 2.5-4 5-5.5s5-2 5-5.5M3 13.5h.01M13 2.5h.01",
  coleta:
    "M3 4c0-1.1 2.2-2 5-2s5 .9 5 2-2.2 2-5 2-5-.9-5-2zM3 4v8c0 1.1 2.2 2 5 2s5-.9 5-2V4M3 8c0 1.1 2.2 2 5 2s5-.9 5-2",
  ativos: "M2.5 2.5h4.5v4.5H2.5zM9 2.5h4.5v4.5H9zM2.5 9h4.5v4.5H2.5zM9 9h4.5v4.5H9z",
  mercado: "M2 12l3.5-3.5 3 2.5L14 4.5M10.5 4.5H14V8",
  estudos: "M6 2h4M7 2v4.2L3.2 12.6c-.4.7.1 1.4.8 1.4h8c.7 0 1.2-.7.8-1.4L9 6.2V2M5 10h6",
  ranking: "M3 13.5V9M8 13.5V3M13 13.5V6.5",
  pesquisa: "M8 2a6 6 0 1 0 6 6H8zM10 1.8A6 6 0 0 1 14.2 6H10z",
  documentos: "M4 1.8h5.2L12 4.6v9.6H4zM9 1.8v3h3M6 8.5h4M6 11h4",
  menu: "M2.5 4h11M2.5 8h11M2.5 12h11",
  fechar: "M3.5 3.5l9 9M12.5 3.5l-9 9",
};

export function Icone({ nome }: { nome: keyof typeof TRACOS | string }) {
  return (
    <svg className="icone" viewBox="0 0 16 16" aria-hidden="true" focusable="false">
      <path
        d={TRACOS[nome]}
        fill="none"
        stroke="currentColor"
        strokeWidth="1.4"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}
