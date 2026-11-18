# Simplificação da parte de matemática — HAWK Cross (CitizenTech)

> Instruções de edição para reduzir a modelagem matemática ao **mínimo necessário** para cumprir o objetivo da entrega.
> Vale para pessoas e para agentes de IA. Idioma: pt-br. Dependências: apenas `matplotlib` (já usada). Nada de `numpy`, `sympy` ou `scipy`.

---

## 1. O que a entrega realmente exige

| Exigência do objetivo | O que vamos mostrar (mínimo) |
|---|---|
| Limites | **2 limites** com interpretação |
| Derivadas e taxas de variação | **Velocidade instantânea** `v(t) = x'(t)` e o **ponto de máximo** (`v'(t) = 0`) |
| Integrais para grandezas acumuladas | **Deslocamento** `∫v dt = L` e **veículos acumulados na fila** `∫(λ−μ) dt` |
| Fenômeno urbano real | Travessia de pedestres em um cruzamento (dados da API HAWK) |
| Comportamentos extremos | Velocidade máxima do pedestre e limite que "explode" (→ ∞) |
| Subsidiar o protótipo CitizenTech | Os resultados justificam a regra de **extensão da proteção** |
| Python ou GeoGebra | **Python** (o app que já existe) |

Tudo o que não está nessa tabela **sai**.

---

## 2. Modelo único (usar só este)

Variáveis:
- `L` largura da via (m) — **vem da API** (`largura_via_m`)
- `v_ref = 0,6 m/s` e `margem = 5 s` — padrões do endpoint `/calculos/tempo-minimo`
- `T_min = L / v_ref + margem` — tempo mínimo de proteção
- `T` — tempo que o pedestre realmente leva (pedestre mais lento)
- `s = t / T`, com `0 ≤ t ≤ T`

Funções (as **únicas** do relatório):

```
x(t) = L · (3s² − 2s³)         posição (parte e termina parado)
v(t) = (6L/T) · (s − s²)       velocidade  = x'(t)
a(t) = (6L/T²) · (1 − 2s)      aceleração  = v'(t)
```

Fila de veículos (premissas **simuladas**, avisar no relatório):
- `λ = 0,20` veículos/s chegando
- `μ = 0` durante a fase de pedestres (carros parados)
- `Q(t) = ∫₀ᵗ λ dτ = λ·t`

---

## 3. Exemplo numérico fixo (usar no relatório e conferir no código)

Dados: `L = 10 m`, `v_ref = 0,6`, `margem = 5`, pedestre lento com `T = 28 s`.

| Grandeza | Valor |
|---|---|
| `T_min` | 10/0,6 + 5 = **21,67 s** |
| `T` em relação a `T_min` | **+29,2 %** (dentro da faixa 5–40 % que a API chama de extensão) |
| Velocidade média `L/T` | **0,357 m/s** (abaixo de 0,6) |
| Velocidade máxima `1,5·L/T` em `t = T/2` | **0,536 m/s** |
| Posição em `t = T_min` | `x(21,67) ≈ 8,70 m` → faltam **≈ 1,30 m** |
| Fila ao fim da fase, sem extensão (`T_min`) | `0,2 × 21,67 ≈ 4,3` veículos |
| Fila ao fim da fase, com extensão (`T = 28`) | `0,2 × 28 = 5,6` veículos |
| Custo da extensão | **≈ 1,3 veículo a mais** |

Tabela do limite 2 (`v_req` quando `t → T_min⁻`), já calculada:

| `h = T_min − t` | `v_req(t) = d(t)/h` (m/s) |
|---|---|
| 1 | 1,70 |
| 0,1 | 13,4 |
| 0,01 | 130,7 |
| 0,001 | 1303,8 |

Se qualquer número do seu código não bater com estes, há erro no código (ou nos parâmetros).

---

## 4. Conteúdo matemático final (mínimo)

### 4.1 Limites (2)

1. **Chegada ao outro lado:** `lim_{t→T⁻} x(t) = L`.
   *Interpretação:* a posição é contínua; ao fim do tempo o pedestre completa exatamente a travessia.
2. **Velocidade exigida para terminar no prazo:** `v_req(t) = d(t) / (T_min − t)`, com `d(t) = L − x(t)`, quando `t → T_min⁻`.
   Se `d(T_min) > 0`, então `v_req → +∞`.
   *Interpretação:* se o pedestre ainda não chegou quando o tempo mínimo acaba, nenhuma velocidade razoável resolve. **É esse limite que justifica estender a proteção.**

### 4.2 Derivadas (taxa de variação)

- `v(t) = x'(t)` — velocidade instantânea.
- `a(t) = v'(t)` — aceleração. **Extremo:** `a(t) = 0` em `t = T/2`, onde `v` é máxima: `v_max = 1,5·L/T`.
- *Interpretação:* o pedestre acelera na primeira metade, desacelera na segunda; o ponto crítico é no meio da faixa, onde ele está mais rápido. Em `t = 0` e `t = T` a velocidade é zero.

