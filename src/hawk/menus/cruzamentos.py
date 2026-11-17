"""Menu e operações de gerenciamento de Cruzamentos (CRUD).

Todas as validações de entrada são realizadas diretamente nas funções utilizando try/except.
"""

from typing import Any
from src.hawk import api_client, config, formatacao, persistencia, sessao


def obter_lista_cruzamentos() -> list[dict[str, Any]]:
    """Recupera lista de cruzamentos da API ou do cache em caso de offline/falha."""
    if not sessao.esta_offline():
        ok, dados, _ = api_client.listar_cruzamentos()
        if ok and isinstance(dados, list):
            persistencia.salvar_cache("cruzamentos", dados)
            return dados

    cache = persistencia.ler_cache("cruzamentos")
    return cache if isinstance(cache, list) else []


def selecionar_cruzamento(mensagem: str = "Selecione o cruzamento") -> str | None:
    """Apresenta lista numerada de cruzamentos para seleção pelo usuário, evitando digitação manual de ID."""
    cruzamentos = obter_lista_cruzamentos()
    if not cruzamentos:
        formatacao.imprimir_aviso("Nenhum cruzamento encontrado no sistema.")
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
                print(f"Erro: {e} Tente novamente.")

    print(f"\n--- {mensagem} ---")
    for i, c in enumerate(cruzamentos, start=1):
        print(f"  [{i}] {c.get('nome', 'Sem nome')} ({c.get('bairro', 'Sem bairro')}) - ID: {c.get('id')}")
    print("  [D] Digitar ID manualmente")
    print("  [0] Cancelar")

    while True:
        opcao = input("Escolha o número ou [D] para digitar: ").strip().upper()
        if opcao == "0":
            return None
        if opcao == "D":
            while True:
                id_man = input("Digite o ID do cruzamento (24 hex, ou 0 para cancelar): ").strip()
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
            if 1 <= idx <= len(cruzamentos):
                return cruzamentos[idx - 1].get("id")
            print(f"Opção fora da faixa. Escolha entre 1 e {len(cruzamentos)}.")
        except ValueError:
            print("Opção inválida. Digite o número correspondente, 'D' para digitar ID ou '0' para cancelar.")


def listar() -> None:
    """Lista cruzamentos cadastrados com suporte a filtro e cache offline."""
    formatacao.imprimir_subtitulo("Listagem de Cruzamentos")

    filtro_status: str | None = None
    resp = input("Deseja filtrar por status? [s/N]: ").strip().lower()
    if resp in ("s", "sim", "y", "yes"):
        print("\nEscolha o status para filtrar:")
        for i, st in enumerate(config.STATUS_CRUZAMENTO, start=1):
            print(f"  [{i}] {st}")
        print("  [0] Todos os status (sem filtro)")
        while True:
            try:
                entrada_op = input("Opção desejada: ").strip()
                op_st = int(entrada_op)
                if op_st == 0:
                    break
                if 1 <= op_st <= len(config.STATUS_CRUZAMENTO):
                    filtro_status = config.STATUS_CRUZAMENTO[op_st - 1]
                    break
                print(f"Opção fora da faixa. Digite de 0 a {len(config.STATUS_CRUZAMENTO)}.")
            except ValueError:
                print("Entrada inválida. Digite um número inteiro.")

    if sessao.esta_offline():
        salvo_em = persistencia.ler_cache("salvo_em") or "data desconhecida"
        formatacao.imprimir_aviso(f"Modo offline ativo. Exibindo dados do cache local salvos em: {salvo_em}")
        cruzamentos = persistencia.ler_cache("cruzamentos") or []
        if filtro_status:
            cruzamentos = [c for c in cruzamentos if c.get("status") == filtro_status]
        formatacao.formatar_cruzamentos(cruzamentos)
        return

    ok, dados_ou_msg, _ = api_client.listar_cruzamentos(status=filtro_status)
    if ok and isinstance(dados_ou_msg, list):
        persistencia.salvar_cache("cruzamentos", dados_ou_msg)
        formatacao.formatar_cruzamentos(dados_ou_msg)
    else:
        formatacao.imprimir_erro(f"Falha ao consultar API: {dados_ou_msg}")
        formatacao.imprimir_aviso("Tentando carregar dados do cache local...")
        cruzamentos = persistencia.ler_cache("cruzamentos") or []
        formatacao.formatar_cruzamentos(cruzamentos)


