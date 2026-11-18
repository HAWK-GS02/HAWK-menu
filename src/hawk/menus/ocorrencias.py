"""Menu e operações de gerenciamento de Ocorrências (CRUD e atualização de situação).

Todas as validações de entrada são realizadas diretamente nas funções utilizando try/except.
"""

from typing import Any
from src.hawk import api_client, config, formatacao, persistencia, sessao
from src.hawk.menus.cruzamentos import selecionar_cruzamento


def obter_lista_ocorrencias(
    cruzamento_id: str | None = None,
    prioridade: str | None = None,
    situacao: str | None = None,
) -> list[dict[str, Any]]:
    """Recupera lista de ocorrências da API ou do cache em caso de offline/falha."""
    if not sessao.esta_offline():
        ok, dados, _ = api_client.listar_ocorrencias(
            cruzamento_id=cruzamento_id,
            prioridade=prioridade,
            situacao=situacao,
        )
        if ok and isinstance(dados, list):
            persistencia.salvar_cache("ocorrencias", dados)
            return dados

    cache = persistencia.ler_cache("ocorrencias")
    if not isinstance(cache, list):
        return []

    resultado = cache
    if cruzamento_id:
        resultado = [o for o in resultado if o.get("cruzamento_id") == cruzamento_id]
    if prioridade:
        resultado = [o for o in resultado if o.get("prioridade") == prioridade]
    if situacao:
        resultado = [o for o in resultado if o.get("situacao") == situacao]
    return resultado


def selecionar_ocorrencia(mensagem: str = "Selecione a ocorrência") -> str | None:
    """Apresenta lista numerada de ocorrências para seleção pelo usuário, evitando digitação de ID."""
    ocorrencias = obter_lista_ocorrencias()
    if not ocorrencias:
        formatacao.imprimir_aviso("Nenhuma ocorrência encontrada no sistema.")
        while True:
            id_man = input("Digite o ID manualmente (24 hex, ou 0 para cancelar): ").strip()
            if id_man in ("0", ""):
                return None
            try:
                if len(id_man) != 24:
                    raise ValueError("O ID deve conter exatamente 24 caracteres hexadecimais.")
                int(id_man, 16)
                return id_man
            except ValueError as e:
                print(f"Erro: {e} Digite um hexadecimal válido.")

    formatacao.console.rule(f"[bold cyan]{mensagem}[/]")
    tabela_sel = formatacao.Table(show_header=True, header_style="bold magenta", box=None)
    tabela_sel.add_column("#", style="bold yellow", width=4)
    tabela_sel.add_column("Tipo", style="white")
    tabela_sel.add_column("Prioridade", style="cyan")
    tabela_sel.add_column("Situação", style="green")
    tabela_sel.add_column("ID", style="dim")
    for i, o in enumerate(ocorrencias, start=1):
        oid = str(o.get("id", ""))
        oid_curto = f"{oid[:8]}..." if len(oid) > 10 else oid
        tabela_sel.add_row(
            str(i),
            str(o.get("tipo", "Sem tipo")),
            str(o.get("prioridade", "-")),
            str(o.get("situacao", "-")),
            oid_curto,
        )
    formatacao.console.print(tabela_sel)
    formatacao.console.print("[yellow]  [D] Digitar ID manualmente   [0] Cancelar[/]\n")

    while True:
        opcao = input("Escolha o número ou [D] para digitar: ").strip().upper()
        if opcao == "0":
            return None
        if opcao == "D":
            while True:
                id_man = input("Digite o ID da ocorrência (24 hex, ou 0 para cancelar): ").strip()
                if id_man in ("0", ""):
                    return None
                try:
                    if len(id_man) != 24:
                        raise ValueError("O ID deve ter 24 caracteres hexadecimais.")
                    int(id_man, 16)
                    return id_man
                except ValueError as e:
                    print(f"Erro: {e} Digite um hexadecimal válido (0-9, a-f).")
        try:
            idx = int(opcao)
            if 1 <= idx <= len(ocorrencias):
                return ocorrencias[idx - 1].get("id")
            print(f"Opção fora da faixa. Escolha entre 1 e {len(ocorrencias)}.")
        except ValueError:
            print("Opção inválida. Digite o número correspondente, 'D' para digitar ID ou '0' para cancelar.")


