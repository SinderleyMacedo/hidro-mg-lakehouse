"""Configuração única, lida de variáveis de ambiente."""

import os


def catalog() -> str:
    return os.getenv("UC_CATALOG", "hidro_mg")


def schema(layer: str) -> str:
    """Nome qualificado do schema de uma camada (raw, bronze, silver, gold)."""
    return f"{catalog()}.{layer}"


def table(layer: str, name: str) -> str:
    """Nome qualificado de uma tabela (catálogo.schema.tabela)."""
    return f"{schema(layer)}.{name}"


def raw_volume_root() -> str:
    """Raiz do volume com os arquivos de origem (ADR 0003)."""
    default = f"/Volumes/{catalog()}/raw/arquivos"
    return os.getenv("UC_RAW_VOLUME", default)
