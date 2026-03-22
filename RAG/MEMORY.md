# RAG MEMORY - sisPROJETOS LIGHT S.A.

## 1. Objetivo
Centralizar contexto minimo obrigatorio para agentes e automacoes, reduzindo tokens por tarefa e preservando consistencia de decisoes tecnicas.

## 2. Fontes de Verdade (ordem de prioridade)
1. Planilhas e documentos de referencia da LIGHT (xlsx/xlsm/pdf).
2. Casos reais de exemplo (normal e clandestino).
3. Regras consolidadas nos legados cqt_light, calculo_tracao_light e plugin_autocad.
4. Decisoes oficiais deste repositorio (ROADMAP, ARCHITECTURE, ADR).

Regra:
- Em caso de conflito, a planilha oficial prevalece.

## 3. Regras Nao Negociaveis
- Excel e fonte de verdade.
- Nao usar dados mockados.
- Somente 2.5D.
- DDD + separacao de responsabilidades.
- Thin frontend / smart backend.
- APIs externas somente publicas ou gratuitas.
- Interface e documentacao em pt-BR.
- Trabalhar em dev.
- main somente release.
- teste para validacao parcial e experimentacao.

## 4. Contexto de Negocio (resumo operacional)
Fluxo alvo:
1. Receber levantamento de campo.
2. Classificar tipo de projeto.
3. Executar CQT e regras complementares.
4. Processar area de atuacao, geometria e DXF.
5. Calcular tracao poste a poste.
6. Gerar pacote final (ZIP, PDF, Excel).

Analise paralela obrigatoria:
- Comparar levantamento com desenho, street view e fotos.

## 5. Politica de Paridade com Excel
Modelo:
- Paridade progressiva por modulo.

Processo:
1. Selecionar golden cases por categoria.
2. Fixar inputs e outputs esperados.
3. Definir tolerancia numerica por campo.
4. Versionar baseline de comparacao.
5. Bloquear avanco de fase sem meta de paridade.

## 6. Estrategia de Economia de Tokens
Ao iniciar qualquer tarefa, usar este checklist curto:
1. Ler RAG/MEMORY.md.
2. Ler somente secoes relevantes de ROADMAP.md e ARCHITECTURE.md.
3. Consultar ADRs apenas se houver decisao relacionada.
4. Evitar releitura integral de arquivos grandes sem necessidade.
5. Registrar aprendizado em resumo objetivo (maximo 5 bullets).

Padrao de resposta de agente:
- Primeiro: decisao executiva em 1 a 3 linhas.
- Segundo: somente contexto estritamente necessario.
- Terceiro: proximas acoes objetivas.

## 7. Guardrails para Agentes
- Nao inferir regra tecnica sem evidencia.
- Nao alterar regra de calculo sem teste de regressao.
- Nao introduzir dependencia paga.
- Nao mover para main sem gate de qualidade.

## 8. Estrutura de Memoria Recomendada
Arquivos no RAG:
- RAG/MEMORY.md: regras globais e contexto fixo.
- RAG/golden-cases.md: lista de casos de validacao.
- RAG/decisions-log.md: decisoes e impactos.
- RAG/data-sources.md: mapeamento de fontes e confiabilidade.

## 9. Registro de Decisoes Atuais
- Plataforma hibrida (Desktop + SaaS) desde o inicio.
- Fase inicial sem login para acelerar entrega.
- Login social Google/Microsoft e convidado leitura para producao.
- Integracao CAD orientada pelo plugin_autocad.
- Reuso tecnico de CQT e tracao dos legados.

## 10. Quando Atualizar Este Arquivo
Atualizar quando houver:
- Nova regra de negocio validada.
- Mudanca de processo operacional.
- Divergencia confirmada entre sistema e planilha.
- Nova decisao arquitetural aprovada.

Formato de entrada de atualizacao:
- Data
- Contexto
- Decisao
- Impacto
- Acao imediata