def consultar() -> None:
    """Consulta detalhes de um cruzamento pelo ID."""
    formatacao.imprimir_subtitulo("Consulta de Cruzamento")
    cruzamento_id = selecionar_cruzamento("Cruzamento para consulta")
    if not cruzamento_id:
        return

    if sessao.esta_offline():
        cruzamentos = persistencia.ler_cache("cruzamentos") or []
        encontrado = next((c for c in cruzamentos if c.get("id") == cruzamento_id), None)
        if encontrado:
            formatacao.exibir_detalhes("Cruzamento (Cache Local)", encontrado)
        else:
            formatacao.imprimir_erro(f"Cruzamento ID '{cruzamento_id}' não encontrado no cache local.")
        return

    ok, dados_ou_msg, _ = api_client.obter_cruzamento(cruzamento_id)
    if ok and isinstance(dados_ou_msg, dict):
        formatacao.exibir_detalhes("Dados do Cruzamento", dados_ou_msg)
    else:
        formatacao.imprimir_erro(str(dados_ou_msg))


def cadastrar() -> None:
    """Cadastra um novo cruzamento na API, validando todas as entradas."""
    if sessao.bloquear_se_offline():
        return

    formatacao.imprimir_subtitulo("Novo Cruzamento")

    # Validação do nome
    while True:
        nome = input("Nome do cruzamento (ex: Av. Paulista com Augusta): ").strip()
        if nome:
            break
        print("Erro: O nome é obrigatório e não pode ser vazio.")

    # Validação do bairro
    while True:
        bairro = input("Bairro: ").strip()
        if bairro:
            break
        print("Erro: O bairro é obrigatório e não pode ser vazio.")

    # Validação de latitude
    while True:
        try:
            entrada_lat = input("Latitude (-90.0 a 90.0): ").strip().replace(",", ".")
            lat = float(entrada_lat)
            if -90.0 <= lat <= 90.0:
                break
            print("Erro: A latitude deve estar entre -90.0 e 90.0 graus.")
        except ValueError:
            print("Erro: Digite um número decimal válido (ex: -23.5558).")

    # Validação de longitude
    while True:
        try:
            entrada_lon = input("Longitude (-180.0 a 180.0): ").strip().replace(",", ".")
            lon = float(entrada_lon)
            if -180.0 <= lon <= 180.0:
                break
            print("Erro: A longitude deve estar entre -180.0 e 180.0 graus.")
        except ValueError:
            print("Erro: Digite um número decimal válido (ex: -46.6603).")

    # Validação de largura da via
    while True:
        try:
            entrada_largura = input("Largura da via em metros (> 0): ").strip().replace(",", ".")
            largura = float(entrada_largura)
            if largura > 0:
                break
            print("Erro: A largura da via deve ser estritamente maior que zero.")
        except ValueError:
            print("Erro: Digite um número decimal válido para a largura (ex: 14.0).")

    # Validação de status inicial
    print("\nEscolha o status inicial:")
    for i, st in enumerate(config.STATUS_CRUZAMENTO, start=1):
        print(f"  [{i}] {st}")
    status = config.STATUS_CRUZAMENTO[0]
    while True:
        try:
            entrada_st = input("Opção [1 para ativo]: ").strip()
            if not entrada_st or entrada_st == "1":
                status = config.STATUS_CRUZAMENTO[0]
                break
            idx_st = int(entrada_st)
            if 1 <= idx_st <= len(config.STATUS_CRUZAMENTO):
                status = config.STATUS_CRUZAMENTO[idx_st - 1]
                break
            print(f"Opção fora da faixa. Digite entre 1 e {len(config.STATUS_CRUZAMENTO)}.")
        except ValueError:
            print("Erro: Digite um número inteiro correspondente ao status.")

    corpo = {
        "nome": nome,
        "bairro": bairro,
        "latitude": lat,
        "longitude": lon,
        "largura_via_m": largura,
        "status": status,
    }

    conf = input("\nConfirmar o envio dos dados deste cruzamento? [S/n]: ").strip().lower()
    if conf in ("n", "nao", "não", "no"):
        print("Cadastro cancelado pelo usuário.")
        return

    ok, dados_ou_msg, _ = api_client.criar_cruzamento(corpo)
    if ok and isinstance(dados_ou_msg, dict):
        formatacao.imprimir_sucesso(f"Cruzamento cadastrado com sucesso! ID: {dados_ou_msg.get('id')}")
        formatacao.exibir_detalhes("Cruzamento Cadastrado", dados_ou_msg)
        persistencia.registrar_acao("CRIAR_CRUZAMENTO", dados_ou_msg, sucesso=True)
    else:
        formatacao.imprimir_erro(f"Não foi possível cadastrar o cruzamento: {dados_ou_msg}")
        persistencia.registrar_acao("CRIAR_CRUZAMENTO", corpo, sucesso=False)


