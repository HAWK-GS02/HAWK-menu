# Relatório de Modelagem Matemática — HAWK Cross (CitizenTech)

> **Aviso Legal e Limites do Projeto:**  
> Este documento constitui uma **proposta acadêmica** desenvolvida para as disciplinas de *Computational Thinking with Python* e *Matemática*. O sistema HAWK Cross é uma prova de conceito de tecnologia assistiva urbana (CitizenTech) para cruzamentos semafóricos adaptativos. **Não é um sistema certificado nem homologado para segurança viária**, não comanda diretamente semáforos reais em vias públicas e **não realiza qualquer reconhecimento facial, biometria ou rastreamento individual de pessoas**. As taxas de tráfego veicular utilizadas são premissas simuladas de engenharia de tráfego.

---

## 1. Problema Urbano e Proposta de Valor

A mobilidade urbana contemporânea enfrenta o desafio de equilibrar a segurança de pedestres vulneráveis com a fluidez do tráfego veicular. Em semáforos convencionais com tempos de verde fixos, pedestres em ritmos mais lentos — como idosos, pessoas com deficiência ou mobilidade reduzida, crianças e gestantes — frequentemente não conseguem concluir a travessia antes da abertura do sinal verde aos automóveis. Esse descompasso gera situações de risco iminente de atropelamento e insegurança viária. O protótipo **HAWK Cross** soluciona essa vulnerabilidade monitorando a ocupação física da faixa e estendendo dinamicamente o tempo de proteção semafórica quando necessário, preservando integralmente a privacidade dos cidadãos (sem biometria nem identificação individual).

---

## 2. Modelo Matemático e Parâmetros

### 2.1 Variáveis e Parâmetros Fundamentais

| Parâmetro | Símbolo | Valor de Referência | Unidade | Origem / Justificativa |
|---|---|---|---|---|
| Largura da via | $L$ | $10{,}0$ | metros (m) | Cruzamento de teste / API HAWK (`largura_via_m`) |
| Velocidade de projeto | $v_{ref}$ | $0{,}60$ | m/s | Norma de acessibilidade para pedestres vulneráveis |
| Margem de segurança | $margem$ | $5{,}0$ | segundos (s) | Tempo de percepção e reação / API (`/calculos/tempo-minimo`) |
| Tempo mínimo regulamentar | $T_{min}$ | $21{,}67$ | segundos (s) | Equação normativa: $T_{min} = L / v_{ref} + margem$ |
| Tempo real do pedestre lento | $T$ | $28{,}0$ | segundos (s) | Travessia assistida (+29,2% sobre $T_{min}$, faixa de extensão) |
| Variável normalizada | $s$ | $t / T$ | adimensional | Intervalo contínuo $s \in [0, 1]$ para $t \in [0, T]$ |
| Taxa de chegada veicular | $\lambda$ | $0{,}20$ | veículos/s | Premissa simulada ($\approx 720$ veíc/h retidos no vermelho) |
| Taxa de escoamento na fase | $\mu$ | $0$ | veículos/s | Carros parados durante o sinal verde para pedestres |

### 2.2 Equações Analíticas da Travessia

Para modelar o pedestre partindo do repouso na calçada de origem ($v(0) = 0$) e parando ao atingir a calçada de destino ($v(T) = 0$), adota-se o polinômio cúbico suave com derivadas contínuas de classe $C^1$:

1. **Posição:**
   $$x(t) = L \cdot \left(3s^2 - 2s^3\right), \quad s = \frac{t}{T}$$
