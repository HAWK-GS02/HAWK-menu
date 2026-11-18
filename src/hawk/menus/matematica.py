"""Menu de modelagem matemática do HAWK Cross (5 opções).

1. Tempo mínimo de proteção (T_min = L/v + margem) 
2. Estudo dos 2 limites fundamentais (continuidade e assíntota v_req -> +infinito)
3. Análise de derivadas (velocidade v(t), aceleração a(t) e v_max em t = T/2)
4. Grandezas acumuladas por integrais (deslocamento L e fila veicular Q(t))
5. Geração dos 3 gráficos técnicos em PNG e análise de dados reais da API
"""

from datetime import datetime
from pathlib import Path
from typing import Any

from src.hawk import api_client, config, formatacao, persistencia, sessao
from src.hawk.matematica import graficos, modelo
from src.hawk.menus.cruzamentos import selecionar_cruzamento

# Estado em memória com parâmetros padrão baseados na entrega simplificada (L = 10m, T = 28s)
_ultimos_calculos: dict[str, Any] = {
    "cruzamento_id": None,
    "cruzamento_nome": "Padrão de Referência (L = 10 m)",
    "largura_m": 10.0,
    "T": 28.0,
    "lambda": modelo.LAMBDA,
    "tempo_minimo_local": 21.67,
    "tempo_minimo_api": None,
    "limites": None,
    "derivadas": None,
    "integrais": None,
    "dado_real_api": None,
    "graficos": None,
    "salvo_em": None,
}


def _salvar_estado_em_arquivo() -> None:
    """Salva automaticamente o dicionário de cálculos em dados/calculos.json."""
    caminho = config.DIR_DADOS / "calculos.json"
    _ultimos_calculos["salvo_em"] = datetime.now().isoformat()
    sucesso = persistencia.salvar_json(caminho, _ultimos_calculos)
    if sucesso:
        persistencia.registrar_acao(
            "ATUALIZAR_CALCULOS_MATEMATICA",
            {"arquivo": str(caminho), "largura_m": _ultimos_calculos["largura_m"]},
            sucesso=True,
        )


def pedir_tempo_travessia(sugestao: float = 28.0) -> float:
    """Solicita e valida o tempo total de travessia do pedestre (T > 0)."""
    while True:
        entrada = (
            input(f"Tempo de travessia do pedestre T em segundos [padrão {sugestao:.1f}s]: ")
            .strip()
            .replace(",", ".")
        )
        if not entrada:
            return sugestao
        try:
            val = float(entrada)
            if val > 0:
                return val
            print("  [ERRO] O tempo T deve ser estritamente maior que zero.")
        except ValueError:
            print("  [ERRO] Entrada inválida. Digite um número positivo.")


def pedir_taxa_chegada(sugestao: float = modelo.LAMBDA) -> float:
    """Solicita e valida a taxa de chegada de veículos λ (lambda > 0)."""
    entrada = (
        input(f"Taxa de chegada de veículos λ [padrão {sugestao:.2f} veíc/s]: ")
        .strip()
        .replace(",", ".")
    )
    if not entrada:
        return sugestao
    try:
        val = float(entrada)
        if val > 0:
            return val
        print(f"  [AVISO] Valor não positivo; adotando padrão {sugestao:.2f} veíc/s.")
        return sugestao
    except ValueError:
        print(f"  [AVISO] Entrada inválida; adotando padrão {sugestao:.2f} veíc/s.")
        return sugestao


