import { expect, test } from "@playwright/test";

function buildJwt(email = "engenheiro@light.com", role = "ENGENHEIRO") {
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

test("fluxo principal: login, tracao e exibicao de resultado", async ({ page }) => {
  const projetoId = `PROJ-E2E-${Date.now()}`;

  await page.route("**/auth/token", async (route) => {
    const body = route.request().postDataJSON() || {};
    const token = buildJwt(body.email || "engenheiro@light.com", body.role || "ENGENHEIRO");

    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({ access_token: token, token_type: "bearer" }),
    });
  });

  await page.route("**/projetos/", async (route) => {
    await route.fulfill({
      status: 201,
      contentType: "application/json",
      body: JSON.stringify({
        id: projetoId,
        codigo: "WEB-E2E-TRACAO",
        nome: "Projeto E2E Tracao",
        localidade: "Bangu",
      }),
    });
  });

  await page.route("**/projetos/*/tracao", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        resultados: [
          {
            esforco_resultante_daN: 142.7,
            percentual_carregamento: 47.6,
            estado_mecanico: "APROVADO",
          },
        ],
      }),
    });
  });

  await page.goto("/login");

  await page.getByLabel("Email").fill("engenheiro@light.com");
  await page.getByLabel("Perfil de Acesso").selectOption("ENGENHEIRO");
  await page.getByRole("button", { name: "Entrar" }).click();

  await expect(page).toHaveURL(/\/$/);

  await page.getByRole("button", { name: "Criar Novo Projeto" }).click();
  await expect(page.getByTestId("project-created-success")).toBeVisible();

  await page.getByRole("link", { name: "Tracao" }).click();
  await expect(page.getByText("Calculo de Tracao")).toBeVisible();

  await page.getByPlaceholder("Ex: 300").fill("300");
  await page.getByLabel("Vao, travessia 1, MT - 1o Nivel").fill("50");
  await page.getByLabel("Flecha, travessia 1, MT - 1o Nivel").fill("5");

  const tracaoResponse = page.waitForResponse((response) =>
    response.url().includes(`/projetos/${projetoId}/tracao`) && response.status() === 200
  );

  await page.getByRole("button", { name: "Calcular Tracao" }).click();

  await tracaoResponse;
  await expect(page.locator("td", { hasText: "APROVADO" }).first()).toBeVisible();
});
