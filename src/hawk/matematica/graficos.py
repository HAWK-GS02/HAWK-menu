"""Geração de gráficos técnicos com matplotlib para o relatório matemático do HAWK Cross."""

from pathlib import Path
from typing import Any
import matplotlib
# Configura backend não-interativo para evitar problemas de interface gráfica
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from src.hawk import config
from src.hawk.matematica import derivadas, fila_veiculos, integrais, limites, modelo


def grafico_posicao(L: float = 14.0, T: float = 28.3, caminho: Path | None = None) -> Path:
    """1. Gráfico da posição x(t): Modelo Suave (Cúbico) vs Modelo Constante."""
    destino = caminho or (config.DIR_GRAFICOS / "grafico_posicao.png")
    destino.parent.mkdir(parents=True, exist_ok=True)

    tempos = modelo.linspace(0.0, T, 150)
    v_cte = L / T
    x_suave = [modelo.posicao_suave(t, L, T) for t in tempos]
    x_cte = [modelo.posicao_constante(t, v_cte, L=L) for t in tempos]

    plt.figure(figsize=(8, 5))
    plt.plot(tempos, x_suave, label=r"Modelo Suave: $x(t) = L(3s^2 - 2s^3)$", color="#1f77b4", linewidth=2.5)
    plt.plot(tempos, x_cte, label=r"Modelo Linear: $x(t) = v_{méd} \cdot t$", color="#ff7f0e", linestyle="--", linewidth=2)
    plt.axhline(L, color="gray", linestyle=":", label=f"Largura da Via L = {L:.1f} m")

    plt.title("Cinemática de Travessia: Posição do Pedestre x(t)", fontsize=13, fontweight="bold")
    plt.xlabel("Tempo t (segundos)", fontsize=11)
    plt.ylabel("Posição x (metros)", fontsize=11)
    plt.grid(True, linestyle="--", alpha=0.6)
    plt.legend(loc="lower right")
    plt.tight_layout()
    plt.savefig(destino, dpi=150)
    plt.close()

    return destino


def grafico_velocidade_aceleracao(L: float = 14.0, T: float = 28.3, caminho: Path | None = None) -> Path:
    """2. Gráficos de velocidade v(t) e aceleração a(t) do pedestre."""
    destino = caminho or (config.DIR_GRAFICOS / "grafico_velocidade_aceleracao.png")
    destino.parent.mkdir(parents=True, exist_ok=True)

    tempos = modelo.linspace(0.0, T, 150)
    vels = [modelo.velocidade_suave(t, L, T) for t in tempos]
    acels = [modelo.aceleracao_suave(t, L, T) for t in tempos]

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(8, 7), sharex=True)

    # Subplot Velocidade
    ax1.plot(tempos, vels, color="#2ca02c", linewidth=2.5, label=r"Velocidade $v(t) = x'(t)$")
    ax1.axhline(1.5 * L / T, color="#d62728", linestyle=":", label=f"v_max = {1.5 * L / T:.2f} m/s (em t = T/2)")
    ax1.axhline(L / T, color="#ff7f0e", linestyle="--", label=f"v_méd = {L / T:.2f} m/s")
    ax1.set_ylabel("Velocidade (m/s)", fontsize=11)
    ax1.set_title("Perfil Dinâmico: Velocidade Instantânea e Aceleração", fontsize=13, fontweight="bold")
    ax1.grid(True, linestyle="--", alpha=0.6)
    ax1.legend(loc="upper right")

    # Subplot Aceleração
    ax2.plot(tempos, acels, color="#9467bd", linewidth=2.5, label=r"Aceleração $a(t) = x''(t)$")
    ax2.axhline(0, color="black", linestyle="-", linewidth=0.8)
    ax2.axvspan(0, T / 2.0, color="#2ca02c", alpha=0.08, label="Fase de Aceleração (a > 0)")
    ax2.axvspan(T / 2.0, T, color="#d62728", alpha=0.08, label="Fase de Desaceleração (a < 0)")
    ax2.set_xlabel("Tempo t (segundos)", fontsize=11)
    ax2.set_ylabel("Aceleração (m/s²)", fontsize=11)
    ax2.grid(True, linestyle="--", alpha=0.6)
    ax2.legend(loc="upper right")

    plt.tight_layout()
    plt.savefig(destino, dpi=150)
    plt.close()

    return destino


