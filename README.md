# HAWK Cross — Console (Gerenciamento, Simulação e Modelagem Matemática)

Aplicação integrada de console em Python para gerenciamento de cruzamentos semafóricos adaptativos, simulação de travessias acessíveis, persistência local e modelagem matemática.

A modelagem matemática do projeto é reduzida ao essencial para justificar a proteção aos pedestres: limites de velocidade requerida ($v_{req} \to +\infty$), perfil suave via derivadas ($v(t) = x'(t)$ com pico em $t = T/2$), e cálculo de grandezas acumuladas por integrais (deslocamento $\int v\,dt = L$ e fila simulada $\Delta Q \approx 1{,}3$ veículo).

---

## Proposta de Valor

> *"A infraestrutura urbana deve se adaptar às pessoas, e não exigir que todas as pessoas se adaptem ao mesmo ritmo."*

O **HAWK Cross** monitora a ocupação da faixa de pedestres durante a fase de verde e **estende dinamicamente o tempo de proteção** quando um pedestre vulnerável (idoso, cadeirante, pessoa com deficiência ou criança) necessita de tempo adicional para concluir a travessia com total segurança.

---

## Requisitos do Sistema

- **Python:** Versão 3.10 ou superior (suporte nativo a `match/case` e tipagem estática moderna).
- **Dependências Externas:** `requests`, `matplotlib` e `rich` (declaradas em `requirements.txt`).
- **Interface Enriquecida:** Terminal visual formatado com a biblioteca `rich` (painéis com bordas, tabelas coloridas, divisores estilizados e fluxo limpo).

---

## Instalação e Execução

### 1. Clonar o Repositório
```bash
git clone https://github.com/HAWK-GS02/HAWK-menu.git
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

### Resiliência e Modo Offline
Se a rede estiver indisponível ou o servidor estiver hibernando (cold start do plano gratuito do Render), a aplicação entra automaticamente em **Modo Offline**, permitindo a consulta segura aos dados armazenados no cache local (`dados/cache_api.json`) e bloqueando com segurança operações de escrita para manter a integridade dos dados.

### Validações Embutidas
Todas as validações de entrada do usuário são tratadas diretamente dentro das próprias funções com blocos `try/except` e loops interativos. Rejeitam valores vazios, tipos inválidos, opções fora de faixa e IDs mal formatados, garantindo que o programa nunca seja interrompido por entradas inesperadas.

---

## Roteiro de Demonstração

Para apresentações e avaliações acadêmicas, siga este roteiro de ponta a ponta:

1. **Inicialização e Diagnóstico:**
   - Execute `python main.py`. Mostre o painel de boas-vindas e o diagnóstico automático de conectividade com o status `[ONLINE]`.
2. **Gerenciamento de Cruzamentos (Opção 1):**
   - Acesse `[1] Listar cruzamentos` para ver a tabela rica com os cruzamentos obtidos da API.
   - Acesse `[3] Cadastrar novo cruzamento`: cadastre um cruzamento (ex: *Av. Paulista com Augusta*, largura *10.0 m*). Mostre a validação com coordenadas `(lat, lon)` e o ID gerado.
3. **Simulação de Travessia Adaptativa (Opção 4):**
   - Acesse `[1] Executar Simulação Individual`. Selecione o cruzamento recém-criado.
   - Escolha o cenário `[2] Extensão`: visualize o evento `travessia_estendida` onde o tempo adicional de proteção foi acionado.
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

```text
HAWK-menu/
├── .env.example                       # Modelo de variáveis de ambiente
├── .gitignore                         # Regras de exclusão do Git (.venv, pycache, etc.)
├── main.py                            # Ponto de entrada da aplicação
├── prompts.md                         # Registro de uso de Inteligência Artificial e rastreabilidade
├── README.md                          # Documentação principal e guia de apresentação
├── requirements.txt                   # Dependências do projeto (requests, matplotlib, rich)
├── dados/                             # Camada de persistência local em JSON
│   ├── cache_api.json                 # Cache local das consultas da API para suporte offline
│   ├── calculos.json                  # Parâmetros e estado salvo dos cálculos matemáticos
│   ├── historico_local.json           # Registro cronológico de auditoria das ações do console
│   └── relatorios/                    # Exportações geradas (.json estruturado e .txt legível)
├── graficos/                          # Gráficos técnicos gerados com Matplotlib
│   ├── 01_posicao_velocidade.png      # Curvas de posição x(t) e velocidade instantânea v(t)
│   ├── 02_velocidade_requerida.png    # Curva v_req(t) com assíntota vertical em T_min
│   └── 03_fila_veiculos.png           # Fila de veículos acumulada Q(t) (premissa simulada)
├── relatorio/                         # Relatório acadêmico da disciplina de Matemática
│   └── relatorio_matematico.md        # Relatório formal completo em Markdown (7 tópicos)
├── src/                               # Código-fonte da aplicação
│   └── hawk/                          # Pacote principal HAWK
        ├── __init__.py                # Inicializador do pacote
        ├── config.py                  # Constantes, URLs, timeouts e tuplas de enums
        ├── api_client.py              # Cliente HTTP centralizado (22 endpoints)
        ├── formatacao.py              # Utilitários de interface visual e temas Rich
        ├── persistencia.py            # Escrita atômica em JSON, cache e histórico local
        ├── sessao.py                  # Gerenciador de estado de conexão (online/offline)
        ├── matematica/                # Modelagem matemática e cinemática de pedestres
        │   ├── __init__.py            # Inicializador do submódulo
        │   ├── modelo.py              # Equações fundamentais (limites, derivadas e integrais)
        │   └── graficos.py            # Geração dos 3 gráficos técnicos com Matplotlib
        └── menus/                     # Submenus interativos estilizados com Rich
            ├── __init__.py            # Inicializador do submódulo
            ├── principal.py           # Loop de navegação e menu principal
            ├── cruzamentos.py         # CRUD de cruzamentos semafóricos
            ├── ocorrencias.py         # CRUD e ciclo de vida de ocorrências
            ├── eventos.py             # Histórico, eventos manuais e estado atual
            ├── simulacoes.py          # Simulação individual e em lote (dados simulados)
            ├── relatorios.py          # Relatórios operacionais e consolidados
            └── matematica.py          # Menu interativo da modelagem matemática

```

---

## Testes Automatizados

O sistema conta com testes automatizados desenvolvidos com o framework `unittest` da biblioteca padrão, cobrindo os cálculos fundamentais da modelagem matemática sem necessidade de conexão externa para rodar:

```bash
python -m unittest discover -s tests -v
```

### Casos de Teste Cobertos:
1. `test_tempo_minimo`: Confere $T_{min} = L/v + m \approx 21{,}667\text{ s}$ para $L = 10\text{ m}$, $v_{ref} = 0{,}6\text{ m/s}$ e margem $m = 5\text{ s}$.
2. `test_posicao_e_velocidade_extremidades`: Valida repouso nas extremidades ($v(0) = v(T) = 0$) e percurso completo ($x(0) = 0$ e $x(T) = L$).
3. `test_velocidade_maxima`: Confirma a velocidade máxima teórica $v_{max} = 1{,}5 \cdot (L/T) \approx 0{,}5357\text{ m/s}$ atingida no ponto crítico do meio da via ($t = T/2$).
4. `test_custo_extensao`: Avalia a retenção adicional de tráfego veicular $\Delta Q \approx 1{,}267\text{ veículo}$ (com $\lambda = 0{,}20\text{ veíc/s}$).

---

## Transparência e Uso de IA

O projeto conta com um arquivo [`prompts.md`](prompts.md) que documenta todas as ferramentas utilizadas, histórico de prompts, decisões arquiteturais propostas e o processo de validação técnica realizado pelo grupo.

---

## Equipe HAWK

| Integrante | RM |
|---|---:|
| Esther dos Santos de Almeida Tozzo | 570860 |
| Felipe de Oliveira Zimmermann | 570863 |
| Izabela Pordeus de Almeida | 570316 |
| João Victor Santos Souza | 569949 |
| Matheus Lopes Lima | 571458 |

---

## Link do Swagger UI

https://hawk-api-fsgy.onrender.com/docs

---

<p align="center">
  HAWK — A cidade que se adapta a você.
  <br/>
  FIAP • Global Solution 2026.2
</p>
