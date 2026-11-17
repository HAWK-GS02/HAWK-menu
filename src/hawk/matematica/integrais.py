"""Cálculo e análise de integrais numéricas aplicadas à travessia de pedestres."""

from typing import Any, Callable
from src.hawk.matematica import modelo


def trapezio(f: Callable[[float], float], a: float, b: float, n: int) -> float:
    """Calcula a integral de f de a até b usando a regra do trapézio composta."""
    if n <= 0:
        raise ValueError("O número de subintervalos n deve ser maior que zero.")
    h = (b - a) / n
    soma = 0.5 * (f(a) + f(b))
    for i in range(1, n):
        soma += f(a + i * h)
    return soma * h


def simpson(f: Callable[[float], float], a: float, b: float, n: int) -> float:
    """Calcula a integral de f de a até b usando a regra de Simpson 1/3 composta (n par)."""
    if n <= 0:
        raise ValueError("O número de subintervalos n deve ser maior que zero.")
    if n % 2 != 0:
        n += 1  # Simpson 1/3 exige número par de subintervalos

    h = (b - a) / n
    soma = f(a) + f(b)
    for i in range(1, n):
        coef = 4.0 if i % 2 != 0 else 2.0
        soma += coef * f(a + i * h)
    return (soma * h) / 3.0


def verificar_deslocamento_total(
    L: float,
    T: float,
    n_valores: list[int] | None = None,
) -> list[dict[str, Any]]:
    """Calcula a integral da velocidade ∫_0^T v(t) dt e compara com a largura L:
    
    Teorema Fundamental do Cálculo: Deslocamento = ∫_0^T x'(t) dt = x(T) - x(0) = L.
    Retorna resultados numéricos para diferentes valores de subintervalos n.
    """
    if n_valores is None:
        n_valores = [10, 100, 1000]

    resultados: list[dict[str, Any]] = []
    func_v = lambda t: modelo.velocidade_suave(t, L, T)

    for n in n_valores:
        int_trap = trapezio(func_v, 0.0, T, n)
        int_simp = simpson(func_v, 0.0, T, n)

        resultados.append({
            "n": n,
            "trapezio": int_trap,
            "erro_trapezio": abs(int_trap - L),
            "simpson": int_simp,
            "erro_simpson": abs(int_simp - L),
        })

    return resultados


def deslocamento_acumulado(L: float, T: float, num_pontos: int = 21) -> list[dict[str, float]]:
    """Gera a curva de deslocamento acumulado integrando a velocidade até cada instante t."""
    tempos = modelo.linspace(0.0, T, num_pontos)
    curva: list[dict[str, float]] = []
    func_v = lambda tau: modelo.velocidade_suave(tau, L, T)

    for t in tempos:
        if t == 0.0:
            x_int = 0.0
        else:
            x_int = simpson(func_v, 0.0, t, n=20)
        x_analitico = modelo.posicao_suave(t, L, T)
        curva.append({
            "t": t,
            "x_integral": x_int,
            "x_analitico": x_analitico,
            "erro": abs(x_int - x_analitico),
        })

    return curva


def tempo_para_atingir_percentual(L: float, T: float, percentual: float) -> float:
    """Determina o instante t no qual o pedestre atinge X% da travessia (busca binária)."""
    alvo = (percentual / 100.0) * L
    inicio, fim = 0.0, T

    for _ in range(60):
        meio = (inicio + fim) / 2.0
        pos = modelo.posicao_suave(meio, L, T)
        if pos < alvo:
            inicio = meio
        else:
            fim = meio

    return (inicio + fim) / 2.0


def analisar_velocidades_eventos(
    eventos: list[dict[str, Any]],
    largura_padrao: float = 14.0,
) -> dict[str, Any]:
    """Estima as velocidades médias reais observadas na API e compara com a referência de 0.6 m/s."""
    velocidades: list[float] = []

    for ev in eventos:
        t_trav = ev.get("tempo_travessia_s")
        if t_trav is not None and float(t_trav) > 0:
            # Se o evento tiver largura associada, usa-a; caso contrário usa a largura padrão
            l_via = float(ev.get("largura_via_m", largura_padrao))
            v_med = l_via / float(t_trav)
            velocidades.append(v_med)

    if not velocidades:
        return {
            "total_amostras": 0,
            "velocidade_media": 0.0,
            "velocidade_minima": 0.0,
            "velocidade_maxima": 0.0,
            "abaixo_de_0_6": 0,
            "percentual_abaixo_0_6": 0.0,
        }

    v_media = sum(velocidades) / len(velocidades)
    v_min = min(velocidades)
    v_max = max(velocidades)
    abaixo = sum(1 for v in velocidades if v < 0.60)
    pct_abaixo = (abaixo / len(velocidades)) * 100.0

    return {
        "total_amostras": len(velocidades),
        "velocidade_media": v_media,
        "velocidade_minima": v_min,
        "velocidade_maxima": v_max,
        "abaixo_de_0_6": abaixo,
        "percentual_abaixo_0_6": pct_abaixo,
    }