def listar() -> None:
    """Lista ocorrências cadastradas com opções de filtros."""
    formatacao.imprimir_subtitulo("Listagem de Ocorrências")

    filtro_cid: str | None = None
    filtro_prioridade: str | None = None
    filtro_situacao: str | None = None

    resp_filtros = input("Deseja aplicar filtros na listagem? [s/N]: ").strip().lower()
    if resp_filtros in ("s", "sim", "y", "yes"):
        resp_cid = input("Filtrar por cruzamento específico? [s/N]: ").strip().lower()
        if resp_cid in ("s", "sim", "y", "yes"):
            filtro_cid = selecionar_cruzamento("Cruzamento para filtrar")

        resp_prio = input("Filtrar por prioridade? [s/N]: ").strip().lower()
        if resp_prio in ("s", "sim", "y", "yes"):
            print("\nEscolha a prioridade:")
            for i, p in enumerate(config.PRIORIDADES, start=1):
                print(f"  [{i}] {p}")
            print("  [0] Nenhuma")
            while True:
                try:
                    op_p = int(input("Opção: ").strip())
                    if op_p == 0:
                        break
                    if 1 <= op_p <= len(config.PRIORIDADES):
                        filtro_prioridade = config.PRIORIDADES[op_p - 1]
                        break
                    print(f"Opção inválida. Escolha de 0 a {len(config.PRIORIDADES)}.")
                except ValueError:
                    print("Digite um número inteiro válido.")

        resp_sit = input("Filtrar por situação? [s/N]: ").strip().lower()
        if resp_sit in ("s", "sim", "y", "yes"):
            print("\nEscolha a situação operacional:")
            for i, s in enumerate(config.SITUACOES, start=1):
                print(f"  [{i}] {s}")
            print("  [0] Nenhuma")
            while True:
                try:
                    op_s = int(input("Opção: ").strip())
                    if op_s == 0:
                        break
                    if 1 <= op_s <= len(config.SITUACOES):
                        filtro_situacao = config.SITUACOES[op_s - 1]
                        break
                    print(f"Opção inválida. Escolha de 0 a {len(config.SITUACOES)}.")
                except ValueError:
                    print("Digite um número inteiro válido.")

    if sessao.esta_offline():
        salvo_em = persistencia.ler_cache("salvo_em") or "data desconhecida"
        formatacao.imprimir_aviso(f"Modo offline ativo. Exibindo dados do cache local salvos em: {salvo_em}")
        ocorrencias = obter_lista_ocorrencias(
            cruzamento_id=filtro_cid,
            prioridade=filtro_prioridade,
            situacao=filtro_situacao,
        )
        formatacao.formatar_ocorrencias(ocorrencias)
        return

    ok, dados_ou_msg, _ = api_client.listar_ocorrencias(
        cruzamento_id=filtro_cid,
        prioridade=filtro_prioridade,
        situacao=filtro_situacao,
    )
    if ok and isinstance(dados_ou_msg, list):
        persistencia.salvar_cache("ocorrencias", dados_ou_msg)
        formatacao.formatar_ocorrencias(dados_ou_msg)
    else:
        formatacao.imprimir_erro(f"Falha ao consultar API: {dados_ou_msg}")
        formatacao.imprimir_aviso("Carregando ocorrências do cache local...")
        ocorrencias = persistencia.ler_cache("ocorrencias") or []
        formatacao.formatar_ocorrencias(ocorrencias)


def consultar() -> None:
    """Consulta detalhes de uma ocorrência pelo ID."""
    formatacao.imprimir_subtitulo("Consulta de Ocorrência")
    ocorrencia_id = selecionar_ocorrencia("Ocorrência para consulta")
    if not ocorrencia_id:
        return

    if sessao.esta_offline():
        ocorrencias = persistencia.ler_cache("ocorrencias") or []
        encontrada = next((o for o in ocorrencias if o.get("id") == ocorrencia_id), None)
        if encontrada:
            formatacao.exibir_detalhes("Ocorrência (Cache Local)", encontrada)
        else:
            formatacao.imprimir_erro(f"Ocorrência ID '{ocorrencia_id}' não encontrada no cache local.")
        return

    ok, dados_ou_msg, _ = api_client.obter_ocorrencia(ocorrencia_id)
    if ok and isinstance(dados_ou_msg, dict):
        formatacao.exibir_detalhes("Dados da Ocorrência", dados_ou_msg)
    else:
        formatacao.imprimir_erro(str(dados_ou_msg))


