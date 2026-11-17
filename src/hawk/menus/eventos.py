"""Menu e operações de consulta e registro de Eventos e Histórico Operacional."""

from datetime import datetime
from typing import Any
from src.hawk import api_client, config, formatacao, persistencia, sessao
from src.hawk.menus.cruzamentos import selecionar_cruzamento


def registrar_evento_manual() -> None:
    """Registra manualmente um evento de travessia na API com origem fixa."""
    if sessao.bloquear_se_offline():
        return

    formatacao.imprimir_subtitulo("Registro Manual de Evento")
    print("[ROTULO OBRIGATÓRIO] Origem fixa: 'simulacao_console' (proposta acadêmica)")

    cruzamento_id = selecionar_cruzamento("Cruzamento onde ocorreu o evento")
    if not cruzamento_id:
        print("Registro cancelado.")
        return

    # Tipo do evento
    print("\nEscolha o tipo de evento:")
    for i, t in enumerate(config.TIPOS_EVENTO, start=1):
        print(f"  [{i}] {t}")
    tipo = config.TIPOS_EVENTO[0]
    while True:
        try:
            op_t = input("Opção [1 para deteccao]: ").strip()
            if not op_t or op_t == "1":
                tipo = config.TIPOS_EVENTO[0]
                break
            idx_t = int(op_t)
            if 1 <= idx_t <= len(config.TIPOS_EVENTO):
                tipo = config.TIPOS_EVENTO[idx_t - 1]
                break
            print(f"Opção fora da faixa. Digite entre 1 e {len(config.TIPOS_EVENTO)}.")
        except ValueError:
            print("Entrada inválida. Digite um número inteiro.")

    # Estado semafórico associado
    print("\nEscolha o estado semafórico correspondente:")
    for i, est in enumerate(config.ESTADOS, start=1):
        print(f"  [{i}] {est}")
    estado = config.ESTADOS[0]
    while True:
        try:
            op_e = input("Opção [1 para normal]: ").strip()
            if not op_e or op_e == "1":
                estado = config.ESTADOS[0]
                break
            idx_e = int(op_e)
            if 1 <= idx_e <= len(config.ESTADOS):
                estado = config.ESTADOS[idx_e - 1]
                break
            print(f"Opção fora da faixa. Digite entre 1 e {len(config.ESTADOS)}.")
        except ValueError:
            print("Entrada inválida. Digite um número inteiro.")

    # Opcionais: Confiança (0.0 a 1.0)
    confianca: float | None = None
    while True:
        conf_input = input("Grau de confiança (0.0 a 1.0, [Enter] para ignorar): ").strip().replace(",", ".")
        if not conf_input:
            break
        try:
            val_conf = float(conf_input)
            if 0.0 <= val_conf <= 1.0:
                confianca = val_conf
                break
            print("Erro: A confiança deve estar no intervalo [0.0, 1.0].")
        except ValueError:
            print("Erro: Digite um número decimal válido.")

    # Opcionais: Tempo de espera (s) >= 0
    tempo_espera: float | None = None
    while True:
        esp_input = input("Tempo de espera em segundos (≥ 0, [Enter] para ignorar): ").strip().replace(",", ".")
        if not esp_input:
            break
        try:
            val_esp = float(esp_input)
            if val_esp >= 0.0:
                tempo_espera = val_esp
                break
            print("Erro: O tempo de espera não pode ser negativo.")
        except ValueError:
            print("Erro: Digite um número decimal válido.")

    # Opcionais: Tempo de travessia (s) >= 0
    tempo_travessia: float | None = None
    while True:
        trav_input = input("Tempo de travessia em segundos (≥ 0, [Enter] para ignorar): ").strip().replace(",", ".")
        if not trav_input:
            break
        try:
            val_trav = float(trav_input)
            if val_trav >= 0.0:
                tempo_travessia = val_trav
                break
            print("Erro: O tempo de travessia não pode ser negativo.")
        except ValueError:
            print("Erro: Digite um número decimal válido.")

    # Opcionais: Data/Hora ISO 8601
    data_hora: str | None = None
    while True:
        dt_input = input("Data/Hora (ISO 8601, ex: 2026-11-16T14:30:00, [Enter] para atual): ").strip()
        if not dt_input:
            break
        try:
            datetime.fromisoformat(dt_input)
            data_hora = dt_input
            break
        except ValueError:
            print("Erro: Formato ISO 8601 inválido. Tente novamente.")

    payload: dict[str, Any] = {
        "cruzamento_id": cruzamento_id,
        "tipo": tipo,
        "estado": estado,
        "origem": "simulacao_console",
    }
    if confianca is not None:
        payload["confianca"] = confianca
    if tempo_espera is not None:
        payload["tempo_espera_s"] = tempo_espera
    if tempo_travessia is not None:
        payload["tempo_travessia_s"] = tempo_travessia
    if data_hora is not None:
        payload["data_hora"] = data_hora

    conf = input("\nConfirmar envio do evento manual? [S/n]: ").strip().lower()
    if conf in ("n", "nao", "não", "no"):
        print("Envio cancelado.")
        return

    ok, dados_ou_msg, _ = api_client.criar_evento(payload)
    if ok and isinstance(dados_ou_msg, dict):
        formatacao.imprimir_sucesso(f"Evento registrado com sucesso! ID: {dados_ou_msg.get('id')}")
        formatacao.exibir_detalhes("Detalhes do Evento", dados_ou_msg)

        if dados_ou_msg.get("ocorrencia_criada"):
            oco = dados_ou_msg["ocorrencia_criada"]
            print("\n" + "!" * 70)
            print("  [ALERTA] OCORRÊNCIA DE SEGURANÇA CRIADA AUTOMATICAMENTE NO SERVIDOR")
            print(f"  ID Ocorrência : {oco.get('id')}")
            print(f"  Prioridade    : {str(oco.get('prioridade')).upper()}")
            print(f"  Situação      : {str(oco.get('situacao')).upper()}")
            print("!" * 70 + "\n")

        persistencia.registrar_acao("CRIAR_EVENTO", dados_ou_msg, sucesso=True)
    else:
        formatacao.imprimir_erro(f"Falha ao registrar evento: {dados_ou_msg}")
        persistencia.registrar_acao("CRIAR_EVENTO", payload, sucesso=False)


