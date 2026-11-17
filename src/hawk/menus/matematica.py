"""Menu interativo para execução de cálculos matemáticos, limites, derivadas, integrais e geração de gráficos."""

from datetime import datetime
from pathlib import Path
from typing import Any
from src.hawk import api_client, config, formatacao, persistencia, sessao
from src.hawk.matematica import derivadas, fila_veiculos, graficos, integrais, limites, modelo
from src.hawk.menus.cruzamentos import selecionar_cruzamento

# Armazena em memória os últimos cálculos para permitir salvamento consolidado em dados/calculos.json
_ultimos_calculos: dict[str, Any] = {
    "cruzamento_id": None,
    "largura_m": 14.0,
    "tempo_minimo_local": 28.33,
    "tempo_minimo_api": None,
    "limites": None,
    "derivadas": None,
    "integrais": None,
    "fila": None,
    "analise_real": None,
}


def calcular_tempo_minimo_comparativo() -> None:
    """1 e 2. Seleciona cruzamento, obtém largura e calcula T_min local e via API, conferindo se coincidem."""
    formatacao.imprimir_subtitulo("Cálculo de Tempo Mínimo Seguro (Local vs API HAWK)")

    cruzamento_id = selecionar_cruzamento("Cruzamento para cálculo")
    L = 14.0
    cruzamento_nome = "Padrão (14m)"

    if cruzamento_id:
        if not sessao.esta_offline():
            ok, dados_cruz, _ = api_client.obter_cruzamento(cruzamento_id)
            if ok and isinstance(dados_cruz, dict):
                L = float(dados_cruz.get("largura_via_m", 14.0))
                cruzamento_nome = str(dados_cruz.get("nome", cruzamento_id))
        else:
            cruzamentos = persistencia.ler_cache("cruzamentos") or []
            item = next((c for c in cruzamentos if c.get("id") == cruzamento_id), None)
            if item:
                L = float(item.get("largura_via_m", 14.0))
                cruzamento_nome = str(item.get("nome", cruzamento_id))

    print(f"\nCruzamento Selecionado: {cruzamento_nome} (Largura da Via: {L:.1f} m)")
    
    # Parâmetros
    v_padrao = config.VELOCIDADE_PADRAO
    m_padrao = config.MARGEM_PADRAO

    # 1. Cálculo local
    t_local = modelo.tempo_minimo(L, v=v_padrao, m=m_padrao)

    # 2. Cálculo via API (GET /calculos/tempo-minimo)
    t_api: float | None = None
    if not sessao.esta_offline():
        ok, res_api, _ = api_client.calcular_tempo_minimo(L, velocidade=v_padrao, margem=m_padrao)
        if ok and isinstance(res_api, dict):
            t_api = float(res_api.get("tempo_minimo_s", 0.0))

    print("\n" + "=" * 65)
    print("  RESULTADOS DO CÁLCULO DE TEMPO MÍNIMO (T_min = L / v + m)")
    print("=" * 65)
    print(f"  Largura da Via (L)           : {L:.2f} m")
    print(f"  Velocidade de Projeto (v)    : {v_padrao:.2f} m/s")
    print(f"  Margem de Segurança (m)      : {m_padrao:.2f} s")
    print(f"  -> Tempo Mínimo (Local)      : {t_local:.2f} s")
    if t_api is not None:
        print(f"  -> Tempo Mínimo (API HAWK)   : {t_api:.2f} s")
        diferenca = abs(t_local - t_api)
        if diferenca < 0.05:
            print("  -> CONFERÊNCIA: Valores coincidem perfeitamente! (Divergência < 0.05s)")
        else:
            print(f"  -> ATENÇÃO: Divergência de {diferenca:.2f}s entre API e cálculo local.")
    else:
        print("  -> Tempo Mínimo (API HAWK)   : Indisponível (modo offline ou sem conexão)")
    print("=" * 65 + "\n")

    _ultimos_calculos["cruzamento_id"] = cruzamento_id
    _ultimos_calculos["largura_m"] = L
    _ultimos_calculos["tempo_minimo_local"] = t_local
    _ultimos_calculos["tempo_minimo_api"] = t_api


