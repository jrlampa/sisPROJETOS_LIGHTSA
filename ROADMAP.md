# ROADMAP - sisPROJETOS LIGHT S.A.

## 1. Visao Executiva
O sisPROJETOS LIGHT S.A. sera uma plataforma hibrida (Desktop + SaaS) para gestao integral de projetos de rede de distribuicao, com foco em produtividade operacional, paridade com planilhas de referencia e conformidade tecnica.

Objetivos estrategicos:
- Reduzir tempo total de elaboracao de projeto sem perda de qualidade.
- Eliminar retrabalho por divergencia entre levantamento, desenho e calculo.
- Automatizar CQT, tracao, exportacoes e montagem do pacote tecnico final.
- Manter o Excel como fonte de verdade durante toda a fase de transicao.

Principios fixos:
- Branch de desenvolvimento: dev.
- Sem uso de dados mockados.
- 2.5D em toda modelagem geometrica.
- DDD, modularidade e responsabilidade unica.
- Thin frontend / smart backend.
- Docker first e stack de custo zero.
- Interface 100% pt-BR.

## 2. Escopo
## 2.1 Escopo Funcional
1. Triagem e classificacao de levantamento de campo.
2. CQT com regras por tipo de projeto (incluindo clandestino).
3. Importacao/exportacao e processamento CAD/DXF para area de atuacao.
4. Calculo de tracao poste a poste.
5. Workflow de etapas com trilha de auditoria.
6. Exportacoes em PDF e Excel padrao.
7. Empacotamento ZIP com todos os artefatos de entrega.
8. Captura e validacao de coordenadas no sistema.

## 2.2 Fora de Escopo Inicial
- Login durante desenvolvimento inicial.
- Integracoes pagas.
- Colaboracao multiusuario em tempo real na primeira entrega.

## 3. Estrategia de Entrega
Modelo de branch:
- main: somente releases estaveis e prontas.
- dev: implementacao e integracao oficial.
- teste: features em validacao parcial e experimentos IA.

Estrategia de paridade:
- Paridade progressiva por modulo.
- Golden cases por tipo de projeto.
- Gate de aceite por tolerancia numerica definida.

## 4. Ondas de Implementacao
## Onda 0 - Fundacao (concluida)
Entregas:
- ROADMAP, ARCHITECTURE e RAG/MEMORY.
- Baseline de monorepo e docker.
- Regras de governanca e ADR inicial.

## Onda 1 - Nucleo de Dominio e Workflow (Sprint 1 e 2)
Entregas:
- Entidades de Projeto, Etapas, Evidencias e Checklist de Triagem.
- API de ciclo de vida de projeto.
- Auditoria de alteracoes por etapa.
- Persistencia local-first para single-user.

Criterios de aceite:
- Criar projeto, mover etapas e registrar historico completo.
- Validacao de dados de entrada e sanitizacao ativa.

## Onda 2 - Motor CQT (Sprint 3 e 4)
Entregas:
- Integracao do nucleo CQT legado com isolamento por camada de aplicacao.
- Regras de clandestino e leitura de trafo.
- Validacao de centro de carga, substituicao, recondu toramento e extensao.

Criterios de aceite:
- Resultados batendo com planilhas de referencia em golden cases CQT.

## Onda 3 - CAD/DXF e Geometria 2.5D (Sprint 5 e 6)
Entregas:
- Pipeline de ingestao de area de atuacao e arruamento.
- Importacao/exportacao DXF basica.
- Persistencia de geometrias e coordenadas.

Criterios de aceite:
- Projeto com geometria validada e exportavel para fluxo tecnico.

## Onda 4 - Tracao Poste a Poste (Sprint 7 e 8)
Entregas:
- Integracao do motor de tracao legado.
- Resultado mecanico por poste e trecho.
- Alertas de nao conformidade tecnica.

Criterios de aceite:
- Golden cases de tracao aprovados com tolerancia numerica definida.

## Onda 5 - Relatorios e Pacote Final (Sprint 9)
Entregas:
- PDF tecnico automatizado.
- Exportacao Excel no formato das planilhas padrao.
- Geracao de pacote ZIP final por projeto.

Criterios de aceite:
- Pipeline final completo reproduzindo o processo atual.

## Onda 6 - Readiness de Producao (Sprint 10)
Entregas:
- Login social Google e Microsoft.
- Perfil convidado somente leitura.
- Hardening de seguranca, monitoramento e release governance.

Criterios de aceite:
- Checklist de producao aprovado.
- Fluxo dev -> teste -> main operacional.

## 5. Backlog Inicial Priorizado (Top 12)
1. Modelagem de entidades centrais de projeto.
2. API de criacao e transicao de etapas.
3. Registro de evidencias do levantamento.
4. Caso de uso de triagem tecnica.
5. Integracao inicial de calculo CQT.
6. Regras de clandestino no CQT.
7. Pipeline de coordenadas e geometria.
8. Exportacao DXF basica.
9. Integracao inicial de tracao.
10. Exportacao Excel padrao.
11. Geracao PDF tecnico.
12. Empacotamento ZIP final.

## 6. Qualidade e Testes
Metas:
- Cobertura 100% para 20% dos modulos de maior impacto.
- Cobertura minima 80% para os demais.
- E2E cobrindo o fluxo critico ponta a ponta.

Gates:
- Lint + unit + integracao + E2E + seguranca antes de merge.
- Evidencia de paridade por modulo antes de promover para teste.

## 7. Indicadores de Sucesso
- Tempo medio de elaboracao de projeto.
- Taxa de retrabalho por divergencia.
- Percentual de paridade validada com Excel.
- Tempo medio de geracao de pacote final.
- Taxa de falha em exportacoes.

## 8. Riscos e Mitigacoes
1. Divergencia de regra tecnica.
Mitigacao: planilha como fonte de verdade + golden cases versionados.

2. Acoplamento com ferramentas CAD.
Mitigacao: adaptadores e contratos independentes de fornecedor.

3. Regressao em calculos criticos.
Mitigacao: testes de regressao numerica em CI.

4. Complexidade de fusao dos legados.
Mitigacao: migracao por contextos e anti-corruption layer.

5. Risco de custo externo.
Mitigacao: somente APIs publicas/gratuitas.

## 9. Governanca de Time (Papeis)
- Tech Lead: direcao tecnica, qualidade, arquitetura.
- Fullstack Senior: implementacao principal.
- DevOps/QA: pipelines, testes e seguranca.
- UI/UX: experiencia Excel-like em pt-BR.
- Estagiario Criativo: propostas de automacao e produtividade.

## 10. Marco de Aprovacao Enterprise
Este roadmap esta pronto para apresentacao executiva quando:
- Escopo e ondas forem aceitos por engenharia e operacao.
- Golden cases forem priorizados e publicados.
- Responsabilidades por papel e branch forem formalizadas.
- Onda 1 iniciar com backlog priorizado e criterios de aceite claros.
