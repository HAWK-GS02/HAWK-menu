# Contexto, Regras de Negócio e Limites Éticos — HAWK Cross

## 1. Visão Geral do Produto
O HAWK Cross é uma prova de conceito de tecnologia assistiva urbana voltada para travessias semafóricas adaptativas. O sistema monitora a ocupação da faixa de pedestres durante o verde de pedestres e estende o tempo de proteção quando detecta que pedestres vulneráveis necessitam de tempo adicional para concluir a travessia com segurança.

## 2. Tecnologias e Dependências
- **Linguagem:** Python 3.10+
- **Bibliotecas Externas:** `requests` (para comunicação HTTP com a API HAWK) e `matplotlib` (exclusivamente para geração dos 3 gráficos técnicos).
- **Sem bibliotecas matemáticas pesadas:** Não utilizar `numpy`, `scipy` ou `sympy`. Todo o cálculo analítico é implementado em Python padrão puro.

## 3. Limites Éticos e Legais
- Proposta acadêmica: NÃO controla semáforos reais em vias públicas.
- NÃO comanda abertura de sinais aos automóveis.
- NÃO realiza reconhecimento facial, biometria ou identificação de deficiências.
- Dados veiculares de fila são premissas simuladas de tráfego.

## 4. Arquitetura do Sistema
- `main.py`: Inicialização e loop principal.
- `src/hawk/config.py`: Constantes, parâmetros de projeto e caminhos de diretórios.
- `src/hawk/api_client.py`: Comunicação com a API HAWK em produção.
- `src/hawk/formatacao.py`: Exibição visual de tabelas e banners.
- `src/hawk/persistencia.py`: Gravação de arquivos JSON e histórico local.
- `src/hawk/sessao.py`: Gerenciamento do estado online/offline.
- `src/hawk/menus/`: Menus interativos baseados em `match/case`.

## 5. Estrutura dos Módulos de Matemática
- `src/hawk/matematica/modelo.py`: Funções analíticas puras cobrindo limites, derivadas, integrais e fila veicular.
- `src/hawk/matematica/graficos.py`: Geração dos 3 gráficos técnicos (`01_posicao_velocidade.png`, `02_velocidade_requerida.png`, `03_fila_veiculos.png`).
- `src/hawk/menus/matematica.py`: Interface de console reduzida a 5 opções interativas.

## 6. Modelo Matemático Simplificado
- **Variáveis:**
  - $L$: largura da via (m) — obtida via API (`largura_via_m`) ou padrão de 10 m
  - $v_{ref} = 0{,}6$ m/s e $margem = 5{,}0$ s (padrões de projeto para pedestres vulneráveis)
  - $T_{min} = L / v_{ref} + margem$: tempo mínimo regulamentar
  - $T$: tempo de travessia do pedestre lento
  - $s = t / T \in [0, 1]$
- **Funções:**
  - Posição: $x(t) = L \cdot (3s^2 - 2s^3)$
  - Velocidade: $v(t) = (6L/T) \cdot (s - s^2)$
  - Aceleração: $a(t) = (6L/T^2) \cdot (1 - 2s)$
  - Ponto Crítico: $v_{max} = 1{,}5 \cdot L/T$ em $t = T/2$
- **Fila de Veículos (Premissas Simuladas):**
  - $\lambda = 0{,}20$ veíc/s chegando
  - $\mu = 0$ durante a travessia de pedestres
  - $Q(t) = \int_0^t \lambda\,d\tau = \lambda \cdot t$