def menu_estudo_limites() -> None:
    """3. Apresenta os 4 estudos de limites requeridos na modelagem."""
    formatacao.imprimir_subtitulo("Estudo de Limites Matemáticos no HAWK Cross")
    L = _ultimos_calculos.get("largura_m", 14.0)
    T = _ultimos_calculos.get("tempo_minimo_local", 28.3)

    print("1. LIMITE DE CONTINUIDADE AO FIM DA TRAVESSIA (t -> T-):")
    print(f"   lim_{{t -> {T:.1f}-}} x(t) = {L:.1f} m  e  lim_{{t -> {T:.1f}-}} d(t) = 0.0 m")
    tabela_fim, lim_x, lim_d = limites.limite_fim_travessia(L, T)
    cab_fim = ["Passo h = T - t", "Tempo t (s)", "Posição x(t) (m)", "Distância Restante d(t) (m)"]
    lin_fim = [[f"{h:.6f}", f"{T - h:.6f}", f"{x:.4f}", f"{d:.4f}"] for h, x, d in tabela_fim]
    formatacao.formatar_tabela(cab_fim, lin_fim, alinhamentos=[">", ">", ">", ">"])

    print("\n2. LIMITE LATERAL INFINITO DA VELOCIDADE REQUERIDA (v_req):")
    print(f"   Se o pedestre ainda está na via a {0.3 * L:.1f}m do fim quando o tempo expira:")
    tabela_vreq, interp_vreq = limites.limite_velocidade_requerida(L, T, d_restante=0.3 * L)
    cab_vreq = ["Delta t = T_lim - t (s)", "Velocidade Requerida v_req (m/s)"]
    lin_vreq = [[f"{dt:.3f}", f"{v:.2f}"] for dt, v in tabela_vreq]
    formatacao.formatar_tabela(cab_vreq, lin_vreq, alinhamentos=[">", ">"])
    print(interp_vreq + "\n")

    print("3. LIMITE DO QUOCIENTE DE DIFERENÇAS (Convergência para a Derivada):")
    t_meio = T / 2.0
    tabela_quoc, v_exata = limites.limite_quociente_diferencas(t_meio, L, T)
    cab_quoc = ["Passo h (s)", "Quociente [x(t+h)-x(t)]/h", "v(t) Exata (m/s)", "Erro Absoluto"]
    lin_quoc = [[f"{h:.6f}", f"{q:.6f}", f"{v_exata:.6f}", f"{err:.2e}"] for h, q, err in tabela_quoc]
    formatacao.formatar_tabela(cab_quoc, lin_quoc, alinhamentos=[">", ">", ">", ">"])

    print("4. LIMITE DA DISSIPAÇÃO DA FILA DE VEÍCULOS NO INFINITO:")
    tabela_fila, _, interp_fila = limites.limite_fila_infinito(lambda_chegada=0.20, mu_sat=0.50, Q_pico=5.66)
    cab_fila = ["Tempo pós-liberação (s)", "Fila Q(t) (veículos)"]
    lin_fila = [[f"{t:.1f}", f"{q:.2f}"] for t, q in tabela_fila]
    formatacao.formatar_tabela(cab_fila, lin_fila, alinhamentos=[">", ">"])
    print(interp_fila + "\n")

    _ultimos_calculos["limites"] = {
        "limite_fim": {"limite_x": lim_x, "limite_d": lim_d},
        "velocidade_requerida": tabela_vreq,
        "convergencia_quociente": tabela_quoc,
    }


def menu_analise_derivadas() -> None:
    """4. Apresenta o cálculo de derivadas analíticas vs numéricas e pontos críticos."""
    formatacao.imprimir_subtitulo("Cálculo e Análise de Derivadas")
    L = _ultimos_calculos.get("largura_m", 14.0)
    T = _ultimos_calculos.get("tempo_minimo_local", 28.3)

    t_teste = T / 2.0
    dados = derivadas.comparar_velocidades(L, T, t_teste)

    print("\n" + "=" * 65)
    print("  COMPARAÇÃO DA VELOCIDADE: DERIVADA ANALÍTICA VS NUMÉRICA")
    print("=" * 65)
    print(f"  Instante Avaliado (t = T/2)   : {t_teste:.2f} s")
    print(f"  Velocidade Analítica v(t)     : {dados['v_analitica']:.6f} m/s")
    print(f"  Derivada Numérica (Diferença) : {dados['v_numerica']:.6f} m/s")
    print(f"  Erro Absoluto |v_num - v_ana| : {dados['erro_absoluto']:.2e} m/s")
    print("-----------------------------------------------------------------")
    print(f"  Velocidade Média Constante    : {dados['v_constante']:.2f} m/s")
    print(f"  Velocidade Inicial v(0)       : {dados['v_inicio']:.2f} m/s (Repouso inicial)")
    print(f"  Velocidade Final v(T)         : {dados['v_fim']:.2f} m/s (Repouso final)")
    print(f"  Velocidade Máxima (t = T/2)   : {dados['v_ponto_medio']:.2f} m/s (1.5 * v_med)")
    print("=" * 65 + "\n")

    _ultimos_calculos["derivadas"] = dados


