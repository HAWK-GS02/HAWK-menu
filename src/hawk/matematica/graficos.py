"""Geração dos 3 gráficos técnicos com matplotlib para o HAWK Cross.

Gera exclusivamente:
1. 01_posicao_velocidade.png - Curvas x(t) e v(t) com destaque para v_max e área = L
2. 02_velocidade_requerida.png - Curva v_req(t) com assíntota vertical em T_min
3. 03_fila_veiculos.png - Evolução da fila Q(t) com/sem extensão e aviso de premissa simulada
"""

import os
import tempfile
from pathlib import Path

# Configura diretório de cache temporário para evitar erros de permissão no Windows
os.environ.setdefault("MPLCONFIGDIR", tempfile.gettempdir())

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from src.hawk import config
from src.hawk.matematica import modelo


def grafico_posicao_velocidade(
    L: float = 10.0,
    T: float = 28.0,
    caminho: Path | None = None,
) -> Path:
    """1. Gráfico duplo: Posição x(t) e Velocidade Instantânea v(t).
    
    Destaca a velocidade máxima em t = T/2 e a integral (área sob v(t) = L).
    """
    destino = caminho or (config.DIR_GRAFICOS / "01_posicao_velocidade.png")
    destino.parent.mkdir(parents=True, exist_ok=True)

    tempos = modelo.linspace(0.0, T, 200)
    posicoes = [modelo.posicao(t, L, T) for t in tempos]
    velocidades = [modelo.velocidade(t, L, T) for t in tempos]
    v_max = modelo.velocidade_maxima(L, T)

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(8.5, 7.5), sharex=True)

    # Subgráfico 1: Posição x(t)
    ax1.plot(tempos, posicoes, label=r"Posição $x(t) = L(3s^2 - 2s^3)$", color="#1f77b4", linewidth=2.5)
    ax1.axhline(L, color="#7f7f7f", linestyle=":", label=f"Largura da Via $L = {L:.1f}$ m")
    ax1.set_title("Cinemática de Travessia: Posição $x(t)$", fontsize=12, fontweight="bold")
    ax1.set_ylabel("Posição (m)", fontsize=11)
    ax1.grid(True, linestyle="--", alpha=0.6)
    ax1.legend(loc="lower right")

    # Subgráfico 2: Velocidade v(t)
    ax2.plot(tempos, velocidades, label=r"Velocidade $v(t) = \frac{6L}{T}(s - s^2)$", color="#2ca02c", linewidth=2.5)
    ax2.plot(T / 2.0, v_max, marker="o", markersize=7, color="#d62728", label=f"$v_{{max}} = {v_max:.3f}$ m/s (em $t = T/2$)")
    ax2.axvline(T / 2.0, color="#d62728", linestyle="--", alpha=0.5)

    # Área sob a curva representando a integral
    ax2.fill_between(
        tempos,
        velocidades,
        color="#2ca02c",
        alpha=0.25,
        hatch="//",
        label=f"Área $= \\int_0^T v(t) dt = L = {L:.1f}$ m",
    )
    ax2.text(
        T / 2.0,
        v_max * 0.40,
        f"Área = L = {L:.1f} m\n(Deslocamento Total)",
        ha="center",
        va="center",
        fontsize=10,
        fontweight="bold",
        bbox=dict(boxstyle="round,pad=0.3", fc="white", ec="#2ca02c", alpha=0.9),
    )

    ax2.set_title(r"Velocidade Instantânea $v(t) = x'(t)$ e Integral $\int v dt = L$", fontsize=12, fontweight="bold")
    ax2.set_xlabel("Tempo $t$ (segundos)", fontsize=11)
    ax2.set_ylabel("Velocidade (m/s)", fontsize=11)
    ax2.grid(True, linestyle="--", alpha=0.6)
    ax2.legend(loc="upper right")

    plt.tight_layout()
    plt.savefig(destino, dpi=150)
    plt.close()

    return destino


def grafico_velocidade_requerida(
    L: float = 10.0,
    T: float = 28.0,
    T_min: float = 21.67,
    caminho: Path | None = None,
) -> Path:
    """2. Gráfico da velocidade requerida v_req(t) quando t -> T_min-.
    
    Apresenta a assíntota vertical em T_min justificando a extensão de tempo.
    """
    destino = caminho or (config.DIR_GRAFICOS / "02_velocidade_requerida.png")
    destino.parent.mkdir(parents=True, exist_ok=True)

    # Gera pontos se aproximando de T_min pela esquerda
    tempos = modelo.linspace(0.0, T_min - 0.05, 250)
    v_reqs = [modelo.velocidade_requerida(t, L, T, T_min) for t in tempos]

    plt.figure(figsize=(8.5, 5.5))
    plt.plot(
        tempos,
        v_reqs,
        color="#d62728",
        linewidth=2.5,
        label=r"$v_{req}(t) = \frac{L - x(t)}{T_{min} - t}$",
    )
    plt.axvline(
        T_min,
        color="black",
        linestyle="--",
        linewidth=2.0,
        label=f"Prazo Padrão $T_{{min}} = {T_min:.2f}$ s (Assíntota)",
    )
    plt.axhline(
        modelo.VELOCIDADE_REF,
        color="#1f77b4",
        linestyle=":",
        linewidth=1.8,
        label=f"Velocidade de Projeto ($v_{{ref}} = {modelo.VELOCIDADE_REF:.2f}$ m/s)",
    )

    # Destaque da assíntota vertical
    teto_y = min(max(v_reqs) * 1.05, 30.0)
    plt.ylim(0.0, teto_y)
    plt.annotate(
        r"Se $x(T_{min}) < L \Rightarrow v_{req} \to +\infty$" + "\n(Exige velocidade inatingível)",
        xy=(T_min - 0.1, teto_y * 0.85),
        xytext=(T_min * 0.30, teto_y * 0.70),
        arrowprops=dict(facecolor="#d62728", shrink=0.05, width=1.5, headwidth=6),
        fontsize=10,
        fontweight="bold",
        color="#d62728",
        bbox=dict(boxstyle="round,pad=0.3", fc="#fff3cd", ec="#d62728", alpha=0.95),
    )

    plt.title(r"Limite Infinito: Velocidade Requerida $v_{req}(t)$ para $t \to T_{min}^-$", fontsize=12, fontweight="bold")
    plt.xlabel("Tempo Atual $t$ (segundos)", fontsize=11)
    plt.ylabel("Velocidade Requerida $v_{req}$ (m/s)", fontsize=11)
    plt.grid(True, linestyle="--", alpha=0.6)
    plt.legend(loc="upper left")

    plt.tight_layout()
    plt.savefig(destino, dpi=150)
    plt.close()

    return destino