def consultar_historico_eventos() -> None:
    """Consulta o histórico de eventos com filtros combináveis e resumo estatístico."""
    formatacao.imprimir_subtitulo("Histórico de Eventos de Travessia")

    filtro_cid: str | None = None
    filtro_tipo: str | None = None
    filtro_origem: str | None = None
    filtro_de: str | None = None
    filtro_ate: str | None = None
    limite = 50

    resp_filtros = input("Deseja aplicar filtros na consulta de eventos? [s/N]: ").strip().lower()
    if resp_filtros in ("s", "sim", "y", "yes"):
        # Filtro Cruzamento
        resp_c = input("Filtrar por cruzamento específico? [s/N]: ").strip().lower()
        if resp_c in ("s", "sim", "y", "yes"):
            filtro_cid = selecionar_cruzamento("Cruzamento para filtrar")

        # Filtro Tipo
        resp_t = input("Filtrar por tipo de evento? [s/N]: ").strip().lower()
        if resp_t in ("s", "sim", "y", "yes"):
            print("\nTipos disponíveis:")
            for i, t in enumerate(config.TIPOS_EVENTO, start=1):
                print(f"  [{i}] {t}")
            print("  [0] Todos")
            while True:
                try:
                    op = int(input("Opção: ").strip())
                    if op == 0:
                        break
                    if 1 <= op <= len(config.TIPOS_EVENTO):
                        filtro_tipo = config.TIPOS_EVENTO[op - 1]
                        break
                    print(f"Opção fora da faixa. Digite entre 0 e {len(config.TIPOS_EVENTO)}.")
                except ValueError:
                    print("Digite um número inteiro válido.")

        # Filtro Origem
        resp_o = input("Filtrar por origem do evento? [s/N]: ").strip().lower()
        if resp_o in ("s", "sim", "y", "yes"):
            print("\nOrigens disponíveis:")
            for i, orig in enumerate(config.ORIGENS, start=1):
                print(f"  [{i}] {orig}")
            print("  [0] Todas")
            while True:
                try:
                    op = int(input("Opção: ").strip())
                    if op == 0:
                        break
                    if 1 <= op <= len(config.ORIGENS):
                        filtro_origem = config.ORIGENS[op - 1]
                        break
                    print(f"Opção fora da faixa. Digite entre 0 e {len(config.ORIGENS)}.")
                except ValueError:
                    print("Digite um número inteiro válido.")

        # Filtro Período (de / ate)
        resp_p = input("Filtrar por período de datas (ISO 8601)? [s/N]: ").strip().lower()
        if resp_p in ("s", "sim", "y", "yes"):
            while True:
                de_input = input("Data inicial (ex: 2026-11-01, [Enter] para ignorar): ").strip()
                if not de_input:
                    break
                try:
                    datetime.fromisoformat(de_input)
                    filtro_de = de_input
                    break
                except ValueError:
                    print("Data inválida. Digite no formato ISO 8601.")
            while True:
                ate_input = input("Data final (ex: 2026-11-30, [Enter] para ignorar): ").strip()
                if not ate_input:
                    break
                try:
                    datetime.fromisoformat(ate_input)
                    filtro_ate = ate_input
                    break
                except ValueError:
                    print("Data inválida. Digite no formato ISO 8601.")

        # Limite
        while True:
            lim_input = input("Limite de registros (1 a 500, padrão 50): ").strip()
            if not lim_input:
                limite = 50
                break
            try:
                val_lim = int(lim_input)
                if 1 <= val_lim <= 500:
                    limite = val_lim
                    break
                print("O limite deve ser entre 1 e 500.")
            except ValueError:
                print("Digite um número inteiro.")

    # Execução da consulta
    eventos: list[dict[str, Any]] = []

    if sessao.esta_offline():
        salvo_em = persistencia.ler_cache("salvo_em") or "data desconhecida"
        formatacao.imprimir_aviso(f"Modo offline ativo. Exibindo eventos do cache local salvos em: {salvo_em}")
        cache_ev = persistencia.ler_cache("eventos") or []
        # Aplica filtros em memória
        for ev in cache_ev:
            if filtro_cid and ev.get("cruzamento_id") != filtro_cid:
                continue
            if filtro_tipo and ev.get("tipo") != filtro_tipo:
                continue
            if filtro_origem and ev.get("origem") != filtro_origem:
                continue
            eventos.append(ev)
        eventos = eventos[:limite]
    else:
        ok, dados_ou_msg, _ = api_client.listar_eventos(
            cruzamento_id=filtro_cid,
            tipo=filtro_tipo,
            origem=filtro_origem,
            de=filtro_de,
            ate=filtro_ate,
            limite=limite,
        )
        if ok and isinstance(dados_ou_msg, list):
            eventos = dados_ou_msg
            persistencia.salvar_cache("eventos", eventos)
        else:
            formatacao.imprimir_erro(f"Falha ao consultar eventos na API: {dados_ou_msg}")
            formatacao.imprimir_aviso("Carregando eventos do cache local...")
            eventos = persistencia.ler_cache("eventos") or []

    if not eventos:
        formatacao.imprimir_aviso("Nenhum evento retornado para os filtros informados.")
        return

    # Contagem estatística agrupada internamente por tipo (dicionário de contagem)
    contagem_tipos: dict[str, int] = {t: 0 for t in config.TIPOS_EVENTO}
    contagem_tipos["outros"] = 0

    for ev in eventos:
        tp = ev.get("tipo")
        if tp in contagem_tipos:
            contagem_tipos[tp] += 1
        else:
            contagem_tipos["outros"] += 1

    print("\n--- RESUMO DE EVENTOS (Contagem Agrupada) ---")
    for t_nome, total in contagem_tipos.items():
        if total > 0:
            print(f"  * {t_nome:<20}: {total} evento(s)")
    print(f"  * Total retornado     : {len(eventos)} evento(s)")
    print("--------------------------------------------\n")

    formatacao.formatar_eventos(eventos)


