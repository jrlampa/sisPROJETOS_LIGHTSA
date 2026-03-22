# ROAMAP - sisPROJETOS LIGHT S.A.

## 1. Visao Executiva
Este documento define o plano de execucao enterprise do sisPROJETOS LIGHT S.A., plataforma hibrida (Desktop + SaaS) para gerenciar ciclo completo de projetos de rede de distribuicao.

Objetivo central:
- Reproduzir o comportamento operacional das planilhas Excel existentes (fonte de verdade).
- Unificar fluxo: levantamento -> CQT -> CAD/DXF -> tracao -> pacote final -> lista de material.
- Garantir ganho de produtividade, rastreabilidade e qualidade tecnica sem aumentar custo de operacao.

Principios nao negociaveis:
- Branch principal de desenvolvimento: dev.
- Sem dados mockados.
- Modelagem 2.5D (nao 3D).
- Modularidade, responsabilidade unica, clean code.
- Thin frontend e smart backend.
- Docker first.
- DDD orientando estrutura.
- UI e UX em pt-BR.
- APIs externas somente publicas ou gratuitas (zero custo).

## 2. Escopo do Produto
## 2.1 Escopo Funcional Faseado
1. Intake e triagem de levantamento de campo.
2. Motor CQT com regras por tipo de projeto (incluindo clandestino).
3. Integracao CAD/DXF para area de atuacao e geometria de projeto.
4. Calculo de tracao poste a poste.
5. Workflow de etapas com trilha de auditoria.
6. Exportacao de pacote final (ZIP tecnico), PDF e Excel padrao.
7. Captura e validacao de coordenadas geograficas no sistema.

## 2.2 Fora de Escopo Inicial
- Login em desenvolvimento local (sera habilitado antes da producao).
- Integracoes pagas.
- Colaboracao multiusuario em tempo real na fase inicial.

## 3. Estrategia de Entrega
Modelo de release:
- main: apenas versoes estaveis e prontas para release.
- dev: desenvolvimento, integracao e testes.
- teste: experimentacao de features parciais e iteracoes de IA.

Abordagem:
- Paridade progressiva com Excel por modulo.
- Casos dourados por tipo de projeto para validar comportamento.
- Entregas curtas com criterio de aceite mensuravel.

## 4. Ondas de Implementacao
## Onda 0 - Fundacao (Semana 1)
Entregas:
- Documentos enterprise: ROAMAP, ARCHITECTURE e RAG/MEMORY.
- Monorepo base (api, web, desktop, packages).
- Baseline de qualidade: .gitignore, .dockerignore, docker-compose.
- Catalogo inicial de decisoes arquiteturais (ADR).

Aceite:
- Repositorio em dev com baseline operacional.
- Regras de branch e qualidade publicadas.

## Onda 1 - Nucleo de Dominio (Semanas 2 a 5)
Entregas:
- Bounded contexts e entidades centrais implementadas.
- Persistencia local-first para fase single-user.
- API de projetos e etapas.
- Pipeline de ingestao de evidencias (fotos, anotações, metadados).

Aceite:
- Criar e rastrear projeto completo com historico.
- Validacao de entradas e sanitizacao de dados ativa.

## Onda 2 - CQT e Regras Tecnicas (Semanas 6 a 9)
Entregas:
- Integracao do motor CQT reaproveitando ativos do cqt_light.
- Regras especiais de clandestino e leitura de trafo.
- Validacao contra limites de engenharia.

Aceite:
- Casos dourados de CQT com equivalencia aos resultados de referencia.

## Onda 3 - CAD/DXF e Geometria 2.5D (Semanas 10 a 13)
Entregas:
- Importacao/exportacao DXF basica.
- Integracao de referencia do plugin AutoCAD.
- Persistencia de coordenadas e geometria de projeto.

Aceite:
- Fluxo de area de atuacao com dados de arruamento e desenho tecnico exportavel.

## Onda 4 - Tracao e Validacao Mecanica (Semanas 14 a 17)
Entregas:
- Integracao do motor de tracao reaproveitando ativos do calculo_tracao_light.
- Resultado poste a poste com status tecnico.
- Checklist de conformidade de saida.

Aceite:
- Casos dourados de tracao aprovados com tolerancia definida.

## Onda 5 - Exportacoes e Pacote Final (Semanas 18 a 20)
Entregas:
- Geracao PDF tecnico.
- Exportacao Excel baseado nas planilhas padrao.
- Empacotamento ZIP com todos os artefatos.

Aceite:
- Pipeline final reproduz o processo atual sem perda de informacao.

## Onda 6 - Producao e Governanca (Semanas 21 a 24)
Entregas:
- Login social Google e Microsoft.
- Perfil convidado somente leitura.
- Observabilidade, hardening de seguranca e readiness de release.

Aceite:
- Checklist de producao aprovado e trilha dev->teste->main operacional.

## 5. Arquitetura de Trabalho por Papeis
- Tech Lead (orquestrador): garante direcao tecnica, qualidade e decisao de trade-offs.
- Dev Fullstack Senior (principal coder): implementacao de dominio e integracoes.
- DevOps/QA: CI/CD, testes unitarios e E2E, cobertura e seguranca.
- UI/UX Designer: telas Excel-like em pt-BR, usabilidade operacional.
- Estagiario Criativo: alternativas de automacao e ganho de produtividade fora da caixa.

## 6. Qualidade, Testes e Metricas
Metas:
- Cobertura 100% para 20% dos modulos de maior impacto.
- Cobertura minima 80% para os demais modulos.
- E2E cobrindo fluxo critico ponta a ponta.

Gates obrigatorios:
- Lint, testes, cobertura e scans de seguranca antes de merge para dev.
- Evidencia de paridade por modulo antes de promover para teste.

KPIs de produto:
- Tempo medio por projeto.
- Taxa de retrabalho por divergencia tecnica.
- Percentual de paridade validada por modulo.
- Tempo de geracao do pacote final.

## 7. Riscos e Mitigacoes
1. Risco: divergencia entre regra real e interpretacao tecnica.
Mitigacao: Excel como fonte de verdade + golden cases assinados.

2. Risco: dependencia excessiva de ferramenta CAD.
Mitigacao: camada de abstracao de geometria e contrato de exportacao.

3. Risco: regressao em calculos criticos.
Mitigacao: testes de regressao por baseline numerica.

4. Risco: aumento de custo operacional.
Mitigacao: politica zero custo em APIs externas e stack open-source.

## 8. Criterios de Autorizacao LIGHT S.A.
Este plano esta pronto para avaliacao executiva quando:
- Escopo e fases estiverem aprovados por engenharia e operacao.
- Casos dourados de validacao forem definidos e priorizados.
- Responsabilidades e governanca de branch forem formalizadas.
- Marco da Onda 0 estiver concluido e versionado na branch dev.
