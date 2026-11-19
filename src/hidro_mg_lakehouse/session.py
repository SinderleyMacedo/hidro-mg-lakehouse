"""Criação da sessão Spark: único lugar do projeto que faz isso."""

from typing import Any


def get_spark() -> Any:
    """Devolve a sessão Spark.

    Dentro do Databricks usa a sessão ativa. Fora dele (VS Code), abre uma sessão
    remota pelo Databricks Connect no compute serverless, o único do Free Edition.
    A autenticação vem do perfil em DATABRICKS_CONFIG_PROFILE (OAuth, `make db-auth`).
    """
    from pyspark.sql import SparkSession  # importado aqui: só existe com o extra `databricks`

    active = SparkSession.getActiveSession()
    if active is not None:
        return active

    from databricks.connect import DatabricksSession

    return DatabricksSession.builder.serverless(True).getOrCreate()