def menu_analise_integrais() -> None:
    """5. Apresenta o cálculo de integrais numéricas (Trapézio e Simpson) e recuperação de L."""
    formatacao.imprimir_subtitulo("Cálculo de Integrais Numéricas: Deslocamento Total")
    L = _ultimos_calculos.get("largura_m", 14.0)
    T = _ultimos_calculos.get("tempo_minimo_local", 28.3)

    print(f"Calculando ∫_0^{T:.1f} v(t) dt para recuperar o deslocamento L = {L:.1f} m:")
    resultados = integrais.verificar_deslocamento_total(L, T, [10, 100, 1000])

    cabecalhos = ["Subintervalos n", "Trapézio (m)", "Erro Trapézio", "Simpson (m)", "Erro Simpson"]
    linhas = []
    for r in resultados:
        linhas.append([
            r["n"],
            f"{r['trapezio']:.8f}",
            f"{r['erro_trapezio']:.2e}",
            f"{r['simpson']:.8f}",
            f"{r['erro_simpson']:.2e}",
        ])
    formatacao.formatar_tabela(cabecalhos, linhas, alinhamentos=[">", ">", ">", ">", ">"])

    print("Tempos para atingir frações da travessia:")
    for pct in [25.0, 50.0, 75.0, 100.0]:
        t_pct = integrais.tempo_para_atingir_percentual(L, T, pct)
        print(f"  * {pct:>5.1f}% da travessia ({pct*L/100.0:>4.1f} m) atingido em t = {t_pct:.2f} s")
    print()

    _ultimos_calculos["integrais"] = {"convergencia": resultados}


def menu_fila_veiculos() -> None:
    """6. Apresenta a modelagem da fila de veículos com parâmetros configuráveis."""
    formatacao.imprimir_subtitulo("Modelo de Fila de Veículos dQ/dt = λ - μ(t)")
    print("[ROTULO] PARÂMETROS SIMULADOS (Premissas de Engenharia de Tráfego):")

    try:
        entrada_lam = input(f"Taxa de chegada λ [padrão {fila_veiculos.LAMBDA_PADRAO:.2f} veíc/s]: ").strip().replace(",", ".")
        lam = float(entrada_lam) if entrada_lam else fila_veiculos.LAMBDA_PADRAO
        if lam <= 0:
            lam = fila_veiculos.LAMBDA_PADRAO
    except ValueError:
        lam = fila_veiculos.LAMBDA_PADRAO

    try:
        entrada_mu = input(f"Capacidade de saturação μ_sat [padrão {fila_veiculos.MU_SAT_PADRAO:.2f} veíc/s]: ").strip().replace(",", ".")
        mu = float(entrada_mu) if entrada_mu else fila_veiculos.MU_SAT_PADRAO
        if mu <= 0:
            mu = fila_veiculos.MU_SAT_PADRAO
    except ValueError:
        mu = fila_veiculos.MU_SAT_PADRAO

    T_min = _ultimos_calculos.get("tempo_minimo_local", 28.3)
    comp = fila_veiculos.comparar_cenarios_fila(T_min, percentual_extensao=0.25, lambda_chegada=lam, mu_sat=mu)

    print("\n" + "=" * 65)
    print("  COMPARAÇÃO: CENÁRIO NORMAL VS CENÁRIO COM EXTENSÃO HAWK")
    print("=" * 65)
    print(f"  Taxa de Chegada (λ)                     : {lam:.2f} veíc/s")
    print(f"  Taxa de Escoamento (μ_sat)              : {mu:.2f} veíc/s")
    print(f"  Tempo Verde Pedestres Normal (T_min)    : {comp['T_min']:.1f} s")
    print(f"  Tempo Verde Estendido (T_ext)           : {comp['T_ext']:.1f} s (+{comp['percentual_extensao']:.0f}%)")
    print("-----------------------------------------------------------------")
    print(f"  Fila Máxima no Cenário Normal           : {comp['normal']['Q_pico']:.1f} veículos")
    print(f"  Fila Máxima no Cenário Estendido        : {comp['extensao']['Q_pico']:.1f} veículos")
    print(f"  Veículos Adicionais Acumulados no Pico  : +{comp['veiculos_extras_pico']:.1f} veículos")
    print("-----------------------------------------------------------------")
    if comp["normal"]["dissipa"]:
        print(f"  Tempo para Dissipação (Normal)          : {comp['normal']['tempo_dissipacao']:.1f} s")
        print(f"  Tempo para Dissipação (Estendido)       : {comp['extensao']['tempo_dissipacao']:.1f} s")
        print(f"  Acréscimo no Tempo de Dissipação        : +{comp['tempo_extra_dissipacao']:.1f} s")
        print(f"  Atraso Veicular Total Adicional         : +{comp['atraso_adicional_veic_s']:.1f} veíc·s")
    else:
        print("  [ALERTA] λ >= μ_sat: A capacidade da via é insuficiente; a fila cresce sem dissipar.")
    print("=" * 65 + "\n")

    _ultimos_calculos["fila"] = {
        "lambda": lam,
        "mu_sat": mu,
        "Q_pico_normal": comp["normal"]["Q_pico"],
        "Q_pico_ext": comp["extensao"]["Q_pico"],
        "veiculos_extras": comp["veiculos_extras_pico"],
        "atraso_adicional": comp["atraso_adicional_veic_s"],
    }


