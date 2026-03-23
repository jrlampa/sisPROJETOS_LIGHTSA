import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Navigate, Outlet, Route, Routes } from "react-router-dom";

import { Layout } from "./components/Layout";
import { CAD } from "./pages/CAD";
import { CQT } from "./pages/CQT";
import { Dashboard } from "./pages/Dashboard";
import { Exportacao } from "./pages/Exportacao";
import { Login } from "./pages/Login";
import { Tracao } from "./pages/Tracao";
import { useAuthStore } from "./store/useAuthStore";

const queryClient = new QueryClient();

/**
 * Guarda de rota: redireciona para /login se não houver token JWT.
 * Envolve as rotas internas usando <Outlet /> quando autenticado.
 */
function ProtectedRoute() {
  const token = useAuthStore((s) => s.token);
  return token ? <Outlet /> : <Navigate to="/login" replace />;
}

export function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <Routes>
          {/* Rota pública — não precisa de token */}
          <Route path="/login" element={<Login />} />

          {/* Rotas protegidas — exigem token válido */}
          <Route element={<ProtectedRoute />}>
            <Route element={<Layout />}>
              <Route path="/" element={<Dashboard />} />
              <Route path="/cqt" element={<CQT />} />
              <Route path="/tracao" element={<Tracao />} />
              <Route path="/cad" element={<CAD />} />
              <Route path="/exportacao" element={<Exportacao />} />
            </Route>
          </Route>
        </Routes>
      </BrowserRouter>
    </QueryClientProvider>
  );
}
