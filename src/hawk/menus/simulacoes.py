"""Módulo de simulação de travessias e falhas no HAWK Cross.

Permite simular cenários individuais (normal, extensão, falha) e simulações em lote
para geração de massa de dados. Todas as saídas são rotuladas como dados simulados.
"""

import random
from typing import Any
from src.hawk import api_client, config, formatacao, persistencia, sessao
from src.hawk.menus.cruzamentos import selecionar_cruzamento


def exibir_sequencia_eventos(eventos: list[dict[str, Any]]) -> None:
    """Exibe e interpreta a sequência de eventos resultante de uma simulação."""
    print("\n--- SEQUÊNCIA DE EVENTOS DA SIMULAÇÃO (Origem: simulacao_console) ---")
    cabecalhos = ["Passo", "Tipo", "Estado", "Espera (s)", "Trav. (s)", "Acionador"]
    linhas = []

    ocorrencia_auto: dict[str, Any] | None = None

    for i, ev in enumerate(eventos, start=1):
        tipo = ev.get("tipo", "")
        estado = ev.get("estado", "")
        esp = ev.get("tempo_espera_s")
        esp_str = f"{float(esp):.1f}" if esp is not None else "-"
        trav = ev.get("tempo_travessia_s")
        trav_str = f"{float(trav):.1f}" if trav is not None else "-"
        acionador = "SIM" if ev.get("acionador") else "NÃO"

        linhas.append([i, tipo, estado, esp_str, trav_str, acionador])

        if ev.get("ocorrencia_criada"):
            ocorrencia_auto = ev["ocorrencia_criada"]

    formatacao.formatar_tabela(cabecalhos, linhas, alinhamentos=["^", "<", "<", ">", ">", "^"])

    # Interpretação dos eventos com match/case
    print("Interpretação da simulação:")
    for ev in eventos:
        tipo = ev.get("tipo", "")
        match tipo:
            case "deteccao":
                print("  * Pedestre detectado aguardando na calçada.")
            case "travessia_normal":
                t = ev.get("tempo_travessia_s", 0)
                print(f"  * Travessia concluída dentro do tempo seguro padrão ({t:.1f}s).")
            case "travessia_estendida":
                t = ev.get("tempo_travessia_s", 0)
                print(f"  * [EXTENSÃO] Pedestre necessitou de tempo adicional: semáforo estendido ({t:.1f}s).")
            case "falha":
                print("  * [FALHA DETECTADA] Anomalia operacional detectada no cruzamento.")
            case _:
                print(f"  * Evento: {tipo}")

    # Exibe ocorrência de segurança gerada automaticamente no servidor com Rich Panel
    if ocorrencia_auto:
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
    print("[ROTULO] DADOS SIMULADOS - Proposta Acadêmica HAWK Cross")

    cruzamento_id = selecionar_cruzamento("Cruzamento para a simulação")
    if not cruzamento_id:
        print("Simulação cancelada.")
        return

    print("\nEscolha o cenário a ser simulado:")
    print("  [1] Normal (travessia dentro do tempo padrão)")
    print("  [2] Extensao (travessia lenta com extensão do tempo de proteção)")
    print("  [3] Falha (anomalia de hardware gerando ocorrência automática)")
    print("  [0] Cancelar")

    cenario: str | None = None
    while True:
        try:
            op = input("Cenário desejado: ").strip()
            if op in ("0", ""):
                print("Simulação cancelada.")
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
            print("Opção inválida. Escolha entre 1, 2 ou 3.")
        except ValueError:
            print("Digite um número inteiro.")

    print(f"\nDisparando simulação '{cenario}' para o cruzamento ID: {cruzamento_id}...")
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
    print("[ROTULO] DADOS SIMULADOS - Origem fixa: 'simulacao_console'")

    cruzamento_id = selecionar_cruzamento("Cruzamento alvo da simulação em lote")
    if not cruzamento_id:
        print("Simulação em lote cancelada.")
        return

    while True:
        try:
            entrada_qtd = input("Quantidade de travessias a simular (ex: 5, 10, 20): ").strip()
            qtd = int(entrada_qtd)
            if 1 <= qtd <= 100:
                break
            print("Escolha uma quantidade entre 1 e 100 ciclos.")
        except ValueError:
            print("Entrada inválida. Digite um número inteiro.")

    conf = input(f"Confirmar a execução de {qtd} simulações em lote? [S/n]: ").strip().lower()
    if conf in ("n", "nao", "não", "no"):
        print("Operação cancelada.")
        return

    print(f"\nIniciando execução de {qtd} ciclos simulados...")
    contagem_cenarios = {"normal": 0, "extensao": 0, "falha": 0}
    total_eventos_gerados = 0
    total_falhas_com_ocorrencia = 0

    # Probabilidades realistas: 70% normal, 20% extensão, 10% falha
    pesos_cenarios = ["normal"] * 7 + ["extensao"] * 2 + ["falha"] * 1

    for i in range(1, qtd + 1):
        cenario_sorteado = random.choice(pesos_cenarios)
        contagem_cenarios[cenario_sorteado] += 1

        print(f"  Ciclo {i}/{qtd} -> Cenário: {cenario_sorteado:<8} ... ", end="", flush=True)
        ok, res, _ = api_client.simular(cruzamento_id, cenario_sorteado)

        if ok and isinstance(res, dict):
            evs = res.get("eventos", [])
            total_eventos_gerados += len(evs)
            tem_oco = any(ev.get("ocorrencia_criada") for ev in evs)
            if tem_oco:
                total_falhas_com_ocorrencia += 1
                print("OK (Ocorrência criada)")
            else:
                print("OK")
        else:
            print(f"FALHA ({res})")

    # Resumo da simulação em lote
    tabela_resumo = formatacao.Table(show_header=False, box=None)
    tabela_resumo.add_column("Métrica", style="bold yellow", width=26)
    tabela_resumo.add_column("Valor", style="white")
    tabela_resumo.add_row("Cruzamento Alvo", str(cruzamento_id))
    tabela_resumo.add_row("Total de Ciclos", str(qtd))
    tabela_resumo.add_row("Travessias Normais", f"[green]{contagem_cenarios['normal']}[/]")
    tabela_resumo.add_row("Extensões de Tempo", f"[cyan]{contagem_cenarios['extensao']}[/]")
    tabela_resumo.add_row("Falhas Operacionais", f"[red]{contagem_cenarios['falha']}[/]")
    tabela_resumo.add_row("Total de Eventos API", str(total_eventos_gerados))
    tabela_resumo.add_row("Ocorrências Altas Geradas", str(total_falhas_com_ocorrencia))

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
