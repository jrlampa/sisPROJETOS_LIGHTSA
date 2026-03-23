import { expect, test } from "@playwright/test";

function buildJwt(email = "qa@light.com", role = "ENGENHEIRO") {
  const header = Buffer.from(JSON.stringify({ alg: "HS256", typ: "JWT" })).toString("base64url");
  const payload = Buffer.from(
    JSON.stringify({
      sub: email,
      role,
      exp: Math.floor(Date.now() / 1000) + 3600,
    })
  ).toString("base64url");
  return `${header}.${payload}.assinatura-fake`;
}

async function mockAuthToken(page) {
  await page.route("**/auth/token", async (route) => {
    const body = route.request().postDataJSON();
    const token = buildJwt(body?.email || "qa@light.com", body?.role || "ENGENHEIRO");
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({ access_token: token, token_type: "bearer" }),
    });
  });
}

test("redireciona rota protegida para /login", async ({ page }) => {
  await page.goto("/cqt");

  await expect(page).toHaveURL(/\/login$/);
  await expect(page.getByRole("button", { name: "Entrar" })).toBeVisible();
});

test("mantem projeto ativo apos F5 com persist", async ({ page }) => {
  await mockAuthToken(page);

  const persistedProjectId = `PW-${Date.now()}`;
  await page.route("**/projetos/", async (route) => {
    await route.fulfill({
      status: 201,
      contentType: "application/json",
      body: JSON.stringify({
        id: persistedProjectId,
        codigo: "WEB-000001",
        nome: "Projeto Teste",
        localidade: "Bangu",
      }),
    });
  });

  await page.goto("/login");
  await page.getByLabel("Email").fill("engenheiro@light.com");
  await page.getByLabel("Perfil de Acesso").selectOption("ENGENHEIRO");
  await page.getByRole("button", { name: "Entrar" }).click();

  await expect(page).toHaveURL(/\/$/);
  await page.getByRole("button", { name: "Criar Novo Projeto" }).click();

  const successBanner = page.getByTestId("project-created-success");
  await expect(successBanner).toContainText(`ID: ${persistedProjectId}`);

  await page.reload();

  const activeProject = page.getByTestId("active-project-id");
  await expect(activeProject).toContainText(`ID: ${persistedProjectId}`);
});

test("campo de comprimento aceita input invalido sem quebrar a tela", async ({ page }) => {
  await page.addInitScript(() => {
    localStorage.setItem(
      "sisprojetos-auth",
      JSON.stringify({
        state: {
          token: "token-qa",
          usuario: { email: "qa@light.com", role: "ENGENHEIRO" },
        },
        version: 0,
      })
    );

    localStorage.setItem(
      "sisprojetos-project",
      JSON.stringify({
        state: {
          projetoAtivo: {
            id: "PROJ-E2E-001",
            nome: "Projeto E2E",
            localidade: "Bangu",
          },
        },
        version: 0,
      })
    );
  });

  await page.goto("/cqt");

  const comprimentoInput = page.locator("table tbody tr:first-child td:nth-child(2) input");
  await comprimentoInput.fill("abc");

  await expect(comprimentoInput).toHaveValue("abc");
  await expect(page.getByText("Etapa 2: CQT - Planilha")).toBeVisible();
  await expect(page.getByRole("button", { name: "Calcular CQT" })).toBeVisible();
});