def grafico_fila_veiculos(
    T_min: float = 21.67,
    T: float = 28.0,
    lam: float = 0.20,
    caminho: Path | None = None,
) -> Path:
    """3. Gráfico da fila de veículos Q(t) acumulada: Cenário Normal vs Estendido.
    
    Apresenta a fase de pedestres sombreada e o rótulo de premissa simulada.
    """
    destino = caminho or (config.DIR_GRAFICOS / "03_fila_veiculos.png")
    destino.parent.mkdir(parents=True, exist_ok=True)

    tempos = modelo.linspace(0.0, T, 200)
    fila_total = [modelo.fila(t, lam) for t in tempos]

    q_min = modelo.fila(T_min, lam)
    q_ext = modelo.fila(T, lam)
    delta_q = modelo.custo_extensao(T_min, T, lam)

    plt.figure(figsize=(8.5, 5.5))
    plt.plot(tempos, fila_total, color="#333333", linewidth=2.2, label=r"Fila Acumulada $Q(t) = \int_0^t \lambda\,d\tau = \lambda \cdot t$")

    # Destaque dos pontos finais
    plt.plot(T_min, q_min, marker="o", color="#1f77b4", markersize=8, label=f"Fim sem extensão ($T_{{min}} = {T_min:.2f}$ s, $Q = {q_min:.2f}$ veíc)")
    plt.plot(T, q_ext, marker="s", color="#d62728", markersize=8, label=f"Fim com extensão ($T = {T:.1f}$ s, $Q = {q_ext:.2f}$ veíc)")

    # Áreas sombreadas das fases
    plt.axvspan(0.0, T_min, color="#1f77b4", alpha=0.12, label="Fase Normal de Pedestres")
    plt.axvspan(T_min, T, color="#d62728", alpha=0.18, label=f"Extensão da Proteção (+{T - T_min:.1f} s)")

    # Anotação do custo da extensão
    plt.annotate(
        f"Custo da Extensão:\n+{delta_q:.2f} veículo a mais",
        xy=(T, q_ext),
        xytext=(T * 0.55, q_ext * 0.55),
        arrowprops=dict(facecolor="#d62728", shrink=0.05, width=1.5, headwidth=6),
        fontsize=10,
        fontweight="bold",
        color="#721c24",
        bbox=dict(boxstyle="round,pad=0.3", fc="#f8d7da", ec="#d62728", alpha=0.95),
    )

    # Rótulo de premissa simulada
    plt.text(
        0.03,
        0.92,
        r"[Premissa Simulada: $\lambda = 0{,}20$ veíc/s, $\mu = 0$]",
        transform=plt.gca().transAxes,
        fontsize=10,
        fontweight="bold",
        color="#383d41",
        bbox=dict(boxstyle="round,pad=0.3", fc="#e2e3e5", ec="#d6d8db"),
    )

    plt.title("Impacto no Tráfego: Fila de Veículos Acumulada $Q(t)$ [Premissa Simulada]", fontsize=12, fontweight="bold")
    plt.xlabel("Tempo de Travessia $t$ (segundos)", fontsize=11)
    plt.ylabel("Fila Acumulada $Q(t)$ (veículos)", fontsize=11)
    plt.grid(True, linestyle="--", alpha=0.6)
    plt.legend(loc="lower right")

    plt.tight_layout()
    plt.savefig(destino, dpi=150)
    plt.close()

    return destino


def gerar_todos_os_graficos(
    L: float = 10.0,
    T: float = 28.0,
    T_min: float | None = None,
    lam: float = 0.20,
) -> list[Path]:
    """Gera o conjunto completo dos 3 gráficos requeridos para a entrega simplificada."""
    if T_min is None:
        T_min = modelo.tempo_minimo(L)

    caminhos = [
        grafico_posicao_velocidade(L=L, T=T),
        grafico_velocidade_requerida(L=L, T=T, T_min=T_min),
        grafico_fila_veiculos(T_min=T_min, T=T, lam=lam),
    ]
    return caminhos
