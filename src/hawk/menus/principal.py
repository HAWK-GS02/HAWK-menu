"""Menu principal interativo do HAWK Cross Console estilizado com Rich."""

import sys
from rich.panel import Panel

from src.hawk import config, formatacao, persistencia, sessao
from src.hawk.menus.cruzamentos import menu_cruzamentos
from src.hawk.menus.eventos import menu_eventos
from src.hawk.menus.matematica import menu_matematica
from src.hawk.menus.ocorrencias import menu_ocorrencias
from src.hawk.menus.relatorios import menu_relatorios
from src.hawk.menus.simulacoes import menu_simulacoes


def exibir_status_conexao() -> None:
    """Mostra indicador visual de status de conectividade em painel colorido."""
    if sessao.esta_offline():
        motivo = sessao.obter_motivo_offline() or "Apenas leitura de cache local"
        formatacao.console.print(
            Panel(
                f"[bold yellow]STATUS: MODO OFFLINE[/]\n{motivo}",
                border_style="yellow",
                expand=False,
            )
        )
    else:
        formatacao.console.print(
            Panel(
                f"[bold green]STATUS: ONLINE[/]\nConectado à API: [cyan]{config.URL_BASE}[/]",
                border_style="green",
                expand=False,
            )
        )


def gerenciar_status_conexao() -> None:
    """Submenu para testar a conexão com a API e alternar modo offline manualmente."""
    while True:
        formatacao.limpar_tela()
        formatacao.titulo_terminal("STATUS DA API E CONEXÃO", f"URL: {config.URL_BASE}", "bold cyan")
        exibir_status_conexao()

        opcoes = [
            ("1", "Testar conexão / Reconectar à API"),
            ("2", "Forçar Modo Offline (testar cache e bloqueio de escrita)"),
            ("3", "Retornar ao Modo Online"),
            ("0", "Voltar ao menu principal"),
        ]
        formatacao.exibir_menu_painel("GERENCIAMENTO DE CONEXÃO", opcoes, border_style="cyan")

        opcao = input("\nEscolha uma opção: ").strip()

        match opcao:
            case "1":
                formatacao.console.print("\n[yellow]Testando conexão com a API...[/]")
                ok, msg = sessao.testar_ou_reconectar(notificar=formatacao.console.print)
                if ok:
                    formatacao.imprimir_sucesso(msg)
                else:
                    formatacao.imprimir_aviso(f"{msg}\nModo offline mantido.")
                formatacao.pausar()
            case "2":
                sessao.definir_modo_offline(True, motivo="Ativado manualmente pelo usuário")
                formatacao.imprimir_aviso("Modo offline ativado manualmente. Operações de escrita bloqueadas.")
                formatacao.pausar()
            case "3":
                sessao.definir_modo_offline(False)
                formatacao.imprimir_sucesso("Modo online reativado. Testando conexão...")
                ok, msg = sessao.testar_ou_reconectar(notificar=formatacao.console.print)
                if not ok:
                    formatacao.imprimir_aviso(f"Atenção: A API não respondeu ({msg}). Retornando para offline.")
                formatacao.pausar()
            case "0":
                break
            case _:
                formatacao.console.print("[bold red]Opção inválida. Tente novamente.[/]")
                formatacao.pausar("Pressione Enter para continuar...")


def inicializar_aplicacao() -> None:
    """Prepara os arquivos locais e verifica o status da API no início da sessão."""
    formatacao.limpar_tela()
    formatacao.titulo_terminal(
        "HAWK - TRAVESSIA ADAPTATIVA",
        "Sistema de Gerenciamento, Simulação e Análise (CitizenTech)",
        "bold cyan",
    )
    persistencia.inicializar_cache()
    persistencia.inicializar_historico()

    formatacao.console.print("[yellow]Verificando conexão com o servidor da API HAWK...[/]")
    ok, msg = sessao.testar_ou_reconectar(notificar=formatacao.console.print)
    if ok:
        formatacao.imprimir_sucesso("Servidor online e pronto para uso.")
    else:
        formatacao.imprimir_aviso(
            f"{msg}\n"
            "O sistema iniciará em MODO OFFLINE.\n"
            "Você poderá consultar os dados em cache local, mas gravações estarão bloqueadas."
        )
    formatacao.pausar("Pressione Enter para acessar o Menu Principal...")


def executar() -> None:
    """Loop principal de navegação do console com match/case e formatação Rich."""
    inicializar_aplicacao()

    opcoes_menu = [
        ("1", "Gerenciar Cruzamentos"),
        ("2", "Gerenciar Ocorrências"),
        ("3", "Eventos de Travessia e Histórico"),
        ("4", "Simulações de Travessia"),
        ("5", "Relatórios do Sistema"),
        ("6", "Modelagem Matemática e Gráficos"),
        ("7", "Status da API / Alternar Modo Offline"),
        ("0", "Sair do sistema"),
    ]

    while True:
        formatacao.limpar_tela()
        formatacao.titulo_terminal(
            "HAWK - TRAVESSIA ADAPTATIVA",
            "Sistema de Gerenciamento, Simulação e Análise (CitizenTech)",
            "bold cyan",
        )
        exibir_status_conexao()
        formatacao.exibir_menu_painel("MENU PRINCIPAL — HAWK CROSS CONSOLE", opcoes_menu, border_style="cyan")

        opcao = input("\nEscolha uma opção: ").strip()

        match opcao:
            case "1":
                menu_cruzamentos()
            case "2":
                menu_ocorrencias()
            case "3":
                menu_eventos()
            case "4":
                menu_simulacoes()
            case "5":
                menu_relatorios()
            case "6":
                menu_matematica()
            case "7":
                gerenciar_status_conexao()
            case "0":
                formatacao.limpar_tela()
                conf = input("Deseja realmente sair do HAWK Console? [S/n]: ").strip().lower()
                if conf not in ("n", "nao", "não", "no"):
                    formatacao.console.print(
                        Panel(
                            "[bold cyan]Saindo do sistema HAWK Cross Console. Até a próxima![/]",
                            border_style="cyan",
                            expand=False,
                        )
                    )
                    sys.exit(0)
            case _:
                formatacao.console.print("[bold red]Opção inválida. Tente novamente.[/]")
                formatacao.pausar("Pressione Enter para continuar...")
