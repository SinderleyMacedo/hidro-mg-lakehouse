"""Escrita de arquivos em volumes do Unity Catalog."""

import io


def write_to_volume(path: str, content: bytes) -> None:
    """Grava `content` em `path` (um caminho /Volumes/...), sobrescrevendo se existir.

    TODO(verificar): upload pelo SDK no volume do Free Edition (testar no primeiro uso).
    """
    from databricks.sdk import WorkspaceClient  # importado aqui: só existe com o extra `databricks`

    WorkspaceClient().files.upload(path, io.BytesIO(content), overwrite=True)