2. **Velocidade Instantânea ($x'(t)$):**
   $$v(t) = \frac{dx}{dt} = \frac{6L}{T} \cdot \left(s - s^2\right)$$
3. **Aceleração Instantânea ($v'(t)$):**
   $$a(t) = \frac{dv}{dt} = \frac{6L}{T^2} \cdot \left(1 - 2s\right)$$
4. **Fila de Veículos Acumulada ($Q(t)$):**
   $$Q(t) = \int_0^t \lambda\,d\tau = \lambda \cdot t \quad (\text{com } \mu = 0)$$

---

## 3. Estudo dos Limites Matemáticos

Dois limites fundamentais justificam matematicamente a dinâmica da travessia e a regra de decisão de extensão semafórica:

### 3.1 Limite 1: Chegada ao Outro Lado da Faixa (Continuidade)

$$\lim_{t \to T^-} x(t) = \lim_{s \to 1^-} L(3s^2 - 2s^3) = L$$

*Interpretação:* A função de posição é contínua e suave em todo o intervalo fechado $[0, T]$. Ao completar o tempo total concedido $T$, o pedestre atinge exatamente a extensão total da via $x(T) = L = 10{,}0$ m, garantindo a conclusão integral da travessia.

### 3.2 Limite 2: Velocidade Exigida para Terminar no Prazo Fixo ($v_{req} \to +\infty$)

Definindo a distância restante até a calçada como $d(t) = L - x(t)$, a velocidade média necessária para que o pedestre conclua a travessia antes que o tempo fixo $T_{min}$ se esgote é dada por:

$$v_{req}(t) = \frac{L - x(t)}{T_{min} - t}, \quad \text{para } t < T_{min}$$

Se o pedestre é vulnerável e leva $T = 28{,}0$ s, no instante limite do tempo regulamentar fixo ($t = T_{min} = 21{,}67$ s) sua posição é de apenas $x(21{,}67) \approx 8{,}70$ m, restando ainda $d(T_{min}) \approx 1{,}30$ m na via. Portanto:

$$\lim_{t \to T_{min}^-} v_{req}(t) = \lim_{t \to T_{min}^-} \frac{1{,}30}{T_{min} - t} = +\infty$$

A tabela numérica gerada pelo sistema demonstra a explosão dessa grandeza à medida que o tempo limite se aproxima:

| Passo $h = T_{min} - t$ (s) | Instante $t$ (s) | Distância Restante $d(t)$ (m) | Velocidade Requerida $v_{req}$ (m/s) |
|---|---|---|---|
| $1{,}000$ | $20{,}667$ | $1{,}70$ | $1{,}70$ |
| $0{,}100$ | $21{,}567$ | $1{,}34$ | $13{,}4$ |
| $0{,}010$ | $21{,}657$ | $1{,}31$ | $130{,}7$ |
| $0{,}001$ | $21{,}666$ | $1{,}30$ | $1303{,}8$ |

![Velocidade Requerida e Assíntota](../graficos/02_velocidade_requerida.png)

*Interpretação do Gráfico:* À medida que o tempo fixo de proteção expira sem que o pedestre tenha alcançado a calçada oposta, a velocidade necessária para evitar um atropelamento tende ao infinito. Como nenhum pedestre vulnerável pode acelerar a essas magnitudes, **é esse limite infinito que fundamenta ética e matematicamente o algoritmo do HAWK Cross: estender dinamicamente o denominador ($T_{min} \to T$), eliminando a assíntota e protegendo a vida**.

---

## 4. Derivadas e Ponto Crítico de Máxima Velocidade

A análise da primeira e da segunda derivada da posição descreve o perfil biomecânico da caminhada:

- **Velocidade instantânea:** $v(t) = (6L/T)(s - s^2)$.
- **Ponto crítico:** O extremo ocorre onde $v'(t) = a(t) = 0$:
  $$a(t) = \frac{6L}{T^2}(1 - 2s) = 0 \implies 1 - 2s = 0 \implies s = \frac{1}{2} \iff t = \frac{T}{2}$$
- **Velocidade máxima:**
  $$v_{max} = v\left(\frac{T}{2}\right) = \frac{6L}{T}\left(\frac{1}{2} - \frac{1}{4}\right) = 1{,}5 \cdot \frac{L}{T} = 1{,}5 \cdot v_{médio}$$

Para os dados do cruzamento de teste ($L = 10{,}0$ m e $T = 28{,}0$ s):
- Velocidade média: $v_{médio} = 10 / 28 \approx 0{,}357$ m/s.
- Velocidade máxima no centro da via: $v_{max} = 1{,}5 \times 0{,}357 \approx 0{,}536$ m/s em $t = 14{,}0$ s.
- Repouso inicial e final: $v(0) = v(28) = 0{,}0$ m/s.

![Cinemática de Travessia e Ponto Crítico](../graficos/01_posicao_velocidade.png)

*Interpretação do Gráfico:* O gráfico superior demonstra a transição suave de posição de $0$ a $10$ m. O gráfico inferior ilustra a velocidade em parábola invertida com pico de $0{,}536$ m/s em $t = 14$ s (metade da via) e destaca a área hachurada sob a curva, que equivale geometricamente ao deslocamento total $L = 10$ m.

---

## 5. Integrais e Grandezas Acumuladas

O cálculo integral é utilizado para quantificar duas grandezas físicas acumuladas cruciais para o sistema:

### 5.1 Deslocamento do Pedestre (Teorema Fundamental do Cálculo)

A distância percorrida pelo pedestre entre $t = 0$ e $t = T$ é a integral definida de sua velocidade:

$$\Delta x = \int_0^T v(t)\,dt = \int_0^T \frac{6L}{T}\left(\frac{t}{T} - \frac{t^2}{T^2}\right)dt = \frac{6L}{T}\left[\frac{t^2}{2T} - \frac{t^3}{3T^2}\right]_0^T = \frac{6L}{T}\left(\frac{T}{6}\right) = L$$

Para $L = 10{,}0$ m, a área sob a curva de $v(t)$ recupera exatamente $10{,}0$ metros de deslocamento.

### 5.2 Fila de Veículos e Custo da Extensão Semafórica

Durante o sinal verde para pedestres, os veículos na via transversal permanecem parados ($\mu = 0$). Com taxa média de chegada $\lambda = 0{,}20$ veículos/s:

$$Q(t) = \int_0^t \lambda\,d\tau = \lambda \cdot t$$

Comparando o término no tempo nominal $T_{min}$ versus o tempo estendido $T$:
- **Fila no tempo nominal ($T_{min} = 21{,}67$ s):** $Q(21{,}67) = 0{,}20 \times 21{,}67 \approx 4{,}33$ veículos.
- **Fila no tempo estendido ($T = 28{,}0$ s):** $Q(28) = 0{,}20 \times 28 = 5{,}60$ veículos.
- **Custo urbano da extensão:**
  $$\Delta Q = Q(T) - Q(T_{min}) = \lambda \cdot (T - T_{min}) = 0{,}20 \times (28 - 21{,}67) \approx 1{,}27 \text{ veículo}$$

![Evolução da Fila de Veículos](../graficos/03_fila_veiculos.png)

*Interpretação do Gráfico:* A curva linear destaca a retenção acumulada sob a taxa constante $\lambda = 0{,}20$ veíc/s. A extensão de $6{,}33$ segundos para salvar a vida de um pedestre vulnerável adiciona apenas **$\approx 1{,}3$ veículo a mais** à fila veicular, provando quantitativamente que a priorização da segurança humana tem impacto negligenciável na malha viária.

---

## 6. Análise com Dados Reais da API HAWK

A aplicação integra os modelos analíticos com a API HAWK em produção através da rota `GET /relatorios/tempos`. A métrica de `tempo_medio_travessia_s` observada nos eventos coletados na via permite calcular a velocidade média empírica do público atendido:

$$v_{médio} = \frac{L}{tempo\_medio\_travessia\_s}$$

Ao comparar $v_{médio}$ com a velocidade normativa de projeto ($v_{ref} = 0{,}60$ m/s), identifica-se a demanda real por adaptação temporal no cruzamento. Quando a rota remota está indisponível ou em cruzamentos recém-cadastrados sem eventos prévios, o sistema utiliza o exemplo simulado de referência ($L = 10{,}0$ m, $T = 28{,}0$ s, $v_{médio} = 0{,}357$ m/s), explicitamente identificado no console como premissa de simulação.

---

## 7. Conclusão e Subsídios ao Protótipo CitizenTech

Os resultados obtidos fornecem uma fundamentação quantitativa sólida para o protótipo HAWK Cross:

1. **Justificativa Ética e Matemática:** O limite infinito $v_{req} \to +\infty$ quando $t \to T_{min}^-$ demonstra com rigor irrefutável que tempos semafóricos rígidos impõem exigências fisicamente inatingíveis a pedestres lentos, justificando a intervenção adaptativa do algoritmo.
2. **Trade-off Urbano Favorável:** A modelagem integral da fila comprova que estender a fase de pedestres em cerca de $6{,}3$ segundos custa apenas $\approx 1{,}3$ veículo adicional retido, desmistificando a ideia de que a acessibilidade urbana prejudica a mobilidade dos automóveis.
3. **Decisão Calibrável:** O algoritmo opera com parâmetros ajustáveis ($L$, $T_{min}$, $\lambda$), permitindo que gestores de tráfego calibrem a sensibilidade da extensão conforme o horário e a densidade de pedestres.
4. **Limitações do Estudo:** Trata-se de uma prova de conceito acadêmica baseada em premissas simuladas para taxas veiculares e sem homologação do CONTRAN/SENATRAN para controle semafórico ativo.
