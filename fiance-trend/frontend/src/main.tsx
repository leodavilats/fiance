import { StrictMode, useEffect, useLayoutEffect, useRef, useState } from "react";
import { createRoot } from "react-dom/client";
import { BrowserRouter, NavLink, Navigate, Route, Routes, useLocation } from "react-router-dom";
import "./estilo.css";
import { Icone } from "./Icones";
import Simbolo, { Logotipo } from "./Simbolo";
import Alertas from "./telas/Alertas";
import Ativos from "./telas/Ativos";
import Caminho from "./telas/Caminho";
import Coleta from "./telas/Coleta";
import Documento from "./telas/Documento";
import Empresa from "./telas/Empresa";
import Estudos from "./telas/Estudos";
import Fundo from "./telas/Fundo";
import Mercado from "./telas/Mercado";
import Pesquisa from "./telas/Pesquisa";
import Planos from "./telas/Planos";
import Ranking from "./telas/Ranking";

type Item = { para: string; rotulo: string; icone: string; tambem?: string[] };

const GRUPOS: { titulo: string; itens: Item[] }[] = [
  {
    titulo: "Base",
    itens: [
      { para: "/caminho", rotulo: "Caminho", icone: "caminho" },
      { para: "/coleta", rotulo: "Coleta", icone: "coleta" },
      { para: "/ativos", rotulo: "Ativos", icone: "ativos", tambem: ["/empresa/", "/fundo/"] },
      { para: "/mercado", rotulo: "Dólar e Tesouro", icone: "mercado" },
    ],
  },
  {
    titulo: "Estudos",
    itens: [
      { para: "/estudos", rotulo: "Todos os estudos", icone: "estudos" },
      { para: "/ranking", rotulo: "Ranking de tendência", icone: "ranking" },
      { para: "/pesquisa", rotulo: "Pesquisa de carteira", icone: "pesquisa" },
    ],
  },
  {
    titulo: "Referência",
    itens: [{ para: "/documentos", rotulo: "Documentos", icone: "documentos" }],
  },
];

function Marca() {
  return (
    <span className="marca">
      <Simbolo />
      <Logotipo />
      <span className="produto">trend</span>
    </span>
  );
}

function Navegacao({ aberta, fechar }: { aberta: boolean; fechar: () => void }) {
  const { pathname } = useLocation();
  const lista = useRef<HTMLDivElement>(null);
  const [marcador, setMarcador] = useState<{ y: number; h: number } | null>(null);
  const [desliza, setDesliza] = useState(false);

  useLayoutEffect(() => {
    const medir = () => {
      const caixa = lista.current;
      const ativo = caixa?.querySelector<HTMLElement>("a.active");
      if (!caixa || !ativo) return setMarcador(null);
      const y = ativo.getBoundingClientRect().top - caixa.getBoundingClientRect().top + caixa.scrollTop;
      setMarcador({ y, h: ativo.offsetHeight });
    };
    medir();
    const observador = new ResizeObserver(medir);
    if (lista.current) observador.observe(lista.current);
    return () => observador.disconnect();
  }, [pathname]);

  useEffect(() => {
    if (!marcador || desliza) return;
    const quadro = requestAnimationFrame(() => setDesliza(true));
    return () => cancelAnimationFrame(quadro);
  }, [marcador, desliza]);

  return (
    <aside className={aberta ? "lateral aberta" : "lateral"} id="navegacao">
      <div className="lateral-topo">
        <Marca />
        <button type="button" className="so-estreito icone-botao" onClick={fechar} aria-label="Fechar o menu">
          <Icone nome="fechar" />
        </button>
      </div>
      <div className="itens" ref={lista}>
        {marcador && (
          <span
            className={desliza ? "marcador desliza" : "marcador"}
            style={{ transform: `translateY(${marcador.y}px)`, height: marcador.h }}
            aria-hidden="true"
          />
        )}
        {GRUPOS.map((g) => (
          <nav key={g.titulo} aria-label={g.titulo}>
            <span className="grupo">{g.titulo}</span>
            {g.itens.map((i) => (
              <NavLink
                key={i.para}
                to={i.para}
                onClick={fechar}
                className={({ isActive }) =>
                  isActive || i.tambem?.some((p) => pathname.startsWith(p)) ? "active" : ""
                }
              >
                <Icone nome={i.icone} />
                <span>{i.rotulo}</span>
              </NavLink>
            ))}
          </nav>
        ))}
      </div>
      <p className="lateral-pe">Laboratório · B3, CVM e BCB</p>
    </aside>
  );
}

function Painel() {
  const { pathname } = useLocation();
  const [aberta, setAberta] = useState(false);

  useEffect(() => {
    if (!aberta) return;
    const tecla = (e: KeyboardEvent) => e.key === "Escape" && setAberta(false);
    document.addEventListener("keydown", tecla);
    return () => document.removeEventListener("keydown", tecla);
  }, [aberta]);

  useEffect(() => {
    window.scrollTo(0, 0);
  }, [pathname]);

  return (
    <div className="painel">
      <header className="barra so-estreito">
        <button
          type="button"
          className="icone-botao"
          onClick={() => setAberta(true)}
          aria-label="Abrir o menu"
          aria-expanded={aberta}
          aria-controls="navegacao"
        >
          <Icone nome="menu" />
        </button>
        <Marca />
      </header>
      <Navegacao aberta={aberta} fechar={() => setAberta(false)} />
      <div className={aberta ? "veu visivel" : "veu"} onClick={() => setAberta(false)} aria-hidden="true" />
      <main>
        <Alertas />
        <div className="tela" key={pathname.split("/")[1]}>
        <Routes>
          <Route path="/" element={<Navigate to="/caminho" replace />} />
          <Route path="/caminho" element={<Caminho />} />
          <Route path="/coleta" element={<Coleta />} />
          <Route path="/ativos" element={<Ativos />} />
          <Route path="/empresas" element={<Navigate to="/ativos" replace />} />
          <Route path="/empresa/:cnpj/:classe" element={<Empresa />} />
          <Route path="/fundo/:emissor/:classe" element={<Fundo />} />
          <Route path="/mercado" element={<Mercado />} />
          <Route path="/estudos" element={<Estudos />} />
          <Route path="/ranking" element={<Ranking />} />
          <Route path="/pesquisa" element={<Pesquisa />} />
          <Route path="/documentos" element={<Planos />} />
          <Route path="/documentos/*" element={<Documento />} />
          <Route path="/planos/*" element={<Navigate to="/documentos" replace />} />
        </Routes>
        </div>
      </main>
    </div>
  );
}

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <BrowserRouter>
      <Painel />
    </BrowserRouter>
  </StrictMode>,
);