def registrar() -> None:
    """Registra uma nova ocorrência vinculada a um cruzamento."""
    if sessao.bloquear_se_offline():
        return

    formatacao.imprimir_subtitulo("Registro de Ocorrência")
    print("Selecione o cruzamento onde ocorreu o problema:")
    cruzamento_id = selecionar_cruzamento("Cruzamento associado")
    if not cruzamento_id:
        print("Registro cancelado: nenhum cruzamento selecionado.")
        return

    # Tipo
    while True:
        tipo = input("Tipo da ocorrência (ex: Botoeira com defeito, Falha no sensor): ").strip()
        if tipo:
            break
        print("Erro: O tipo da ocorrência é obrigatório.")

    # Prioridade
    print("\nEscolha a prioridade:")
    for i, p in enumerate(config.PRIORIDADES, start=1):
        print(f"  [{i}] {p}")
    prioridade = "media"
    while True:
        try:
            entrada_p = input("Opção [2 para media]: ").strip()
            if not entrada_p or entrada_p == "2":
                prioridade = "media"
                break
            idx_p = int(entrada_p)
            if 1 <= idx_p <= len(config.PRIORIDADES):
                prioridade = config.PRIORIDADES[idx_p - 1]
                break
            print(f"Opção fora da faixa. Escolha entre 1 e {len(config.PRIORIDADES)}.")
        except ValueError:
            print("Erro: Digite um número inteiro.")

    # Descrição
    while True:
        descricao = input("Descrição detalhada: ").strip()
        if descricao:
            break
        print("Erro: A descrição é obrigatória.")

    corpo = {
        "cruzamento_id": cruzamento_id,
        "tipo": tipo,
        "prioridade": prioridade,
        "descricao": descricao,
        "situacao": "aberta",
    }

    conf = input("\nConfirmar o envio desta ocorrência? [S/n]: ").strip().lower()
    if conf in ("n", "nao", "não", "no"):
        print("Registro cancelado pelo usuário.")
        return

    ok, dados_ou_msg, _ = api_client.criar_ocorrencia(corpo)
    if ok and isinstance(dados_ou_msg, dict):
        formatacao.imprimir_sucesso(f"Ocorrência registrada com sucesso! ID: {dados_ou_msg.get('id')}")
        formatacao.exibir_detalhes("Ocorrência Registrada", dados_ou_msg)
        persistencia.registrar_acao("CRIAR_OCORRENCIA", dados_ou_msg, sucesso=True)
    else:
        formatacao.imprimir_erro(f"Falha ao registrar ocorrência: {dados_ou_msg}")
        persistencia.registrar_acao("CRIAR_OCORRENCIA", corpo, sucesso=False)