def atualizar() -> None:
    """Atualiza todos os dados de um cruzamento existente (PUT).
    
    Exibe os valores atuais e permite pressionar Enter para mantê-los.
    """
    if sessao.bloquear_se_offline():
        return

    formatacao.imprimir_subtitulo("Atualização de Cruzamento")
    cruzamento_id = selecionar_cruzamento("Cruzamento para atualizar")
    if not cruzamento_id:
        return

    ok, atual, _ = api_client.obter_cruzamento(cruzamento_id)
    if not ok or not isinstance(atual, dict):
        formatacao.imprimir_erro(f"Não foi possível obter dados do cruzamento: {atual}")
        return

    print("\nPressione [Enter] para manter o valor atual entre colchetes:")
    
    # Nome
    nome_input = input(f"Nome [{atual.get('nome')}]: ").strip()
    nome = nome_input if nome_input else atual.get("nome", "")

    # Bairro
    bairro_input = input(f"Bairro [{atual.get('bairro')}]: ").strip()
    bairro = bairro_input if bairro_input else atual.get("bairro", "")

    # Latitude
    while True:
        lat_input = input(f"Latitude [{atual.get('latitude')}]: ").strip().replace(",", ".")
        if not lat_input:
            lat = float(atual.get("latitude", 0.0))
            break
        try:
            val_lat = float(lat_input)
            if -90.0 <= val_lat <= 90.0:
                lat = val_lat
                break
            print("Erro: A latitude deve estar entre -90.0 e 90.0 graus.")
        except ValueError:
            print("Erro: Digite um número decimal válido.")

    # Longitude
    while True:
        lon_input = input(f"Longitude [{atual.get('longitude')}]: ").strip().replace(",", ".")
        if not lon_input:
            lon = float(atual.get("longitude", 0.0))
            break
        try:
            val_lon = float(lon_input)
            if -180.0 <= val_lon <= 180.0:
                lon = val_lon
                break
            print("Erro: A longitude deve estar entre -180.0 e 180.0 graus.")
        except ValueError:
            print("Erro: Digite um número decimal válido.")

    # Largura da via
    while True:
        larg_input = input(f"Largura da via em metros [{atual.get('largura_via_m')}]: ").strip().replace(",", ".")
        if not larg_input:
            largura = float(atual.get("largura_via_m", 1.0))
            break
        try:
            val_larg = float(larg_input)
            if val_larg > 0:
                largura = val_larg
                break
            print("Erro: A largura da via deve ser estritamente maior que zero.")
        except ValueError:
            print("Erro: Digite um número decimal válido.")

    # Status
    print(f"\nStatus atual: {atual.get('status')}")
    print("Opções de status:")
    for i, st in enumerate(config.STATUS_CRUZAMENTO, start=1):
        print(f"  [{i}] {st}")
    print("  [0] Manter status atual")
    status = atual.get("status", "ativo")
    while True:
        entrada_st = input("Opção [0 para manter]: ").strip()
        if not entrada_st or entrada_st == "0":
            break
        try:
            idx_st = int(entrada_st)
            if 1 <= idx_st <= len(config.STATUS_CRUZAMENTO):
                status = config.STATUS_CRUZAMENTO[idx_st - 1]
                break
            print(f"Opção fora da faixa. Digite entre 0 e {len(config.STATUS_CRUZAMENTO)}.")
        except ValueError:
            print("Erro: Digite um número válido.")

    corpo = {
        "nome": nome,
        "bairro": bairro,
        "latitude": lat,
        "longitude": lon,
        "largura_via_m": largura,
        "status": status,
    }

    conf = input("\nConfirmar a atualização deste cruzamento? [S/n]: ").strip().lower()
    if conf in ("n", "nao", "não", "no"):
        print("Atualização cancelada.")
        return

    ok, dados_ou_msg, _ = api_client.atualizar_cruzamento(cruzamento_id, corpo)
    if ok and isinstance(dados_ou_msg, dict):
        formatacao.imprimir_sucesso("Cruzamento atualizado com sucesso!")
        formatacao.exibir_detalhes("Cruzamento Atualizado", dados_ou_msg)
        persistencia.registrar_acao("ATUALIZAR_CRUZAMENTO", dados_ou_msg, sucesso=True)
    else:
        formatacao.imprimir_erro(f"Falha ao atualizar cruzamento: {dados_ou_msg}")
        persistencia.registrar_acao("ATUALIZAR_CRUZAMENTO", {"id": cruzamento_id, "corpo": corpo}, sucesso=False)


