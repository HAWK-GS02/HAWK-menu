# HAWK Cross — Console (Gerenciamento, Simulação e Modelagem Matemática)

Aplicação integrada de console em Python para gerenciamento de cruzamentos semafóricos adaptativos, simulação de travessias acessíveis, persistência local e modelagem matemática.
A modelagem matemática do projeto é reduzida ao essencial para justificar a proteção aos pedestres: limites de velocidade requerida ($v_{req} \to +\infty$), perfil suave via derivadas ($v(t) = x'(t)$ com pico em $t = T/2$), e cálculo de grandezas acumuladas por integrais (deslocamento $\int v\,dt = L$ e fila simulada $\Delta Q \approx 1{,}3$ veículo).

> **Aviso Legal e Limites do Projeto:**  
> Este software é uma **proposta acadêmica** desenvolvida para as disciplinas de *Computational Thinking with Python* e *Matemática*.  
> - **NÃO** controla semáforos reais e não deve ser implantado em vias públicas.  
> - **NÃO** comanda abertura de sinais (apenas registra/simula eventos e consulta métricas).  
> - **NÃO** realiza reconhecimento facial, biometria nem rastreamento ou classificação individual de pessoas.  
> - **NÃO** é um sistema homologado ou certificado para segurança viária.  
> - Todos os dados de simulação são explicitamente identificados (`origem = "simulacao_console"`).

---

## Proposta de Valor

> *"A infraestrutura urbana deve se adaptar às pessoas, e não exigir que todas as pessoas se adaptem ao mesmo ritmo."*

O **HAWK Cross** monitora a ocupação da faixa de pedestres durante a fase de verde e **estende dinamicamente o tempo de proteção** quando um pedestre vulnerável (idoso, cadeirante, pessoa com deficiência ou criança) necessita de tempo adicional para concluir a travessia com total segurança.

---

## Requisitos do Sistema

- **Python:** Versão estável mais recente (mínimo Python 3.10 para suporte pleno a `match/case`).
- **Dependências Externas:** `requests`, `matplotlib` e `rich` (declaradas em `requirements.txt`).
- **Sem bibliotecas matemáticas pesadas:** Modelagem realizada em Python padrão puro (sem `numpy`, `scipy` ou `sympy`).
- **Interface Enriquecida:** Terminal visual formatado com a biblioteca `rich` (painéis com bordas, tabelas coloridas e fluxo limpo).

---

## Instalação e Execução

### 1. Clonar o Repositório
```bash
git clone <URL_DO_REPOSITORIO>
cd HAWK-menu
```

### 2. Criar e Ativar o Ambiente Virtual
- **Windows (PowerShell):**
  ```powershell
  python -m venv .venv
  .venv\Scripts\Activate.ps1
  ```
- **Linux / macOS:**
  ```bash
  python3 -m venv .venv
  source .venv/bin/activate
  ```

### 3. Instalar Dependências
```bash
pip install -r requirements.txt
```

### 4. Configuração de Variáveis de Ambiente (Opcional)
Por padrão, a aplicação se conecta automaticamente à API HAWK em produção hospedada no Render (`https://hawk-api-fsgy.onrender.com`). Caso deseje alterar:
```bash
cp .env.example .env
```

### 5. Executar a Aplicação
```bash
python main.py
```

---

## Interface e Navegação do Console

A interface de terminal foi desenvolvida com a biblioteca **Rich**, fornecendo cabeçalhos estilizados em painéis, tabelas com colunas coloridas, alertas visuais destacados e limpeza de tela automática entre opções:

```text
┌─────────────────────────────────────────────────────────────┐
│ HAWK - TRAVESSIA ADAPTATIVA                                 │
│ Sistema de Gerenciamento, Simulação e Análise (CitizenTech) │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│ STATUS: ONLINE                                                              │
│ Conectado à API: https://hawk-api-fsgy.onrender.com                         │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│        MENU PRINCIPAL — HAWK CROSS CONSOLE                                  │
│  1         Gerenciar Cruzamentos                                            │
│  2         Gerenciar Ocorrências                                            │
│  3         Eventos de Travessia e Histórico                                 │
│  4         Simulações de Travessia                                          │
│  5         Relatórios do Sistema                                            │
│  6         Modelagem Matemática e Gráficos                                  │
│  7         Status da API / Alternar Modo Offline                            │
│  0         Sair do sistema                                                  │
└─────────────────────────────────────────────────────────────────────────────┘
```

Se a rede estiver indisponível ou o servidor estiver hibernando, a aplicação entra automaticamente em **Modo Offline**, permitindo a consulta segura aos dados armazenados no cache local (`dados/cache_api.json`).

---

## Roteiro de Demonstração (5 a 7 minutos)

Para apresentações e avaliações acadêmicas, siga este roteiro de ponta a ponta:

1. **Inicialização e Diagnóstico:**
   - Execute `python main.py`. Mostre o painel de boas-vindas e o diagnóstico automático de conectividade com o status `[ONLINE]`.
2. **Gerenciamento de Cruzamentos (Opção 1):**
   - Acesse `[1] Listar cruzamentos` para ver a tabela rica com os cruzamentos obtidos da API.
   - Acesse `[3] Cadastrar novo cruzamento`: cadastre um cruzamento (ex: *Av. Paulista com Augusta*, largura *10.0 m*). Mostre a validação com coordenadas `(lat, lon)` e o ID gerado.
3. **Simulação de Travessia Adaptativa (Opção 4):**
   - Acesse `[1] Executar Simulação Individual`. Selecione o cruzamento recém-criado.
   - Escolha o cenário `[2] Extensao`: visualize o evento `travessia_estendida` onde o tempo adicional de proteção foi acionado.
   - Em seguida, escolha o cenário `[3] Falha`: destaque o painel vermelho de **Alerta de Segurança** informando que o servidor gerou automaticamente uma **ocorrência de prioridade alta**.
4. **Gerenciamento de Ocorrências (Opção 2):**
   - Acesse `[1] Listar ocorrências` para ver a ocorrência gerada pelo cenário de falha.
   - Acesse `[5] Mudar situação da ocorrência (PATCH)` e altere a situação de `aberta` para `em_andamento` e depois `resolvida`.
5. **Eventos e Estado Semafórico em Tempo Real (Opção 3):**
   - Acesse `[4] Consultar Estado Semafórico Atual`: selecione o cruzamento e observe a interpretação do estado atual dos grupos semafóricos.
   - Acesse `[2] Consultar Histórico de Eventos`: visualize a contagem agregada de eventos por tipo (`deteccao`, `travessia_normal`, `travessia_estendida`, `falha`).
6. **Relatórios Operacionais e Exportação (Opção 5):**
   - Acesse `[5] Relatório Consolidado Completo`. Confirme a exportação e mostre os arquivos gerados em `dados/relatorios/*.json` e `*.txt`.
7. **Modelagem Matemática e Gráficos Técnicos (Opção 6):**
   - Acesse `[1] Tempo Mínimo Seguro`: confere o cálculo local com o endpoint `/calculos/tempo-minimo`.
   - Acesse `[2] Estudo dos Limites`: observa a assíntota $v_{req} \to +\infty$, demonstrando por que estender a proteção é indispensável para pedestres lentos.
   - Acesse `[3] Análise de Derivadas`: avalia a velocidade instantânea $v(t)$, aceleração $a(t)$ e o pico no ponto crítico do meio da via ($t = T/2$).
   - Acesse `[4] Grandezas Acumuladas por Integrais`: comprova que a extensão retém apenas $\approx 1{,}3$ veículo a mais na fila veicular simulada.
   - Acesse `[5] Gerar Gráficos e Integração com API`: gera os 3 gráficos técnicos em `graficos/` (`01_posicao_velocidade.png`, `02_velocidade_requerida.png`, `03_fila_veiculos.png`) e analisa a velocidade média observada.

---

## Estrutura do Repositório

```
hawk-cross-console/
├── AGENTS.md                  # Contexto, regras de negócio e limites éticos
├── README.md                  # Documentação principal e roteiro de apresentação
├── requirements.txt           # Dependências (requests, matplotlib, rich)
├── .env.example               # Modelo de variáveis de ambiente
├── .gitignore                 # Arquivos ignorados pelo Git
├── main.py                    # Ponto de entrada do sistema
├── docs/
│   ├── etapas/                # Roteiro das etapas de desenvolvimento (07 e 08)
│   └── rastreabilidade.md     # Matriz de atendimento aos requisitos acadêmicos
├── src/hawk/
│   ├── config.py              # Constantes, caminhos e tuplas de enums
│   ├── api_client.py          # Cliente HTTP centralizado e tratamento de status
│   ├── formatacao.py          # Formatação de tabelas, painéis e cores com Rich
│   ├── persistencia.py        # Escrita atômica em JSON, cache e histórico local
│   ├── sessao.py              # Gerenciamento de estado online/offline
│   ├── menus/
│   │   ├── principal.py       # Loop principal de navegação estilizado com Rich
│   │   ├── cruzamentos.py     # CRUD de cruzamentos
│   │   ├── ocorrencias.py     # CRUD de ocorrências e PATCH de situação
│   │   ├── eventos.py         # Histórico, eventos manuais e estado atual
│   │   ├── simulacoes.py      # Simulação individual e em lote (dados simulados)
│   │   ├── relatorios.py      # Relatórios operacionais e consolidados
│   │   └── matematica.py      # Menu integrado da modelagem matemática (5 opções)
│   └── matematica/
│       ├── modelo.py          # Modelo simplificado: limites, derivadas, integrais e fila
│       └── graficos.py        # Geração dos 3 gráficos técnicos com matplotlib
├── dados/                     # cache_api.json, historico_local.json, calculos.json
├── graficos/                  # 3 figuras PNG técnicas geradas (01, 02 e 03)
├── relatorio/
│   └── relatorio_matematico.md # Relatório formal completo em Markdown (7 tópicos)
└── tests/                     # Bateria de testes automatizados com unittest
    └── test_matematica.py     # 4 testes cobrindo limites, derivadas, integrais e fila
```

---

## Testes Automatizados

O sistema conta com testes automatizados desenvolvidos com o framework `unittest` da biblioteca padrão, cobrindo os cálculos fundamentais da modelagem matemática sem necessidade de conexão externa para rodar:

```bash
python -m unittest discover -s tests -v
```

Os 4 testes cobrem:
1. `tempo_minimo(10) ≈ 21.667 s`
2. `posicao(T) == L` e `velocidade(0) == velocidade(T) == 0`
3. `velocidade_maxima(10, 28) ≈ 0.5357 m/s` (atingida em $t = T/2$)
4. `custo_extensao(21.667, 28) ≈ 1.267 veículos` (com $\lambda = 0{,}20$ veíc/s)

---

## Integrantes do Grupo

- Projeto Acadêmico — FIAP
- **Disciplinas:**
  - *Computational Thinking with Python*
  - *Differentiated Problem Solving*