def atualizar_completa() -> None:
    """Atualização completa de uma ocorrência (PUT: tipo, prioridade, descricao, situacao)."""
    if sessao.bloquear_se_offline():
        return

    formatacao.imprimir_subtitulo("Atualização Completa de Ocorrência")
    ocorrencia_id = selecionar_ocorrencia("Ocorrência para atualizar")
    if not ocorrencia_id:
        return

    ok, atual, _ = api_client.obter_ocorrencia(ocorrencia_id)
    if not ok or not isinstance(atual, dict):
        formatacao.imprimir_erro(f"Não foi possível obter dados da ocorrência: {atual}")
        return

    print("\nPressione [Enter] para manter o valor atual:")
    tipo_input = input(f"Tipo [{atual.get('tipo')}]: ").strip()
    tipo = tipo_input if tipo_input else atual.get("tipo", "")

    print(f"\nPrioridade atual: {atual.get('prioridade')}")
    print("Opções de prioridade:")
    for i, p in enumerate(config.PRIORIDADES, start=1):
        print(f"  [{i}] {p}")
    print("  [0] Manter prioridade atual")
    prioridade = atual.get("prioridade", "media")
    while True:
        entrada_p = input("Opção [0 para manter]: ").strip()
        if not entrada_p or entrada_p == "0":
            break
        try:
            idx_p = int(entrada_p)
            if 1 <= idx_p <= len(config.PRIORIDADES):
                prioridade = config.PRIORIDADES[idx_p - 1]
                break
            print(f"Opção fora da faixa. Digite entre 0 e {len(config.PRIORIDADES)}.")
        except ValueError:
            print("Erro: Digite um número inteiro.")

    desc_input = input(f"Descrição [{atual.get('descricao')}]: ").strip()
    descricao = desc_input if desc_input else atual.get("descricao", "")

    print(f"\nSituação atual: {atual.get('situacao')}")
    print("Opções de situação:")
    for i, s in enumerate(config.SITUACOES, start=1):
        print(f"  [{i}] {s}")
    print("  [0] Manter situação atual")
    situacao = atual.get("situacao", "aberta")
    while True:
        entrada_s = input("Opção [0 para manter]: ").strip()
        if not entrada_s or entrada_s == "0":
            break
        try:
            idx_s = int(entrada_s)
            if 1 <= idx_s <= len(config.SITUACOES):
                situacao = config.SITUACOES[idx_s - 1]
                break
            print(f"Opção fora da faixa. Digite entre 0 e {len(config.SITUACOES)}.")
        except ValueError:
            print("Erro: Digite um número inteiro.")

    corpo = {
        "tipo": tipo,
        "prioridade": prioridade,
        "descricao": descricao,
        "situacao": situacao,
    }

    conf = input("\nConfirmar a atualização desta ocorrência? [S/n]: ").strip().lower()
    if conf in ("n", "nao", "não", "no"):
        print("Atualização cancelada.")
        return

    ok, dados_ou_msg, _ = api_client.atualizar_ocorrencia(ocorrencia_id, corpo)
    if ok and isinstance(dados_ou_msg, dict):
        formatacao.imprimir_sucesso("Ocorrência atualizada com sucesso!")
        formatacao.exibir_detalhes("Ocorrência Atualizada", dados_ou_msg)
        persistencia.registrar_acao("ATUALIZAR_OCORRENCIA", dados_ou_msg, sucesso=True)
    else:
        formatacao.imprimir_erro(f"Falha ao atualizar ocorrência: {dados_ou_msg}")
        persistencia.registrar_acao("ATUALIZAR_OCORRENCIA", {"id": ocorrencia_id, "corpo": corpo}, sucesso=False)


def mudar_situacao() -> None:
    """Muda especificamente a situação da ocorrência via PATCH (aberta -> em_andamento -> resolvida)."""
    if sessao.bloquear_se_offline():
        return

    formatacao.imprimir_subtitulo("Alterar Situação Operacional (PATCH)")
    ocorrencia_id = selecionar_ocorrencia("Ocorrência para alterar situação")
    if not ocorrencia_id:
        return

    ok, atual, _ = api_client.obter_ocorrencia(ocorrencia_id)
    if not ok or not isinstance(atual, dict):
        formatacao.imprimir_erro(f"Não foi possível obter dados da ocorrência: {atual}")
        return

    situacao_atual = atual.get("situacao", "aberta")
    print(f"\nSituação atual da ocorrência: '{situacao_atual}'")
    print("Opções de situação operacional:")
    for i, s in enumerate(config.SITUACOES, start=1):
        print(f"  [{i}] {s}")
    print("  [0] Cancelar / Não alterar")

    nova_situacao: str | None = None
    while True:
        try:
            op_s = input("Escolha a nova situação: ").strip()
            if op_s in ("0", ""):
                print("Operação cancelada.")
                return
            idx = int(op_s)
            if 1 <= idx <= len(config.SITUACOES):
                nova_situacao = config.SITUACOES[idx - 1]
                break
            print(f"Opção fora da faixa. Escolha entre 1 e {len(config.SITUACOES)}.")
        except ValueError:
            print("Entrada inválida. Digite um número inteiro.")

    if nova_situacao == situacao_atual:
        print("A situação escolhida é igual à atual. Nenhuma alteração realizada.")
        return

    conf = input(f"Mudar situação de '{situacao_atual}' para '{nova_situacao}'? [S/n]: ").strip().lower()
    if conf in ("n", "nao", "não", "no"):
        print("Operação cancelada.")
        return

    ok, dados_ou_msg, _ = api_client.atualizar_situacao(ocorrencia_id, nova_situacao)
    if ok and isinstance(dados_ou_msg, dict):
        formatacao.imprimir_sucesso(f"Situação alterada para '{nova_situacao}' com sucesso!")
        formatacao.exibir_detalhes("Situação Atualizada", dados_ou_msg)
        persistencia.registrar_acao(
            "MUDAR_SITUACAO_OCORRENCIA",
            {"id": ocorrencia_id, "de": situacao_atual, "para": nova_situacao},
            sucesso=True,
        )
    else:
        formatacao.imprimir_erro(f"Falha ao atualizar situação: {dados_ou_msg}")
        persistencia.registrar_acao(
            "MUDAR_SITUACAO_OCORRENCIA",
            {"id": ocorrencia_id, "para": nova_situacao},
            sucesso=False,
        )


