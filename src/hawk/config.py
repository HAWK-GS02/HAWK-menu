"""Configurações, constantes e enums do sistema HAWK."""

import os
from pathlib import Path
import tempfile

# Configura diretório temporário para cache do Matplotlib
os.environ.setdefault("MPLCONFIGDIR", tempfile.gettempdir())

# Diretórios principais do projeto
DIR_BASE = Path(__file__).resolve().parent.parent.parent
DIR_DADOS = DIR_BASE / "dados"
DIR_GRAFICOS = DIR_BASE / "graficos"
DIR_RELATORIOS = DIR_BASE / "relatorio"

# Arquivos de persistência local
ARQ_CACHE = DIR_DADOS / "cache_api.json"
ARQ_HISTORICO = DIR_DADOS / "historico_local.json"

# Configurações de comunicação com a API HAWK
URL_BASE = os.getenv("HAWK_API_URL", "https://hawk-api-fsgy.onrender.com").rstrip("/")
TIMEOUT_PADRAO: float = 10.0
TIMEOUT_PRIMEIRA_CHAMADA: float = 60.0

# Enums da API definidos como tuplas imutáveis
STATUS_CRUZAMENTO: tuple[str, ...] = ("ativo", "inativo", "manutencao")

TIPOS_EVENTO: tuple[str, ...] = (
    "deteccao",
    "travessia_normal",
    "travessia_estendida",
    "falha",
)

ESTADOS: tuple[str, ...] = (
    "normal",
    "detectado",
    "travessia",
    "liberacao",
    "falha",
)

ORIGENS: tuple[str, ...] = (
    "simulacao_console",
    "wokwi",
    "esp32",
    "camera",
    "painel",
)

PRIORIDADES: tuple[str, ...] = ("baixa", "media", "alta")

SITUACOES: tuple[str, ...] = ("aberta", "em_andamento", "resolvida")

CENARIOS: tuple[str, ...] = ("normal", "extensao", "falha")

# Constantes do modelo matemático (norma de cálculo de tempo mínimo)
VELOCIDADE_PADRAO: float = 0.6  # m/s (velocidade de referência para pedestres vulneráveis)
MARGEM_PADRAO: float = 5.0      # segundos de margem de segurança
