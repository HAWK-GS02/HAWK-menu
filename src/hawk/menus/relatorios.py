"""Módulo de emissão, análise e exportação de relatórios operacionais do HAWK Cross."""

from datetime import datetime
from typing import Any
from src.hawk import api_client, config, formatacao, persistencia, sessao


def calcular_relatorio_ocorrencias(ocorrencias: list[dict[str, Any]]) -> dict[str, Any]:
    """Processa a lista de ocorrências com laços e dicionários para gerar estatísticas locais."""
    total = len(ocorrencias)
    por_prioridade = {p: 0 for p in config.PRIORIDADES}
    por_situacao = {s: 0 for s in config.SITUACOES}
    tempos_resolucao_segundos: list[float] = []

    for o in ocorrencias:
        prio = o.get("prioridade", "media")
        por_prioridade[prio] = por_prioridade.get(prio, 0) + 1

        sit = o.get("situacao", "aberta")
        por_situacao[sit] = por_situacao.get(sit, 0) + 1

        if sit == "resolvida":
            criado = o.get("criado_em")
            atualizado = o.get("atualizado_em")
            if criado and atualizado:
                try:
                    dt_ini = datetime.fromisoformat(str(criado))
                    dt_fim = datetime.fromisoformat(str(atualizado))
                    diff = (dt_fim - dt_ini).total_seconds()
                    if diff >= 0:
                        tempos_resolucao_segundos.append(diff)
                except ValueError:
                    pass

    tempo_medio_minutos = (
        sum(tempos_resolucao_segundos) / (len(tempos_resolucao_segundos) * 60)
        if tempos_resolucao_segundos
        else None
    )

    return {
        "total": total,
        "por_prioridade": por_prioridade,
        "por_situacao": por_situacao,
        "total_resolvidas_com_tempo": len(tempos_resolucao_segundos),
        "tempo_medio_resolucao_minutos": tempo_medio_minutos,
    }


def comparar_taxa_extensao(pct_api: float, eventos: list[dict[str, Any]]) -> dict[str, Any]:
    """Compara o percentual de extensões reportado pela API com o calculado localmente a partir de eventos."""
    normais = sum(1 for e in eventos if e.get("tipo") == "travessia_normal")
    extensoes = sum(1 for e in eventos if e.get("tipo") == "travessia_estendida")
    total_travessias = normais + extensoes

    pct_local = (extensoes / total_travessias * 100.0) if total_travessias > 0 else 0.0
    divergencia = abs(pct_api - pct_local)

    return {
        "percentual_api": pct_api,
        "percentual_local": pct_local,
        "total_travessias_amostra": total_travessias,
        "extensoes_amostra": extensoes,
        "divergencia": divergencia,
        "divergencia_relevante": (divergencia > 1.0 and total_travessias > 0),
    }


def oferecer_exportacao(nome_base: str, dados_json: Any, texto_formatado: str) -> None:
    """Pergunta ao usuário se deseja exportar o relatório para arquivo .txt e .json."""
    resp = input("\nDeseja exportar este relatório para arquivo (.txt e .json)? [s/N]: ").strip().lower()
    if resp in ("s", "sim", "y", "yes"):
        arq_json, arq_txt = persistencia.exportar_relatorio(nome_base, dados_json, texto_formatado)
        formatacao.imprimir_sucesso(
            f"Relatório exportado com sucesso!\n"
            f"  - JSON : {arq_json}\n"
            f"  - TXT  : {arq_txt}"
        )
        persistencia.registrar_acao("EXPORTAR_RELATORIO", {"nome": nome_base, "json": str(arq_json)}, sucesso=True)


