import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Route, Routes } from "react-router-dom";

import { Layout } from "./components/Layout";
import { CAD } from "./pages/CAD";
import { CQT } from "./pages/CQT";
import { Dashboard } from "./pages/Dashboard";
import { Tracao } from "./pages/Tracao";

const queryClient = new QueryClient();

export function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <Routes>
          <Route element={<Layout />}>
            <Route path="/" element={<Dashboard />} />
            <Route path="/cqt" element={<CQT />} />
            <Route path="/tracao" element={<Tracao />} />
            <Route path="/cad" element={<CAD />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </QueryClientProvider>
  );
}
