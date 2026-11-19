"""Leitura e escrita de arquivos em volumes do Unity Catalog (pelo Databricks SDK).

Verificado em 18/11/2026 no Free Edition: upload, listagem e download funcionam.
O SDK registra um aviso "Unexpected status resolving file endpoints (403)" e usa os
endpoints padrão; o aviso não impede a operação.
"""

import io


def _client():
    from databricks.sdk import WorkspaceClient  # importado aqui: só existe com o extra `databricks`

    return WorkspaceClient()


def write_to_volume(path: str, content: bytes) -> None:
    """Grava `content` em `path` (um caminho /Volumes/...), sobrescrevendo se existir."""
    _client().files.upload(path, io.BytesIO(content), overwrite=True)


def read_from_volume(path: str) -> bytes:
    """Lê o conteúdo de um arquivo em /Volumes/..."""
    return _client().files.download(path).contents.read()


def list_volume_dir(path: str) -> list[str]:
    """Lista os caminhos (arquivos e pastas) dentro de uma pasta em /Volumes/..."""
    return [entry.path for entry in _client().files.list_directory_contents(path)]