def consultar_evento_por_id() -> None:
    """Consulta detalhes de um evento específico pelo ID."""
    formatacao.imprimir_subtitulo("Consulta de Evento por ID")
    while True:
        id_input = input("Digite o ID do evento (24 hex, ou 0 para cancelar): ").strip()
        if id_input in ("0", ""):
            return
        try:
            if len(id_input) != 24:
                raise ValueError("O ID deve conter exatamente 24 caracteres hexadecimais.")
            int(id_input, 16)
            evento_id = id_input
            break
        except ValueError as e:
            print(f"Erro: {e} Digite um hexadecimal válido.")

    if sessao.esta_offline():
        cache_ev = persistencia.ler_cache("eventos") or []
        encontrado = next((e for e in cache_ev if e.get("id") == evento_id), None)
        if encontrado:
            formatacao.exibir_detalhes("Evento (Cache Local)", encontrado)
        else:
            formatacao.imprimir_erro(f"Evento ID '{evento_id}' não encontrado no cache local.")
        return

    ok, dados_ou_msg, _ = api_client.obter_evento(evento_id)
    if ok and isinstance(dados_ou_msg, dict):
        formatacao.exibir_detalhes("Dados do Evento", dados_ou_msg)
    else:
        formatacao.imprimir_erro(str(dados_ou_msg))


