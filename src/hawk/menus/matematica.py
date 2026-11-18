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

    print("\n" + "=" * 65)
    print("  RESULTADOS DO CÁLCULO DE TEMPO MÍNIMO REGULAMENTAR")
    print("=" * 65)
    print(f"  Largura da Via (L)           : {L:.2f} m")
    print(f"  Velocidade de Ref. (v_ref)   : {modelo.VELOCIDADE_REF:.2f} m/s (pedestre vulnerável)")
    print(f"  Margem de Segurança (m)      : {modelo.MARGEM:.2f} s")
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

    print("\n" + "-" * 65)
    print("  LIMITE 1: CHEGADA AO OUTRO LADO DA VIA (CONTINUIDADE)")
    print("  lim_{t -> T-} x(t) = L")
    print("-" * 65)
    print(f"  Para L = {L:.1f} m e tempo real de travessia T = {T:.1f} s:")
    print(f"  x({T:.1f}) = {modelo.posicao(T, L, T):.2f} m.")
    print("  Interpretação: a trajetória x(t) é contínua no intervalo fechado [0, T].")
    print("  Ao final do tempo concedido, o pedestre atinge exatamente a calçada oposta.")

    print("\n" + "-" * 65)
    print("  LIMITE 2: VELOCIDADE EXIGIDA PARA CONCLUIR NO PRAZO")
    print("  v_req(t) = [L - x(t)] / (T_min - t)  quando  t -> T_min-")
    print("-" * 65)
    print(f"  Cenário: pedestre lento com T = {T:.1f} s quando o tempo fixo é T_min = {T_min:.2f} s.")
    print(f"  Posição em t = T_min: x({T_min:.2f}) ≈ {modelo.posicao(T_min, L, T):.2f} m (faltam {L - modelo.posicao(T_min, L, T):.2f} m).")
    print("\n  Aproximação lateral (h = T_min - t):")

    hs = (1.0, 0.1, 0.01, 0.001)
    tabela = modelo.tabela_limite(L, T, T_min, hs=hs)
    cabecalhos = ["Passo h = T_min - t", "Instante t (s)", "Distância Restante d(t)", "v_req(t) Requerida (m/s)"]
    linhas = []
    for h, v_req in tabela:
        t_inst = T_min - h
        d_rest = L - modelo.posicao(t_inst, L, T)
        linhas.append([f"{h:g}", f"{t_inst:.4f}", f"{d_rest:.4f} m", f"{v_req:.2f}"])
    formatacao.formatar_tabela(cabecalhos, linhas, alinhamentos=[">", ">", ">", ">"])

    print("\n  INTERPRETAÇÃO DO LIMITE 2:")
    print("  Se o pedestre ainda não completou a travessia quando o tempo mínimo T_min se")
    print("  esgota (d(T_min) > 0), a velocidade exigida para não ser atropelado explode")
    print("  para o infinito (v_req -> +infinito). Como nenhum ser humano consegue correr a")
    print("  essas velocidades, É ESSE LIMITE QUE JUSTIFICA A REGRA DE EXTENSÃO DO HAWK CROSS.")
    print("=" * 65 + "\n")

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

    print("\n" + "=" * 65)
    print("  DERIVADAS DA TRAJETÓRIA DO PEDESTRE")
    print("=" * 65)
    print(f"  Largura da Via (L)              : {L:.2f} m")
    print(f"  Tempo Total de Travessia (T)    : {T:.2f} s")
    print(f"  Velocidade Média (L / T)        : {v_media:.3f} m/s")
    print("-----------------------------------------------------------------")
    print("  Função Velocidade:  v(t) = x'(t) = (6L/T) * (s - s²), onde s = t/T")
    print("  Função Aceleração:  a(t) = v'(t) = (6L/T²) * (1 - 2s)")
    print("-----------------------------------------------------------------")
    print(f"  Velocidade Inicial v(0)         : {modelo.velocidade(0, L, T):.3f} m/s (Repouso inicial)")
    print(f"  Velocidade no Meio v(T/2)       : {modelo.velocidade(t_meio, L, T):.3f} m/s (Pico máximo)")
    print(f"  Velocidade Final v(T)           : {modelo.velocidade(T, L, T):.3f} m/s (Repouso final)")
    print(f"  Aceleração no Meio a(T/2)       : {modelo.aceleracao(t_meio, L, T):.4f} m/s² (a = 0)")
    print("-----------------------------------------------------------------")
    print(f"  Ponto Crítico (v'(t) = a(t) = 0): t = T/2 = {t_meio:.2f} s")
    print(f"  Velocidade Máxima (v_max)       : 1,5 * (L / T) = {v_max:.3f} m/s")
    print("=" * 65)
    print("\n  INTERPRETAÇÃO FÍSICA:")
    print("  O pedestre parte do repouso (v(0) = 0), acelera durante a primeira metade da via")
    print("  (a > 0), atinge a velocidade máxima de 1,5*v_médio exatamente no centro da faixa")
    print("  (onde a = 0), e desacelera na segunda metade (a < 0) até parar na calçada oposta.")
    print("=" * 65 + "\n")

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

    print("\n" + "=" * 65)
    print("  INTEGRAIS E GRANDEZAS ACUMULADAS")
    print("=" * 65)
    print("  1. DESLOCAMENTO TOTAL DO PEDESTRE:")
    print(f"     ∫₀ᵀ v(t) dt = x(T) - x(0) = L = {desloc:.2f} metros")
    print("     Interpretação: a área sob a curva de velocidade instantânea recupera")
    print("     com precisão analítica exata a extensão total da faixa de pedestres.")
    print("-----------------------------------------------------------------")
    print("  2. FILA DE VEÍCULOS RETIDA NO VERMELHO [PREMISSA SIMULADA]:")
    print(f"     Q(t_fase) = ∫₀^{{t_fase}} λ dt = λ · t_fase  (com λ = {lam:.2f} veíc/s)")
    print(f"     -> Fila ao fim do tempo normal (T_min = {T_min:.2f} s) : {q_normal:.2f} veículos")
    print(f"     -> Fila ao fim do tempo estendido (T = {T:.2f} s)    : {q_ext:.2f} veículos")
    print(f"     -> Custo da extensão (+{T - T_min:.2f} s)              : +{custo:.2f} veículos na fila")
    print("=" * 65)
    print("\n  INTERPRETAÇÃO DO IMPACTO URBANO:")
    print(f"  Cada segundo de extensão custa apenas {lam:.2f} veículos acumulados.")
    print(f"  Conceder {T - T_min:.1f} segundos a mais para que um idoso atravesse com segurança")
    print(f"  custa cerca de {custo:.1f} veículo a mais na fila veicular. O custo urbano é desprezível")
    print("  diante do benefício da segurança da vida humana.")
    print("  [AVISO] Premissa simulada de fluxo veicular / Protótipo não homologado.")
    print("=" * 65 + "\n")

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
    print("[1/2] Consultando relatório de tempos da API HAWK...")
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

    print("\n" + "-" * 65)
    print(f"  ANÁLISE DE VELOCIDADE MÉDIA OBSERVADA [{origem_dados}]")
    print("-" * 65)
    if tempo_medio_api is not None and v_medio_api is not None:
        print(f"  Tempo Médio Registrado na API : {tempo_medio_api:.2f} s")
        print(f"  Velocidade Média Observada    : {v_medio_api:.3f} m/s")
        print(f"  Velocidade de Projeto (v_ref) : {modelo.VELOCIDADE_REF:.2f} m/s")
        if v_medio_api < modelo.VELOCIDADE_REF:
            print("  -> Diagnóstico: O público observado caminha abaixo da referência normativa,")
            print("     comprovando a necessidade de extensão da proteção semafórica.")
        else:
            print("  -> Diagnóstico: Velocidade média superior à de projeto para vulneráveis.")
    else:
        # Exemplo simulado da seção 3 do guia
        v_simulado = L / T
        print(f"  [AVISO] Dados reais da API não disponíveis no momento (ou sem amostras).")
        print(f"  Utilizando exemplo simulado da Seção 3:")
        print(f"  Tempo de Travessia (T)        : {T:.1f} s")
        print(f"  Velocidade Média (L / T)      : {v_simulado:.3f} m/s")
        print(f"  Comparação com v_ref (0,6 m/s): Pedestre {((modelo.VELOCIDADE_REF - v_simulado) / modelo.VELOCIDADE_REF) * 100:.1f}% mais lento que a norma.")

    # 2. Geração dos 3 gráficos técnicos
    print("\n[2/2] Gerando os 3 gráficos técnicos com matplotlib...")
    caminhos = graficos.gerar_todos_os_graficos(L=L, T=T, T_min=T_min, lam=lam)

    formatacao.imprimir_sucesso("Os 3 gráficos técnicos foram salvos com sucesso em 'graficos/':")
    for idx, cam in enumerate(caminhos, start=1):
        tamanho_kb = cam.stat().st_size / 1024.0
        print(f"  [{idx}] {cam.name:<30} ({tamanho_kb:.1f} KB)")
    print()

    _ultimos_calculos["dado_real_api"] = {
        "origem": origem_dados,
        "tempo_medio_s": tempo_medio_api,
        "v_medio_mps": round(v_medio_api, 4) if v_medio_api else round(L / T, 4),
    }
    _ultimos_calculos["graficos"] = [str(c.name) for c in caminhos]
    _salvar_estado_em_arquivo()


