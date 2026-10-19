import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { BrowserRouter, NavLink, Navigate, Route, Routes, useLocation } from "react-router-dom";
import "./estilo.css";
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

type Item = { para: string; rotulo: string; tambem?: string[] };

const GRUPOS: { titulo: string; itens: Item[] }[] = [
  {
    titulo: "Base",
    itens: [
      { para: "/caminho", rotulo: "Caminho" },
      { para: "/coleta", rotulo: "Coleta" },
      { para: "/ativos", rotulo: "Ativos", tambem: ["/empresa/", "/fundo/"] },
      { para: "/mercado", rotulo: "Dólar e Tesouro" },
    ],
  },
  {
    titulo: "Estudos",
    itens: [
      { para: "/estudos", rotulo: "Todos os estudos" },
      { para: "/ranking", rotulo: "Ranking de tendência" },
      { para: "/pesquisa", rotulo: "Pesquisa de carteira" },
    ],
  },
  { titulo: "Referência", itens: [{ para: "/documentos", rotulo: "Documentos" }] },
];

function Navegacao() {
  const { pathname } = useLocation();
  return (
    <aside className="lateral">
      <strong className="marca">trend</strong>
      {GRUPOS.map((g) => (
        <nav key={g.titulo} aria-label={g.titulo}>
          <span className="grupo">{g.titulo}</span>
          {g.itens.map((i) => (
            <NavLink
              key={i.para}
              to={i.para}
              className={({ isActive }) =>
                isActive || i.tambem?.some((p) => pathname.startsWith(p)) ? "active" : ""
              }
            >
              {i.rotulo}
            </NavLink>
          ))}
        </nav>
      ))}
    </aside>
  );
}

function App() {
  return (
    <BrowserRouter>
      <div className="painel">
        <Navegacao />
        <main>
          <Alertas />
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
        </main>
      </div>
    </BrowserRouter>
  );
}

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <App />
  </StrictMode>,
);
