# ARCHITECTURE - sisPROJETOS LIGHT S.A.

## 1. Objetivo Arquitetural
Construir uma plataforma hibrida (Desktop + SaaS) para o ciclo completo de projetos da LIGHT, com paridade progressiva ao Excel, automacao de engenharia e rastreabilidade ponta a ponta.

## 2. Principios Arquiteturais
- DDD com bounded contexts explicitos.
- Thin frontend e smart backend.
- Local-first na fase inicial, cloud-ready na evolucao.
- Contratos versionados entre camadas.
- Sem acoplamento forte entre modulos de negocio e integracoes externas.
- Regra de modularizacao quando arquivo exceder 500 linhas.
- 2.5D como padrao geometrico.

## 3. Stack Tecnologica Alvo
## 3.1 Backend Python
- Python 3.11+.
- FastAPI para API HTTP e validacao de contratos.
- Pydantic v2 para schema validation.
- SQLAlchemy 2.x para ORM e repositorios.
- Alembic para migracoes.
- PostgreSQL para SaaS e SQLite para modo local single-user.
- Redis opcional para cache e rate limit em ambientes server.
- Structlog para logs estruturados.
- Pytest para testes unitarios e de integracao.

## 3.2 Frontend React (Excel-like)
- React 18 + Vite.
- TanStack Query para estado assicrono e cache de API.
- Zustand para estado local de fluxo (etapas e formularios).
- React Data Grid para experiencia tabular estilo planilha.
- React Hook Form + Zod para validacao de entrada.
- Playwright para E2E.
- i18n em pt-BR desde a base do projeto.

## 3.3 Desktop
- Electron para shell desktop na fase inicial.
- IPC restrito por contrato de mensagens (schema validado).
- Armazenamento local com SQLite e sincronizacao futura.

## 3.4 CAD e DXF (2.5D)
- ezdxf para leitura/escrita DXF.
- pyproj para transformacoes de coordenadas.
- shapely para operacoes geometricas.
- GeoJSON como formato intermediario interno entre UI e motor DXF.
- Camada adaptadora para interoperar com referencia do plugin AutoCAD.

## 4. Context Map (DDD)
## 4.1 Intake e Evidencias
Responsabilidade:
- Ingestao do levantamento, evidencias e dados de comparacao (fotos, street view, anotacoes).

Entidades:
- Projeto, Evidencia, FonteExterna, ChecklistTriagem.

## 4.2 Engenharia CQT
Responsabilidade:
- Regras de CQT por tipo de projeto com comportamento aderente a planilhas.

Entidades:
- CQTAnalise, CentroCarga, TrechoEletrico, Condutor, Transformador.

## 4.3 CAD e Geometria 2.5D
Responsabilidade:
- Gerenciar area de atuacao, geometria, layers e artefatos DXF.

Entidades:
- GeometriaProjeto, Ponto, Segmento, LayerTecnica, ArquivoDXF.

## 4.4 Tracao
Responsabilidade:
- Calcular esforcos e status poste a poste.

Entidades:
- Poste, Vao, ResultadoTracao, EstadoMecanico.

## 4.5 Materiais e Orcamento
Responsabilidade:
- Consolidar kits, materiais e saida para lista de material.

Entidades:
- Material, Kit, ComposicaoKit, ItemProjeto.

## 4.6 Workflow e Governanca
Responsabilidade:
- Orquestrar etapas, transicoes, criterios de aceite e auditoria.

Entidades:
- EtapaProjeto, TransicaoEtapa, HistoricoAuditoria.

## 4.7 Relatorios e Exportacoes
Responsabilidade:
- Gerar PDF, Excel e pacote ZIP final.

Entidades:
- RelatorioTecnico, ExportacaoExcel, PacoteEntrega.

## 5. Arquitetura Logica do Monorepo
- apps/api: endpoints, casos de uso e orchestration facade.
- apps/web: interface operacional web.
- apps/desktop: shell local e recursos offline.
- packages/domain: entidades, value objects e regras puras.
- packages/application: use cases, orchestrators e policies.
- packages/infrastructure: repositorios, drivers, adaptadores e integrações.
- packages/shared: tipos comuns, erros e utilitarios.

## 6. Arquitetura do Backend (Camadas)
Camadas:
1. API layer (FastAPI routers): entrada e saida HTTP.
2. Application layer: casos de uso e regras de fluxo.
3. Domain layer: entidades, agregados e servicos de dominio.
4. Infrastructure layer: banco, arquivos, DXF, excel adapters, clientes externos.

Regras:
- API nao acessa banco diretamente.
- Regras de negocio nao ficam no frontend.
- Integration adapters nao contaminam dominio com detalhes de framework.

## 7. Fluxo Tecnico Principal
1. Intake recebe evidencias e metadados.
2. Engine CQT processa analise e validacoes.
3. Motor CAD consolida coordenadas e geometrias para DXF.
4. Engine de tracao calcula resultado mecanico por trecho/poste.
5. Modulo de exportacao gera PDF, Excel e ZIP.
6. Workflow atualiza etapa e registra auditoria.

## 8. Contratos e Integracoes
Contratos internos:
- DTOs versionados (v1, v2) para evitar breaking changes.
- Eventos de dominio para mudancas de etapa e resultado de calculo.

Integracoes:
- Excel adapter (openpyxl/pandas + motor legado de formulas) para paridade.
- DXF adapter (ezdxf + geo conversion) para interoperabilidade CAD.
- Mapas publicos/gratuitos para referencia de arruamento.

## 9. Persistencia e Estrategia de Dados
Fase inicial:
- SQLite local por projeto para operacao single-user.

Fase SaaS:
- PostgreSQL centralizado, com estrategia de sincronizacao e reconciliacao.

Padroes de dados:
- Audit trail por entidade critica.
- Idempotencia em importacoes.
- Versionamento de baseline Excel por tipo de projeto.

## 10. Seguranca
- Validacao de schema em todos os endpoints.
- Sanitizacao de entrada e normalizacao de payload.
- Controle de autorizacao por role na fase de producao.
- Protecao contra abuso com rate limiting.
- Segredo e credenciais fora do codigo fonte.

## 11. Observabilidade
- Logging estruturado com correlation-id por projeto.
- Health checks por servico.
- Metricas de latencia por modulo critico.
- Tracing de fluxo CQT -> DXF -> Tracao -> Exportacao.

## 12. Testes e Qualidade
- Unit tests para dominio e calculos.
- Integration tests para API + banco + adaptadores.
- E2E para fluxo completo do usuario.
- Regressao numerica comparando saidas com golden cases do Excel.

Metas:
- 100% de cobertura no top 20% de impacto.
- >=80% de cobertura nos demais modulos.

## 13. NFRs
- Confiabilidade de calculo em cenarios criticos.
- Tempo de resposta adequado para operacao de escritorio.
- Robustez de exportacao em lote.
- Compatibilidade com ambiente Windows corporativo.
- Evolucao para operacao multiusuario sem refatoracao estrutural.

## 14. Release Governance
- main: releases estaveis.
- dev: desenvolvimento e integracao.
- teste: homologacao parcial e features em validacao.

Politica de merge:
- Sem merge para main sem testes, seguranca e aceite funcional.
