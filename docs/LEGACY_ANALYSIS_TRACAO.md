# Análise Exploratória — Projeto Legado `calculo_tração_light`

> **Tipo:** Spike Exploratório (Read-Only)  
> **Data:** 2026-03-23  
> **Fonte:** `C:\Users\jonat\OneDrive - IM3 Brasil\utils\myworld\calculo_tração_light`  
> **Workbook de referência:** `AP COSMO LDA NOVA 03 - PROJETO 5 - POSTE 1D.xlsm`  
> **Branch destino:** `dev` (sisPROJETOS_LIGHTSA)

---

## 1. Arquitetura do Legado

### 1.1 Stack Tecnológica

| Camada        | Tecnologia                                                         |
|---------------|--------------------------------------------------------------------|
| Frontend      | React 18 + Vite, Tailwind CSS                                      |
| Backend       | FastAPI (Python 3.11), Pydantic v2, structlog                      |
| Banco de Dados| PostgreSQL via Supabase, SQLAlchemy, Alembic (migrações)           |
| Cache         | Redis (rate-limiting + cache de respostas)                         |
| Infra         | Docker multi-stage + Docker Compose                                |
| Segurança     | JWT Auth, Bandit (SAST), Rate-limit por IP                         |
| Observabilidade| Prometheus + Instrumentator, `/health/deep`                       |
| Testes        | pytest (46+ testes), Playwright (E2E)                              |

### 1.2 Organização do Backend (DDD)

```
python/
├── api/
│   ├── main.py               ← Ponto de entrada FastAPI, middlewares globais
│   ├── schemas.py            ← Pydantic v2: CalculoInput / CalculoOutput / QDTInput / QDTOutput
│   └── routers/
│       ├── calculo.py        ← POST /calcular  +  POST /calcular/qdt
│       ├── projetos.py       ← CRUD de projetos e pontos
│       ├── ai_assistant.py   ← Integração Ollama (LLM local)
│       ├── cache.py          ← Endpoints de gestão de cache Redis
│       ├── monitoring.py     ← Métricas e health check
│       ├── admin.py          ← Endpoints administrativos
│       └── public.py         ← Endpoints sem autenticação
├── translated/
│   ├── ponto_blocks.py       ← ENGINE PRINCIPAL: transcrição fiel das 289 fórmulas do Excel
│   ├── plan1_tables.py       ← Tabelas de lookup (cabos, redes, postes, BTZero)
│   ├── qdt_blocks.py         ← Cálculo de Queda de Tensão (QDT)
│   ├── plan4_selectors.py    ← Relacionamento rede → cabos disponíveis
│   └── solver_coin.py        ← Solver auxiliar
├── services/
│   ├── projeto_service.py    ← Orquestração de projetos
│   └── ai_service.py         ← IA assistente
├── repositories/
│   └── projeto_repository.py ← Isolamento da camada de dados
├── models/
│   └── projeto.py            ← Pydantic schemas de persistência
├── alembic/
│   └── versions/
│       ├── ff3afec586b4_initial_schema.py  ← Schema inicial completo
│       └── d55ff4ae541f_create_activity_logs.py
├── core/
│   ├── config.py, exceptions.py, logging.py, ratelimit.py
└── tests/
    ├── test_parity_excel.py  ← Testes de paridade com o workbook (golden values)
    ├── test_api_validation.py
    ├── test_fuzzy_inputs.py
    ├── test_qdt_parity.py
    └── ...
```

### 1.3 Organização do Frontend

