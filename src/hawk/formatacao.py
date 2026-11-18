"""Utilitários de formatação visual para console utilizando a biblioteca Rich.

Baseado no padrão estético e estrutural do exemplo de referência:
- Uso de Console, Panel, Table e Text da biblioteca Rich
- Títulos em Panels estilizados (titulo_terminal)
- Divisores de seção com console.rule()
- Menus em tabelas sem cabeçalho envolvidas em Panels com border_style
- Tabelas com colunas coloridas (bold yellow, bold green, white, etc.)
- Mensagens de sucesso, erro e alerta com formatação rica
"""

import os
from typing import Any, Sequence

from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()


def limpar_tela() -> None:
    """Limpa a tela do terminal conforme o sistema operacional (cls no Windows, clear no Unix)."""
    os.system("cls" if os.name == "nt" else "clear")


def titulo_terminal(titulo: str, subtitulo: str | None = None, estilo: str = "bold cyan") -> None:
    """Exibe um painel de cabeçalho no estilo titulo_terminal do exemplo."""
    conteudo = titulo if not subtitulo else f"{titulo}\n{subtitulo}"
    console.print(Panel(conteudo, style=estilo, expand=False))


def imprimir_titulo(titulo: str, subtitulo: str | None = None) -> None:
    """Exibe título estilizado em painel ciano."""
    titulo_terminal(titulo, subtitulo, estilo="bold cyan")


def imprimir_subtitulo(subtitulo: str) -> None:
    """Exibe divisor de seção com console.rule."""
    console.rule(f"[bold cyan]{subtitulo}[/]")


def imprimir_sucesso(mensagem: str) -> None:
    """Exibe mensagem de sucesso com destaque verde."""
    console.print(f"[bold green]✔ [SUCESSO][/] {mensagem}")


def imprimir_erro(mensagem: str) -> None:
    """Exibe mensagem de erro com destaque vermelho."""
    console.print(f"[bold red]✖ [ERRO][/] {mensagem}")


def imprimir_aviso(mensagem: str) -> None:
    """Exibe mensagem de aviso com destaque amarelo."""
    console.print(f"[bold yellow]⚠ [AVISO][/] {mensagem}")


def pausar(mensagem: str = "Pressione Enter para retornar ao menu...") -> None:
    """Solicita confirmação do usuário antes de limpar a tela ou prosseguir."""
    input(f"\n{mensagem}")


def exibir_menu_painel(
    titulo: str,
    opcoes: Sequence[tuple[str, str]],
    border_style: str = "cyan",
    rodape_info: str | None = None,
) -> None:
    """Renderiza menu com Rich Table embutida em Panel, seguindo exatamente o exemplo de referência."""
    tabela = Table(title=f"[bold]{titulo}[/]", box=None, show_header=False)
    tabela.add_column("Opção", style="bold green", width=8)
    tabela.add_column("Descrição", style="white")

    for num, desc in opcoes:
        tabela.add_row(str(num), desc)

    if rodape_info:
        console.print(f"[yellow]{rodape_info}[/]")

    console.print(Panel(tabela, border_style=border_style))


def formatar_tabela(
    cabecalhos: Sequence[str],
    linhas: Sequence[Sequence[Any]],
    alinhamentos: Sequence[str] | None = None,
    titulo: str | None = None,
) -> None:
    """Imprime uma tabela rica e alinhada utilizando Rich Table."""
    if not cabecalhos:
        return

    tabela = Table(
        title=f"[bold]{titulo}[/]" if titulo else None,
        show_header=True,
        header_style="bold magenta",
        box=box.SIMPLE,
    )

    justify_map = {"<": "left", ">": "right", "^": "center"}

    for idx, h in enumerate(cabecalhos):
        alin = alinhamentos[idx] if alinhamentos and idx < len(alinhamentos) else "<"
        just = justify_map.get(alin, "left")
        col_style = "bold yellow" if idx == 0 else "white"
        tabela.add_column(h, justify=just, style=col_style)

    if not linhas:
        console.print(tabela)
        console.print("[dim]  (Nenhum registro encontrado)[/]\n")
        return

    for linha in linhas:
        str_linha = [str(item if item is not None else "-") for item in linha]
        tabela.add_row(*str_linha)

    console.print(tabela)


def formatar_cruzamentos(cruzamentos: Sequence[dict[str, Any]]) -> None:
    """Exibe lista de cruzamentos em tabela formatada com Rich Table."""
    cabecalhos = ["#", "ID", "Nome", "Bairro", "Largura (m)", "Status"]
    linhas = []
    for i, c in enumerate(cruzamentos, start=1):
        cid = str(c.get("id", ""))
        cid_resumido = f"{cid[:8]}..." if len(cid) > 10 else cid
        linhas.append([
            i,
            cid_resumido,
            c.get("nome", ""),
            c.get("bairro", ""),
            f"{float(c.get('largura_via_m', 0)):.1f}",
            c.get("status", ""),
        ])
    formatar_tabela(cabecalhos, linhas, alinhamentos=["^", "<", "<", "<", ">", "^"])


