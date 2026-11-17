"""Cliente HTTP para a API HAWK com tratamento centralizado de erros."""

import os
from typing import Any, Callable
import requests
from src.hawk import config


def _extrair_mensagem_erro(corpo_json: Any, fallback: str) -> str:
    """Extrai mensagem amigável a partir do corpo JSON da resposta de erro."""
    if isinstance(corpo_json, dict):
        # Padrão {"erro": "...", "campo": "..."}
        if "erro" in corpo_json:
            erro = corpo_json["erro"]
            campo = corpo_json.get("campo")
            return f"{erro} (campo: {campo})" if campo else str(erro)

        # Padrão FastAPI {"detail": [...]} ou {"detail": "..."}
        if "detail" in corpo_json:
            detail = corpo_json["detail"]
            if isinstance(detail, list):
                detalhes = []
                for item in detail:
                    if isinstance(item, dict):
                        loc = item.get("loc", [])
                        campo = loc[-1] if loc else ""
                        msg = item.get("msg", "")
                        detalhes.append(f"{campo}: {msg}" if campo else msg)
                    else:
                        detalhes.append(str(item))
                return "; ".join(detalhes)
            return str(detail)

    return fallback


def _tratar_resposta(resposta: requests.Response) -> tuple[bool, Any, int]:
    """Aplica match/case no código HTTP e extrai dados ou mensagens de erro."""
    status = resposta.status_code

    # Tentativa de parse do corpo como JSON
    try:
        dados_json = resposta.json()
    except (ValueError, requests.exceptions.JSONDecodeError):
        dados_json = None

    match status:
        case 200 | 201:
            conteudo = dados_json if dados_json is not None else resposta.text
            return (True, conteudo, status)

        case 204:
            return (True, None, status)

        case 404:
            msg = _extrair_mensagem_erro(
                dados_json,
                "Recurso não encontrado no servidor.",
            )
            return (False, f"Não encontrado (404): {msg}", status)

        case 409:
            msg = _extrair_mensagem_erro(
                dados_json,
                "Operação em conflito: o recurso possui registros vinculados no histórico e não pode ser excluído.",
            )
            return (False, f"Conflito (409): {msg}", status)

        case 422:
            msg = _extrair_mensagem_erro(
                dados_json,
                "Dados de entrada inválidos para o servidor.",
            )
            return (False, f"Erro de validação (422): {msg}", status)

        case 503:
            msg = _extrair_mensagem_erro(
                dados_json,
                "Serviço temporariamente indisponível (banco de dados fora do ar).",
            )
            return (False, f"Indisponível (503): {msg}", status)

        case 500:
            return (False, "Erro interno no servidor da API HAWK (500).", status)

        case _:
            msg = _extrair_mensagem_erro(
                dados_json,
                f"Resposta inesperada do servidor (HTTP {status}).",
            )
            return (False, msg, status)