def relatorio_resumo_geral() -> None:
    """Gera e exibe o relatório de resumo geral do sistema."""
    formatacao.imprimir_subtitulo("Relatório: Resumo Geral do Sistema")

    if sessao.esta_offline():
        salvo_em = persistencia.ler_cache("salvo_em") or "data desconhecida"
        formatacao.imprimir_aviso(f"Modo offline. Exibindo resumo do cache salvo em: {salvo_em}")
        dados = persistencia.ler_cache("resumo") or {}
    else:
        ok, res, _ = api_client.relatorio_resumo()
        if ok and isinstance(res, dict):
            dados = res
            persistencia.salvar_cache("resumo", dados)
        else:
            formatacao.imprimir_erro(f"Falha ao consultar API: {res}")
            formatacao.imprimir_aviso("Carregando resumo do cache local...")
            dados = persistencia.ler_cache("resumo") or {}

    total_trav = dados.get("total_travessias", 0)
    total_ext = dados.get("total_extensoes", 0)
    total_fal = dados.get("total_falhas", 0)
    total_oco = dados.get("total_ocorrencias", 0)

    linhas_txt = [
        "============================================================",
        "             HAWK CROSS - RELATÓRIO DE RESUMO GERAL          ",
        "============================================================",
        f"Data/Hora de Geração : {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}",
        "------------------------------------------------------------",
        f"  Total de Travessias Registradas : {total_trav}",
        f"  Total de Extensões de Tempo     : {total_ext}",
        f"  Total de Falhas Detectadas      : {total_fal}",
        f"  Total de Ocorrências Abertas    : {total_oco}",
        "============================================================",
    ]
    texto_formatado = "\n".join(linhas_txt)
    print("\n" + texto_formatado)

    persistencia.registrar_acao("GERAR_RELATORIO_RESUMO", dados, sucesso=True)
    oferecer_exportacao("resumo_geral", dados, texto_formatado)


def relatorio_medias_tempos() -> None:
    """Gera o relatório de médias de tempo e compara taxa de extensões com o histórico de eventos."""
    formatacao.imprimir_subtitulo("Relatório: Médias de Tempos Operacionais")

    if sessao.esta_offline():
        salvo_em = persistencia.ler_cache("salvo_em") or "data desconhecida"
        formatacao.imprimir_aviso(f"Modo offline. Exibindo tempos do cache salvo em: {salvo_em}")
        dados_tempos = persistencia.ler_cache("tempos") or {}
        eventos = persistencia.ler_cache("eventos") or []
    else:
        ok, res, _ = api_client.relatorio_tempos()
        if ok and isinstance(res, dict):
            dados_tempos = res
            persistencia.salvar_cache("tempos", dados_tempos)
        else:
            formatacao.imprimir_erro(f"Falha ao consultar API: {res}")
            dados_tempos = persistencia.ler_cache("tempos") or {}

        ok_ev, evs, _ = api_client.listar_eventos(limite=500)
        eventos = evs if ok_ev and isinstance(evs, list) else (persistencia.ler_cache("eventos") or [])

    espera = float(dados_tempos.get("tempo_medio_espera_s", 0.0))
    travessia = float(dados_tempos.get("tempo_medio_travessia_s", 0.0))
    pct_api = float(dados_tempos.get("percentual_extensoes", 0.0))

    comparacao = comparar_taxa_extensao(pct_api, eventos)

    linhas_txt = [
        "============================================================",
        "           HAWK CROSS - MÉDIAS DE TEMPOS OPERACIONAIS       ",
        "============================================================",
        f"Data/Hora de Geração : {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}",
        "------------------------------------------------------------",
        f"  Tempo Médio de Espera dos Pedestres : {espera:.2f} s",
        f"  Tempo Médio de Travessia            : {travessia:.2f} s",
        f"  Percentual de Extensões (API)       : {pct_api:.2f}%",
        "------------------------------------------------------------",
        "  VALIDAÇÃO LOCAL (Amostra de Eventos):",
        f"  - Travessias na amostra             : {comparacao['total_travessias_amostra']}",
        f"  - Extensões na amostra              : {comparacao['extensoes_amostra']}",
        f"  - Taxa Calculada Localmente         : {comparacao['percentual_local']:.2f}%",
        f"  - Diferença Absoluta                : {comparacao['divergencia']:.2f}%",
    ]
    if comparacao["divergencia_relevante"]:
        linhas_txt.append("  [AVISO] Divergência identificada: A taxa da API considera todo o histórico;")
        linhas_txt.append("          a taxa local baseia-se na amostra recente de eventos consultados.")
    else:
        linhas_txt.append("  [OK] Consistência estatística confirmada entre API e dados locais.")
    linhas_txt.append("============================================================")

    texto_formatado = "\n".join(linhas_txt)
    print("\n" + texto_formatado)

    payload = {"tempos_api": dados_tempos, "comparacao_local": comparacao}
    persistencia.registrar_acao("GERAR_RELATORIO_TEMPOS", payload, sucesso=True)
    oferecer_exportacao("medias_tempos", payload, texto_formatado)