### 4.3 Integrais (grandezas acumuladas)

1. **Deslocamento:** `∫₀ᵀ v(t) dt = x(T) − x(0) = L`.
   *Interpretação:* a área sob a curva da velocidade é a distância percorrida.
2. **Fila:** `Q(T_fase) = ∫₀^{T_fase} λ dt = λ · T_fase`.
   *Interpretação:* cada segundo de extensão custa `λ` veículos na fila; a extensão de ≈ 6,3 s custa ≈ 1,3 veículo.

### 4.4 Dado real da API (um só)

Usar `GET /relatorios/tempos` (`tempo_medio_travessia_s`) e `largura_via_m` do cruzamento:
`v_médio = L / tempo_medio_travessia_s` → comparar com 0,6 m/s. Se não houver dados, avisar e usar o exemplo da seção 3 (rotulado como simulado).

---

## 5. Edições no código

> Se os nomes de arquivos do projeto forem diferentes dos listados em `AGENTS.md`, adaptar. A ideia é **diminuir** o código.

### 5.1 Estrutura alvo

Fundir `limites.py`, `derivadas.py`, `integrais.py` e `fila_veiculos.py` em **um arquivo só** e deixar os gráficos em outro:

```
src/hawk/matematica/
├── modelo.py     # tudo da seção 4 (funções puras)
└── graficos.py   # 3 gráficos
```

### 5.2 O que **remover**

- Derivada numérica (diferença central) e o quociente de diferenças com `h → 0`.
- Regra do trapézio e Simpson, e comparação de erros para `n = 10, 100, 1000`.
- Integração da fila por Euler, tempo de dissipação `Q/(μ−λ)` e o limite `lim Q(t)`.
- Função de "tempo para atingir X % da travessia".
- Histograma de eventos reais e classificação `normal/estendida/crítica` evento a evento.
- 4 dos 7 gráficos.
- Qualquer opção de menu que chame o que foi removido.

> Não precisa apagar do histórico: o Git guarda. Só tire do código final, porque **tudo o que está no código pode ser perguntado na apresentação**.

### 5.3 O que **deixar** em `modelo.py` (referência de implementação)

```python
"""Modelagem matemática do HAWK Cross (versão simples)."""

VELOCIDADE_REF = 0.6   # m/s
MARGEM = 5.0           # s
LAMBDA = 0.20          # veículos/s (premissa simulada)


def tempo_minimo(largura, v=VELOCIDADE_REF, margem=MARGEM):
    return largura / v + margem


def posicao(t, largura, T):
    s = t / T
    return largura * (3 * s**2 - 2 * s**3)


def velocidade(t, largura, T):          # derivada de posicao
    s = t / T
    return (6 * largura / T) * (s - s**2)


def aceleracao(t, largura, T):          # derivada de velocidade
    s = t / T
    return (6 * largura / T**2) * (1 - 2 * s)


def velocidade_maxima(largura, T):      # em t = T/2, onde a(t) = 0
    return 1.5 * largura / T


def velocidade_requerida(t, largura, T, T_min):
    """v_req(t) = distância que falta / tempo que falta (t < T_min)."""
    return (largura - posicao(t, largura, T)) / (T_min - t)


def tabela_limite(largura, T, T_min, hs=(1, 0.1, 0.01, 0.001)):
    """Lista de tuplas (h, v_req) para t = T_min - h."""
    return [(h, velocidade_requerida(T_min - h, largura, T, T_min)) for h in hs]


def deslocamento(largura):              # ∫0^T v dt = x(T) - x(0)
    return largura


def fila(t_fase, lam=LAMBDA):           # ∫0^t_fase lam dt
    return lam * t_fase


def custo_extensao(T_min, T, lam=LAMBDA):
    return fila(T, lam) - fila(T_min, lam)
```

Pontos de atenção:
- Garantir `0 ≤ t ≤ T` em `posicao`/`velocidade` (usar `min`/`max`).
- Em `velocidade_requerida`, exigir `t < T_min` para não dividir por zero.
- Funções puras: sem `input`, `print` nem HTTP.

### 5.4 Gráficos (`graficos.py`, só 3, salvar em `graficos/`)

| Arquivo | Conteúdo |
|---|---|
| `01_posicao_velocidade.png` | 2 subgráficos: `x(t)` e `v(t)`, marcando `v_max` em `t = T/2` |
| `02_velocidade_requerida.png` | `v_req(t)` para `t → T_min⁻`, com linha vertical tracejada em `T_min` (assíntota) |
| `03_fila_veiculos.png` | `Q(t)` com e sem extensão, fase de pedestres sombreada, rótulo "premissa simulada" |

Todos com título, eixos com unidade e legenda. Para o gráfico 1 usar `fill_between` sob `v(t)` e escrever "área = L" (isso mostra a integral).

### 5.5 Menu de matemática (`menus/matematica.py`)

Reduzir para **5 opções** (`match/case`):

