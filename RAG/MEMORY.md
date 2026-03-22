# RAG MEMORY - sisPROJETOS LIGHT S.A.

## 1. Finalidade
Este arquivo centraliza memoria de contexto para agentes e automacoes, reduzindo custo de tokens e mantendo consistencia tecnica.

## 2. Fontes de Verdade
Prioridade de confiabilidade:
1. Planilhas e arquivos de referencia LIGHT (Excel, xlsm, xlsx, documentos tecnicos e padroes construtivos).
2. Casos reais de exemplo LIGHT (normal e clandestino).
3. Regras tecnicas consolidadas nos projetos cqt_light, calculo_tracao_light e plugin_autocad.
4. Decisoes registradas neste repositorio (ADR e documentos oficiais).

## 3. Regras Operacionais Fixas
- Excel e fonte de verdade para comportamento de calculo.
- Nao usar dados mockados.
- Usar 2.5D, nao 3D.
- Aplicar DDD e separacao de responsabilidades.
- Garantir modularidade e clean code.
- Priorizar thin frontend e smart backend.
- APIs externas somente gratuitas/publicas.
- UI/UX em pt-BR.
- Branch de trabalho: dev.
- main somente para release estavel.
- teste para validacoes paralelas e experimentos.

## 4. Conhecimento de Dominio (Resumo)
Fluxo operacional alvo:
1. Receber levantamento e classificar tipo de trabalho.
2. Executar CQT e validar centro de carga, transformador, recondu toramento, extensao e subdivisao.
3. Tratar regra de clandestino e necessidade de leitura de trafo.
4. Adquirir area em DXF, projetar no CAD com arruamento.
5. Calcular tracao poste a poste.
6. Gerar pacote ZIP para lista de material.

Analise paralela obrigatoria:
- Comparar levantamento, desenho, street view e fotos enviadas.

## 5. Politica de Paridade
Modelo:
- Paridade progressiva por modulo.

Metodologia:
- Definir golden cases por tipo de projeto.
- Comparar outputs de calculo com tolerancia explicita.
- Bloquear promocao de fase sem atingir criterio minimo.

## 6. Estrutura de Contexto para Agentes
Ao iniciar uma task, agente deve:
1. Ler este arquivo.
2. Verificar documentos ROAMAP e ARCHITECTURE.
3. Consultar pasta docs/adr para decisoes.
4. Registrar novas decisoes e aprendizados validos.

## 7. Registro de Decisoes Iniciais
- Plataforma sera hibrida (Desktop + SaaS) desde o inicio.
- Fase inicial sem login para acelerar desenvolvimento.
- Login social Google/Microsoft e convidado leitura em fase de producao.
- Integracao CAD tera referencia no projeto plugin_autocad.
- Reuso de modulos CQT e Tracao dos projetos legados e obrigatorio.

## 8. Atualizacao de Memoria
Critrios para atualizar:
- Nova regra de negocio validada.
- Mudanca de requisito operacional.
- Descoberta de divergencia entre sistema e Excel.
- Decisao arquitetural aprovada.

Formato de registro:
- Data
- Contexto
- Decisao
- Impacto
- Acoes decorrentes
