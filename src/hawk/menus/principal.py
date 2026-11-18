"""Menu principal interativo do HAWK Cross Console."""

import sys
from src.hawk import config, formatacao, persistencia, sessao
from src.hawk.menus.cruzamentos import menu_cruzamentos
from src.hawk.menus.eventos import menu_eventos
from src.hawk.menus.matematica import menu_matematica
from src.hawk.menus.ocorrencias import menu_ocorrencias
from src.hawk.menus.relatorios import menu_relatorios
from src.hawk.menus.simulacoes import menu_simulacoes

BANNER = """
========================================================================
                      HAWK - TRAVESSIA ADAPTATIVA                      
             Sistema de Gerenciamento, Simulação e Análise             
========================================================================

"""


def exibir_status_conexao() -> None:
    """Mostra indicador visual de status de conectividade no cabeçalho."""
    if sessao.esta_offline():
        motivo = sessao.obter_motivo_offline()
        print(f"[STATUS] MODO OFFLINE (Apenas leitura de cache local) | Motivo: {motivo or 'Offline'}")
    else:
        print(f"[STATUS] ONLINE (Conectado à API: {config.URL_BASE})")
    print("-" * 72)


def gerenciar_status_conexao() -> None:
    """Submenu para testar a conexão com a API e alternar modo offline manualmente."""
    formatacao.imprimir_titulo("Status da API e Modo de Conexão")
    print(f"URL configurada: {config.URL_BASE}")
    exibir_status_conexao()

    print("\nOpções:")
    print("  [1] Testar conexão / Reconectar à API")
    print("  [2] Forçar Modo Offline (testar cache e bloqueio de escrita)")
    print("  [3] Retornar ao Modo Online")
    print("  [0] Voltar ao menu principal\n")

    try:
        entrada = input("Opção desejada: ").strip()
        opcao = int(entrada)
    except ValueError:
        print("Opção inválida.")
        return

    match opcao:
        case 1:
            print("\nTestando conexão com a API...")
            ok, msg = sessao.testar_ou_reconectar(notificar=print)
            if ok:
                formatacao.imprimir_sucesso(msg)
            else:
                formatacao.imprimir_aviso(f"{msg}\nModo offline mantido.")
        case 2:
            sessao.definir_modo_offline(True, motivo="Ativado manualmente pelo usuário")
            formatacao.imprimir_aviso("Modo offline ativado manualmente. Operações de escrita estão bloqueadas.")
        case 3:
            sessao.definir_modo_offline(False)
            formatacao.imprimir_sucesso("Modo online reativado. Testando conexão...")
            ok, msg = sessao.testar_ou_reconectar(notificar=print)
            if not ok:
                formatacao.imprimir_aviso(f"Atenção: A API não respondeu ({msg}). Retornando para offline.")
        case 0:
            pass
        case _:
            print("Opção inválida.")


def inicializar_aplicacao() -> None:
    """Prepara os arquivos locais e verifica o status da API no início da sessão."""
    print(BANNER)
    persistencia.inicializar_cache()
    persistencia.inicializar_historico()

    print("Verificando conexão com o servidor da API HAWK...")
    ok, msg = sessao.testar_ou_reconectar(notificar=print)
    if ok:
        formatacao.imprimir_sucesso("Servidor online e pronto para uso.")
    else:
        formatacao.imprimir_aviso(
            f"{msg}\n"
            "O sistema iniciará em MODO OFFLINE.\n"
            "Você poderá consultar os dados armazenados em cache local,\n"
            "mas operações de escrita (cadastro, edição e exclusão) estarão bloqueadas."
        )


def executar() -> None:
    """Loop principal de navegação do console com match/case."""
    inicializar_aplicacao()

    while True:
        formatacao.imprimir_titulo("Menu Principal - HAWK Cross Console")
        exibir_status_conexao()

        print("  [1] Gerenciar Cruzamentos")
        print("  [2] Gerenciar Ocorrências")
        print("  [3] Eventos de Travessia e Histórico")
        print("  [4] Simulações de Travessia")
        print("  [5] Relatórios do Sistema")
        print("  [6] Modelagem Matemática e Gráficos")
        print("  [7] Status da API / Alternar Modo Offline")
        print("  [0] Sair do sistema\n")

        try:
            entrada = input("Opção desejada: ").strip()
            opcao = int(entrada)
        except ValueError:
            print("Entrada inválida. Digite um número de 0 a 7.")
            continue

        match opcao:
            case 1:
                menu_cruzamentos()
            case 2:
                menu_ocorrencias()
            case 3:
                menu_eventos()
            case 4:
                menu_simulacoes()
            case 5:
                menu_relatorios()
            case 6:
                menu_matematica()
            case 7:
                gerenciar_status_conexao()
            case 0:
                conf = input("Deseja realmente sair do HAWK Console? [S/n]: ").strip().lower()
                if conf not in ("n", "nao", "não", "no"):
                    print("\nEncerrando aplicação. Obrigado por utilizar o HAWK Cross Console!\n")
                    sys.exit(0)
            case _:
                print("Opção inválida. Escolha entre 0 e 7.")