def calcular_tempo_minimo_comparativo() -> None:
    """1. Seleciona cruzamento, obtém largura L e calcula """
    formatacao.imprimir_subtitulo("1. Tempo Mínimo Seguro de Proteção (T_min = L / v_ref + margem)")

    cruzamento_id = selecionar_cruzamento("Cruzamento para obter a largura da via L")
    L = 10.0
    cruzamento_nome = "Padrão de Referência (L = 10 m)"

    if cruzamento_id:
        if not sessao.esta_offline():
            ok, dados_cruz, _ = api_client.obter_cruzamento(cruzamento_id)
            if ok and isinstance(dados_cruz, dict):
                L = float(dados_cruz.get("largura_via_m", 10.0))
                cruzamento_nome = str(dados_cruz.get("nome", cruzamento_id))
        else:
            cruzamentos = persistencia.ler_cache("cruzamentos") or []
            item = next((c for c in cruzamentos if c.get("id") == cruzamento_id), None)
            if item:
                L = float(item.get("largura_via_m", 10.0))
                cruzamento_nome = str(item.get("nome", cruzamento_id))

    print(f"\nCruzamento Ativo: {cruzamento_nome}")
    print(f"Largura da Via (L): {L:.2f} metros")

    # 1. Cálculo local via modelo analítico
    t_local = modelo.tempo_minimo(L, v=modelo.VELOCIDADE_REF, margem=modelo.MARGEM)

    # 2. Consulta à API HAWK (GET /calculos/tempo-minimo)
    t_api: float | None = None
    if not sessao.esta_offline():
        ok, res_api, _ = api_client.calcular_tempo_minimo(
            L, velocidade=modelo.VELOCIDADE_REF, margem=modelo.MARGEM
        )
        if ok and isinstance(res_api, dict):
            t_api = float(res_api.get("tempo_minimo_s", 0.0))

    # Exibe resultados em painel estilizado com Rich
    tabela_min = formatacao.Table(show_header=False, box=None)
    tabela_min.add_column("Parâmetro", style="bold yellow", width=30)
    tabela_min.add_column("Valor", style="white")
    tabela_min.add_row("Largura da Via (L)", f"{L:.2f} m")
    tabela_min.add_row("Velocidade de Ref. (v_ref)", f"{modelo.VELOCIDADE_REF:.2f} m/s (pedestre vulnerável)")
    tabela_min.add_row("Margem de Segurança (m)", f"{modelo.MARGEM:.2f} s")
    tabela_min.add_row("Tempo Mínimo (Local)", f"[bold green]{t_local:.2f} s[/]")
    if t_api is not None:
        tabela_min.add_row("Tempo Mínimo (API HAWK)", f"[bold green]{t_api:.2f} s[/]")
        diferenca = abs(t_local - t_api)
        if diferenca < 0.05:
            tabela_min.add_row("Conferência", "[bold green]Valores coincidem perfeitamente! (< 0.05s)[/]")
        else:
            tabela_min.add_row("Conferência", f"[bold yellow]Divergência de {diferenca:.2f}s entre API e local[/]")
    else:
        tabela_min.add_row("Tempo Mínimo (API HAWK)", "[dim]Indisponível (modo offline)[/]")

    formatacao.console.print(
        formatacao.Panel(
            tabela_min,
            title="[bold cyan]RESULTADOS DO CÁLCULO DE TEMPO MÍNIMO (T_min = L / v_ref + margem)[/]",
            border_style="cyan",
        )
    )

    _ultimos_calculos["cruzamento_id"] = cruzamento_id
    _ultimos_calculos["cruzamento_nome"] = cruzamento_nome
    _ultimos_calculos["largura_m"] = L
    _ultimos_calculos["tempo_minimo_local"] = t_local
    _ultimos_calculos["tempo_minimo_api"] = t_api
    _salvar_estado_em_arquivo()