def excluir() -> None:
    """Exclui um cruzamento após confirmação, tratando bloqueio por conflito (409)."""
    if sessao.bloquear_se_offline():
        return

    formatacao.imprimir_subtitulo("Exclusão de Cruzamento")
    cruzamento_id = selecionar_cruzamento("Cruzamento para excluir")
    if not cruzamento_id:
        return

    confirmado = input(f"ATENÇÃO: Deseja realmente excluir o cruzamento ID '{cruzamento_id}'? [s/N]: ").strip().lower()
    if confirmado not in ("s", "sim", "y", "yes"):
        print("Exclusão cancelada pelo usuário.")
        return

    ok, dados_ou_msg, status_http = api_client.excluir_cruzamento(cruzamento_id)
    match status_http:
        case 200 | 204:
            formatacao.imprimir_sucesso(f"Cruzamento '{cruzamento_id}' excluído com sucesso.")
            persistencia.registrar_acao("EXCLUIR_CRUZAMENTO", {"id": cruzamento_id}, sucesso=True)
        case 409:
            formatacao.imprimir_erro(
                "A exclusão foi BLOQUEADA pelo servidor (HTTP 409 - Conflito).\n"
                "Motivo: Este cruzamento possui histórico vinculado (eventos de travessia ou ocorrências registradas).\n"
                "Para preservar a integridade dos dados históricos, o sistema não permite a exclusão."
            )
            persistencia.registrar_acao("EXCLUIR_CRUZAMENTO", {"id": cruzamento_id, "motivo": "409_conflito"}, sucesso=False)
        case _:
            formatacao.imprimir_erro(f"Falha ao excluir cruzamento: {dados_ou_msg}")
            persistencia.registrar_acao("EXCLUIR_CRUZAMENTO", {"id": cruzamento_id}, sucesso=False)


def menu_cruzamentos() -> None:
    """Menu interativo para gerenciamento de cruzamentos com match/case."""
    while True:
        formatacao.imprimir_titulo("Gerenciamento de Cruzamentos")
        print("  [1] Listar cruzamentos")
        print("  [2] Consultar cruzamento por ID")
        print("  [3] Cadastrar novo cruzamento")
        print("  [4] Atualizar cruzamento existente")
        print("  [5] Excluir cruzamento")
        print("  [0] Voltar ao menu principal\n")

        try:
            entrada = input("Opção desejada: ").strip()
            opcao = int(entrada)
        except ValueError:
            print("Entrada inválida. Digite um número de 0 a 5.")
            continue

        match opcao:
            case 1:
                listar()
            case 2:
                consultar()
            case 3:
                cadastrar()
            case 4:
                atualizar()
            case 5:
                excluir()
            case 0:
                break
            case _:
                print("Opção inválida. Escolha entre 0 e 5.")