def grafico_convergencia_limites(L: float = 14.0, T: float = 28.3, caminho: Path | None = None) -> Path:
    """3. Gráfico da convergência do quociente de diferenças para a derivada analítica."""
    destino = caminho or (config.DIR_GRAFICOS / "grafico_convergencia_limites.png")
    destino.parent.mkdir(parents=True, exist_ok=True)

    t_teste = T / 2.0
    h_lista = [1.0, 0.5, 0.2, 0.1, 0.05, 0.01, 1e-3, 1e-4, 1e-5, 1e-6]
    tabela, v_exata = limites.limite_quociente_diferencas(t_teste, L, T, h_lista)

    h_vals = [item[0] for item in tabela]
    erros = [item[2] for item in tabela]

    plt.figure(figsize=(8, 5))
    plt.loglog(h_vals, erros, marker="o", color="#d62728", linewidth=2, label="Erro |Quociente - v(t)|")
    plt.title(f"Convergência do Limite do Quociente de Diferenças (t = {t_teste:.1f} s)", fontsize=13, fontweight="bold")
    plt.xlabel("Passo h (segundos) - Escala Logarítmica", fontsize=11)
    plt.ylabel("Erro Absoluto (m/s) - Escala Logarítmica", fontsize=11)
    plt.grid(True, which="both", linestyle="--", alpha=0.6)
    plt.legend()
    plt.tight_layout()
    plt.savefig(destino, dpi=150)
    plt.close()

    return destino


def grafico_velocidade_requerida(L: float = 14.0, T_lim: float = 28.3, caminho: Path | None = None) -> Path:
    """4. Velocidade requerida v_req(t) com assíntota em T_lim."""
    destino = caminho or (config.DIR_GRAFICOS / "grafico_velocidade_requerida.png")
    destino.parent.mkdir(parents=True, exist_ok=True)

    # Simula pedestre com velocidade reduzida que chega a 70% de L quando t se aproxima de T_lim
    d_restante = 0.30 * L  # 30% da via restante (ex: 4.2 metros)
    delta_t_vals = [5.0, 4.0, 3.0, 2.0, 1.5, 1.0, 0.5, 0.2, 0.1, 0.05]
    t_vals = [T_lim - dt for dt in delta_t_vals]
    v_req_vals = [d_restante / dt for dt in delta_t_vals]

    plt.figure(figsize=(8, 5))
    plt.plot(t_vals, v_req_vals, marker="s", color="#e377c2", linewidth=2.5, label=r"$v_{req}(t) = \frac{d(t)}{T_{lim} - t}$")
    plt.axvline(T_lim, color="red", linestyle="--", linewidth=2, label=f"Prazo Padrão T_lim = {T_lim:.1f} s (Assíntota)")
    plt.axhline(0.6, color="green", linestyle=":", label="Velocidade Normal (0.60 m/s)")

    plt.title("Limite Infinito: Velocidade Requerida para Concluir no Prazo", fontsize=13, fontweight="bold")
    plt.xlabel("Tempo Atual t (segundos)", fontsize=11)
    plt.ylabel("Velocidade Requerida v_req (m/s)", fontsize=11)
    plt.ylim(0, max(v_req_vals) * 1.1)
    plt.grid(True, linestyle="--", alpha=0.6)
    plt.legend(loc="upper left")
    plt.tight_layout()
    plt.savefig(destino, dpi=150)
    plt.close()

    return destino


def grafico_integral_area(L: float = 14.0, T: float = 28.3, caminho: Path | None = None) -> Path:
    """5. Área sob a curva v(t) destacando o Teorema Fundamental do Cálculo: ∫ v dt = L."""
    destino = caminho or (config.DIR_GRAFICOS / "grafico_integral_area.png")
    destino.parent.mkdir(parents=True, exist_ok=True)

    tempos = modelo.linspace(0.0, T, 150)
    vels = [modelo.velocidade_suave(t, L, T) for t in tempos]

    plt.figure(figsize=(8, 5))
    plt.plot(tempos, vels, color="#1f77b4", linewidth=2.5, label=r"$v(t) = \frac{6L}{T}(s - s^2)$")
    plt.fill_between(
        tempos,
        vels,
        color="#1f77b4",
        alpha=0.25,
        hatch="//",
        label=f"Área = $\\int_0^T v(t) dt = L = {L:.1f}$ m (Deslocamento)",
    )

    plt.title("Interpretação Geométrica da Integral: Deslocamento Total", fontsize=13, fontweight="bold")
    plt.xlabel("Tempo t (segundos)", fontsize=11)
    plt.ylabel("Velocidade v (m/s)", fontsize=11)
    plt.grid(True, linestyle="--", alpha=0.6)
    plt.legend(loc="upper right")
    plt.tight_layout()
    plt.savefig(destino, dpi=150)
    plt.close()

    return destino