def relatorio_por_cruzamento() -> None:
    """Gera o relatório com métricas por cruzamento com opção de ordenação dinâmica."""
    formatacao.imprimir_subtitulo("Relatório: Métricas por Cruzamento")

    if sessao.esta_offline():
        salvo_em = persistencia.ler_cache("salvo_em") or "data desconhecida"
        formatacao.imprimir_aviso(f"Modo offline. Exibindo dados do cache local salvos em: {salvo_em}")
        cruzamentos_cache = persistencia.ler_cache("cruzamentos") or []
        # Constrói visão aproximada do cache caso offline
        dados_lista = [
            {
                "cruzamento_id": c.get("id"),
                "nome": c.get("nome"),
                "total_travessias": 0,
                "total_extensoes": 0,
                "total_falhas": 0,
                "percentual_extensoes": 0.0,
            }
            for c in cruzamentos_cache
        ]
    else:
        ok, res, _ = api_client.relatorio_por_cruzamento()
        if ok and isinstance(res, list):
            dados_lista = res
        else:
            formatacao.imprimir_erro(f"Falha ao consultar API: {res}")
            formatacao.imprimir_aviso("Carregando lista de cruzamentos do cache...")
            dados_lista = []

    if not dados_lista:
        formatacao.imprimir_aviso("Nenhum dado por cruzamento disponível no momento.")
        return

    print("Opções de ordenação da tabela:")
    print("  [1] Por total de travessias (decrescente)")
    print("  [2] Por total de extensões (decrescente)")
    print("  [3] Por total de falhas (decrescente)")
    print("  [4] Por percentual de extensão (decrescente)")
    print("  [5] Por nome do cruzamento (alfabético A-Z)")

    chave_ord: str = "total_travessias"
    inverter: bool = True

    try:
        entrada_ord = input("Escolha a ordenação [1 a 5, padrão 1]: ").strip()
        op_ord = int(entrada_ord) if entrada_ord else 1
        match op_ord:
            case 1:
                chave_ord = "total_travessias"
                inverter = True
            case 2:
                chave_ord = "total_extensoes"
                inverter = True
            case 3:
                chave_ord = "total_falhas"
                inverter = True
            case 4:
                chave_ord = "percentual_extensoes"
                inverter = True
            case 5:
                chave_ord = "nome"
                inverter = False
            case _:
                print("Opção inválida. Usando ordenação por total de travessias.")
    except ValueError:
        print("Entrada inválida. Usando ordenação padrão.")

    dados_ordenados = sorted(
        dados_lista,
        key=lambda item: (item.get(chave_ord) is not None, item.get(chave_ord, 0 if inverter else "")),
        reverse=inverter,
    )

    print()
    formatacao.formatar_relatorio_cruzamentos(dados_ordenados)

    # Monta texto para exportação
    linhas_txt = [
        "=======================================================================",
        "                 HAWK CROSS - MÉTRICAS POR CRUZAMENTO                  ",
        "=======================================================================",
        f"Data/Hora de Geração : {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}",
        f"Critério de Ordenação: {chave_ord} (inverso: {inverter})",
        "-----------------------------------------------------------------------",
        f"{'#':<3} | {'Cruzamento':<25} | {'Travessias':>10} | {'Extensões':>9} | {'Falhas':>6} | {'% Ext.':>7}",
        "----+---------------------------+------------+-----------+--------+--------",
    ]
    for idx, item in enumerate(dados_ordenados, start=1):
        nome_str = str(item.get("nome") or item.get("cruzamento_id"))[:25]
        trav = item.get("total_travessias", 0)
        ext = item.get("total_extensoes", 0)
        fal = item.get("total_falhas", 0)
        pct = float(item.get("percentual_extensoes", 0.0))
        linhas_txt.append(f"{idx:<3} | {nome_str:<25} | {trav:>10} | {ext:>9} | {fal:>6} | {pct:>6.1f}%")
    linhas_txt.append("=======================================================================")

    texto_formatado = "\n".join(linhas_txt)
    persistencia.registrar_acao("GERAR_RELATORIO_POR_CRUZAMENTO", {"total_itens": len(dados_ordenados)}, sucesso=True)
    oferecer_exportacao("metricas_por_cruzamento", dados_ordenados, texto_formatado)