```
src/
├── App.jsx                   ← Orquestrador principal (etapas: cabecalho → calculo)
├── features/calculo/
│   └── formConfig.js         ← Definição de campos por seção (CAMPOS_MT, CAMPOS_BTZ, CAMPOS_RAL)
├── hooks/
│   ├── useCalculo.js         ← Debounce 600ms + AbortController → POST /api/calcular
│   ├── useFormState.js       ← Estado completo do formulário (cabecalho, poste, mt1…ral)
│   ├── useConfigState.js     ← Catálogos de redes/cabos/postes via GET /api/config
│   ├── useValidation.js      ← Motor de validação genérico com regras configuráveis
│   ├── usePersistenciaCalculo.js ← Fila de persistência com retry exponencial
│   └── useUndoStack.js       ← Stack de undo local por ponto (max 10, TTL 5min)
├── services/
│   └── calculoApi.js         ← fetch wrappers: buildCalculoRequest, buildSalvarCalculoPayload, CRUD projetos
└── components/
    ├── relogio/RelogioAngulos.jsx   ← Relógio vetorial SVG (diagrama polar)
    ├── secao/DiagramaPoste.jsx      ← Diagrama 2D do poste com níveis MT1/MT2/BT
    ├── tabela/TabelaCarga.jsx       ← Tabela de cargas admissíveis por ângulo α
    └── actionBar/MobileActionBar.jsx ← Barra contextual mobile (Confirmar/Reenviar/Próximo)
```

### 1.4 Modelo de Dados (Banco)

```
projetos          (id UUID, orgao, ns, nome, endereco, estudado_por, matricula, data_estudo, owner_id)
  └── pontos      (id UUID, projeto_id, ponto, tipo_poste, modelo_poste)
        ├── niveis_calculo   (id UUID, ponto_id, nivel [MT1/MT2/BT/BTZ/RAL], altura_poste, altura_ancoragem)
        │     └── travessias (id UUID, nivel_id, posicao [1-4], tipo_rede, tipo_cabo, vao, flecha, angulo, qtd_ligacoes, qtd_cabos)
        └── resultados_calculo (ponto_id PK: mt1_tracao, mt1_angulo, ..., total_tracao, total_angulo, poste_ecc, calculado_em)

cabos      (id, nome, diametro, peso)
redes      (id, tipo, descricao)
postes     (id, tipo, modelo, altura_m, carga_admissivel_dan)
normas_regras (id, categoria, titulo, descricao, regra_tecnica, aplicavel_a, fonte_referencia)
```

### 1.5 Princípio Arquitetural Central

> **"Thin Frontend / Smart Backend"** — Toda a lógica matemática reside estritamente no backend Python. O frontend é responsável apenas por capturar inputs, exibir resultados e orquestrar a UX.

---

## 2. Regras Matemáticas e Físicas

### 2.1 Constante de Vento

```python
WIND_COEFF = 0.00471 * 60**2  # = 16.956 daN/m²
```

Derivada da norma ABNT: pressão dinâmica do vento com velocidade de referência 60 km/h.  
Aplicada uniformemente em **todos os blocos** (MT1, MT2, BT, BTZero, Ramais).

### 2.2 Cálculo por Travessia (Bloco MT1, MT2 e BT T2–T4)

Para cada travessia ativa `(tipo_rede, tipo_cabo, vao, flecha, angulo)`:

**Lookup de propriedades do cabo:**
```
peso_linear  = lookup_cable_peso(tipo_cabo)    [kgf/m]
diam         = lookup_cable_diam(tipo_cabo)    [m]
qtd_cabos    = lookup_rede_qtd_cabos(tipo_rede) [1 ou 3]
```

**Massa cordoalha (mensageiro) — apenas rede Compacta (MT) ou Armado (BT):**
```
peso_extra = 0.407  (kgf/m, Cordoalha de aço 3/8")
diam_extra = 0.0095 (m)
```

**Totais de diâmetro e peso:**
```
diam_total  = qtd_cabos * diam  + diam_extra
peso_total  = peso_linear * qtd_cabos + peso_extra
```

**Componentes de vento** (ROUND 2 casas decimais — fiel ao Excel):
```
ang_rad  = angulo * π / 180
wind_H   = ROUND(WIND_COEFF * vao/2 * diam_total * cos(ang_rad), 2)
wind_V   = ROUND(WIND_COEFF * vao/2 * diam_total * sin(ang_rad), 2)
```