def grafico_fila_veiculos(
    T_min: float = 28.3,
    percentual_ext: float = 0.25,
    caminho: Path | None = None,
) -> Path:
    """6. Evolução temporal da fila de veículos Q(t): Cenário Normal vs Extensão."""
    destino = caminho or (config.DIR_GRAFICOS / "grafico_fila_veiculos.png")
    destino.parent.mkdir(parents=True, exist_ok=True)

    dados = fila_veiculos.comparar_cenarios_fila(T_min, percentual_extensao=percentual_ext)
    sim_norm = dados["normal"]
    sim_ext = dados["extensao"]

    plt.figure(figsize=(9, 5.5))
    # Curvas de fila
    plt.plot(sim_norm["pontos_t"], sim_norm["pontos_Q_euler"], label=f"Cenário Normal (T_fase = {T_min:.1f} s)", color="#1f77b4", linewidth=2)
    plt.plot(sim_ext["pontos_t"], sim_ext["pontos_Q_euler"], label=f"Cenário Estendido (T_fase = {dados['T_ext']:.1f} s, +{dados['percentual_extensao']:.0f}%)", color="#d62728", linewidth=2.5)

    # Destaque das fases de pedestres
    plt.axvspan(0, T_min, color="#1f77b4", alpha=0.10, label="Fase Pedestres Normal")
    plt.axvspan(T_min, dados["T_ext"], color="#d62728", alpha=0.15, label="Tempo Estendido HAWK")

    plt.title("Impacto no Tráfego Veicular: Formação e Dissipação de Fila [Dados Simulados]", fontsize=13, fontweight="bold")
    plt.xlabel("Tempo t (segundos)", fontsize=11)
    plt.ylabel("Extensão da Fila Q(t) (veículos)", fontsize=11)
    plt.grid(True, linestyle="--", alpha=0.6)
    plt.legend(loc="upper right")
    plt.tight_layout()
    plt.savefig(destino, dpi=150)
    plt.close()

    return destino


def grafico_histograma_travessias(
    eventos: list[dict[str, Any]] | None = None,
    T_min: float = 28.3,
    caminho: Path | None = None,
) -> Path:
    """7. Histograma dos tempos de travessia com linha de referência T_min."""
    destino = caminho or (config.DIR_GRAFICOS / "grafico_histograma_travessias.png")
    destino.parent.mkdir(parents=True, exist_ok=True)

    tempos: list[float] = []
    if eventos:
        for ev in eventos:
            t = ev.get("tempo_travessia_s")
            if t is not None and float(t) > 0:
                tempos.append(float(t))

    rotulo_fonte = "Eventos da API HAWK"
    if not tempos:
        # Massa de dados padrão representativa se não houver dados reais
        tempos = [18.2, 20.5, 22.1, 23.0, 24.5, 26.0, 27.2, 28.0, 29.5, 31.0, 32.5, 35.0, 38.2]
        rotulo_fonte = "Massa Amostral Simulada"

    plt.figure(figsize=(8, 5))
    plt.hist(tempos, bins=8, color="#2ca02c", edgecolor="black", alpha=0.75, label=f"Distribuição ({rotulo_fonte})")
    plt.axvline(T_min, color="red", linestyle="--", linewidth=2.5, label=f"T_min Seguro = {T_min:.1f} s")

    plt.title(f"Distribuição dos Tempos de Travessia ({rotulo_fonte})", fontsize=13, fontweight="bold")
    plt.xlabel("Tempo de Travessia (segundos)", fontsize=11)
    plt.ylabel("Frequência de Ocorrência", fontsize=11)
    plt.grid(True, linestyle="--", alpha=0.5)
    plt.legend()
    plt.tight_layout()
    plt.savefig(destino, dpi=150)
    plt.close()

    return destino


def gerar_todos_os_graficos(
    L: float = 14.0,
    T_min: float = 28.3,
    eventos: list[dict[str, Any]] | None = None,
) -> list[Path]:
    """Gera o conjunto completo dos 7 gráficos requeridos na Etapa 07."""
    caminhos = [
        grafico_posicao(L=L, T=T_min),
        grafico_velocidade_aceleracao(L=L, T=T_min),
        grafico_convergencia_limites(L=L, T=T_min),
        grafico_velocidade_requerida(L=L, T_lim=T_min),
        grafico_integral_area(L=L, T=T_min),
        grafico_fila_veiculos(T_min=T_min),
        grafico_histograma_travessias(eventos=eventos, T_min=T_min),
    ]
    return caminhos
