"""Modelagem da formação e dissipação de fila de veículos em semáforos adaptativos.

Equação diferencial de conservação de fluxo: dQ/dt = λ - μ(t), onde:
- λ: taxa média de chegada de veículos (parâmetro simulado, padrão 0.20 veíc/s ≈ 720 veíc/h)
- μ(t): taxa de partida (0 durante a travessia de pedestres; μ_sat após liberação do tráfego)
"""

from typing import Any
from src.hawk.matematica import modelo

# Parâmetros padrão simulados (premissas de engenharia de tráfego)
LAMBDA_PADRAO = 0.20   # veíc/s (chegada)
MU_SAT_PADRAO = 0.50   # veíc/s (capacidade de escoamento saturado ≈ 1800 veíc/h)
Q0_PADRAO = 0.0        # veículos já parados no início do ciclo


def simular_trajetoria_fila(
    T_fase: float,
    lambda_chegada: float = LAMBDA_PADRAO,
    mu_sat: float = MU_SAT_PADRAO,
    Q0: float = Q0_PADRAO,
    dt: float = 0.1,
    t_max: float = 120.0,
) -> dict[str, Any]:
    """Simula a dinâmica temporal da fila Q(t) comparando Euler com a solução analítica exata."""
    if lambda_chegada >= mu_sat:
        dissipa = False
        tempo_dissipacao = None
        tempo_total_ciclo = t_max
    else:
        dissipa = True
        Q_pico = Q0 + lambda_chegada * T_fase
        tempo_dissipacao = Q_pico / (mu_sat - lambda_chegada)
        tempo_total_ciclo = T_fase + tempo_dissipacao

    # Simulação por Método de Euler
    pontos_t: list[float] = []
    pontos_Q_euler: list[float] = []
    pontos_Q_exato: list[float] = []

    t = 0.0
    Q_atual = Q0
    limite_tempo = min(t_max, (tempo_total_ciclo * 1.25) if dissipa else t_max)

    while t <= limite_tempo:
        pontos_t.append(t)
        pontos_Q_euler.append(max(0.0, Q_atual))

        # Solução Analítica Exata
        if t <= T_fase:
            Q_exato = Q0 + lambda_chegada * t
            mu = 0.0
        else:
            if dissipa:
                Q_exato = max(0.0, (Q0 + lambda_chegada * T_fase) - (mu_sat - lambda_chegada) * (t - T_fase))
            else:
                Q_exato = (Q0 + lambda_chegada * T_fase) + (lambda_chegada - mu_sat) * (t - T_fase)
            mu = mu_sat if Q_atual > 0 else lambda_chegada

        pontos_Q_exato.append(Q_exato)

        # Passo de Euler: Q(t + dt) = Q(t) + [λ - μ(t)] * dt
        dQ = (lambda_chegada - mu) * dt
        Q_atual = max(0.0, Q_atual + dQ)
        t += dt

    return {
        "T_fase": T_fase,
        "lambda_chegada": lambda_chegada,
        "mu_sat": mu_sat,
        "Q0": Q0,
        "Q_pico": Q0 + lambda_chegada * T_fase,
        "dissipa": dissipa,
        "tempo_dissipacao": tempo_dissipacao,
        "tempo_total_ciclo": tempo_total_ciclo,
        "pontos_t": pontos_t,
        "pontos_Q_euler": pontos_Q_euler,
        "pontos_Q_exato": pontos_Q_exato,
    }


def comparar_cenarios_fila(
    T_min: float,
    percentual_extensao: float = 0.25,
    lambda_chegada: float = LAMBDA_PADRAO,
    mu_sat: float = MU_SAT_PADRAO,
) -> dict[str, Any]:
    """Compara o impacto na fila entre o cenário Normal (T_min) e com Extensão (T_min * (1 + p))."""
    T_ext = T_min * (1.0 + percentual_extensao)

    sim_norm = simular_trajetoria_fila(T_min, lambda_chegada, mu_sat)
    sim_ext = simular_trajetoria_fila(T_ext, lambda_chegada, mu_sat)

    # Métricas de diferença
    veiculos_extras_pico = sim_ext["Q_pico"] - sim_norm["Q_pico"]
    tempo_extra_dissipacao = (
        (sim_ext["tempo_dissipacao"] - sim_norm["tempo_dissipacao"])
        if (sim_norm["dissipa"] and sim_ext["dissipa"])
        else 0.0
    )
    tempo_extra_total = (
        (sim_ext["tempo_total_ciclo"] - sim_norm["tempo_total_ciclo"])
        if (sim_norm["dissipa"] and sim_ext["dissipa"])
        else 0.0
    )

    # Atraso total de veículos acumulados (área do triângulo da fila = 0.5 * Q_pico * T_ciclo)
    atraso_norm_veic_s = 0.5 * sim_norm["Q_pico"] * sim_norm["tempo_total_ciclo"] if sim_norm["dissipa"] else 0.0
    atraso_ext_veic_s = 0.5 * sim_ext["Q_pico"] * sim_ext["tempo_total_ciclo"] if sim_ext["dissipa"] else 0.0
    atraso_adicional_veic_s = atraso_ext_veic_s - atraso_norm_veic_s

    return {
        "T_min": T_min,
        "T_ext": T_ext,
        "percentual_extensao": percentual_extensao * 100.0,
        "lambda_chegada": lambda_chegada,
        "mu_sat": mu_sat,
        "normal": sim_norm,
        "extensao": sim_ext,
        "veiculos_extras_pico": veiculos_extras_pico,
        "tempo_extra_dissipacao": tempo_extra_dissipacao,
        "tempo_extra_total": tempo_extra_total,
        "atraso_adicional_veic_s": atraso_adicional_veic_s,
    }