**Catenária** (tensão horizontal pelo método parabólico):
```
catenary = (peso_total * vao²) / (8 * flecha)
cat_H    = ROUND(catenary * cos(ang_rad), 2)
cat_V    = ROUND(catenary * sin(ang_rad), 2)
```

### 2.3 Resultante do Nível (Composição Vetorial de Forças)

```
resultante = √(ΣcatH² + ΣcatV²) + √(ΣwindH² + ΣwindV²)
```

onde as somas abrangem as 4 travessias do nível.  
Esta fórmula soma **separadamente** a norma da catenária e a norma do vento (não compõe os vetores juntos).

### 2.4 Ângulo do Nível

Fórmula Excel ATAN (não ATAN2) com tratamento de quadrantes:

```python
def _angle_formula(sum_H, sum_V):
    if sum_H == 0:
        return ROUNDUP(atan(sum_V / 1) * 180/π, 0)   # evita divisão por zero
    angle = atan(sum_V / sum_H) * 180/π
    if sum_H < 0:
        angle += 180                                   # 2º e 3º quadrante
    return angle                                       # [0°, 360°)
```

> **Atenção:** Esta fórmula **não usa `atan2`** — usa `atan` simples com correção manual. A distinção é crítica: `atan2` retorna `(-180°, +180°]`, enquanto esta fórmula retorna `[0°, 360°)` para sum_H < 0.

O ângulo é calculado **apenas sobre os componentes da catenária** (cat_H / cat_V), não sobre o vento.

### 2.5 Normalização para a Ponta do Poste (Tip Force)

```
F_tip = resultante * altura_ancoragem / (altura_poste * 0.9 − 0.6 − 0.1)
```

- `altura_poste * 0.9` — 10% enterrado no solo
- `− 0.6 − 0.1` — reservas de topo: 60cm (fixação) + 10cm (ponta)
- O denominador representa o **comprimento efetivo livre do poste**

### 2.6 Regras de Compartilhamento BT ↔ MT1 (Critical!)

O bloco BT introduz as regras mais críticas de paridade com o Excel:

```
BT T1 cabo + propriedades    = MT1 T1 (C71=C19 … C75=C23)
BT T1 dados de vento/catenária = MT1 T1 (C79=C27 … C83=C31)
BT T1 geometria (vao/flecha/angulo/alturaPoste) = MT1 T1 (C66=C14 … C69=C17)
BT T2 geometria (vao/flecha/angulo) = MT1 T2 (F66=F14, F67=F15, F68=F16)

BT resultante (C84) = MT1 resultante (C32)   ← regra ABSOLUTA
```

**Consequência prática:** Os campos `vao`, `flecha`, `angulo`, `altura_poste` inseridos pelo utilizador no bloco BT para T1 e T2 são **ignorados** pelo motor de cálculo. Apenas `altura_ancoragem` de cada travessia BT é próprio.

A força normalizada BT usa a altura do poste de MT1 T1:
```
F_tip_BT = MT1_resultante * BT_T1_altura_ancoragem / (MT1_T1_altura_poste * 0.9 − 0.7)
```

### 2.7 Bloco BTZero (Redes de Ligação)

Segue lógica piecewise para número de fios por ligação:

```
qtd_fios = piecewise(qtd_ligacoes):
    < 3  → 1 fio
    < 8  → 3 fios
    < 20 → 5 fios
    < 38 → 7 fios
    < 61 → 9 fios
    ≥ 61 → 11 fios

diam_total  = qtd_fios * 0.0115  + 0.0095   (m)
peso_total  = qtd_ligacoes * 0.15 + 0.407   (kgf/m)
```