def menu_estudo_limites() -> None:
    """2. Apresenta os 2 limites fundamentais da entrega simplificada."""
    formatacao.imprimir_subtitulo("2. Estudo dos Limites Matemáticos e Interpretação")

    L = float(_ultimos_calculos.get("largura_m", 10.0))
    T_sugerido = float(_ultimos_calculos.get("T", 28.0))
    T = pedir_tempo_travessia(T_sugerido)
    _ultimos_calculos["T"] = T

    T_min = modelo.tempo_minimo(L)

    formatacao.console.rule("[bold cyan]LIMITE 1: CHEGADA AO OUTRO LADO DA VIA (CONTINUIDADE)[/]")
    formatacao.console.print(
        formatacao.Panel(
            f"[bold]lim_{{t -> T-}} x(t) = L[/]\n\n"
            f"Para L = {L:.1f} m e tempo de travessia T = {T:.1f} s: x({T:.1f}) = [bold green]{modelo.posicao(T, L, T):.2f} m[/].\n"
            "[green]Interpretação:[/] A trajetória x(t) é contínua no intervalo fechado [0, T].\n"
            "Ao final do tempo concedido, o pedestre atinge exatamente a calçada oposta.",
            border_style="green",
        )
    )

    formatacao.console.rule("[bold cyan]LIMITE 2: VELOCIDADE EXIGIDA PARA CONCLUIR NO PRAZO[/]")
    formatacao.console.print(
        f"[bold]v_req(t) = [L - x(t)] / (T_min - t)[/] quando [bold]t -> T_min-[/]\n"
        f"Cenário: pedestre lento com T = {T:.1f} s quando o tempo fixo é T_min = {T_min:.2f} s.\n"
        f"Posição em t = T_min: x({T_min:.2f}) ≈ {modelo.posicao(T_min, L, T):.2f} m (faltam {L - modelo.posicao(T_min, L, T):.2f} m).\n"
        "\n[yellow]Aproximação lateral (h = T_min - t):[/]"
    )

    hs = (1.0, 0.1, 0.01, 0.001)
    tabela = modelo.tabela_limite(L, T, T_min, hs=hs)
    cabecalhos = ["Passo h = T_min - t", "Instante t (s)", "Distância Restante d(t)", "v_req(t) Requerida (m/s)"]
    linhas = []
    for h, v_req in tabela:
        t_inst = T_min - h
        d_rest = L - modelo.posicao(t_inst, L, T)
        linhas.append([f"{h:g}", f"{t_inst:.4f}", f"{d_rest:.4f} m", f"{v_req:.2f}"])
    formatacao.formatar_tabela(cabecalhos, linhas, alinhamentos=[">", ">", ">", ">"])

    formatacao.console.print(
        formatacao.Panel(
            "[bold yellow]INTERPRETAÇÃO DO LIMITE 2:[/]\n"
            "Se o pedestre ainda não completou a travessia quando o tempo mínimo T_min se esgota (d(T_min) > 0), "
            "a velocidade exigida para não ser atropelado explode para o infinito ([bold red]v_req -> +infinito[/]).\n"
            "[bold red]Como nenhum ser humano vulnerável consegue correr a essas velocidades, "
            "É ESSE LIMITE QUE JUSTIFICA A REGRA DE EXTENSÃO DO HAWK CROSS.[/]",
            title="[bold red]Fundamentação Teórica da Extensão Semafórica[/]",
            border_style="red",
        )
    )

    _ultimos_calculos["limites"] = {
        "limite_1_x_T": modelo.posicao(T, L, T),
        "limite_2_tabela": [(h, round(v, 2)) for h, v in tabela],
    }
    _salvar_estado_em_arquivo()


