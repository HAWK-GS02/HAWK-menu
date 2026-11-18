# Etapa 07 — Modelagem Matemática Simplificada

## 7.1 Objetivo
Reduzir a modelagem matemática ao mínimo necessário para fundamentar a tecnologia assistiva urbana do HAWK Cross:
1. 2 limites com interpretação física
2. Derivadas de posição e velocidade com ponto de máximo crítico
3. 2 integrais analíticas (deslocamento e fila veicular)
4. Integração com 1 dado real da API HAWK (`/relatorios/tempos`)
5. Geração de 3 gráficos técnicos
6. 4 testes unitários automatizados

## 7.2 Funções Analíticas (`src/hawk/matematica/modelo.py`)
- `tempo_minimo(largura, v=0.6, margem=5.0)`: tempo regulamentar
- `posicao(t, largura, T)`: $x(t) = L(3s^2 - 2s^3)$ com $s = t/T$
- `velocidade(t, largura, T)`: $v(t) = (6L/T)(s - s^2)$
- `aceleracao(t, largura, T)`: $a(t) = (6L/T^2)(1 - 2s)$
- `velocidade_maxima(largura, T)`: $v_{max} = 1{,}5 \cdot L/T$ em $t = T/2$
- `velocidade_requerida(t, largura, T, T_min)`: $v_{req}(t) = \frac{L - x(t)}{T_{min} - t}$
- `tabela_limite(largura, T, T_min, hs)`: aproximação lateral com $h \in (1, 0.1, 0.01, 0.001)$
- `deslocamento(largura)`: $\int_0^T v(t) dt = L$
- `fila(t_fase, lam=0.20)`: $Q(t) = \lambda \cdot t$
- `custo_extensao(T_min, T, lam=0.20)`: $\Delta Q = \lambda (T - T_{min})$

## 7.3 Gráficos Técnicos (`src/hawk/matematica/graficos.py`)
- `01_posicao_velocidade.png`: $x(t)$ e $v(t)$, com $v_{max}$ em $t = T/2$ e área $= L$
- `02_velocidade_requerida.png`: $v_{req}(t)$ para $t \to T_{min}^-$ com assíntota vertical
- `03_fila_veiculos.png`: $Q(t)$ normal vs estendido com fases sombreadas e premissa simulada

## 7.4 Checklist da Etapa 07
- [x] 2 limites analíticos
- [x] $v(t)$ e $v_{max}$
- [x] 2 integrais analíticas
- [x] 3 gráficos em `graficos/`
- [x] 4 testes unitários em `tests/test_matematica.py`