Constantes físicas (Cordoalha de aço 3/8" como mensageiro):
- `BTZERO_PESO_POR_LIGACAO = 0.15 kgf/m`
- `BTZERO_PESO_MENSAGEIRO  = 0.407 kgf/m`
- `BTZERO_DIAM_POR_FIO     = 0.0115 m`
- `BTZERO_DIAM_MENSAGEIRO  = 0.0095 m`

### 2.8 Bloco Ramais (RAL)

Sem lookup de `tipo_rede` — `qtd_cabos` é inserido diretamente pelo utilizador:

```
diam_total = qtd_cabos * diam(tipo_cabo)
peso_total = peso_linear(tipo_cabo) * qtd_cabos
```

Não há componente de "extra" (sem mensageiro).

### 2.9 Composição Vetorial Final (Total)

```python
for each level (MT1, MT2, BT, BTZ, RAL):
    X[i] = F_tip[i] * cos(angulo_nivel[i] * π / 180)
    Y[i] = F_tip[i] * sin(angulo_nivel[i] * π / 180)

sum_X = Σ X[i]
sum_Y = Σ Y[i]

total_tracao  = √(sum_X² + sum_Y²) + poste_ecc
total_angulo  = _angle_formula(sum_X, sum_Y)
```

> `poste_ecc` (Esforço de Comprimento de Carga do poste) é somado **escalarmente** à magnitude do vetor resultante, não como componente vetorial.

### 2.10 Excentricidade do Poste (ECC)

Lookup em tabela por `(tipo_poste, modelo_poste)`:

```python
POSTE_TABLE = {
    "Concreto circular": [
        ("9 m / 150 daN",   12.24),
        ("9 m / 300 daN",   14.18),
        ("11 m / 300 daN",  18.49),
        ("11 m / 600 daN",  20.09),   # modelo do projeto Cosmo LDA
        ("11 m / 1000 daN", 23.27),
        ("11 m / 1500 daN", 28.06),
        ("12 m / 300 daN",  20.78),
        ("12 m / 600 daN",  22.53),
        ("12 m / 1000 daN", 26.02),
        ("12 m / 2000 daN", 34.76),
        ("15 m / 1000 daN", 34.83),
        ("18 m / 1000 daN", 44.46),
    ],
    "Fibra de vidro circular": [...],
    "Concreto Duplo T": [...],
    "Metalico": [("7,5 m / 200 daN", 7.51)],
}
```

### 2.11 Queda de Tensão — QDT

Cálculo em cadeia sequencial (folha "Alocação % de tensão"):

```python
v_mt_initial = v_nominal_mt * reg_mt                            # 13200 * 1.02 = 13464 V
v_mt_node   = v_mt_initial * (1 − drop_mt_pct  * coef_perda / 10000)
v_bt_start  = (v_mt_node   * (1 − drop_trafo_pct * coef_perda / 10000)) / (v_nom_mt/v_nom_bt)
v_bt_node1  = v_bt_start   * (1 − drop_bt1_pct  * coef_perda / 10000)
v_bt_node2  = v_bt_node1   * (1 − drop_bt2_pct  * coef_perda / 10000)
drop_total  = (v_nominal_bt − v_bt_node2) / v_nominal_bt * 100  # %
```

Valores padrão do workbook: `coef_perda=75`, `reg_mt=1.02`, `drop_mt_pct=3.5`, `drop_trafo_pct=4.5`, `drop_bt1_pct=5.0`, `drop_bt2_pct=1.5`.

### 2.12 Tabela de Reduções de Carga por Ângulo (TABELA_CARGAS_POSTE)

Usada para consulta visual no componente `TabelaCarga.jsx`. Não entra nos cálculos de força diretamente; serve como referência normativa:

| α (°) | R\_300 (daN) | R\_600 (daN) |
|--------|-------------|-------------|
| 0      | 300         | 600         |
| 10     | 288         | 577         |
| 20     | 268         | 536         |
| 30     | 250         | 499         |
| 40     | 232         | 464         |
| 50     | 216         | 432         |
| 60     | 201         | 402         |
| 70     | 187         | 374         |
| 80     | 174         | 348         |
| 90     | 150         | 300         |

### 2.13 Valores Verificados — Projeto Cosmo LDA (Golden Values)

```
MT1  217 daN @ 177°   (C32=217.37, F33=217, F34=177)
MT2  171 daN @  90°   (C58=192.22, F59=171, F60=90)
BT   165 daN @  60°   (C84=C32=217.37, F85=165, F86=60)
BTZ    0 daN @   0°   (sem dados BTZ no projeto)
RAL    0 daN @   0°   (sem dados RAL no projeto)
TOTAL 374 daN @ 112°  (C140=373.67, C141=112)
Poste ECC: 20.09 daN  (C149, modelo "11 m / 600 daN")
```

Tolerância aceite nos testes: **0.5 daN** (~0.2% de 217 daN).

---

## 3. Edge Cases e Situações Específicas da LIGHT S.A.

### 3.1 Flecha Obrigatória com Vão > 0

Validado tanto no frontend quanto no backend (Pydantic `model_validator`):

```
if vao > 0 and flecha <= 0:
    raise ValueError("flecha deve ser > 0 quando vao > 0")
```

Sem esta regra, a fórmula da catenária `(peso * vao²) / (8 * flecha)` divide por zero.

### 3.2 Denominador Zero na Normalização

```python
denom = altura_poste * 0.9 - 0.6 - 0.1
if denom == 0:
    return 0.0  # guarda contra altura_poste ≈ 0.78 m (fisicamente impossível)
```

### 3.3 sum_H = 0 na Fórmula de Ângulo

Quando toda a catenária é perfeitamente vertical (todos os vãos a 90°):

```python
if sum_H == 0:
    return ROUNDUP(atan(sum_V / 1) * 180/π, 0)
```

O denominador é forçado a 1 para evitar divisão por zero e o resultado é arredondado para cima (ROUNDUP, não ROUND).

### 3.4 Cabo Compacta com Mensageiro (MT) vs. Cabo Armado com Mensageiro (BT)

**Regra específica LIGHT S.A.:**
- Em MT: rede `"Compacta"` adiciona cordoalha de aço (mensageiro físico suspenso)
- Em BT: rede `"Armado"` adiciona mensageiro (não `"Compacta"`)
- A confusão entre estas duas regras produz resultados errados — o código separa explicitamente:

```python
# MT (plan1_tables.py):
peso_extra = PESO_MENSAGEIRO if tipo_rede == TIPO_COMPACTA else 0

# BT T2-T4 (_calc_bt_t2_traversal):
peso_extra = PESO_MENSAGEIRO if tipo_rede == TIPO_ARMADO else 0
```

### 3.5 BT T1 e T2 Não Aceitam Geometria Própria

O bloco BT nas posições T1 e T2 ignora silenciosamente os campos `vao`, `flecha`, `angulo` e `altura_poste` inseridos pelo utilizador. A UI aceita esses valores para "round-trip fidelity", mas o motor usa sempre MT1.

> Se um utilizador inserir geometria diferente em BT T1, não verá erro — mas o resultado refletirá MT1 T1. Este é o comportamento esperado, fiel ao Excel.

### 3.6 Postes com Ângulos Muito Agudos (α próximo a 0° ou 180°)

Com ângulos próximos de 0° ou 180°, `sum_V` tende a 0 e `sum_H` domina:
- `_angle_formula` retorna valores próximos de 0° ou 180° corretamente
- Não há sinal de instabilidade numérica nos testes

Com ângulos quase perpendiculares (≈ 90°), `sum_H ≈ 0`:
- `_angle_formula` activa o caminho `sum_H == 0` → usa `atan(sum_V/1)`
- `ROUNDUP` é aplicado (não `ROUND`)

### 3.7 BTZero com Muitas Ligações (> 61)

A tabela de lookup BTZero tem apenas 5 breakpoints até 61 ligações. Valores maiores (`qtd_ligacoes >= 61`) resultam em `qtd_fios = 11`, o máximo previsto. Não há erro — o sistema "satura" silenciosamente.

### 3.8 Fuzzy Inputs — Tipos Inválidos e Valores Extremos

Validações do backend (`schemas.py`):
- `vao`, `flecha`: `ge=0, le=5000` (m)
- `angulo`: `ge=0, le=360` (graus)
- `altura_poste`, `altura_ancoragem`: `ge=0, le=100` (m)
- `qtd_ligacoes`, `qtd_cabos`: `ge=0, le=1000`

O backend captura `ValueError`, `ZeroDivisionError`, `ArithmeticError` e retorna HTTP 422 em vez de 500:

```python
except (ValueError, ZeroDivisionError, ArithmeticError) as domain_err:
    raise HTTPException(status_code=422, detail=f"Entrada fora do domínio operacional: {domain_err}")
```

### 3.9 Normalização de Strings em Lookup Tables

O `_vlookup` normaliza chaves com `.strip().lower()`, tornando a busca robusta a espaços extras (havia trailing spaces em nomes de cabos como `"1/0AWG-CAA, PVC "` e `"Aberta "`).

### 3.10 Compatibilidade de Schema PT-BR/EN

O modelo `ProjetoInDBBase` tem um `root_validator` que mapeia automaticamente:
```python
"criado_em"    → "created_at"
"atualizado_em" → "updated_at"
"deletado_em"  → "deleted_at"
```
Permitindo transição entre convenções de nomenclatura sem quebrar queries antigas.

---

## 4. Oportunidades de Reuso

### 4.1 ALTA PRIORIDADE — Motor de Cálculo Completo

**Ficheiro:** `python/translated/ponto_blocks.py`  
**Recomendação:** Copiar integralmente para o novo monorepo como `packages/tracao-engine/ponto_blocks.py`.

Este ficheiro contém as **289 fórmulas do Excel transcritas fielmente**, incluindo:
- Todas as constantes físicas verificadas
- Os ROUND() intermediários críticos para paridade
- As regras de compartilhamento BT ↔ MT1
- A composição vetorial final

**Não reimplementar do zero.** A paridade com o Excel foi obtida iterativamente e cada detalhe (ROUNDUP vs ROUND, `atan` vs `atan2`, etc.) foi validado com os golden values do projeto Cosmo LDA.

### 4.2 ALTA PRIORIDADE — Tabelas de Lookup

**Ficheiro:** `python/translated/plan1_tables.py`  
**Recomendação:** Migrar para o novo monorepo como tabela de referência.

Contém:
- `CABOS_TABLE`: 33 tipos de cabos com diâmetro e peso linear
- `REDE_TABLE`: 6 tipos de rede com quantidade de cabos
- `POSTE_TABLE`: 4 tipos de poste × N modelos com ECC em daN
- `CABOS_POR_REDE`: lookup rede → lista de cabos compatíveis
- `BTZERO_*`: constantes físicas para redes de ligação
- Função `lookup_btzero_qtd_fios` com os 5 breakpoints canónicos

### 4.3 ALTA PRIORIDADE — Schemas Pydantic de Input/Output

**Ficheiro:** `python/api/schemas.py`  
**Recomendação:** Usar como base para o schema do endpoint `/tracao` no novo sistema.

O schema é maduro e cobre:
- Todos os 5 níveis (MT1, MT2, BT, BTZ, RAL) com 4 travessias cada
- Validação `model_validator` para `flecha > 0 when vao > 0`
- Campos de saída: `tracao_dan`, `angulo_graus`, `resultante_raw`, `texto`, vetores, `poste_ecc_dan`

### 4.4 MÉDIA PRIORIDADE — Motor QDT

**Ficheiro:** `python/translated/qdt_blocks.py`  
**Recomendação:** Reutilizar para implementar o endpoint de Queda de Tensão no novo monorepo.

Fórmulas simples e auto-contidas. Inclui parâmetros defaults calibrados para a LIGHT S.A. (`v_nominal_mt=13200`, `reg_mt=1.02`, `coef_perda=75`).

### 4.5 MÉDIA PRIORIDADE — Componente `RelogioAngulos.jsx`

**Localização:** `src/components/relogio/RelogioAngulos.jsx`  
**Recomendação:** Já foi transplantado para o novo monorepo na commit `abf5995`. Confirmar que a implementação inclui o cálculo:

```javascript
comp_x = F_tip * Math.cos(angulo_graus * Math.PI / 180)
comp_y = F_tip * Math.sin(angulo_graus * Math.PI / 180)
```

O backend retorna esses valores pré-calculados no campo `vetores[]` da resposta.

### 4.6 MÉDIA PRIORIDADE — `TabelaCarga.jsx` + `TABELA_CARGAS_POSTE`

**Localização:** `src/components/tabela/TabelaCarga.jsx` + `src/constants/tabelaCargasPoste.js`  
**Recomendação:** Já transplantados. Verificar que o novo sistema usa a tabela de consulta normativa com os 14 pontos de ângulo (0° a 90°).

### 4.7 MÉDIA PRIORIDADE — `DiagramaPoste.jsx`

**Localização:** `src/components/secao/DiagramaPoste.jsx`  
**Recomendação:** Já transplantado. Componente que representa visualmente os níveis MT1/MT2/BT no poste com alturas de ancoragem.

### 4.8 BAIXA PRIORIDADE — `useUndoStack.js`

**Localização:** `src/hooks/useUndoStack.js`  
**Recomendação:** Stack de undo por ponto com TTL. Útil para UX na tela de preenchimento de dados. Candidato para Onda 7+ (Refinamentos UX).

### 4.9 BAIXA PRIORIDADE — `usePersistenciaCalculo.js`

**Localização:** `src/hooks/usePersistenciaCalculo.js`  
**Recomendação:** Padrão de fila + retry exponencial + detecção de 403 (sessão expirada). Padrão maduro para qualquer operação de persistência com feedback ao utilizador.

### 4.10 BAIXA PRIORIDADE — `uxFunnelInstrumentation.js`

**Localização:** `src/services/uxFunnelInstrumentation.js`  
**Recomendação:** Eventos de instrumentação UX (`CALCULATION_SUCCEEDED`, etc.). Útil para analytics em Onda 7+ (Produção/Observabilidade).

---

## 5. Checklist de Paridade — O que Garantir no Novo Sistema

- [x] `WIND_COEFF = 0.00471 * 60² = 16.956 daN/m²`
- [x] ROUND(2 decimais) em `wind_H`, `wind_V`, `cat_H`, `cat_V`
- [x] Catenária = `(peso_total * vao²) / (8 * flecha)` (fórmula parabólica)
- [x] Resultante = `√(ΣcatH² + ΣcatV²) + √(ΣwindH² + ΣwindV²)` (somas separadas)
- [x] Ângulo usa `atan` (não `atan2`) com correção manual de quadrante
- [x] `atan(sum_V / 1)` quando `sum_H == 0` + ROUNDUP
- [x] F_tip = `resultante * h_anc / (h_poste * 0.9 − 0.7)`
- [x] BT T1 herda TODO de MT1 T1; BT T2 herda geometria de MT1 T2
- [x] `BT_resultante == MT1_resultante` (C84=C32)
- [x] Rede `Compacta` → mensageiro em MT; rede `Armado` → mensageiro em BT
- [x] `total_tracao = √(ΣX² + ΣY²) + poste_ecc` (ECC somado escalarmente)
- [x] Ângulo do total calculado sobre `sum_X`, `sum_Y` (não catenary separada)
- [x] Textos de saída formatados como `int(round(f))` daN

---

## 6. Referências

| Item                        | Localização                                                  |
|-----------------------------|--------------------------------------------------------------|
| Workbook Excel (fonte de verdade) | `AP COSMO LDA NOVA 03 - PROJETO 5 - POSTE 1D.xlsm` |
| Engine principal Python     | `python/translated/ponto_blocks.py`                          |
| Tabelas de lookup           | `python/translated/plan1_tables.py`                          |
| Motor QDT                   | `python/translated/qdt_blocks.py`                            |
| Testes de paridade          | `python/tests/test_parity_excel.py`                          |
| Schema Pydantic             | `python/api/schemas.py`                                      |
| ADR Monorepo                | `docs/adr/0001-monorepo-e-estrategia-hibrida.md`             |