def menu_analise_derivadas() -> None:
    """3. Apresenta velocidade v(t) = x'(t), aceleracao a(t) = v'(t) e ponto de maximo."""
    formatacao.imprimir_subtitulo("3. Derivadas e Ponto Crítico de Máxima Velocidade")

    L = float(_ultimos_calculos.get("largura_m", 10.0))
    T_sugerido = float(_ultimos_calculos.get("T", 28.0))
    T = pedir_tempo_travessia(T_sugerido)
    _ultimos_calculos["T"] = T

    v_max = modelo.velocidade_maxima(L, T)
    t_meio = T / 2.0
    v_media = L / T

    tabela_der = formatacao.Table(show_header=False, box=None)
    tabela_der.add_column("Métrica / Ponto", style="bold yellow", width=32)
    tabela_der.add_column("Valor", style="white")
    tabela_der.add_row("Largura da Via (L)", f"{L:.2f} m")
    tabela_der.add_row("Tempo Total de Travessia (T)", f"{T:.2f} s")
    tabela_der.add_row("Velocidade Média (L / T)", f"{v_media:.3f} m/s")
    tabela_der.add_row("Função Velocidade", "v(t) = x'(t) = (6L/T) * (s - s²), s = t/T")
    tabela_der.add_row("Função Aceleração", "a(t) = v'(t) = (6L/T²) * (1 - 2s)")
    tabela_der.add_row("Velocidade Inicial v(0)", f"{modelo.velocidade(0, L, T):.3f} m/s (Repouso inicial)")
    tabela_der.add_row("Velocidade no Meio v(T/2)", f"[bold green]{modelo.velocidade(t_meio, L, T):.3f} m/s (Pico máximo)[/]")
    tabela_der.add_row("Velocidade Final v(T)", f"{modelo.velocidade(T, L, T):.3f} m/s (Repouso final)")
    tabela_der.add_row("Aceleração no Meio a(T/2)", f"{modelo.aceleracao(t_meio, L, T):.4f} m/s² (a = 0)")
    tabela_der.add_row("Ponto Crítico (a(t) = 0)", f"t = T/2 = [cyan]{t_meio:.2f} s[/]")
    tabela_der.add_row("Velocidade Máxima (v_max)", f"[bold green]1,5 * (L / T) = {v_max:.3f} m/s[/]")

    formatacao.console.print(
        formatacao.Panel(
            tabela_der,
            title="[bold cyan]DERIVADAS DA TRAJETÓRIA DO PEDESTRE[/]",
            border_style="cyan",
        )
    )
    formatacao.console.print(
        formatacao.Panel(
            "O pedestre parte do repouso (v(0) = 0), acelera durante a primeira metade da via (a > 0), "
            "atinge a velocidade máxima de 1,5 * v_médio exatamente no centro da faixa (onde a = 0), "
            "e desacelera na segunda metade (a < 0) até parar na calçada oposta.",
            title="[bold green]Interpretação Física[/]",
            border_style="green",
        )
    )

    _ultimos_calculos["derivadas"] = {
        "v_media": round(v_media, 4),
        "v_max": round(v_max, 4),
        "t_critico": round(t_meio, 2),
        "v_inicio": 0.0,
        "v_fim": 0.0,
    }
    _salvar_estado_em_arquivo()


