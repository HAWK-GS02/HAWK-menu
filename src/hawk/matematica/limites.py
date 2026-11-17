"""Estudo analítico e numérico de limites aplicados ao sistema HAWK Cross."""

from typing import Any
from src.hawk.matematica import modelo


def limite_fim_travessia(
    L: float,
    T: float,
    h_valores: list[float] | None = None,
) -> tuple[list[tuple[float, float, float]], float, float]:
    """Estuda a continuidade da travessia ao se aproximar do tempo final:
    
    lim_{t -> T-} x(t) = L  e  lim_{t -> T-} d(t) = 0 (onde d(t) = L - x(t)).
    Retorna: (tabela_h_x_d, limite_x, limite_d).
    """
    if h_valores is None:
        h_valores = [1.0, 0.5, 0.1, 0.05, 0.01, 1e-3, 1e-4, 1e-5, 1e-6]

    tabela: list[tuple[float, float, float]] = []
    for h in h_valores:
        t = T - h
        x_val = modelo.posicao_suave(t, L, T)
        d_val = max(0.0, L - x_val)
        tabela.append((h, x_val, d_val))

    return tabela, L, 0.0


def limite_velocidade_requerida(
    L: float,
    T_lim: float,
    d_restante: float,
    delta_t_valores: list[float] | None = None,
) -> tuple[list[tuple[float, float]], str]:
    """Calcula a velocidade que o pedestre precisaria desenvolver para concluir no prazo:
    
    v_req(t) = d(t) / (T_lim - t), quando t -> T_lim-.
    Se d_restante > 0, o limite lateral é +infinito.
    Interpretação: O pedestre precisaria de velocidade infinita para não ser atropelado;
    portanto, o sistema HAWK Cross DEVE estender o tempo de proteção.
    """
    if delta_t_valores is None:
        delta_t_valores = [2.0, 1.0, 0.5, 0.2, 0.1, 0.05, 0.01, 1e-3]

    tabela: list[tuple[float, float]] = []
    for dt in delta_t_valores:
        v_req = d_restante / dt if dt > 0 else float("inf")
        tabela.append((dt, v_req))

    if d_restante > 0:
        interpretacao = (
            "Como d(T_lim) > 0, o limite lateral de v_req quando t -> T_lim- é +INFINITO.\n"
            "Interpretação física: O pedestre ainda está na via ao fim do tempo padrão.\n"
            "Exigir conclusão no prazo exigiria velocidade infinita.\n"
            "Ação do HAWK Cross: O sistema detecta a presença e estende a fase de proteção."
        )
    else:
        interpretacao = (
            "Como d(T_lim) = 0, a travessia já foi concluída e v_req -> 0.\n"
            "O semáforo pode abrir para os veículos com segurança total."
        )

    return tabela, interpretacao


def limite_quociente_diferencas(
    t: float,
    L: float,
    T: float,
    h_valores: list[float] | None = None,
) -> tuple[list[tuple[float, float, float]], float]:
    """Demonstra a convergência do quociente de diferenças para a derivada (velocidade instantânea):
    
    lim_{h -> 0} [x(t + h) - x(t)] / h = x'(t) = v(t).
    Retorna: (tabela_h_quociente_erro, v_analitica).
    """
    if h_valores is None:
        h_valores = [1.0, 0.1, 0.01, 1e-3, 1e-4, 1e-5, 1e-6]

    v_analitica = modelo.velocidade_suave(t, L, T)
    x_t = modelo.posicao_suave(t, L, T)

    tabela: list[tuple[float, float, float]] = []
    for h in h_valores:
        x_th = modelo.posicao_suave(t + h, L, T)
        quociente = (x_th - x_t) / h
        erro = abs(quociente - v_analitica)
        tabela.append((h, quociente, erro))

    return tabela, v_analitica


def limite_fila_infinito(
    lambda_chegada: float = 0.20,
    mu_sat: float = 0.50,
    Q_pico: float = 6.0,
    t_passos: list[float] | None = None,
) -> tuple[list[tuple[float, float]], float, str]:
    """Estuda a dissipação da fila de veículos quando lambda < mu_sat:
    
    lim_{t -> inf} Q(t) = 0.
    """
    if lambda_chegada >= mu_sat:
        return [], float("inf"), "A taxa de chegada é superior ou igual à saturação. A fila não se dissipa."

    tempo_dissipacao = Q_pico / (mu_sat - lambda_chegada)

    if t_passos is None:
        passos = modelo.linspace(0.0, tempo_dissipacao * 1.5, 8)
    else:
        passos = t_passos

    tabela: list[tuple[float, float]] = []
    for t in passos:
        q_t = max(0.0, Q_pico - (mu_sat - lambda_chegada) * t)
        tabela.append((t, q_t))

    interpretacao = (
        f"Com lambda = {lambda_chegada:.2f} veíc/s < mu_sat = {mu_sat:.2f} veíc/s, "
        f"a fila atinge o pico de {Q_pico:.1f} veículos e dissipa-se completamente "
        f"em {tempo_dissipacao:.1f} s, convergindo para 0."
    )
    return tabela, 0.0, interpretacao
