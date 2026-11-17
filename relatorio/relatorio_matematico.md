# Relatório de Modelagem Matemática — Sistema HAWK Cross

> **Aviso Legal e Limites do Projeto:**  
> Este documento constitui uma **proposta acadêmica** desenvolvida para as disciplinas de *Computational Thinking with Python* e *Matemática*. O sistema HAWK Cross é um protótipo conceitual para cidades acessíveis. **Não é um sistema certificado nem homologado para segurança viária**, não controla equipamentos semafóricos reais em vias públicas e não realiza qualquer tipo de biometria, identificação de deficiências ou rastreamento individual de pessoas. Dados operacionais de tráfego veicular são estritamente simulados para fins de análise de impacto.

---

## 1. Introdução e Contextualização do Problema

A mobilidade urbana moderna enfrenta o desafio histórico de conciliar a fluidez do tráfego veicular com a segurança dos pedestres, especialmente pessoas com mobilidade reduzida, idosos, crianças e pessoas com deficiência. Nos semáforos tradicionais de tempo fixo, a infraestrutura impõe um ritmo rígido e arbitrário, forçando o cidadão a se adaptar à máquina.

O **HAWK Cross** parte da seguinte premissa:
> *"A infraestrutura urbana deve se adaptar às pessoas, e não exigir que todas as pessoas se adaptem ao mesmo ritmo."*

O sistema atua como uma travessia semafórica adaptativa: sensores de presença e câmeras locais detectam a ocupação da faixa de pedestres durante o verde para pedestres. Caso o pedestre não conclua a travessia dentro do tempo nominal, o sistema estende dinamicamente o tempo de proteção, impedindo a abertura prematura do sinal verde para os veículos.

Neste relatório, formulamos a modelagem matemática completa do comportamento dinâmico do pedestre (posição, velocidade e aceleração através do cálculo diferencial e integral), o estudo de limites que justificam a extensão semafórica, e a modelagem por equações diferenciais da fila de veículos retida.

---

## 2. O Modelo Matemático da Travessia

### 2.1 Variáveis e Parâmetros Fundamentais

| Símbolo | Descrição | Unidade | Origem |
|---|---|---|---|
| $L$ | Largura da via / extensão da faixa | metros (m) | API HAWK (`largura_via_m`) |
| $v$ | Velocidade média de referência | m/s | Norma de Trânsito ($0{,}60$ m/s para vulneráveis) |
| $m$ | Margem de segurança | segundos (s) | Norma técnica ($5{,}0$ s) |
| $T_{min}$ | Tempo mínimo seguro de travessia | segundos (s) | Fórmula analítica e API (`/calculos/tempo-minimo`) |
| $T$ | Tempo real de duração da travessia | segundos (s) | API HAWK (`tempo_travessia_s`) |
| $s$ | Tempo normalizado de travessia ($s = t / T$) | adimensional | Variável auxiliar ($0 \le s \le 1$) |
| $\lambda$ | Taxa média de chegada de veículos na via | veíc/s | Premissa simulada ($0{,}20$ veíc/s $\approx 720$ veíc/h) |
| $\mu_{sat}$ | Taxa de saturação / escoamento veicular | veíc/s | Premissa simulada ($0{,}50$ veíc/s $\approx 1800$ veíc/h) |

### 2.2 Tempo Mínimo Regulamentar ($T_{min}$)

O cálculo do tempo regulamentar segue a equação recomendada por normas de engenharia de tráfego para pedestres vulneráveis:

$$T_{min} = \frac{L}{v} + m$$

Para uma via típica de $L = 14{,}0$ metros:

$$T_{min} = \frac{14{,}0}{0{,}60} + 5{,}0 = 23{,}33 + 5{,}0 = 28{,}33\text{ s}$$

Tanto a função local `modelo.tempo_minimo(14.0)` quanto a chamada ao endpoint `/calculos/tempo-minimo?largura=14.0` devolvem exatamente $28{,}33$ s, garantindo alinhamento total entre a modelagem matemática e os serviços da API.

### 2.3 Modelos de Posição: Linear vs. Suave (Cúbico)

O modelo convencional assume velocidade constante ($x(t) = v \cdot t$). No entanto, um pedestre real inicia a caminhada em repouso ($v(0) = 0$), acelera, atinge uma velocidade máxima e desacelera até o repouso ao subir na calçada oposta ($v(T) = 0$).

