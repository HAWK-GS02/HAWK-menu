"""Módulo de simulação de travessias e falhas no HAWK Cross.

Permite simular cenários individuais (normal, extensão, falha) e simulações em lote
para geração de massa de dados. Todas as saídas são rotuladas como dados simulados.
"""

import random
from typing import Any
from src.hawk import api_client, config, formatacao, persistencia, sessao
from src.hawk.menus.cruzamentos import selecionar_cruzamento


def exibir_sequencia_eventos(eventos: list[dict[str, Any]]) -> None:
    """Exibe e interpreta a sequência de eventos resultante de uma simulação com Rich Table e Panel."""
    formatacao.imprimir_subtitulo("Sequência de Eventos da Simulação")
    formatacao.console.print("[dim yellow]Origem: 'simulacao_console'[/]\n")

    tabela = formatacao.Table(show_header=True, header_style="bold magenta", box=formatacao.box.SIMPLE)
    tabela.add_column("Passo", style="bold yellow", justify="center", width=6)
    tabela.add_column("Tipo", style="cyan", width=22)
    tabela.add_column("Estado", style="green", width=14)
    tabela.add_column("Espera (s)", style="white", justify="right", width=11)
    tabela.add_column("Trav. (s)", style="white", justify="right", width=11)
    tabela.add_column("Acionador", style="magenta", justify="center", width=10)

    ocorrencia_auto: dict[str, Any] | None = None

    for i, ev in enumerate(eventos, start=1):
        tipo = ev.get("tipo", "")
        estado = ev.get("estado", "")
        esp = ev.get("tempo_espera_s")
        esp_str = f"{float(esp):.1f}" if esp is not None else "-"
        trav = ev.get("tempo_travessia_s")
        trav_str = f"{float(trav):.1f}" if trav is not None else "-"
        acionador = "[bold green]SIM[/]" if ev.get("acionador") else "[dim]NÃO[/]"

        tabela.add_row(str(i), tipo, estado, esp_str, trav_str, acionador)

        if ev.get("ocorrencia_criada"):
            ocorrencia_auto = ev["ocorrencia_criada"]

    formatacao.console.print(tabela)

    # Interpretação dos eventos com match/case
    formatacao.console.print("\n[bold cyan]Interpretação da simulação:[/]")
    for ev in eventos:
        tipo = ev.get("tipo", "")
        match tipo:
            case "deteccao":
                formatacao.console.print("  [bold green]•[/] [white]Pedestre detectado aguardando na calçada.[/]")
            case "travessia_normal":
                t = ev.get("tempo_travessia_s", 0)
                formatacao.console.print(
                    f"  [bold green]•[/] [white]Travessia concluída dentro do tempo seguro padrão ([bold green]{t:.1f}s[/]).[/]"
                )
            case "travessia_estendida":
                t = ev.get("tempo_travessia_s", 0)
                formatacao.console.print(
                    f"  [bold yellow]• [EXTENSÃO][/] [yellow]Pedestre necessitou de tempo adicional: semáforo estendido ([bold white]{t:.1f}s[/]).[/]"
                )
            case "falha":
                formatacao.console.print(
                    "  [bold red]• [FALHA DETECTADA][/] [red]Anomalia operacional detectada no cruzamento.[/]"
                )
            case _:
                formatacao.console.print(f"  • Evento: {tipo}")

    # Exibe ocorrência de segurança gerada automaticamente no servidor com Rich Panel
    if ocorrencia_auto:
        formatacao.console.print()
        formatacao.console.print(
            formatacao.Panel(
                f"[bold red]ID Ocorrência :[/] {ocorrencia_auto.get('id')}\n"
                f"[bold red]Prioridade    :[/] {ocorrencia_auto.get('prioridade', 'alta').upper()}\n"
                f"[bold red]Situação      :[/] {ocorrencia_auto.get('situacao', 'aberta').upper()}\n"
                f"[bold white]Regra         :[/] Cenário de falha gera ocorrência de prioridade alta no servidor.",
                title="[bold red]ALERTA DE SEGURANÇA — OCORRÊNCIA AUTOMÁTICA[/]",
                border_style="red",
            )
        )


