"""Módulo de persistência local em arquivos JSON e exportação de relatórios.

Implementa escrita atômica, tolerância a falhas (arquivos corrompidos ou ausentes),
gerenciamento de cache da API e histórico local de operações.
"""

from datetime import datetime
import json
import os
from pathlib import Path
from typing import Any
from src.hawk import config

ESTRUTURA_CACHE_PADRAO: dict[str, Any] = {
    "salvo_em": None,
    "cruzamentos": [],
    "ocorrencias": [],
    "eventos": [],
    "resumo": {},
    "tempos": {},
}


def ler_json(caminho: Path | str, padrao: Any = None) -> Any:
    """Lê um arquivo JSON de forma segura.
    
    Retorna o valor padrão se o arquivo não existir ou estiver corrompido,
    sem lançar exceções para as camadas superiores.
    """
    caminho_path = Path(caminho)
    if not caminho_path.exists():
        return padrao

    try:
        with open(caminho_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, UnicodeDecodeError):
        print(f"[Aviso] Arquivo JSON corrompido em '{caminho_path}'. Usando dados padrão.")
        return padrao
    except OSError as e:
        print(f"[Aviso] Erro de E/S ao ler '{caminho_path}': {e}. Usando dados padrão.")
        return padrao


def salvar_json(caminho: Path | str, dados: Any, indent: int = 2) -> bool:
    """Salva dados em um arquivo JSON utilizando escrita atômica.
    
    Grava primeiro em arquivo temporário no mesmo diretório e renomeia,
    evitando corrupção em caso de encerramento inesperado.
    """
    caminho_path = Path(caminho)
    try:
        caminho_path.parent.mkdir(parents=True, exist_ok=True)
        temp_path = caminho_path.with_suffix(f"{caminho_path.suffix}.tmp")

        with open(temp_path, "w", encoding="utf-8") as f:
            json.dump(dados, f, indent=indent, ensure_ascii=False)
            f.flush()
            os.fsync(f.fileno())

        os.replace(temp_path, caminho_path)
        return True

    except Exception as e:
        print(f"[Aviso] Falha ao salvar arquivo JSON em '{caminho_path}': {e}")
        try:
            if "temp_path" in locals() and temp_path.exists():
                temp_path.unlink()
        except OSError:
            pass
        return False


# ==============================================================================
# Gerenciamento de Cache da API
# ==============================================================================

def inicializar_cache() -> None:
    """Cria o arquivo de cache padrão caso não exista."""
    if not config.ARQ_CACHE.exists():
        salvar_json(config.ARQ_CACHE, ESTRUTURA_CACHE_PADRAO.copy())


def salvar_cache(chave: str, dados: Any) -> bool:
    """Atualiza uma chave específica no cache local da API e atualiza salvo_em."""
    cache = ler_json(config.ARQ_CACHE, padrao=ESTRUTURA_CACHE_PADRAO.copy())
    if not isinstance(cache, dict):
        cache = ESTRUTURA_CACHE_PADRAO.copy()

    cache[chave] = dados
    cache["salvo_em"] = datetime.now().isoformat()
    return salvar_json(config.ARQ_CACHE, cache)


def ler_cache(chave: str | None = None) -> Any:
    """Recupera dados do cache local.
    
    Se chave for informada, devolve o valor associado; caso contrário, devolve o dicionário completo.
    """
    cache = ler_json(config.ARQ_CACHE, padrao=ESTRUTURA_CACHE_PADRAO.copy())
    if not isinstance(cache, dict):
        cache = ESTRUTURA_CACHE_PADRAO.copy()

    if chave is not None:
        return cache.get(chave)
    return cache


# ==============================================================================
# Gerenciamento de Histórico Local de Ações
# ==============================================================================

def inicializar_historico() -> None:
    """Cria o arquivo de histórico local caso não exista."""
    if not config.ARQ_HISTORICO.exists():
        salvar_json(config.ARQ_HISTORICO, [])


def registrar_acao(acao: str, detalhes: Any, sucesso: bool = True) -> bool:
    """Registra uma operação executada pelo usuário no histórico local."""
    historico = ler_json(config.ARQ_HISTORICO, padrao=[])
    if not isinstance(historico, list):
        historico = []

    novo_registro = {
        "data_hora": datetime.now().isoformat(),
        "acao": acao,
        "detalhes": detalhes,
        "sucesso": sucesso,
    }
    historico.append(novo_registro)
    return salvar_json(config.ARQ_HISTORICO, historico)


def ler_historico() -> list[dict[str, Any]]:
    """Devolve a lista de todas as ações registradas no histórico local."""
    historico = ler_json(config.ARQ_HISTORICO, padrao=[])
    if isinstance(historico, list):
        return historico
    return []


# ==============================================================================
# Exportação de Relatórios
# ==============================================================================

def exportar_relatorio(
    nome: str,
    dados: dict[str, Any] | list[Any],
    texto_formatado: str | None = None,
) -> tuple[Path, Path | None]:
    """Exporta relatório gerado em formato JSON e texto legível (.txt).
    
    Grava os arquivos no subdiretório dados/relatorios/.
    """
    dir_relatorios = config.DIR_DADOS / "relatorios"
    dir_relatorios.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    nome_sanitizado = "".join(c if c.isalnum() or c in ("-", "_") else "_" for c in nome)

    caminho_json = dir_relatorios / f"{nome_sanitizado}_{timestamp}.json"
    caminho_txt = dir_relatorios / f"{nome_sanitizado}_{timestamp}.txt"

    # Salva versão em JSON estruturado
    salvar_json(caminho_json, dados)

    # Salva versão em texto plano legível
    conteudo_txt = texto_formatado
    if conteudo_txt is None:
        conteudo_txt = json.dumps(dados, indent=2, ensure_ascii=False)

    try:
        with open(caminho_txt, "w", encoding="utf-8") as f:
            f.write(conteudo_txt)
    except OSError as e:
        print(f"[Aviso] Não foi possível gravar versão em texto do relatório: {e}")
        return (caminho_json, None)

    return (caminho_json, caminho_txt)
