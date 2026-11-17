"""Cálculo e análise de derivadas numéricas e analíticas para o HAWK Cross."""

from typing import Any, Callable
from src.hawk.matematica import modelo


def derivada_numerica(f: Callable[[float], float], t: float, h: float = 1e-6) -> float:
    """Calcula a derivada de f em t usando o método da diferença central finita:
    
    f'(t) ≈ [f(t + h) - f(t - h)] / (2h), com erro de truncamento O(h²).
    """
    return (f(t + h) - f(t - h)) / (2.0 * h)


def comparar_velocidades(L: float, T: float, t: float, h: float = 1e-6) -> dict[str, float]:
    """Compara a velocidade analítica com a derivada numérica da posição em um instante t.
    
    Confirma também as propriedades:
    - v(0) = v(T) = 0 (repouso no início e no final)
    - v_max = 1.5 * L / T no ponto médio t = T/2
    """
    v_analitica = modelo.velocidade_suave(t, L, T)
    v_numerica = derivada_numerica(lambda tau: modelo.posicao_suave(tau, L, T), t, h=h)
    erro_absoluto = abs(v_analitica - v_numerica)
    v_constante = L / T if T > 0 else 0.0

    v_inicio = modelo.velocidade_suave(0.0, L, T)
    v_fim = modelo.velocidade_suave(T, L, T)
    v_meio = modelo.velocidade_suave(T / 2.0, L, T)
    v_max_teorica = 1.5 * (L / T) if T > 0 else 0.0

    return {
        "instante_t": t,
        "v_analitica": v_analitica,
        "v_numerica": v_numerica,
        "erro_absoluto": erro_absoluto,
        "v_constante": v_constante,
        "v_inicio": v_inicio,
        "v_fim": v_fim,
        "v_ponto_medio": v_meio,
        "v_max_teorica": v_max_teorica,
    }


def analise_perfil_movimento(L: float, T: float, num_pontos: int = 21) -> list[dict[str, Any]]:
    """Gera o perfil completo de cinemática (tempo, posição, velocidade e aceleração)."""
    tempos = modelo.linspace(0.0, T, num_pontos)
    perfil: list[dict[str, Any]] = []

    for t in tempos:
        s = t / T if T > 0 else 0.0
        x_val = modelo.posicao_suave(t, L, T)
        v_val = modelo.velocidade_suave(t, L, T)
        a_val = modelo.aceleracao_suave(t, L, T)

        # Interpretação do regime de aceleração
        if a_val > 1e-5:
            regime = "Acelerando (saindo do repouso)"
        elif a_val < -1e-5:
            regime = "Desacelerando (preparando parada)"
        else:
            regime = "Velocidade Máxima (a = 0)"

        perfil.append({
            "t": t,
            "s": s,
            "x": x_val,
            "v": v_val,
            "a": a_val,
            "regime": regime,
        })

    return perfil
