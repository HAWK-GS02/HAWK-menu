"""Modelagem matemática do HAWK Cross (versão simples).

Contém apenas as funções analíticas fundamentais de limites, derivadas,
integrais e conservação de fluxo veicular para justificar a extensão
da proteção semafórica a pedestres lentos/vulneráveis.
Funções puras: sem chamadas de I/O, prints ou requisições de rede.
"""

VELOCIDADE_REF = 0.6  # m/s (velocidade de referência para pedestres vulneráveis)
MARGEM = 5.0          # s (margem de segurança normativa)
LAMBDA = 0.20         # veículos/s (taxa simulada de chegada de veículos)


def linspace(inicio: float, fim: float, num_pontos: int) -> list[float]:
    """Gera uma lista com num_pontos linearmente espaçados entre inicio e fim."""
    if num_pontos <= 1:
        return [inicio]
    passo = (fim - inicio) / (num_pontos - 1)
    return [inicio + i * passo for i in range(num_pontos)]


def tempo_minimo(largura: float, v: float = VELOCIDADE_REF, margem: float = MARGEM) -> float:
    """Calcula o tempo mínimo de proteção: T_min = L / v_ref + margem."""
    if v <= 0:
        raise ValueError("A velocidade de referência deve ser positiva.")
    if largura <= 0:
        raise ValueError("A largura da via deve ser positiva.")
    return largura / v + margem


def posicao(t: float, largura: float, T: float) -> float:
    """Posição x(t) = L * (3s² - 2s³), com s = t / T e s clampado em [0, 1].
    
    O pedestre parte do repouso x(0) = 0 e termina em repouso x(T) = L.
    """
    if T <= 0:
        raise ValueError("O tempo total T deve ser estritamente positivo.")
    s = min(max(t / T, 0.0), 1.0)
    return largura * (3.0 * s**2 - 2.0 * s**3)


def velocidade(t: float, largura: float, T: float) -> float:
    """Velocidade instantânea v(t) = x'(t) = (6L/T) * (s - s²), para 0 <= t <= T.
    
    Para instantes fora do intervalo [0, T], retorna 0.0 (repouso).
    """
    if T <= 0:
        raise ValueError("O tempo total T deve ser estritamente positivo.")
    if t < 0.0 or t > T:
        return 0.0
    s = t / T
    return (6.0 * largura / T) * (s - s**2)


def aceleracao(t: float, largura: float, T: float) -> float:
    """Aceleração a(t) = v'(t) = (6L/T²) * (1 - 2s), para 0 <= t <= T.
    
    Para instantes fora do intervalo [0, T], retorna 0.0.
    """
    if T <= 0:
        raise ValueError("O tempo total T deve ser estritamente positivo.")
    if t < 0.0 or t > T:
        return 0.0
    s = t / T
    return (6.0 * largura / (T**2)) * (1.0 - 2.0 * s)


def velocidade_maxima(largura: float, T: float) -> float:
    """Velocidade máxima v_max = 1.5 * L / T atingida no ponto crítico t = T/2."""
    if T <= 0:
        raise ValueError("O tempo total T deve ser estritamente positivo.")
    return 1.5 * largura / T


def velocidade_requerida(t: float, largura: float, T: float, T_min: float) -> float:
    """v_req(t) = distância restante d(t) / tempo restante (T_min - t).
    
    Exige t < T_min para evitar divisão por zero.
    Se x(T_min) < L, v_req -> +infinito quando t -> T_min-.
    """
    if t >= T_min:
        raise ValueError("t deve ser estritamente menor que T_min para velocidade_requerida.")
    d_restante = largura - posicao(t, largura, T)
    return d_restante / (T_min - t)


def tabela_limite(largura: float, T: float, T_min: float, hs: tuple[float, ...] = (1.0, 0.1, 0.01, 0.001)) -> list[tuple[float, float]]:
    """Lista de tuplas (h, v_req) para aproximação lateral t = T_min - h."""
    return [(h, velocidade_requerida(T_min - h, largura, T, T_min)) for h in hs]


def deslocamento(largura: float) -> float:
    """Deslocamento total percorrido: integral definida de 0 a T de v(t) dt = L."""
    return largura


def fila(t_fase: float, lam: float = LAMBDA) -> float:
    """Fila de veículos acumulada durante a fase de pedestres: integral de 0 a t_fase de lam dt = lam * t_fase."""
    return lam * t_fase


def custo_extensao(T_min: float, T: float, lam: float = LAMBDA) -> float:
    """Custo da extensão em veículos adicionais retidos: Q(T) - Q(T_min) = lam * (T - T_min)."""
    return fila(T, lam) - fila(T_min, lam)
