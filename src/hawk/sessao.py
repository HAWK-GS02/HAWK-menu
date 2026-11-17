"""Gerenciamento de estado de conexão e modo offline da sessão do console."""

from typing import Callable
from src.hawk import api_client, formatacao

_modo_offline: bool = False
_motivo_offline: str = ""


def esta_offline() -> bool:
    """Informa se a aplicação está em modo offline."""
    return _modo_offline


def obter_motivo_offline() -> str:
    """Retorna a razão pela qual o modo offline foi ativado."""
    return _motivo_offline


def definir_modo_offline(ativo: bool, motivo: str = "") -> None:
    """Ativa ou desativa o modo offline."""
    global _modo_offline, _motivo_offline
    _modo_offline = ativo
    _motivo_offline = motivo if ativo else ""


def bloquear_se_offline() -> bool:
    """Verifica se o modo offline está ativo.
    
    Se estiver ativo, exibe aviso informando que operações de escrita
    são proibidas no modo offline e retorna True. Caso contrário, retorna False.
    """
    if _modo_offline:
        formatacao.imprimir_aviso(
            "Operação não permitida em modo offline.\n"
            "Modo offline permite apenas consulta aos dados em cache local.\n"
            f"Motivo: {_motivo_offline or 'Sem conexão ativa com a API.'}"
        )
        return True
    return False


def testar_ou_reconectar(notificar: Callable[[str], None] | None = None) -> tuple[bool, str]:
    """Testa a conexão com o servidor e atualiza o estado da sessão."""
    ok, dados_ou_msg, status = api_client.acordar_servidor(notificar=notificar)
    if ok:
        definir_modo_offline(False)
        return (True, "Conexão com a API estabelecida com sucesso (MongoDB conectado).")
    else:
        motivo = f"HTTP {status} - {dados_ou_msg}"
        definir_modo_offline(True, motivo=motivo)
        return (False, f"Falha ao conectar à API: {dados_ou_msg}")