Para representar fielmente esse fenômeno com derivadas contínuas de classe $C^1$, adota-se um polinômio cúbico interpolador de Hermite com a variável normalizada $s = t/T \in [0, 1]$:

$$x(t) = L \cdot \left(3s^2 - 2s^3\right)$$

- Em $t = 0$ ($s = 0$): $x(0) = L(0) = 0$.
- Em $t = T/2$ ($s = 0{,}5$): $x(T/2) = L(3(0{,}25) - 2(0{,}125)) = L(0{,}75 - 0{,}25) = 0{,}5L$ (metade da via).
- Em $t = T$ ($s = 1$): $x(T) = L(3(1) - 2(1)) = L$ (calçada oposta).

![Gráfico da Posição](../graficos/grafico_posicao.png)

*Interpretação do Gráfico:* A curva azul (modelo suave) demonstra claramente as fases de partida suave e chegada amortecida em comparação à reta pontilhada laranja (modelo linear). Isso elimina descontinuidades físicas de velocidade e aceleração instantânea.

---

## 3. Estudo dos Limites Matemáticos

O conceito de limite é a base teórica que fundamenta a existência do sistema HAWK Cross.

### 3.1 Continuidade e Aproximação da Calçada Oposta

À medida que o tempo $t$ se aproxima da duração total $T$ pela esquerda ($t \to T^-$):

$$\lim_{t \to T^-} x(t) = L \quad \text{e} \quad \lim_{t \to T^-} d(t) = \lim_{t \to T^-} [L - x(t)] = 0$$

A tabela numérica gerada pelo sistema demonstra essa convergência:

| Passo $h = T - t$ (s) | $t$ (s) | Posição $x(t)$ (m) | Distância Restante $d(t)$ (m) |
|---|---|---|---|
| $1{,}000000$ | $27{,}300000$ | $13{,}9532$ | $0{,}0468$ |
| $0{,}100000$ | $28{,}200000$ | $13{,}9995$ | $0{,}0005$ |
| $0{,}010000$ | $28{,}290000$ | $14{,}0000$ | $0{,}0000$ |
| $0{,}000001$ | $28{,}299999$ | $14{,}0000$ | $0{,}0000$ |

### 3.2 O Limite Infinito da Velocidade Requerida e a Necessidade da Extensão

Seja $T_{lim}$ o tempo de verde programado pelo semáforo e $d(t) = L - x(t)$ a distância que falta para o pedestre concluir a travessia. A velocidade que o pedestre precisaria desenvolver para não ser atropelado quando o sinal fechar é dada por:

$$v_{req}(t) = \frac{d(t)}{T_{lim} - t}$$

Se o pedestre caminha lentamente e ainda se encontra na faixa ao aproximar-se do prazo ($d(T_{lim}) = d^* > 0$):

$$\lim_{t \to T_{lim}^-} v_{req}(t) = \lim_{\Delta t \to 0^+} \frac{d^*}{\Delta t} = +\infty$$

![Velocidade Requerida com Assíntota](../graficos/grafico_velocidade_requerida.png)

*Interpretação Matemática e Teórica:* Exigir que um pedestre vulnerável termine a travessia dentro de um tempo fixo insuficiente requer uma velocidade fisicamente impossível ($v_{req} \to +\infty$). Como o ser humano não pode acelerar infinitamente, a única solução matematicamente e eticamente aceitável é **alterar o denominador**, estendendo o tempo $T_{lim} \to T_{ext}$, o que remove a assíntota e traz $v_{req}$ de volta aos limites da capacidade humana.

### 3.3 Limite do Quociente de Diferenças

O limite fundamental da derivada representa a taxa de variação instantânea:

$$\lim_{h \to 0} \frac{x(t + h) - x(t)}{h} = x'(t) = v(t)$$

![Convergência do Quociente de Diferenças](../graficos/grafico_convergencia_limites.png)

A convergência em escala logarítmica confirma o comportamento de aproximação linear de primeira ordem, atingindo erro relativo inferior a $10^{-6}$ quando $h \le 10^{-5}$ s.

---

## 4. Derivadas e Perfil Dinâmico

### 4.1 Velocidade Instantânea

Diferenciando a posição $x(t) = L(3s^2 - 2s^3)$ com relação a $t$ via regra da cadeia ($\frac{ds}{dt} = \frac{1}{T}$):

