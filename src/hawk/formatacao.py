"""Utilitários de formatação visual para console (tabelas, títulos e mensagens)."""

from typing import Any, Sequence


def imprimir_titulo(titulo: str) -> None:
    """Exibe um título de seção com linha dupla."""
    linha = "=" * max(60, len(titulo) + 4)
    print(f"\n{linha}")
    print(f"  {titulo.upper()}")
    print(f"{linha}\n")


def imprimir_subtitulo(subtitulo: str) -> None:
    """Exibe um subtítulo de seção com linha simples."""
    linha = "-" * max(50, len(subtitulo) + 4)
    print(f"\n{subtitulo}")
    print(linha)


def imprimir_sucesso(mensagem: str) -> None:
    """Exibe mensagem de sucesso."""
    print(f"\n[SUCESSO] {mensagem}\n")


def imprimir_erro(mensagem: str) -> None:
    """Exibe mensagem de erro."""
    print(f"\n[ERRO] {mensagem}\n")


def imprimir_aviso(mensagem: str) -> None:
    """Exibe mensagem de aviso/alerta."""
    print(f"\n[AVISO] {mensagem}\n")


def formatar_tabela(
    cabecalhos: Sequence[str],
    linhas: Sequence[Sequence[Any]],
    alinhamentos: Sequence[str] | None = None,
) -> None:
    """Imprime uma tabela alinhada no console puro.
    
    cabecalhos: lista/tupla com nomes das colunas.
    linhas: lista de linhas, cada uma contendo valores para as colunas.
    alinhamentos: '<' para esquerda, '>' para direita, '^' para centro.
    """
    if not cabecalhos:
        return

    num_colunas = len(cabecalhos)
    str_linhas = [[str(item if item is not None else "-") for item in linha] for linha in linhas]

    # Calcula largura máxima de cada coluna
    larguras = [len(h) for h in cabecalhos]
    for linha in str_linhas:
        for idx in range(num_colunas):
            if idx < len(linha):
                larguras[idx] = max(larguras[idx], len(linha[idx]))

    # Formata cabeçalho
    pad_cabecalho = []
    for idx, h in enumerate(cabecalhos):
        pad_cabecalho.append(f"{h:<{larguras[idx]}}")
    linha_cabecalho = " | ".join(pad_cabecalho)
    divisor = "-+-".join(["-" * w for w in larguras])

    print(linha_cabecalho)
    print(divisor)

    if not str_linhas:
        print("  (Nenhum registro encontrado)")
        print()
        return

    # Formata linhas de dados
    for linha in str_linhas:
        cols = []
        for idx in range(num_colunas):
            val = linha[idx] if idx < len(linha) else ""
            alin = alinhamentos[idx] if alinhamentos and idx < len(alinhamentos) else "<"
            if alin == ">":
                cols.append(f"{val:>{larguras[idx]}}")
            elif alin == "^":
                cols.append(f"{val:^{larguras[idx]}}")
            else:
                cols.append(f"{val:<{larguras[idx]}}")
        print(" | ".join(cols))
    print()


def formatar_cruzamentos(cruzamentos: Sequence[dict[str, Any]]) -> None:
    """Exibe lista de cruzamentos em tabela formatada com índice."""
    cabecalhos = ["#", "ID", "Nome", "Bairro", "Largura (m)", "Status"]
    linhas = []
    for i, c in enumerate(cruzamentos, start=1):
        cid = str(c.get("id", ""))
        # Exibe primeiros 8 caracteres do ID para economizar espaço
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
    """Exibe lista de ocorrências em tabela formatada com índice."""
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
    """Exibe lista de eventos em tabela formatada com índice."""
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
    """Exibe um registro detalhado em formato chave: valor alinhado."""
    imprimir_subtitulo(titulo)
    largura_chave = max((len(str(k)) for k in dados.keys()), default=15)
    for k, v in dados.items():
        rotulo = str(k).replace("_", " ").title()
        print(f"  {rotulo:<{largura_chave + 2}}: {v}")
    print()
