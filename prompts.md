# Registro de Uso de Inteligência Artificial no Projeto HAWK-menu

---

## 1. Ferramentas de IA Utilizadas e suas Finalidades

| Ferramenta | Finalidade no Projeto |
|------------|----------------------|
| **Gemini 3.8 no Antigravity** | Modelo principal de raciocínio, arquitetura e geração de código; usado para planejamento do APP, design de `sessao.py`, cache, configuração de API e formatação com Rich |

---

## 2. Prompts Utilizados

### Planejamento do APP
> "Faça um plano para um CLI Python (HAWK-menu) com API REST, cache local, sessão persistente e interface Rich. Inclua estrutura de pastas, fluxos de dados e roadmap."

### Configuração da Conexão da API
> "Crie um arquivo em `src/hawk/api_client.py` com `requests`: função `requisitar()` que retorna `(ok, dados, status)` sem exceções, trate erros de rede e status HTTP, implemente funções de endpoint (pt-br), timeout via config, sem prints. Teste manual em `tests/manual_api.py`."

### `sessao.py` e Cache
> "Crie um arquivo em `src/hawk/sessao.py`: gerencie estado offline com `esta_offline()`, `definir_modo_offline()`, `bloquear_se_offline()` que impede novas escritas, e `testar_ou_reconectar()` que chama `api_client.acordar_servidor()` e atualiza o estado."

### Persistência e Histórico Local (`persistencia.py`)
> "Crie um arquivo em `src/hawk/persistencia.py`: `ler_json`/`salvar_json` com fallback, cache da API, histórico local em JSON/TXT."

### Formatação com Rich
> "Crie tema Rich consistente e componentes reutilizáveis: Table, Panel, Progress e Console baseando-se na referência" - OBS: colocamos como referência outro menu que já tinhamos feito usando a lib rich.

### Comentários e Documentação
> "Adicione docstrings Google-style, type hints completos e comentários em lógica complexa nas funções públicas."

---

## 3. Funcionalidades Desenvolvidas, Sugeridas ou Modificadas com Auxílio da IA

| Funcionalidade | Papel da IA | Resultado |
|----------------|-------------|-----------|
| **Arquitetura geral do Projeto** | Planejamento e roadmap do projeto | Todo o planejamento e roadmap com etapas necessárias para o desenvolvimento do projeto |
| **Cliente API (`api_client.py`)** | Geração completa + refinamento | `requests` síncrono, `requisitar()` retorna `(ok, dados, status)`, 22 endpoints pt-br, `match/case` status HTTP, `acordar_servidor()`, timeout via config |
| **Sessão (`sessao.py`)** | Design + implementação | Módulo simples: estado offline (globals), `esta_offline()`, `definir_modo_offline()`, `bloquear_se_offline()`, `testar_ou_reconectar()` |
| **Persistência (`persistencia.py`)** | Implementação | `ler_json`/`salvar_json` atômicos, cache API (`cache_api.json`), histórico local (`historico_local.json`), `registrar_acao()`, `exportar_relatorio()` (JSON+TXT) |
| **UI Rich (`formatacao.py`)** | Componentes + tema | Tema consistente, `imprimir_aviso()`, `imprimir_erro()`, `imprimir_sucesso()`, `tabela()`, `painel()`, `progresso()`, baseado em menu de referência |
| **Configuração (`config.py`)** | Geração | Configurações simples (timeout, base_url), leitura de `.env` |
| **Docstrings, type hints, comentários** | Geração + revisão | Cobertura documentada do código, facilitando manutenção futura |

---

## 4. Verificação, Testes e Ajustes Realizados pelo Grupo

| Etapa | Ação | Método |
|-------|------|---------------------|
| **Revisão de código** | Leitura crítica de cada arquivo gerado por IA; foco em tratamento de erro e aderência ao estilo do projeto | Revisão manual |
| **Validação de cenários** | CLI em cenários: online normal, offline, cache vazio, cache populado, API lenta (`acordar_servidor`) | Execução manual |
| **Ajustes pós-IA** | Renomear funções para pt-br, remover `async` desnecessário, simplificar `try/except`, ajustar imports, remover código morto | Commits manuais |

---

## 5. Análise Crítica

**Benefícios:** Consistência desde o início, docs/type hints, alternativas rápidas para decisões, poucos erros técnicos.

**Limitações:** A IA não consegue colocar em prática exatamente o que temos em mente, portanto exige revisões constantes e prompts muito bem elaborados.

**Dificuldades:** Desenvolvimento de bons prompts e comunicação entre os agentes e o grupo.

---

## Conclusão

O uso de IA acelerou bastante o desenvolvimento do projeto, desde o planejamento da arquitetura, passando pela escrita do código, até a revisão e documentação do código. 

---