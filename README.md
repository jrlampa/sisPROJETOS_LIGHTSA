# sisPROJETOS LIGHT S.A.

Plataforma de gestao de projetos de rede para a concessionaria LIGHT S.A., com estrategia hibrida (Desktop + SaaS), paridade progressiva com Excel e foco em automacao do fluxo tecnico.

## Documentos Base
- ROAMAP.MD
- ARCHITECTURE.md
- RAG/MEMORY.md

## Estrutura Inicial
- apps/api: backend FastAPI
- apps/web: frontend React + Vite
- apps/desktop: shell desktop (fase seguinte)
- packages/*: camadas DDD compartilhadas

## Como subir local com Docker
1. Ajustar variaveis no .env.example conforme necessario.
2. Executar:

```bash
docker compose up --build
```

## Como subir frontend local
```bash
cd apps/web
npm install
npm run dev
```

## Como subir API local
```bash
cd apps/api
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

## Regras de Branch
- main: release estavel
- dev: desenvolvimento
- teste: validacao paralela e experimentos