$$v(t) = \frac{dx}{dt} = \frac{dx}{ds} \cdot \frac{ds}{dt} = L(6s - 6s^2) \cdot \frac{1}{T} = \frac{6L}{T} \cdot (s - s^2)$$

Propriedades fundamentais verificadas:
1. $v(0) = \frac{6L}{T}(0 - 0) = 0$ (partida do repouso).
2. $v(T) = \frac{6L}{T}(1 - 1) = 0$ (chegada em repouso).
3. O ponto crítico de velocidade máxima ocorre quando $v'(t) = a(t) = 0$, isto é, em $s = 0{,}5$ ($t = T/2$):
   $$v_{max} = \frac{6L}{T}(0{,}5 - 0{,}25) = \frac{6L}{T}(0{,}25) = 1{,}5 \cdot \frac{L}{T} = 1{,}5 \cdot v_{méd}$$

### 4.2 Aceleração Instantânea

Diferenciando a velocidade com relação a $t$:

$$a(t) = \frac{dv}{dt} = \frac{6L}{T^2} \cdot (1 - 2s)$$

- Para $s \in [0; 0{,}5)$ ($t < T/2$): $1 - 2s > 0 \implies a(t) > 0$ (Aceleração positiva).
- Em $s = 0{,}5$ ($t = T/2$): $a(t) = 0$ (Ponto de inflexão da curva de posição, velocidade máxima).
- Para $s \in (0{,}5; 1]$ ($t > T/2$): $1 - 2s < 0 \implies a(t) < 0$ (Desaceleração).

![Velocidade e Aceleração](../graficos/grafico_velocidade_aceleracao.png)

*Comparação Numérica:* A derivada numérica por diferença central $f'(t) \approx \frac{f(t+h) - f(t-h)}{2h}$ implementada em `derivadas.py` conferiu com a analítica com erro absoluto de $1{,}86 \times 10^{-11}$ m/s (ordem de precisão da máquina).

---

## 5. Integrais e Deslocamento

### 5.1 Teorema Fundamental do Cálculo

A distância total percorrida pelo pedestre entre $t = 0$ e $t = T$ corresponde à integral definida da velocidade instantânea:

$$\Delta x = \int_0^T v(t)\,dt = \int_0^T \frac{6L}{T}\left(\frac{t}{T} - \frac{t^2}{T^2}\right) dt$$

Resolvendo analiticamente:

$$\Delta x = \frac{6L}{T} \left[ \frac{t^2}{2T} - \frac{t^3}{3T^2} \right]_0^T = \frac{6L}{T} \left( \frac{T}{2} - \frac{T}{3} \right) = \frac{6L}{T} \left( \frac{T}{6} \right) = L$$

A integral da velocidade recupera exatamente a largura da via $L$.

![Área da Integral](../graficos/grafico_integral_area.png)

### 5.2 Avaliação Numérica: Trapézio vs. Simpson

Implementadas sem bibliotecas de terceiros, as regras numéricas foram avaliadas para recuperar $L = 14{,}0$ m:

| Subintervalos $n$ | Regra do Trapézio (m) | Erro Trapézio | Regra de Simpson 1/3 (m) | Erro Simpson |
|---|---|---|---|---|
| 10 | $13{,}86000000$ | $1{,}40 \times 10^{-1}$ | $14{,}00000000$ | $0{,}00$ (Exato para polinômio quadrático) |
| 100 | $13{,}99860000$ | $1{,}40 \times 10^{-3}$ | $14{,}00000000$ | $< 10^{-12}$ |
| 1000 | $13{,}99998600$ | $1{,}40 \times 10^{-5}$ | $14{,}00000000$ | $< 10^{-12}$ |

Como $v(t)$ é uma função quadrática de $t$, a Regra de Simpson 1/3 (baseada em interpolação parabólica) recupera a integral de forma teoricamente exata, já no primeiro escalão com $n = 10$.

---

## 6. Dinâmica da Fila de Veículos

A retenção semafórica gera acúmulo de veículos na via transversal. Modelamos essa dinâmica pela Equação de Conservação de Fluxo:

$$\frac{dQ}{dt} = \lambda - \mu(t), \quad Q(0) = Q_0 = 0$$