def simular_cenario_individual() -> None:
    """Executa a simulação de um cenário escolhido para um cruzamento."""
    if sessao.bloquear_se_offline():
        return

    formatacao.imprimir_subtitulo("Simulação de Travessia Individual")
    formatacao.console.print("[dim yellow][ROTULO] DADOS SIMULADOS - Proposta Acadêmica HAWK Cross[/]\n")

    cruzamento_id = selecionar_cruzamento("Cruzamento para a simulação")
    if not cruzamento_id:
        formatacao.imprimir_aviso("Simulação cancelada.")
        return

    tabela_cen = formatacao.Table(show_header=False, box=None)
    tabela_cen.add_column("Opção", style="bold green", width=6)
    tabela_cen.add_column("Cenário", style="bold white", width=12)
    tabela_cen.add_column("Descrição", style="cyan")
    tabela_cen.add_row("1", "Normal", "Travessia dentro do tempo padrão")
    tabela_cen.add_row("2", "Extensão", "Travessia lenta com extensão do tempo de proteção")
    tabela_cen.add_row("3", "Falha", "Anomalia de hardware gerando ocorrência automática")
    tabela_cen.add_row("0", "Cancelar", "Retornar ao menu sem executar")

    formatacao.console.print(
        formatacao.Panel(
            tabela_cen,
            title="[bold cyan]Cenários Disponíveis para Simulação[/]",
            border_style="cyan",
        )
    )

    cenario: str | None = None
    while True:
        try:
            op = input("\nCenário desejado: ").strip()
            if op in ("0", ""):
                formatacao.imprimir_aviso("Simulação cancelada.")
                return
            idx = int(op)
            if idx == 1:
                cenario = "normal"
                break
            elif idx == 2:
                cenario = "extensao"
                break
            elif idx == 3:
                cenario = "falha"
                break
            formatacao.imprimir_erro("Opção inválida. Escolha entre 1, 2 ou 3.")
        except ValueError:
            formatacao.imprimir_erro("Digite um número inteiro.")

    formatacao.console.print(
        f"\n[cyan]Disparando simulação '[bold yellow]{cenario}[/]' para o cruzamento ID: [bold white]{cruzamento_id}[/]...[/]"
    )
    ok, dados_ou_msg, _ = api_client.simular(cruzamento_id, cenario)

    if ok and isinstance(dados_ou_msg, dict):
        formatacao.imprimir_sucesso(f"Simulação '{cenario}' executada com sucesso no servidor!")
        eventos = dados_ou_msg.get("eventos", [])
        exibir_sequencia_eventos(eventos)

        persistencia.registrar_acao(
            "SIMULACAO_INDIVIDUAL",
            {
                "cruzamento_id": cruzamento_id,
                "cenario": cenario,
                "total_eventos": len(eventos),
                "origem": "simulacao_console",
            },
            sucesso=True,
        )
    else:
        formatacao.imprimir_erro(f"Falha ao executar simulação: {dados_ou_msg}")
        persistencia.registrar_acao(
            "SIMULACAO_INDIVIDUAL",
            {"cruzamento_id": cruzamento_id, "cenario": cenario},
            sucesso=False,
        )