1. **Tempo mínimo**: escolher cruzamento, pegar `largura_via_m`, calcular localmente **e** via `/calculos/tempo-minimo`; mostrar os dois.
2. **Limites**: mostrar a tabela do limite 2 e o texto de interpretação.
3. **Derivadas**: mostrar `v(t)`, `a(t)`, `v_max` e `t = T/2`.
4. **Integrais**: deslocamento `= L` e fila (`Q` normal × com extensão, custo em veículos).
5. **Gerar gráficos** e **dado real da API** (`v_médio` com `/relatorios/tempos`).

Cada opção pede só `T` (com validação, `T > 0`; sugerir 28 s) e, se quiser, `λ`. Registrar no histórico local e salvar o resultado em `dados/calculos.json` como já está.

### 5.6 Testes (`tests/test_matematica.py`, 4 testes)

- `tempo_minimo(10) ≈ 21.667`
- `posicao(T) == L` e `velocidade(0) == velocidade(T) == 0`
- `velocidade_maxima(10, 28) ≈ 0.5357`
- `custo_extensao(21.667, 28) ≈ 1.267`

---

## 6. Edições nos documentos

1. **`docs/etapas/07-modelagem-matematica.md`**: substituir as seções 7.2 a 7.6 pelo conteúdo das seções 4 e 5 deste arquivo. Checklist novo: 2 limites, `v(t)` e `v_max`, 2 integrais, 3 gráficos, 4 testes.
2. **`docs/etapas/08-integracao-relatorio-e-entrega.md`**: menu de 9 para 5 opções (5.5) e relatório com a estrutura da seção 7.
3. **`AGENTS.md` seção 6**: trocar pelo modelo da seção 2 e remover a menção a Simpson, trapézio, Euler e dissipação. Na seção 5, a linha "Limites/Derivadas/Integrais/Fila" passa a apontar para `matematica/modelo.py`. Na seção 2, manter `matplotlib` como única biblioteca de matemática.
4. **`README.md`**: descrever a matemática em 3 linhas.

---

## 7. Relatório matemático (`relatorio/relatorio_matematico.md`) — roteiro curto

Meta: 4 a 6 páginas. Estrutura:

1. **Problema urbano** (parágrafo): pedestres lentos (idosos, mobilidade reduzida, gestantes) podem não completar a travessia no tempo fixo; o HAWK Cross estende a proteção sem identificar ninguém.
2. **Modelo e dados**: variáveis, fórmula de `T_min`, funções `x`, `v`, `a`, origem (largura da API; `λ` simulado).
3. **Limites**: os 2 do item 4.1 com a tabela da seção 3 e interpretação.
4. **Derivadas**: `v`, `a`, `v_max`, interpretação (gráfico 1).
5. **Integrais**: deslocamento e fila, custo da extensão (gráficos 1 e 3).
6. **Dado real da API** (um parágrafo, com `v_médio`).
7. **Conclusão para o protótipo CitizenTech**: os resultados mostram quando a extensão é necessária (`v_req → ∞`), quanto ela custa (≈ 1,3 veículo para +6,3 s) e que a decisão pode ser calibrada. Limitações: prova de conceito, `λ` simulado, não homologado.

Cada gráfico entra com `![legenda](../graficos/arquivo.png)` seguido de 2–3 linhas de interpretação.

---

## 8. Roteiro de explicação para a apresentação (1 minuto por item)

- **Limite:** "Quando o tempo mínimo acaba e o pedestre ainda não chegou, a velocidade que ele precisaria tende ao infinito. Por isso estendemos."
- **Derivada:** "A derivada da posição é a velocidade; onde a derivada da velocidade é zero está o pico, no meio da faixa."
- **Integral:** "A área sob a curva da velocidade é a distância percorrida, e a integral da taxa de chegada é a fila acumulada."
- **CitizenTech:** "Os números mostram o trade-off: poucos segundos a mais para o pedestre custam poucos carros a mais na fila."

---

## 9. Checklist final

- [ ] `modelo.py` único, funções puras, sem bibliotecas além de `matplotlib` nos gráficos
- [ ] Exemplo da seção 3 reproduzido pelo código (conferir os números)
- [ ] 3 gráficos gerados em `graficos/`
- [ ] Menu de matemática com 5 opções, entradas validadas
- [ ] 4 testes passando
- [ ] Relatório com os 7 tópicos da seção 7, gráficos incluídos e interpretados
- [ ] Aviso de "premissas simuladas / protótipo não homologado" no app e no relatório
- [ ] `AGENTS.md`, etapas 07 e 08 e `README.md` atualizados
- [ ] Todos do grupo conseguem explicar cada função

## 10. Suposições a confirmar

- O professor aceita **Python** (e não exige GeoGebra). Se exigir, os 3 gráficos podem ser refeitos no GeoGebra com as mesmas funções da seção 2.
- Relatório em Markdown/PDF; confirmar o formato.
- Parâmetros `λ = 0,20`, `L = 10 m` e `T = 28 s` são exemplos; podem ser trocados desde que o relatório e os testes usem os mesmos valores.