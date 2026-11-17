"""Ponto de entrada do sistema HAWK Cross Console."""

import sys
from src.hawk.menus.principal import executar


def main() -> None:
    """Inicia a execução do sistema."""
    try:
        executar()
    except KeyboardInterrupt:
        print("\n\nOperação cancelada pelo usuário. Encerrando...")
        sys.exit(0)


if __name__ == "__main__":
    main()
