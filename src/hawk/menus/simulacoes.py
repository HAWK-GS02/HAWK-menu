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

    # Exibe ocorrência de segurança gerada automaticamente no servidor
    if ocorrencia_auto:
        print("\n" + "!" * 70)
        print("  [ALERTA DE SEGURANÇA] OCORRÊNCIA AUTOMÁTICA GERADA PELO SERVIDOR")
        print(f"  ID Ocorrência : {ocorrencia_auto.get('id')}")
        print(f"  Prioridade    : {ocorrencia_auto.get('prioridade', 'alta').upper()}")
        print(f"  Situação      : {ocorrencia_auto.get('situacao', 'aberta').upper()}")
        print("  Regra         : Cenário de falha gera ocorrência de prioridade alta.")
        print("!" * 70 + "\n")


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
    print("\n" + "=" * 60)
    print("  RESUMO DA SIMULAÇÃO EM LOTE [DADOS SIMULADOS]")
    print("=" * 60)
    print(f"  Cruzamento Alvo        : {cruzamento_id}")
    print(f"  Total de Ciclos        : {qtd}")
    print(f"  - Travessias Normais   : {contagem_cenarios['normal']}")
    print(f"  - Extensões de Tempo   : {contagem_cenarios['extensao']}")
    print(f"  - Falhas Operacionais  : {contagem_cenarios['falha']}")
    print(f"  Total de Eventos API   : {total_eventos_gerados}")
    print(f"  Ocorrências Altas      : {total_falhas_com_ocorrencia}")
    print("=" * 60 + "\n")

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
    """Menu principal do módulo de simulações com match/case."""
    while True:
        formatacao.imprimir_titulo("Simulações de Travessia - HAWK Cross")
        print("[AVISO LEGAL] Todos os dados gerados são acadêmicos e simulados.")
        print("  [1] Executar Simulação Individual (Normal / Extensão / Falha)")
        print("  [2] Executar Simulação em Lote (Geração de massa de dados)")
        print("  [0] Voltar ao menu principal\n")

        try:
            entrada = input("Opção desejada: ").strip()
            opcao = int(entrada)
        except ValueError:
            print("Entrada inválida. Digite um número de 0 a 2.")
            continue

        match opcao:
            case 1:
                simular_cenario_individual()
            case 2:
                simular_em_lote()
            case 0:
                break
            case _:
                print("Opção inválida. Escolha entre 0 e 2.")