def analisar_dados_reais_api() -> None:
    """7. Baixa eventos da API com tempo_travessia_s, calcula velocidades e classifica travessias."""
    formatacao.imprimir_subtitulo("Análise Matemática de Dados Reais da API")
    L = _ultimos_calculos.get("largura_m", 14.0)
    T_min = _ultimos_calculos.get("tempo_minimo_local", 28.3)

    if sessao.esta_offline():
        formatacao.imprimir_aviso("Modo offline. Carregando eventos do cache local...")
        eventos = persistencia.ler_cache("eventos") or []
        dados_tempos = persistencia.ler_cache("tempos") or {}
    else:
        print("Baixando eventos da API HAWK...")
        ok, evs, _ = api_client.listar_eventos(limite=500)
        eventos = evs if ok and isinstance(evs, list) else (persistencia.ler_cache("eventos") or [])
        ok_t, t_api, _ = api_client.relatorio_tempos()
        dados_tempos = t_api if ok_t and isinstance(t_api, dict) else {}

    # Filtra eventos com tempo de travessia válido
    travessias_validas = [e for e in eventos if e.get("tempo_travessia_s") is not None and float(e["tempo_travessia_s"]) > 0]

    if not travessias_validas:
        formatacao.imprimir_aviso("Nenhum evento com tempo de travessia registrado para análise.")
        return

    # Contagem e classificação de cada travessia
    contagem_classificacao = {"normal": 0, "estendida": 0, "critica": 0}
    soma_v = 0.0

    print(f"\nTotal de eventos com travessia analisados: {len(travessias_validas)}")
    for ev in travessias_validas:
        t_trav = float(ev["tempo_travessia_s"])
        v_ind = L / t_trav
        soma_v += v_ind
        cls = modelo.classificar_travessia(t_trav, T_min)
        contagem_classificacao[cls] += 1

    total_validas = len(travessias_validas)
    v_medio = soma_v / total_validas if total_validas > 0 else 0.0
    pct_estendidas_local = (contagem_classificacao["estendida"] / total_validas * 100.0) if total_validas > 0 else 0.0
    pct_extensoes_api = float(dados_tempos.get("percentual_extensoes", 0.0))

    print("\n" + "=" * 65)
    print("  ESTATÍSTICAS DA AMOSTRA DE TRAVESSIAS REAIS")
    print("=" * 65)
    print(f"  Total de Amostras Avaliadas : {total_validas}")
    print(f"  Velocidade Média Observada  : {v_medio:.2f} m/s (Referência: {config.VELOCIDADE_PADRAO:.2f} m/s)")
    print(f"  Classificação das Travessias:")
    print(f"    - Normais (T <= T_min)    : {contagem_classificacao['normal']} ({contagem_classificacao['normal']/total_validas*100:.1f}%)")
    print(f"    - Estendidas (HAWK Cross) : {contagem_classificacao['estendida']} ({pct_estendidas_local:.1f}%)")
    print(f"    - Críticas (> 1.40*T_min) : {contagem_classificacao['critica']} ({contagem_classificacao['critica']/total_validas*100:.1f}%)")
    print("-----------------------------------------------------------------")
    print(f"  Taxa de Extensão da API     : {pct_extensoes_api:.1f}%")
    print(f"  Taxa Calculada na Amostra   : {pct_estendidas_local:.1f}%")
    print(f"  Diferença Absoluta          : {abs(pct_extensoes_api - pct_estendidas_local):.1f}%")
    print("=" * 65 + "\n")

    _ultimos_calculos["analise_real"] = {
        "total_amostras": total_validas,
        "velocidade_media": v_medio,
        "classificacao": contagem_classificacao,
        "taxa_extensao_amostra": pct_estendidas_local,
        "taxa_extensao_api": pct_extensoes_api,
    }


