import { render, screen } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { describe, expect, it, vi } from "vitest";

import { Layout } from "../Layout";

vi.mock("../../store/useAuthStore", () => {
  const logoutMock = vi.fn();
  return {
    useAuthStore: vi.fn((selector) =>
      selector({
        usuario: null,
        logout: logoutMock,
      })
    ),
  };
});

describe("Layout", () => {
  it("renderiza cabecalho, navegacao e conteudo interno", () => {
    globalThis.__APP_VERSION__ = "1.0.0";

    render(
      <MemoryRouter initialEntries={["/"]}>
        <Routes>
          <Route element={<Layout />}>
            <Route path="/" element={<div>Conteudo de teste</div>} />
          </Route>
        </Routes>
      </MemoryRouter>
    );

    expect(screen.getByText("sisPROJETOS LIGHT S.A.")).toBeInTheDocument();
    expect(screen.getByText("Painel")).toBeInTheDocument();
    expect(screen.getByText("Conteudo de teste")).toBeInTheDocument();
    expect(screen.getByText("v1.0.0")).toBeInTheDocument();
  });
});