def relatorio_local_ocorrencias() -> None:
    """Gera análise estatística aprofundada de ocorrências calculada em Python."""
    formatacao.imprimir_subtitulo("Relatório Local: Análise de Ocorrências")

    if sessao.esta_offline():
        salvo_em = persistencia.ler_cache("salvo_em") or "data desconhecida"
        formatacao.imprimir_aviso(f"Modo offline. Exibindo ocorrências do cache local salvos em: {salvo_em}")
        ocorrencias = persistencia.ler_cache("ocorrencias") or []
    else:
        ok, res, _ = api_client.listar_ocorrencias()
        if ok and isinstance(res, list):
            ocorrencias = res
            persistencia.salvar_cache("ocorrencias", ocorrencias)
        else:
            formatacao.imprimir_erro(f"Falha ao consultar API: {res}")
            formatacao.imprimir_aviso("Carregando ocorrências do cache local...")
            ocorrencias = persistencia.ler_cache("ocorrencias") or []

    analise = calcular_relatorio_ocorrencias(ocorrencias)
    tot = analise["total"]

    linhas_txt = [
        "============================================================",
        "        HAWK CROSS - ANÁLISE ESTATÍSTICA DE OCORRÊNCIAS     ",
        "============================================================",
        f"Data/Hora de Geração : {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}",
        "------------------------------------------------------------",
        f"  Total de Ocorrências Registradas: {tot}",
        "",
        "  DISTRIBUIÇÃO POR PRIORIDADE:",
    ]
    for p_nome, qtd in analise["por_prioridade"].items():
        pct = (qtd / tot * 100.0) if tot > 0 else 0.0
        linhas_txt.append(f"    * {p_nome.title():<8}: {qtd:>3} ocorrência(s) ({pct:>5.1f}%)")

    linhas_txt.append("")
    linhas_txt.append("  DISTRIBUIÇÃO POR SITUAÇÃO OPERACIONAL:")
    for s_nome, qtd in analise["por_situacao"].items():
        pct = (qtd / tot * 100.0) if tot > 0 else 0.0
        linhas_txt.append(f"    * {s_nome.title():<14}: {qtd:>3} ocorrência(s) ({pct:>5.1f}%)")

    linhas_txt.append("------------------------------------------------------------")
    t_med = analise["tempo_medio_resolucao_minutos"]
    if t_med is not None:
        linhas_txt.append(f"  Tempo Médio de Resolução (Aberta -> Resolvida): {t_med:.1f} minutos")
        linhas_txt.append(f"  Amostra de ocorrências resolvidas com tempo: {analise['total_resolvidas_com_tempo']}")
    else:
        linhas_txt.append("  Tempo Médio de Resolução: Sem dados (nenhuma ocorrência resolvida com datas)")
    linhas_txt.append("============================================================")

    texto_formatado = "\n".join(linhas_txt)
    print("\n" + texto_formatado)

    persistencia.registrar_acao("GERAR_RELATORIO_LOCAL_OCORRENCIAS", analise, sucesso=True)
    oferecer_exportacao("analise_ocorrencias", analise, texto_formatado)


