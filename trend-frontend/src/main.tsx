import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { BrowserRouter, NavLink, Navigate, Route, Routes } from "react-router-dom";
import "./estilo.css";
import Coleta from "./telas/Coleta";
import Documento from "./telas/Documento";
import Empresa from "./telas/Empresa";
import Empresas from "./telas/Empresas";
import Pesquisa from "./telas/Pesquisa";
import Planos from "./telas/Planos";

function App() {
  return (
    <BrowserRouter>
      <header className="topo">
        <strong>trend</strong>
        <nav>
          <NavLink to="/coleta">Coleta</NavLink>
          <NavLink to="/empresas">Empresas</NavLink>
          <NavLink to="/pesquisa">Pesquisa</NavLink>
          <NavLink to="/planos">Planos</NavLink>
        </nav>
      </header>
      <main>
        <Routes>
          <Route path="/" element={<Navigate to="/coleta" replace />} />
          <Route path="/coleta" element={<Coleta />} />
          <Route path="/empresas" element={<Empresas />} />
          <Route path="/empresa/:cnpj/:classe" element={<Empresa />} />
          <Route path="/pesquisa" element={<Pesquisa />} />
          <Route path="/planos" element={<Planos />} />
          <Route path="/planos/*" element={<Documento />} />
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