def menu_matematica() -> None:
    """Menu principal do módulo de modelagem matemática (5 opções com match/case)."""
    while True:
        formatacao.imprimir_titulo("Modelagem Matemática — HAWK Cross (CitizenTech)")
        print("  [AVISO] Premissas simuladas de tráfego | Protótipo acadêmico não homologado\n")
        print("  [1] Tempo Mínimo Seguro (Local vs API HAWK)")
        print("  [2] Estudo dos Limites (Continuidade e Assíntota v_req -> +infinito)")
        print("  [3] Análise de Derivadas (Velocidade v(t), Aceleração a(t) e v_max)")
        print("  [4] Grandezas Acumuladas por Integrais (Deslocamento L e Fila Q(t))")
        print("  [5] Gerar os 3 Gráficos (.png) e Analisar Dado Real da API")
        print("  [0] Voltar ao menu principal\n")

        try:
            entrada = input("Opção desejada: ").strip()
            opcao = int(entrada)
        except ValueError:
            print("Entrada inválida. Digite um número de 0 a 5.")
            continue

        match opcao:
            case 1:
                calcular_tempo_minimo_comparativo()
            case 2:
                menu_estudo_limites()
            case 3:
                menu_analise_derivadas()
            case 4:
                menu_analise_integrais()
            case 5:
                menu_gerar_graficos_e_dados_api()
            case 0:
                break
            case _:
                print("Opção inválida. Escolha entre 0 e 5.")