def menu_analise_integrais() -> None:
    """4. Apresenta o deslocamento acumulado e a fila veicular retida."""
    formatacao.imprimir_subtitulo("4. Grandezas Acumuladas por Integrais (Deslocamento e Fila)")

    L = float(_ultimos_calculos.get("largura_m", 10.0))
    T_sugerido = float(_ultimos_calculos.get("T", 28.0))
    T = pedir_tempo_travessia(T_sugerido)
    _ultimos_calculos["T"] = T

    lam_sugerido = float(_ultimos_calculos.get("lambda", modelo.LAMBDA))
    lam = pedir_taxa_chegada(lam_sugerido)
    _ultimos_calculos["lambda"] = lam

    T_min = modelo.tempo_minimo(L)
    desloc = modelo.deslocamento(L)
    q_normal = modelo.fila(T_min, lam)
    q_ext = modelo.fila(T, lam)
    custo = modelo.custo_extensao(T_min, T, lam)

    tabela_int = formatacao.Table(show_header=False, box=None)
    tabela_int.add_column("Grandeza Acumulada", style="bold yellow", width=34)
    tabela_int.add_column("Resultado", style="white")
    tabela_int.add_row("Deslocamento do Pedestre", f"∫₀ᵀ v(t) dt = [bold green]{desloc:.2f} m[/] (Largura L)")
    tabela_int.add_row("Taxa de Chegada Simulada (λ)", f"{lam:.2f} veíc/s")
    tabela_int.add_row("Fila no Tempo Normal (T_min)", f"{q_normal:.2f} veículos")
    tabela_int.add_row("Fila no Tempo Estendido (T)", f"{q_ext:.2f} veículos")
    tabela_int.add_row("Custo da Extensão (+tempo)", f"[bold red]+{custo:.2f} veículos na fila[/]")

    formatacao.console.print(
        formatacao.Panel(
            tabela_int,
            title="[bold cyan]INTEGRAIS E GRANDEZAS ACUMULADAS[/]",
            border_style="cyan",
        )
    )
    formatacao.console.print(
        formatacao.Panel(
            f"Cada segundo de extensão retém apenas {lam:.2f} veículos na fila.\n"
            f"Conceder {T - T_min:.1f} s a mais para a travessia de um idoso custa cerca de [bold]{custo:.1f} veículo[/] a mais.\n"
            "[green]O custo urbano é desprezível diante do benefício da preservação da vida humana.[/]\n"
            "[yellow][AVISO] Premissa simulada de fluxo veicular / Protótipo não homologado.[/]",
            title="[bold green]Impacto e Trade-off Urbano[/]",
            border_style="green",
        )
    )

    _ultimos_calculos["integrais"] = {
        "deslocamento": desloc,
        "fila_normal": round(q_normal, 3),
        "fila_ext": round(q_ext, 3),
        "custo_extensao": round(custo, 3),
    }
    _salvar_estado_em_arquivo()


def menu_gerar_graficos_e_dados_api() -> None:
    """5. Gera os 3 gráficos técnicos em PNG e consulta dados reais da API."""
    formatacao.imprimir_subtitulo("5. Geração de Gráficos e Integração com API HAWK")

    L = float(_ultimos_calculos.get("largura_m", 10.0))
    T = float(_ultimos_calculos.get("T", 28.0))
    lam = float(_ultimos_calculos.get("lambda", modelo.LAMBDA))
    T_min = modelo.tempo_minimo(L)

    # 1. Consulta de dado real da API (GET /relatorios/tempos)
    formatacao.console.print("[yellow][1/2] Consultando relatório de tempos da API HAWK...[/]")
    v_medio_api: float | None = None
    tempo_medio_api: float | None = None
    origem_dados = "Simulação Local (Exemplo de Referência)"

    if not sessao.esta_offline():
        ok, res_tempos, _ = api_client.relatorio_tempos()
        if ok and isinstance(res_tempos, dict):
            t_m = res_tempos.get("tempo_medio_travessia_s")
            if t_m and float(t_m) > 0:
                tempo_medio_api = float(t_m)
                v_medio_api = L / tempo_medio_api
                origem_dados = "API HAWK (/relatorios/tempos)"

    tabela_api = formatacao.Table(show_header=False, box=None)
    tabela_api.add_column("Métrica", style="bold yellow", width=32)
    tabela_api.add_column("Valor", style="white")

    if tempo_medio_api is not None and v_medio_api is not None:
        tabela_api.add_row("Tempo Médio Registrado na API", f"{tempo_medio_api:.2f} s")
        tabela_api.add_row("Velocidade Média Observada", f"[bold green]{v_medio_api:.3f} m/s[/]")
        tabela_api.add_row("Velocidade de Projeto (v_ref)", f"{modelo.VELOCIDADE_REF:.2f} m/s")
        diag = "Público caminha abaixo da referência (extensão necessária)" if v_medio_api < modelo.VELOCIDADE_REF else "Velocidade média adequada"
        tabela_api.add_row("Diagnóstico", diag)
    else:
        v_simulado = L / T
        tabela_api.add_row("Status", "[yellow]Dados remotos não disponíveis (usando simulação)[/]")
        tabela_api.add_row("Tempo de Travessia (T)", f"{T:.1f} s")
        tabela_api.add_row("Velocidade Média Simulada", f"[bold cyan]{v_simulado:.3f} m/s[/]")
        tabela_api.add_row("Comparação com v_ref", f"Pedestre {((modelo.VELOCIDADE_REF - v_simulado) / modelo.VELOCIDADE_REF) * 100:.1f}% mais lento que a norma")

    formatacao.console.print(
        formatacao.Panel(
            tabela_api,
            title=f"[bold cyan]ANÁLISE DE VELOCIDADE MÉDIA OBSERVADA [{origem_dados}][/]",
            border_style="cyan",
        )
    )

    # 2. Geração dos 3 gráficos técnicos
    formatacao.console.print("\n[yellow][2/2] Gerando os 3 gráficos técnicos com matplotlib...[/]")
    caminhos = graficos.gerar_todos_os_graficos(L=L, T=T, T_min=T_min, lam=lam)

    formatacao.imprimir_sucesso("Os 3 gráficos técnicos foram salvos com sucesso em 'graficos/':")
    tabela_graf = formatacao.Table(show_header=True, header_style="bold magenta", box=None)
    tabela_graf.add_column("#", style="bold yellow", width=4)
    tabela_graf.add_column("Arquivo", style="bold green")
    tabela_graf.add_column("Tamanho", style="white")
    for idx, cam in enumerate(caminhos, start=1):
        tamanho_kb = cam.stat().st_size / 1024.0
        tabela_graf.add_row(str(idx), cam.name, f"{tamanho_kb:.1f} KB")
    formatacao.console.print(tabela_graf)

    _ultimos_calculos["dado_real_api"] = {
        "origem": origem_dados,
        "tempo_medio_s": tempo_medio_api,
        "v_medio_mps": round(v_medio_api, 4) if v_medio_api else round(L / T, 4),
    }
    _ultimos_calculos["graficos"] = [str(c.name) for c in caminhos]
    _salvar_estado_em_arquivo()