def relatorio_consolidado() -> None:
    """Consolida Resumo Geral, Tempos, Cruzamentos e Ocorrências em um documento único."""
    formatacao.imprimir_subtitulo("Emissão do Relatório Consolidado do Sistema")
    print("Coletando e consolidando métricas de todos os subsistemas...")

    # 1. Resumo
    if not sessao.esta_offline():
        ok, res_resumo, _ = api_client.relatorio_resumo()
        dados_resumo = res_resumo if ok and isinstance(res_resumo, dict) else (persistencia.ler_cache("resumo") or {})
    else:
        dados_resumo = persistencia.ler_cache("resumo") or {}

    # 2. Tempos
    if not sessao.esta_offline():
        ok, res_tempos, _ = api_client.relatorio_tempos()
        dados_tempos = res_tempos if ok and isinstance(res_tempos, dict) else (persistencia.ler_cache("tempos") or {})
    else:
        dados_tempos = persistencia.ler_cache("tempos") or {}

    # 3. Cruzamentos
    if not sessao.esta_offline():
        ok, res_cruz, _ = api_client.relatorio_por_cruzamento()
        dados_cruz = res_cruz if ok and isinstance(res_cruz, list) else []
    else:
        dados_cruz = []

    # 4. Ocorrências
    if not sessao.esta_offline():
        ok, res_oco, _ = api_client.listar_ocorrencias()
        ocorrencias = res_oco if ok and isinstance(res_oco, list) else (persistencia.ler_cache("ocorrencias") or [])
    else:
        ocorrencias = persistencia.ler_cache("ocorrencias") or []

    # 5. Eventos para validação cruzada
    if not sessao.esta_offline():
        ok, res_ev, _ = api_client.listar_eventos(limite=500)
        eventos = res_ev if ok and isinstance(res_ev, list) else (persistencia.ler_cache("eventos") or [])
    else:
        eventos = persistencia.ler_cache("eventos") or []

    analise_oco = calcular_relatorio_ocorrencias(ocorrencias)
    pct_api = float(dados_tempos.get("percentual_extensoes", 0.0))
    comparacao_ext = comparar_taxa_extensao(pct_api, eventos)

    # Montagem do relatório consolidado
    data_geracao = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    linhas = [
        "#######################################################################",
        "                 HAWK CROSS - RELATÓRIO OPERACIONAL CONSOLIDADO        ",
        "                  Sistema Adaptativo de Travessia Segura               ",
        "#######################################################################",
        f"Data/Hora de Geração : {data_geracao}",
        f"Modo de Operação     : {'OFFLINE (Cache)' if sessao.esta_offline() else 'ONLINE (API)'}",
        "=======================================================================",
        "1. RESUMO GERAL DO SISTEMA",
        "-----------------------------------------------------------------------",
        f"  Total de Travessias Registradas : {dados_resumo.get('total_travessias', 0)}",
        f"  Total de Extensões de Tempo     : {dados_resumo.get('total_extensoes', 0)}",
        f"  Total de Falhas Operacionais    : {dados_resumo.get('total_falhas', 0)}",
        f"  Total de Ocorrências no Sistema : {dados_resumo.get('total_ocorrencias', 0)}",
        "",
        "=======================================================================",
        "2. INDICADORES DE TEMPO E DESEMPENHO",
        "-----------------------------------------------------------------------",
        f"  Tempo Médio de Espera dos Pedestres : {float(dados_tempos.get('tempo_medio_espera_s', 0)):.2f} s",
        f"  Tempo Médio de Travessia            : {float(dados_tempos.get('tempo_medio_travessia_s', 0)):.2f} s",
        f"  Taxa Geral de Extensão (API)        : {pct_api:.2f}%",
        f"  Taxa Validada Localmente (Amostra)  : {comparacao_ext['percentual_local']:.2f}% (Amostra: {comparacao_ext['total_travessias_amostra']} travessias)",
        "",
        "=======================================================================",
        "3. ANÁLISE DE OCORRÊNCIAS",
        "-----------------------------------------------------------------------",
        f"  Total de Ocorrências : {analise_oco['total']}",
        "  Prioridades:",
    ]
    for p_k, p_v in analise_oco["por_prioridade"].items():
        linhas.append(f"    - {p_k.title():<8}: {p_v}")
    linhas.append("  Situações:")
    for s_k, s_v in analise_oco["por_situacao"].items():
        linhas.append(f"    - {s_k.title():<14}: {s_v}")

    t_res = analise_oco["tempo_medio_resolucao_minutos"]
    linhas.append(f"  Tempo Médio de Resolução : {f'{t_res:.1f} minutos' if t_res is not None else 'Sem dados'}")

    linhas.append("")
    linhas.append("=======================================================================")
    linhas.append("4. MÉTRICAS INDIVIDUAIS POR CRUZAMENTO")
    linhas.append("-----------------------------------------------------------------------")
    linhas.append(f"{'#':<3} | {'Cruzamento':<25} | {'Travessias':>10} | {'Extensões':>9} | {'Falhas':>6} | {'% Ext.':>7}")
    linhas.append("----+---------------------------+------------+-----------+--------+--------")
    if dados_cruz:
        for idx, it in enumerate(dados_cruz, start=1):
            n_str = str(it.get("nome") or it.get("cruzamento_id"))[:25]
            tr = it.get("total_travessias", 0)
            ex = it.get("total_extensoes", 0)
            fa = it.get("total_falhas", 0)
            pc = float(it.get("percentual_extensoes", 0.0))
            linhas.append(f"{idx:<3} | {n_str:<25} | {tr:>10} | {ex:>9} | {fa:>6} | {pc:>6.1f}%")
    else:
        linhas.append("  (Sem dados detalhados de cruzamentos disponíveis)")

    linhas.append("=======================================================================")
    linhas.append("[AVISO LEGAL] Este relatório reflete dados de simulação e proposta acadêmica.")
    linhas.append("Não aplicável para controle semafórico real nem segurança viária certificada.")
    linhas.append("#######################################################################")

    texto_formatado = "\n".join(linhas)
    print("\n" + texto_formatado)

    consolidado_payload = {
        "gerado_em": datetime.now().isoformat(),
        "resumo": dados_resumo,
        "tempos": dados_tempos,
        "ocorrencias": analise_oco,
        "cruzamentos": dados_cruz,
        "validacao_extensoes": comparacao_ext,
    }

    persistencia.registrar_acao("GERAR_RELATORIO_CONSOLIDADO", {"cruzamentos": len(dados_cruz)}, sucesso=True)
    oferecer_exportacao("relatorio_consolidado", consolidado_payload, texto_formatado)