def menu_gerar_graficos() -> None:
    """8. Gera todos os 7 gráficos de uma vez e lista os arquivos salvos."""
    formatacao.imprimir_subtitulo("Geração dos 7 Gráficos Técnicos com Matplotlib")
    L = _ultimos_calculos.get("largura_m", 14.0)
    T = _ultimos_calculos.get("tempo_minimo_local", 28.3)

    eventos = persistencia.ler_cache("eventos") or []
    if not sessao.esta_offline():
        ok, evs, _ = api_client.listar_eventos(limite=200)
        if ok and isinstance(evs, list):
            eventos = evs

    caminhos = graficos.gerar_todos_os_graficos(L=L, T_min=T, eventos=eventos)

    formatacao.imprimir_sucesso("Todos os 7 gráficos gerados com sucesso em 'graficos/':")
    for idx, cam in enumerate(caminhos, start=1):
        print(f"  [{idx}] {cam.name:<34} ({cam.stat().st_size:,} bytes)")
    print()

    persistencia.registrar_acao("GERAR_GRAFICOS_MATEMATICA", {"total": len(caminhos)}, sucesso=True)


def salvar_resultados_calculos() -> None:
    """9. Salva os resultados das modelagens em dados/calculos.json e registra no histórico local."""
    formatacao.imprimir_subtitulo("Persistência dos Resultados em dados/calculos.json")

    caminho_arq = config.DIR_DADOS / "calculos.json"
    _ultimos_calculos["salvo_em"] = datetime.now().isoformat()

    sucesso = persistencia.salvar_json(caminho_arq, _ultimos_calculos)
    if sucesso:
        formatacao.imprimir_sucesso(f"Resultados dos cálculos matemáticos salvos em:\n  {caminho_arq}")
        persistencia.registrar_acao("SALVAR_CALCULOS_JSON", {"arquivo": str(caminho_arq)}, sucesso=True)
    else:
        formatacao.imprimir_erro("Falha ao salvar o arquivo dados/calculos.json.")


def menu_matematica() -> None:
    """Menu principal do módulo de modelagem matemática com match/case."""
    while True:
        formatacao.imprimir_titulo("Modelagem Matemática do HAWK Cross (Entrega 06)")
        print("  [1] Selecionar Cruzamento e Obter Parâmetros (Largura L)")
        print("  [2] Calcular Tempo Mínimo Seguro (Local vs API /calculos/tempo-minimo)")
        print("  [3] Estudo dos 4 Limites Matemáticos (Continuidade, Assíntota, Fila)")
        print("  [4] Análise de Derivadas (Diferença Central vs Analítica, v_max)")
        print("  [5] Análise de Integrais (Trapézio, Simpson e Deslocamento L)")
        print("  [6] Dinâmica da Fila de Veículos (Parâmetros configuráveis λ e μ)")
        print("  [7] Análise de Dados Reais (/eventos, Velocidades e Classificação)")
        print("  [8] Gerar Todos os 7 Gráficos com Matplotlib (.png)")
        print("  [9] Salvar Resultados em dados/calculos.json")
        print("  [0] Voltar ao menu principal\n")

        try:
            entrada = input("Opção desejada: ").strip()
            opcao = int(entrada)
        except ValueError:
            print("Entrada inválida. Digite um número de 0 a 9.")
            continue

        match opcao:
            case 1 | 2:
                calcular_tempo_minimo_comparativo()
            case 3:
                menu_estudo_limites()
            case 4:
                menu_analise_derivadas()
            case 5:
                menu_analise_integrais()
            case 6:
                menu_fila_veiculos()
            case 7:
                analisar_dados_reais_api()
            case 8:
                menu_gerar_graficos()
            case 9:
                salvar_resultados_calculos()
            case 0:
                break
            case _:
                print("Opção inválida. Escolha entre 0 e 9.")