def simular_em_lote() -> None:
    """Executa múltiplos ciclos de simulação aleatórios para gerar massa de dados."""
    if sessao.bloquear_se_offline():
        return

    formatacao.imprimir_subtitulo("Simulação em Lote (Geração de Massa de Dados)")
    formatacao.console.print("[dim yellow][ROTULO] DADOS SIMULADOS - Origem fixa: 'simulacao_console'[/]\n")

    cruzamento_id = selecionar_cruzamento("Cruzamento alvo da simulação em lote")
    if not cruzamento_id:
        formatacao.imprimir_aviso("Simulação em lote cancelada.")
        return

    while True:
        try:
            entrada_qtd = input("Quantidade de travessias a simular (ex: 5, 10, 20): ").strip()
            qtd = int(entrada_qtd)
            if 1 <= qtd <= 100:
                break
            formatacao.imprimir_erro("Escolha uma quantidade entre 1 e 100 ciclos.")
        except ValueError:
            formatacao.imprimir_erro("Entrada inválida. Digite um número inteiro.")

    conf = input(f"\nConfirmar a execução de {qtd} simulações em lote? [S/n]: ").strip().lower()
    if conf in ("n", "nao", "não", "no"):
        formatacao.imprimir_aviso("Operação cancelada.")
        return

    formatacao.console.print(f"\n[bold cyan]Iniciando execução de {qtd} ciclos simulados...[/]")
    contagem_cenarios = {"normal": 0, "extensao": 0, "falha": 0}
    total_eventos_gerados = 0
    total_falhas_com_ocorrencia = 0

    # Probabilidades realistas: 70% normal, 20% extensão, 10% falha
    pesos_cenarios = ["normal"] * 7 + ["extensao"] * 2 + ["falha"] * 1

    for i in range(1, qtd + 1):
        cenario_sorteado = random.choice(pesos_cenarios)
        contagem_cenarios[cenario_sorteado] += 1

        formatacao.console.print(
            f"  Ciclo [bold yellow]{i:>2}/{qtd}[/] -> Cenário: [cyan]{cenario_sorteado:<9}[/] ... ",
            end="",
        )
        ok, res, _ = api_client.simular(cruzamento_id, cenario_sorteado)

        if ok and isinstance(res, dict):
            evs = res.get("eventos", [])
            total_eventos_gerados += len(evs)
            tem_oco = any(ev.get("ocorrencia_criada") for ev in evs)
            if tem_oco:
                total_falhas_com_ocorrencia += 1
                formatacao.console.print("[bold red]OK (Ocorrência criada)[/]")
            else:
                formatacao.console.print("[bold green]OK[/]")
        else:
            formatacao.console.print(f"[bold red]FALHA ({res})[/]")

    # Resumo da simulação em lote
    tabela_resumo = formatacao.Table(show_header=False, box=None)
    tabela_resumo.add_column("Métrica", style="bold yellow", width=28)
    tabela_resumo.add_column("Valor", style="white")
    tabela_resumo.add_row("Cruzamento Alvo", str(cruzamento_id))
    tabela_resumo.add_row("Total de Ciclos", f"[bold white]{qtd}[/]")
    tabela_resumo.add_row("Travessias Normais", f"[bold green]{contagem_cenarios['normal']}[/]")
    tabela_resumo.add_row("Extensões de Tempo", f"[bold yellow]{contagem_cenarios['extensao']}[/]")
    tabela_resumo.add_row("Falhas Operacionais", f"[bold red]{contagem_cenarios['falha']}[/]")
    tabela_resumo.add_row("Total de Eventos API", f"[bold cyan]{total_eventos_gerados}[/]")
    tabela_resumo.add_row("Ocorrências Altas Geradas", f"[bold magenta]{total_falhas_com_ocorrencia}[/]")

    formatacao.console.print()
    formatacao.console.print(
        formatacao.Panel(
            tabela_resumo,
            title="[bold cyan]RESUMO DA SIMULAÇÃO EM LOTE [DADOS SIMULADOS][/]",
            border_style="cyan",
        )
    )

    persistencia.registrar_acao(
        "SIMULACAO_LOTE",
        {
            "cruzamento_id": cruzamento_id,
            "quantidade": qtd,
            "distribuicao": contagem_cenarios,
            "total_eventos": total_eventos_gerados,
            "origem": "simulacao_console",
        },
        sucesso=True,
    )


def menu_simulacoes() -> None:
    """Menu principal do módulo de simulações com match/case e formatação Rich."""
    opcoes = [
        ("1", "Executar Simulação Individual (Normal / Extensão / Falha)"),
        ("2", "Executar Simulação em Lote (Geração de massa de dados)"),
        ("0", "Voltar ao menu principal"),
    ]
    while True:
        formatacao.limpar_tela()
        formatacao.titulo_terminal(
            "SIMULAÇÕES DE TRAVESSIA",
            "Massa de Dados e Teste de Proteção Adaptativa (Dados Simulados)",
            "bold cyan",
        )
        formatacao.exibir_menu_painel(
            "MENU DE SIMULAÇÕES",
            opcoes,
            border_style="cyan",
            rodape_info="[AVISO] Dados acadêmicos simulados com origem 'simulacao_console'",
        )

        opcao = input("\nEscolha uma opção: ").strip()

        match opcao:
            case "1":
                formatacao.limpar_tela()
                simular_cenario_individual()
                formatacao.pausar()
            case "2":
                formatacao.limpar_tela()
                simular_em_lote()
                formatacao.pausar()
            case "0":
                break
            case _:
                formatacao.console.print("[bold red]Opção inválida. Tente novamente.[/]")
                formatacao.pausar("Pressione Enter para continuar...")