def menu_matematica() -> None:
    """Menu principal do módulo de modelagem matemática (5 opções com match/case e formatação Rich)."""
    opcoes = [
        ("1", "Tempo Mínimo Seguro (Local vs API HAWK)"),
        ("2", "Estudo dos Limites (Continuidade e Assíntota v_req -> +infinito)"),
        ("3", "Análise de Derivadas (Velocidade v(t), Aceleração a(t) e v_max)"),
        ("4", "Grandezas Acumuladas por Integrais (Deslocamento L e Fila Q(t))"),
        ("5", "Gerar os 3 Gráficos (.png) e Analisar Dado Real da API"),
        ("0", "Voltar ao menu principal"),
    ]
    while True:
        formatacao.limpar_tela()
        formatacao.titulo_terminal(
            "MODELAGEM MATEMÁTICA — HAWK CROSS",
            "Estudo Analítico de Travessia e Impacto no Tráfego (CitizenTech)",
            "bold cyan",
        )
        formatacao.exibir_menu_painel(
            "MENU DE MODELAGEM MATEMÁTICA",
            opcoes,
            border_style="cyan",
            rodape_info="[AVISO] Premissas simuladas de tráfego | Protótipo acadêmico não homologado",
        )

        opcao = input("\nEscolha uma opção: ").strip()

        match opcao:
            case "1":
                formatacao.limpar_tela()
                calcular_tempo_minimo_comparativo()
                formatacao.pausar()
            case "2":
                formatacao.limpar_tela()
                menu_estudo_limites()
                formatacao.pausar()
            case "3":
                formatacao.limpar_tela()
                menu_analise_derivadas()
                formatacao.pausar()
            case "4":
                formatacao.limpar_tela()
                menu_analise_integrais()
                formatacao.pausar()
            case "5":
                formatacao.limpar_tela()
                menu_gerar_graficos_e_dados_api()
                formatacao.pausar()
            case "0":
                break
            case _:
                formatacao.console.print("[bold red]Opção inválida. Tente novamente.[/]")
                formatacao.pausar("Pressione Enter para continuar...")