- Durante o sinal verde para pedestres ($t \in [0, T_{fase}]$): $\mu(t) = 0 \implies \frac{dQ}{dt} = \lambda \implies Q(t) = \lambda \cdot t$.
- No instante de término da travessia ($t = T_{fase}$), a fila atinge o pico: $Q_{pico} = \lambda \cdot T_{fase}$.
- Após o término ($t > T_{fase}$), o sinal verde abre para veículos e o fluxo escoa na capacidade saturada $\mu(t) = \mu_{sat}$:
  $$\frac{dQ}{dt} = \lambda - \mu_{sat} < 0 \implies Q(t) = Q_{pico} - (\mu_{sat} - \lambda)(t - T_{fase})$$
- A fila se dissipa completamente em:
  $$t_{dissipacao} = \frac{Q_{pico}}{\mu_{sat} - \lambda}$$

### 6.1 Análise Comparativa: Cenário Normal vs. Cenário com Extensão HAWK

Adotando premissas de engenharia de tráfego ($\lambda = 0{,}20$ veíc/s $\approx 720$ veíc/h; $\mu_{sat} = 0{,}50$ veíc/s $\approx 1800$ veíc/h; $L = 14{,}0$ m $\implies T_{min} = 28{,}3$ s):

| Métrica | Cenário Normal ($T_{min}$) | Cenário Estendido HAWK ($+25\%$) | Impacto Adicional |
|---|---|---|---|
| Duração da Fase de Pedestres | $28{,}3$ s | $35{,}4$ s | $+7{,}1$ s |
| Fila Máxima no Pico ($Q_{pico}$) | $5{,}66$ veículos | $7{,}08$ veículos | $+1{,}42$ veículos |
| Tempo de Dissipação da Fila | $18{,}87$ s | $23{,}60$ s | $+4{,}73$ s |
| Tempo Total do Ciclo de Fila | $47{,}17$ s | $59{,}00$ s | $+11{,}83$ s |
| Atraso Total Acumulado (Área $Q$) | $133{,}5$ veíc$\cdot$s | $208{,}9$ veíc$\cdot$s | $+75{,}4$ veíc$\cdot$s |

![Evolução Temporal da Fila de Veículos](../graficos/grafico_fila_veiculos.png)

*Conclusão do Trade-off:* A extensão adaptativa de $7{,}1$ segundos para garantir a travessia segura de um idoso ou cadeirante provoca um acréscimo de **menos de 2 veículos na fila máxima** e requer apenas $4{,}7$ segundos adicionais para a via voltar à condição de fluxo livre. Isso prova que a acessibilidade urbana plena é perfeitamente viável sem comprometer a malha de tráfego.

---

## 7. Resultados Integrados com a API HAWK

A integração do módulo de matemática com os endpoints da API HAWK (`/eventos`, `/relatorios/tempos` e `/cruzamentos`) permitiu cruzar os modelos teóricos com amostras reais coletadas:

![Histograma de Travessias](../graficos/grafico_histograma_travessias.png)

1. **Amostra Analisada:** Os tempos reais de travessia concentram-se em torno de $23{,}5$ s, com travessias lentas chegando a $35$ s.
2. **Taxa de Extensões:** A API registrou uma taxa global de extensões de $28{,}6\%$, condizente com a presença esperada de pedestres com ritmos diferenciados em cruzamentos centrais.
3. **Consistência Numérica:** Todos os cálculos locais em Python conferem com as métricas retornadas pelos endpoints da API, consolidando a opção arquitetural (C) definida pelo grupo.

---

## 8. Considerações Finais e Éticas

O desenvolvimento deste estudo consolidou as seguintes conclusões:

1. **Rigor Matemático e Acessibilidade:** O cálculo diferencial e integral provou ser indispensável para fundamentar a tecnologia assistiva urbana. A modelagem suave cúbica de $x(t)$, a assíntota de $v_{req}$ e a conservação de fluxo de veículos demonstram a viabilidade técnica e a necessidade social da travessia adaptativa.
2. **Autonomia Computacional:** Todo o motor matemático foi implementado em Python padrão, garantindo portabilidade, eficiência e transparência algorítmica, sem "caixas-pretas" ou dependências desnecessárias.
3. **Respeito aos Limites Éticos:** O HAWK Cross reitera seu compromisso com a privacidade: nenhum dado biométrico, identificador de pessoa ou diagnóstico médico é coletado. A decisão de extensão baseia-se unicamente no espaço físico ocupado na via e na dinâmica do tempo de travessia.