def excluir() -> None:
    """Exclui uma ocorrência pelo ID após confirmação."""
    if sessao.bloquear_se_offline():
        return

    formatacao.imprimir_subtitulo("Exclusão de Ocorrência")
    ocorrencia_id = selecionar_ocorrencia("Ocorrência para excluir")
    if not ocorrencia_id:
        return

    conf = input(f"Deseja realmente excluir a ocorrência ID '{ocorrencia_id}'? [s/N]: ").strip().lower()
    if conf not in ("s", "sim", "y", "yes"):
        print("Exclusão cancelada.")
        return

    ok, dados_ou_msg, status_http = api_client.excluir_ocorrencia(ocorrencia_id)
    if ok or status_http in (200, 204):
        formatacao.imprimir_sucesso(f"Ocorrência '{ocorrencia_id}' excluída com sucesso.")
        persistencia.registrar_acao("EXCLUIR_OCORRENCIA", {"id": ocorrencia_id}, sucesso=True)
    else:
        formatacao.imprimir_erro(f"Falha ao excluir ocorrência: {dados_ou_msg}")
        persistencia.registrar_acao("EXCLUIR_OCORRENCIA", {"id": ocorrencia_id}, sucesso=False)


def menu_ocorrencias() -> None:
    """Menu interativo para gerenciamento de ocorrências com match/case e formatação Rich."""
    opcoes = [
        ("1", "Listar ocorrências"),
        ("2", "Consultar ocorrência por ID"),
        ("3", "Registrar nova ocorrência"),
        ("4", "Atualizar ocorrência (completa - PUT)"),
        ("5", "Mudar situação da ocorrência (PATCH)"),
        ("6", "Excluir ocorrência"),
        ("0", "Voltar ao menu principal"),
    ]
    while True:
        formatacao.limpar_tela()
        formatacao.titulo_terminal("GERENCIAMENTO DE OCORRÊNCIAS", "Controle de Falhas e Alertas Semafóricos", "bold cyan")
        formatacao.exibir_menu_painel("MENU DE OCORRÊNCIAS", opcoes, border_style="cyan")

        opcao = input("\nEscolha uma opção: ").strip()

        match opcao:
            case "1":
                formatacao.limpar_tela()
                listar()
                formatacao.pausar()
            case "2":
                formatacao.limpar_tela()
                consultar()
                formatacao.pausar()
            case "3":
                formatacao.limpar_tela()
                registrar()
                formatacao.pausar()
            case "4":
                formatacao.limpar_tela()
                atualizar_completa()
                formatacao.pausar()
            case "5":
                formatacao.limpar_tela()
                mudar_situacao()
                formatacao.pausar()
            case "6":
                formatacao.limpar_tela()
                excluir()
                formatacao.pausar()
            case "0":
                break
            case _:
                formatacao.console.print("[bold red]Opção inválida. Tente novamente.[/]")
                formatacao.pausar("Pressione Enter para continuar...")
