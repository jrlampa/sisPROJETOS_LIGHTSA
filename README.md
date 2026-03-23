# sisPROJETOS LIGHT S.A. - Manual Oficial

## Visao geral

O sisPROJETOS e um motor de calculo hibrido Web/Desktop para projetos de rede da LIGHT S.A., desenhado para padronizar o fluxo tecnico e reduzir retrabalho operacional.

O sistema combina:

- operacao web para workflow e colaboracao;
- capacidade de paridade com legados de engenharia;
- arquitetura orientada a dominio para evolucao segura do produto.

## Arquitetura

### Frontend Thin (React + Vite)

- Aplicacao SPA leve para orquestracao do fluxo.
- Camada de UI focada em experiencia e produtividade, mantendo regras de negocio no backend.

### Backend Smart (FastAPI + DDD)

- API HTTP em FastAPI com organizacao por dominios e casos de uso.
- Responsavel por autenticacao, validacoes de negocio, execucao de calculos e trilha de auditoria.

### Persistencia (SQLite/JSON)

- Persistencia local-first para execucao controlada em ambientes de desenvolvimento e homologacao.
- Suporte a armazenamento estruturado para continuidade de evolucao para ambientes corporativos.

## Como executar (producao)

Na raiz do monorepo, execute:

```bash
docker compose up -d --build
```

Esse comando sobe os servicos `web`, `api` e `db` em rede compartilhada, com frontend servido por Nginx e backend FastAPI.

## Como acessar

- Frontend: http://localhost:3000
- Swagger (via proxy do frontend): http://localhost:3000/api/docs
- Swagger (acesso direto na API): http://localhost:8000/docs

## Credenciais de teste

Enquanto o fluxo de autenticacao permanece em modo mock no frontend:

- use qualquer e-mail valido na tela de login;
- selecione a role `ADMIN` ou `ENGENHEIRO` para operar o sistema.

## Comandos uteis (desenvolvimento local)

### Executar testes com pytest

```bash
pip install -r requirements-dev.txt
python -m pytest -q
```

### Execucao local sem Docker (opcional)

API:

```bash
cd apps/api
pip install -r requirements.txt
uvicorn apps.api.main:app --reload --port 8000
```

Web:

```bash
cd apps/web
npm install
npm run dev
```

## Observabilidade

- `GET /health`: liveness check simples para runtime e balanceadores.
- `GET /health/deep`: readiness check com validacao de conectividade ao banco.

## Build Desktop (PyWebView + PyInstaller)

Para gerar a versao desktop standalone em um unico comando, execute na raiz:

```bash
python build_desktop.py
```

O script automatiza:

1. build do frontend (`apps/web/dist`);
2. empacotamento do `desktop.py` com PyInstaller incluindo os ficheiros estaticos.

Ao final, o executavel e gerado em `dist/sisPROJETOS.exe` (ou pasta `dist/sisPROJETOS/`, dependendo do modo de build).

### Gerar instalador final (Inno Setup)

1. Abra o ficheiro `build_installer.iss` no Inno Setup Compiler.
2. Compile o script para gerar o instalador `.exe`.

O template ja esta configurado para instalacao sem privilegios de administrador:

- `PrivilegesRequired=lowest`
- `DefaultDirName={localappdata}\sisPROJETOS`

## Estrutura do repositorio

- `apps/api`: backend FastAPI
- `apps/web`: frontend React + Vite
- `packages`: camadas compartilhadas de dominio, aplicacao e infraestrutura
- `docs`: documentacao funcional e tecnica

## Handover

Para apresentacao a stakeholders e transicao para infraestrutura:

1. subir stack com `docker compose up -d --build`;
2. validar `http://localhost:3000` e `http://localhost:3000/api/docs`;
3. validar readiness em `http://localhost:8000/health/deep`.