def requisitar(
    metodo: str,
    caminho: str,
    params: dict[str, Any] | None = None,
    corpo: dict[str, Any] | None = None,
    timeout: float | None = None,
) -> tuple[bool, Any, int]:
    """Realiza requisição HTTP centralizada à API HAWK.
    
    Retorna sempre uma tupla (sucesso: bool, dados_ou_mensagem: Any, status_http: int).
    Nunca lança exceção para a camada de menus.
    """
    url = f"{config.URL_BASE}/{caminho.lstrip('/')}"
    tempo_limite = timeout if timeout is not None else config.TIMEOUT_PADRAO

    # Remove parâmetros com valor None antes de enviar
    parametros_limpos: dict[str, Any] | None = None
    if params:
        parametros_limpos = {k: v for k, v in params.items() if v is not None}

    headers = {"Content-Type": "application/json"}
    token = os.getenv("HAWK_API_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"

    try:
        resposta = requests.request(
            method=metodo.upper(),
            url=url,
            params=parametros_limpos,
            json=corpo,
            headers=headers,
            timeout=tempo_limite,
        )
        return _tratar_resposta(resposta)

    except requests.exceptions.Timeout:
        return (
            False,
            f"Tempo limite esgotado ao contatar o servidor ({tempo_limite:.1f}s).",
            408,
        )

    except requests.exceptions.ConnectionError:
        return (
            False,
            "Falha de conexão com o servidor. Verifique sua conexão com a internet.",
            0,
        )

    except requests.exceptions.RequestException as e:
        return (
            False,
            f"Erro na comunicação HTTP com o servidor: {e}",
            0,
        )

    except Exception as e:
        return (
            False,
            f"Erro inesperado durante a requisição: {e}",
            0,
        )


# ==============================================================================
# Funções de Endpoint da API HAWK
# ==============================================================================

def saude(timeout: float | None = None) -> tuple[bool, Any, int]:
    """Consulta o status da API e a conexão com o MongoDB."""
    return requisitar("GET", "/saude", timeout=timeout)


def acordar_servidor(
    notificar: Callable[[str], None] | None = None,
) -> tuple[bool, Any, int]:
    """Acorda o servidor no Render com timeout estendido.
    
    Opcionalmente aciona um callback de notificação antes da chamada.
    """
    if callable(notificar):
        notificar("Acordando o servidor, pode levar até 1 minuto...")
    return saude(timeout=config.TIMEOUT_PRIMEIRA_CHAMADA)


# --- Cruzamentos ---

def listar_cruzamentos(status: str | None = None) -> tuple[bool, Any, int]:
    """Lista cruzamentos cadastrados com filtro opcional por status."""
    return requisitar("GET", "/cruzamentos", params={"status": status})


def criar_cruzamento(dados: dict[str, Any]) -> tuple[bool, Any, int]:
    """Cadastra um novo cruzamento."""
    return requisitar("POST", "/cruzamentos", corpo=dados)


def obter_cruzamento(cruzamento_id: str) -> tuple[bool, Any, int]:
    """Consulta dados de um cruzamento pelo ID."""
    return requisitar("GET", f"/cruzamentos/{cruzamento_id}")


def atualizar_cruzamento(cruzamento_id: str, dados: dict[str, Any]) -> tuple[bool, Any, int]:
    """Atualiza todos os dados de um cruzamento existente."""
    return requisitar("PUT", f"/cruzamentos/{cruzamento_id}", corpo=dados)


def excluir_cruzamento(cruzamento_id: str) -> tuple[bool, Any, int]:
    """Exclui um cruzamento (bloqueado se houver histórico associado)."""
    return requisitar("DELETE", f"/cruzamentos/{cruzamento_id}")


def obter_estado_atual(cruzamento_id: str) -> tuple[bool, Any, int]:
    """Obtém o estado semafórico atual de um cruzamento."""
    return requisitar("GET", f"/cruzamentos/{cruzamento_id}/estado-atual")


def estado_atual(cruzamento_id: str) -> tuple[bool, Any, int]:
    """Alias para obter_estado_atual."""
    return obter_estado_atual(cruzamento_id)


# --- Eventos ---

def criar_evento(dados: dict[str, Any]) -> tuple[bool, Any, int]:
    """Registra um evento de travessia ou falha."""
    return requisitar("POST", "/eventos", corpo=dados)


def listar_eventos(
    cruzamento_id: str | None = None,
    tipo: str | None = None,
    origem: str | None = None,
    de: str | None = None,
    ate: str | None = None,
    limite: int | None = 50,
) -> tuple[bool, Any, int]:
    """Lista eventos com filtros opcionais."""
    params = {
        "cruzamento_id": cruzamento_id,
        "tipo": tipo,
        "origem": origem,
        "de": de,
        "ate": ate,
        "limite": limite,
    }
    return requisitar("GET", "/eventos", params=params)


def obter_evento(evento_id: str) -> tuple[bool, Any, int]:
    """Consulta um evento específico pelo ID."""
    return requisitar("GET", f"/eventos/{evento_id}")


# --- Ocorrências ---

def listar_ocorrencias(
    cruzamento_id: str | None = None,
    prioridade: str | None = None,
    situacao: str | None = None,
) -> tuple[bool, Any, int]:
    """Lista ocorrências com filtros opcionais."""
    params = {
        "cruzamento_id": cruzamento_id,
        "prioridade": prioridade,
        "situacao": situacao,
    }
    return requisitar("GET", "/ocorrencias", params=params)


def criar_ocorrencia(dados: dict[str, Any]) -> tuple[bool, Any, int]:
    """Registra manualmente uma ocorrência."""
    return requisitar("POST", "/ocorrencias", corpo=dados)


def obter_ocorrencia(ocorrencia_id: str) -> tuple[bool, Any, int]:
    """Consulta uma ocorrência pelo ID."""
    return requisitar("GET", f"/ocorrencias/{ocorrencia_id}")


def atualizar_ocorrencia(ocorrencia_id: str, dados: dict[str, Any]) -> tuple[bool, Any, int]:
    """Atualiza dados de uma ocorrência existente."""
    return requisitar("PUT", f"/ocorrencias/{ocorrencia_id}", corpo=dados)


def atualizar_situacao(ocorrencia_id: str, situacao: str) -> tuple[bool, Any, int]:
    """Atualiza apenas a situação de uma ocorrência (aberta, em_andamento, resolvida)."""
    return requisitar(
        "PATCH",
        f"/ocorrencias/{ocorrencia_id}/situacao",
        corpo={"situacao": situacao},
    )


def excluir_ocorrencia(ocorrencia_id: str) -> tuple[bool, Any, int]:
    """Exclui uma ocorrência pelo ID."""
    return requisitar("DELETE", f"/ocorrencias/{ocorrencia_id}")


# --- Simulações ---

def simular(cruzamento_id: str, cenario: str) -> tuple[bool, Any, int]:
    """Executa cenário de simulação no servidor para um cruzamento."""
    return requisitar(
        "POST",
        "/simulacoes",
        corpo={"cruzamento_id": cruzamento_id, "cenario": cenario},
    )


# --- Relatórios ---

def relatorio_resumo() -> tuple[bool, Any, int]:
    """Obtém resumo com totais gerais do sistema."""
    return requisitar("GET", "/relatorios/resumo")


def relatorio_tempos() -> tuple[bool, Any, int]:
    """Obtém médias de tempos e taxa de extensões."""
    return requisitar("GET", "/relatorios/tempos")


def relatorio_por_cruzamento() -> tuple[bool, Any, int]:
    """Obtém relatório agregado de métricas por cruzamento."""
    return requisitar("GET", "/relatorios/por-cruzamento")


# --- Cálculos e Testes ---

def calcular_tempo_minimo(
    largura: float,
    velocidade: float | None = None,
    margem: float | None = None,
) -> tuple[bool, Any, int]:
    """Calcula tempo mínimo seguro via fórmula da API (largura/velocidade + margem)."""
    params: dict[str, Any] = {"largura": largura}
    if velocidade is not None:
        params["velocidade"] = velocidade
    if margem is not None:
        params["margem"] = margem
    return requisitar("GET", "/calculos/tempo-minimo", params=params)


def teste_validacao(numero: Any) -> tuple[bool, Any, int]:
    """Endpoint de teste de validação para disparar 422."""
    return requisitar("GET", "/teste-validacao", params={"numero": numero})
