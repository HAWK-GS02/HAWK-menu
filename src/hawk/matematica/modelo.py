"""Modelagem matemática fundamental da travessia de pedestres no HAWK Cross.

Implementa as equações cinemáticas de posição, velocidade, aceleração e classificação
de travessia sem bibliotecas externas (apenas Python padrão).
"""

from typing import Any


def linspace(inicio: float, fim: float, num_pontos: int) -> list[float]:
    """Gera uma lista com num_pontos linearmente espaçados entre inicio e fim."""
    if num_pontos <= 1:
        return [inicio]
    passo = (fim - inicio) / (num_pontos - 1)
    return [inicio + i * passo for i in range(num_pontos)]


def tempo_minimo(L: float, v: float = 0.6, m: float = 5.0) -> float:
    """Calcula o tempo mínimo seguro de travessia pela norma: T_min = L / v + m."""
    if v <= 0:
        raise ValueError("A velocidade do pedestre deve ser estritamente positiva.")
    if L <= 0:
        raise ValueError("A largura da via deve ser estritamente positiva.")
    return (L / v) + m


def posicao_constante(t: float, v: float, L: float | None = None) -> float:
    """Modelo linear de velocidade constante: x(t) = v * t."""
    pos = v * t
    if L is not None:
        return max(0.0, min(L, pos))
    return pos


def posicao_suave(t: float, L: float, T: float) -> float:
    """Modelo cúbico suave com repouso nas extremidades: x(t) = L * (3s² - 2s³), s = t/T.
    
    Garante x(0) = 0 e x(T) = L, com clamp no intervalo [0, L].
    """
    if T <= 0:
        return L if t >= 0 else 0.0
    s = t / T
    if s <= 0.0:
        return 0.0
    if s >= 1.0:
        return L
    return L * (3.0 * (s**2) - 2.0 * (s**3))


def velocidade_suave(t: float, L: float, T: float) -> float:
    """Derivada analítica da posição suave: v(t) = (6L/T) * (s - s²), s = t/T.
    
    Garante v(0) = 0, v(T) = 0 e v_max = 1.5 * (L/T) em t = T/2.
    """
    if T <= 0 or t < 0 or t > T:
        return 0.0
    s = t / T
    return (6.0 * L / T) * (s - s**2)


def aceleracao_suave(t: float, L: float, T: float) -> float:
    """Segunda derivada analítica da posição: a(t) = (6L/T²) * (1 - 2s), s = t/T.
    
    Positiva na primeira metade (aceleração) e negativa na segunda (desaceleração).
    """
    if T <= 0 or t < 0 or t > T:
        return 0.0
    s = t / T
    return (6.0 * L / (T**2)) * (1.0 - 2.0 * s)


def classificar_travessia(T: float, T_min: float) -> str:
    """Classifica a travessia com match/case e guardas:
    
    - 'normal': T <= T_min
    - 'estendida': T_min < T <= 1.40 * T_min (faixa típica de extensão da API)
    - 'critica': T > 1.40 * T_min (necessidade de intervenção ou alerta)
    """
    if T_min <= 0:
        return "critica"

    razao = T / T_min
    match razao:
        case r if r <= 1.0:
            return "normal"
        case r if 1.0 < r <= 1.40:
            return "estendida"
        case _:
            return "critica"