def menu_relatorios() -> None:
    """Menu interativo para emissão e exportação de relatórios com match/case e formatação Rich."""
    opcoes = [
        ("1", "Resumo Geral do Sistema (GET /relatorios/resumo)"),
        ("2", "Médias de Tempos Operacionais (GET /relatorios/tempos)"),
        ("3", "Métricas por Cruzamento (com ordenação personalizada)"),
        ("4", "Análise Estatística Local de Ocorrências (Python)"),
        ("5", "Relatório Consolidado Completo (com exportação .txt e .json)"),
        ("0", "Voltar ao menu principal"),
    ]
    while True:
        formatacao.limpar_tela()
        formatacao.titulo_terminal(
            "RELATÓRIOS DO SISTEMA",
            "Métricas Operacionais, Estatísticas e Exportação",
            "bold cyan",
        )
        formatacao.exibir_menu_painel("MENU DE RELATÓRIOS", opcoes, border_style="cyan")

        opcao = input("\nEscolha uma opção: ").strip()

        match opcao:
            case "1":
                formatacao.limpar_tela()
                relatorio_resumo_geral()
                formatacao.pausar()
            case "2":
                formatacao.limpar_tela()
                relatorio_medias_tempos()
                formatacao.pausar()
            case "3":
                formatacao.limpar_tela()
                relatorio_por_cruzamento()
                formatacao.pausar()
            case "4":
                formatacao.limpar_tela()
                relatorio_local_ocorrencias()
                formatacao.pausar()
            case "5":
                formatacao.limpar_tela()
                relatorio_consolidado()
                formatacao.pausar()
            case "0":
                break
            case _:
                formatacao.console.print("[bold red]Opção inválida. Tente novamente.[/]")
                formatacao.pausar("Pressione Enter para continuar...")
