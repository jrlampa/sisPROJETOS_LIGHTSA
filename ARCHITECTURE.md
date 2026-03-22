# ARCHITECTURE - sisPROJETOS LIGHT S.A.

## 1. Objetivo Arquitetural
Construir plataforma hibrida (Desktop + SaaS) para gestao de projetos de engenharia da LIGHT, com alta paridade ao Excel, rastreabilidade completa e pipeline tecnico ponta a ponta.

## 2. Principios Arquiteturais
- DDD com contextos delimitados.
- Thin frontend: UI focada em entrada e visualizacao.
- Smart backend: regras de negocio, validacao e calculos.
- Local-first na fase inicial (single-user) com evolucao para sincronizacao cloud.
- Modularidade e limite de complexidade por modulo.
- Contratos explicitos entre contextos e adaptadores de integracao.

## 3. Context Map (DDD)
## 3.1 Intake e Evidencias
Responsabilidade:
- Registrar levantamento de campo, fotos e referencias de validacao.

Entidades:
- Projeto, Evidencia, FonteExterna, ChecklistTriagem.

## 3.2 Engenharia CQT
Responsabilidade:
- Regras de calculo CQT por tipo de projeto.
- Regras especiais para clandestino e cenarios com leitura de trafo.

Entidades:
- CQTAnalise, CentroCarga, TrechoEletrico, Condutor, Transformador.

## 3.3 CAD e Geometria 2.5D
Responsabilidade:
- Receber area de atuacao, coordenadas, geometrias e exportar DXF.

Entidades:
- GeometriaProjeto, Ponto, Segmento, LayerTecnica, ArquivoDXF.

## 3.4 Tracao
Responsabilidade:
- Calcular tracao poste a poste e consolidar resultado mecanico.

Entidades:
- Poste, Vao, ResultadoTracao, EstadoMecanico.

## 3.5 Materiais e Orcamento
Responsabilidade:
- Consolidar materiais, kits e base para lista final.

Entidades:
- Material, Kit, ComposicaoKit, ItemProjeto.

## 3.6 Workflow e Governanca
Responsabilidade:
- Controlar etapas, status, responsavel tecnico e auditoria.

Entidades:
- EtapaProjeto, TransicaoEtapa, HistoricoAuditoria.

## 3.7 Relatorios e Exportacoes
Responsabilidade:
- Gerar PDF, Excel e pacote ZIP final do projeto.

Entidades:
- RelatorioTecnico, ExportacaoExcel, PacoteEntrega.

## 4. Arquitetura Logica (Monorepo)
- apps/api: backend principal (servicos de dominio + APIs).
- apps/web: interface SaaS.
- apps/desktop: app desktop para operacao local.
- packages/domain: entidades e regras de dominio puras.
- packages/application: casos de uso e orquestracao.
- packages/infrastructure: persistencia, adaptadores, IO e integracoes.
- packages/shared: tipos, utilitarios e contratos comuns.

## 5. Contratos Entre Modulos
Padrrao de comunicacao interno:
- Command/Query entre camadas application e domain.
- DTOs versionados para fronteiras com UI, CAD e exportacoes.

Regras:
- Nenhuma regra de negocio no frontend.
- Toda validacao critica no backend.
- Sem dependencias ciclicas entre contexts.

## 6. Persistencia
Fase inicial:
- Banco local para operacao single-user.
- Estrategia de snapshots e historico de mudanca por projeto.

Fase de evolucao:
- Sincronizacao com backend central e estrategia de conflito.

## 7. Integracoes
- CAD/DXF: adaptador de import/export e interoperabilidade 2.5D.
- Planilhas Excel: adaptador de leitura/escrita para paridade funcional.
- Fontes publicas de mapa/rua: uso apenas gratuito/publico.

## 8. Seguranca
- Sanitizacao de entradas em todos os endpoints.
- Validacao de schema em contratos de API.
- Trilha de auditoria para alteracoes de calculo e etapa.
- Politica de minimo privilegio em producao.

## 9. Observabilidade
- Logs estruturados por contexto.
- Correlation id por requisicao/projeto.
- Metricas de performance por modulo de calculo.
- Health checks em backend e servicos criticos.

## 10. Estrategia de Testes
- Unitario no dominio e casos de uso.
- Integracao entre API, persistencia e adaptadores.
- E2E no fluxo operacional completo.
- Testes de regressao de calculo com baseline Excel.

## 11. NFRs (Requisitos Nao Funcionais)
- Confiabilidade de calculo em cenarios criticos.
- Escalabilidade horizontal no backend SaaS.
- Disponibilidade de operacao desktop offline.
- Tempo de exportacao de pacote final previsivel.
- Acessibilidade e legibilidade em interface pt-BR.

## 12. Release Governance
- main: release estavel.
- dev: desenvolvimento e integracao.
- teste: validacao tecnica e experimentacao controlada.

Politica:
- Merge para main somente com qualidade, seguranca e aceite funcional aprovados.
