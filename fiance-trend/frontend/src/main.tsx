import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { BrowserRouter, NavLink, Navigate, Route, Routes } from "react-router-dom";
import "./estilo.css";
import Alertas from "./telas/Alertas";
import Ativos from "./telas/Ativos";
import Caminho from "./telas/Caminho";
import Coleta from "./telas/Coleta";
import Documento from "./telas/Documento";
import Empresa from "./telas/Empresa";
import Fundo from "./telas/Fundo";
import Mercado from "./telas/Mercado";
import Pesquisa from "./telas/Pesquisa";
import Planos from "./telas/Planos";
import Ranking from "./telas/Ranking";

function App() {
  return (
    <BrowserRouter>
      <header className="topo">
        <strong>trend</strong>
        <nav>
          <NavLink to="/caminho">Caminho</NavLink>
          <NavLink to="/coleta">Coleta</NavLink>
          <NavLink to="/ativos">Ativos</NavLink>
          <NavLink to="/mercado">Dólar e Tesouro</NavLink>
          <NavLink to="/ranking">Ranking</NavLink>
          <NavLink to="/pesquisa">Pesquisa</NavLink>
          <NavLink to="/documentos">Documentos</NavLink>
        </nav>
      </header>
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
          <Route path="/ranking" element={<Ranking />} />
          <Route path="/pesquisa" element={<Pesquisa />} />
          <Route path="/documentos" element={<Planos />} />
          <Route path="/documentos/*" element={<Documento />} />
          <Route path="/planos/*" element={<Navigate to="/documentos" replace />} />
        </Routes>
      </main>
    </BrowserRouter>
  );
}

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <App />
  </StrictMode>,
);