def formatar_ocorrencias(ocorrencias: Sequence[dict[str, Any]]) -> None:
    """Exibe lista de ocorrências em tabela formatada com Rich Table."""
    cabecalhos = ["#", "ID", "Cruzamento", "Tipo", "Prioridade", "Situação", "Criado Em"]
    linhas = []
    for i, o in enumerate(ocorrencias, start=1):
        oid = str(o.get("id", ""))
        oid_resumido = f"{oid[:8]}..." if len(oid) > 10 else oid
        cid = str(o.get("cruzamento_id", ""))
        cid_resumido = f"{cid[:8]}..." if len(cid) > 10 else cid
        linhas.append([
            i,
            oid_resumido,
            cid_resumido,
            o.get("tipo", ""),
            o.get("prioridade", ""),
            o.get("situacao", ""),
            str(o.get("criado_em", ""))[:19],
        ])
    formatar_tabela(cabecalhos, linhas, alinhamentos=["^", "<", "<", "<", "^", "^", "<"])


def formatar_eventos(eventos: Sequence[dict[str, Any]]) -> None:
    """Exibe lista de eventos em tabela formatada com Rich Table."""
    cabecalhos = ["#", "ID", "Cruzamento", "Tipo", "Estado", "Origem", "Espera (s)", "Trav. (s)", "Data/Hora"]
    linhas = []
    for i, e in enumerate(eventos, start=1):
        eid = str(e.get("id", ""))
        eid_res = f"{eid[:8]}..." if len(eid) > 10 else eid
        cid = str(e.get("cruzamento_id", ""))
        cid_res = f"{cid[:8]}..." if len(cid) > 10 else cid
        t_esp = e.get("tempo_espera_s")
        t_esp_str = f"{float(t_esp):.1f}" if t_esp is not None else "-"
        t_trav = e.get("tempo_travessia_s")
        t_trav_str = f"{float(t_trav):.1f}" if t_trav is not None else "-"

        linhas.append([
            i,
            eid_res,
            cid_res,
            e.get("tipo", ""),
            e.get("estado", ""),
            e.get("origem", ""),
            t_esp_str,
            t_trav_str,
            str(e.get("data_hora", ""))[:19],
        ])
    formatar_tabela(cabecalhos, linhas, alinhamentos=["^", "<", "<", "<", "<", "<", ">", ">", "<"])


def formatar_historico_local(registros: Sequence[dict[str, Any]]) -> None:
    """Exibe lista de ações do histórico local em tabela formatada."""
    cabecalhos = ["#", "Data/Hora", "Ação", "Resultado", "Detalhes"]
    linhas = []
    for i, r in enumerate(registros, start=1):
        res = "OK" if r.get("sucesso", True) else "FALHA"
        det = str(r.get("detalhes", ""))
        det_res = f"{det[:35]}..." if len(det) > 38 else det
        linhas.append([
            i,
            str(r.get("data_hora", ""))[:19],
            r.get("acao", ""),
            res,
            det_res,
        ])
    formatar_tabela(cabecalhos, linhas, alinhamentos=["^", "<", "<", "^", "<"])


def formatar_relatorio_cruzamentos(itens: Sequence[dict[str, Any]]) -> None:
    """Exibe relatório de métricas agrupadas por cruzamento."""
    cabecalhos = ["#", "Cruzamento", "Travessias", "Extensões", "Falhas", "% Extensão"]
    linhas = []
    for i, item in enumerate(itens, start=1):
        nome = item.get("nome") or item.get("cruzamento_id", "")
        nome_res = f"{nome[:22]}..." if len(nome) > 25 else nome
        pct = float(item.get("percentual_extensoes", 0.0))
        linhas.append([
            i,
            nome_res,
            item.get("total_travessias", 0),
            item.get("total_extensoes", 0),
            item.get("total_falhas", 0),
            f"{pct:.1f}%",
        ])
    formatar_tabela(cabecalhos, linhas, alinhamentos=["^", "<", ">", ">", ">", ">"])


def exibir_detalhes(titulo: str, dados: dict[str, Any]) -> None:
    """Exibe um registro detalhado formatado com Rich Table."""
    console.rule(f"[bold cyan]{titulo}[/]")
    tabela = Table(show_header=False, box=None)
    tabela.add_column("Campo", style="bold yellow", width=25)
    tabela.add_column("Valor", style="white")

    for k, v in dados.items():
        rotulo = str(k).replace("_", " ").title()
        tabela.add_row(rotulo, str(v))

    console.print(Panel(tabela, border_style="cyan"))