def consultar_estado_atual() -> None:
    """Consulta o estado semafórico atual de um cruzamento em tempo real."""
    formatacao.imprimir_subtitulo("Estado Semafórico em Tempo Real")
    cruzamento_id = selecionar_cruzamento("Cruzamento para verificar estado semafórico")
    if not cruzamento_id:
        return

    if sessao.bloquear_se_offline():
        return

    ok, dados_ou_msg, _ = api_client.obter_estado_atual(cruzamento_id)
    if not ok or not isinstance(dados_ou_msg, dict):
        formatacao.imprimir_erro(f"Falha ao consultar estado atual: {dados_ou_msg}")
        return

    estado = dados_ou_msg.get("estado", "desconhecido")
    evento = dados_ou_msg.get("evento")

    # Interpretação do estado semafórico com match/case
    match estado:
        case "normal":
            significado = "Fluxo livre para veículos (VERDE). Pedestres em espera (VERMELHO)."
        case "detectado":
            significado = "Pedestre detectado aguardando travessia. Transição de fase iminente."
        case "travessia":
            significado = "Fase de travessia de pedestres ATIVA (VERDE). Veículos retidos (VERMELHO)."
        case "liberacao":
            significado = "Fase de proteção final / Entreverde para pedestres (PISCANTE)."
        case "falha":
            significado = "ANOMALIA DE HARDWARE OU OPERAÇÃO (Modo de emergência / Alerta)."
        case _:
            significado = f"Estado '{estado}' não reconhecido."

    print("\n" + "=" * 60)
    print(f"  ESTADO ATUAL DO CRUZAMENTO: {cruzamento_id}")
    print("=" * 60)
    print(f"  Estado Semafórico : {str(estado).upper()}")
    print(f"  Significado       : {significado}")

    if evento is not None and isinstance(evento, dict):
        print("\n  Último Evento Registrado:")
        print(f"    - ID            : {evento.get('id')}")
        print(f"    - Tipo          : {evento.get('tipo')}")
        print(f"    - Origem        : {evento.get('origem')}")
        print(f"    - Espera (s)    : {evento.get('tempo_espera_s')}")
        print(f"    - Travessia (s) : {evento.get('tempo_travessia_s')}")
        print(f"    - Data/Hora     : {evento.get('data_hora')}")
    else:
        print("\n  Último Evento Registrado:")
        print("    - (Nenhum evento registrado até o momento para este cruzamento)")
    print("=" * 60 + "\n")


def ver_historico_local_app() -> None:
    """Exibe o histórico de ações e operações realizadas localmente no console."""
    formatacao.imprimir_subtitulo("Histórico Local de Ações do Console")
    historico = persistencia.ler_historico()

    if not historico:
        formatacao.imprimir_aviso("O histórico local está vazio.")
        return

    acoes_distintas = sorted(list({h.get("acao", "") for h in historico if h.get("acao")}))

    filtro_acao: str | None = None
    resp = input("Deseja filtrar por uma ação específica? [s/N]: ").strip().lower()
    if resp in ("s", "sim", "y", "yes"):
        print("\nAções registradas:")
        for i, ac in enumerate(acoes_distintas, start=1):
            print(f"  [{i}] {ac}")
        print("  [0] Todas as ações")
        while True:
            try:
                op = int(input("Opção: ").strip())
                if op == 0:
                    break
                if 1 <= op <= len(acoes_distintas):
                    filtro_acao = acoes_distintas[op - 1]
                    break
                print(f"Opção fora da faixa. Digite entre 0 e {len(acoes_distintas)}.")
            except ValueError:
                print("Digite um número inteiro.")

    registros = historico
    if filtro_acao:
        registros = [r for r in registros if r.get("acao") == filtro_acao]

    print(f"\nExibindo {len(registros)} ação(ões) registrada(s):")
    formatacao.formatar_historico_local(registros)


def menu_eventos() -> None:
    """Menu interativo para gerenciamento e consulta de eventos e histórico com match/case."""
    while True:
        formatacao.imprimir_titulo("Eventos e Histórico - HAWK Cross")
        print("  [1] Registrar Evento Manual (POST /eventos)")
        print("  [2] Consultar Histórico de Eventos da API (com filtros e contagens)")
        print("  [3] Consultar Evento por ID")
        print("  [4] Consultar Estado Semafórico Atual do Cruzamento")
        print("  [5] Ver Histórico Local de Ações do Console (historico_local.json)")
        print("  [0] Voltar ao menu principal\n")

        try:
            entrada = input("Opção desejada: ").strip()
            opcao = int(entrada)
        except ValueError:
            print("Entrada inválida. Digite um número de 0 a 5.")
            continue

        match opcao:
            case 1:
                registrar_evento_manual()
            case 2:
                consultar_historico_eventos()
            case 3:
                consultar_evento_por_id()
            case 4:
                consultar_estado_atual()
            case 5:
                ver_historico_local_app()
            case 0:
                break
            case _:
                print("Opção inválida. Escolha entre 0 e 5.")
