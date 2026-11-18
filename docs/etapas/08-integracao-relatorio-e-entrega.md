# Etapa 08 — Integração, Relatório e Entrega

## 8.1 Menu de Matemática (5 Opções)
O menu interativo `src/hawk/menus/matematica.py` organiza os cálculos em 5 opções:
1. **Tempo Mínimo Seguro:** local vs `/calculos/tempo-minimo`
2. **Estudo dos Limites:** continuidade e assíntota de velocidade requerida ($v_{req} \to +\infty$)
3. **Análise de Derivadas:** $v(t)$, $a(t)$, $v_{max}$ e instante crítico $t = T/2$
4. **Integrais e Grandezas Acumuladas:** deslocamento $L$ e retenção veicular da fila
5. **Geração de Gráficos e API:** salva os 3 PNGs técnicos e analisa dado real de `/relatorios/tempos`

## 8.2 Estrutura do Relatório Formal (`relatorio/relatorio_matematico.md`)
O relatório sintetiza a entrega em 7 tópicos objetivos:
1. Problema urbano e proposta de valor
2. Modelo matemático e parâmetros
3. Estudo dos limites matemáticos
4. Derivadas e ponto crítico de máxima velocidade
5. Integrais e grandezas acumuladas
6. Análise com dados reais da API HAWK
7. Conclusão e subsídios ao protótipo CitizenTech

## 8.3 Roteiro de Apresentação (Pitch de 1 minuto por conceito)
- **Limite:** "Quando o tempo mínimo acaba e o pedestre ainda não chegou, a velocidade que ele precisaria tende ao infinito. Por isso estendemos."
- **Derivada:** "A derivada da posição é a velocidade; onde a derivada da velocidade é zero está o pico, no meio da faixa."
- **Integral:** "A área sob a curva da velocidade é a distância percorrida, e a integral da taxa de chegada é a fila acumulada."
- **CitizenTech:** "Os números mostram o trade-off: poucos segundos a mais para o pedestre custam poucos carros a mais na fila."
