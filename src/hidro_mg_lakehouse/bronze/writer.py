"""Gravação das tabelas bronze em Delta."""

from typing import Any


def to_ddl(columns: list[tuple[str, str]]) -> str:
    """Converte [(nome, tipo), ...] no esquema DDL do Spark ("a STRING, b INT")."""
    return ", ".join(f"{name} {type_}" for name, type_ in columns)


def write_bronze(
    spark: Any, table: str, columns: list[tuple[str, str]], rows: list[dict], source_file: str
) -> int:
    """Grava `rows` em `table` (Delta) e devolve o número de linhas gravadas.

    Primeira carga: cria a tabela. Cargas seguintes: substituem só as linhas do mesmo
    `_source_file` (replaceWhere). Reprocessar um arquivo não duplica linhas, e as
    cargas de outros arquivos ficam intactas.
    """
    if "'" in source_file:
        raise ValueError(f"Caminho com aspas não é aceito: {source_file}")
    names = [name for name, _ in columns]
    data = [tuple(row[name] for name in names) for row in rows]
    writer = spark.createDataFrame(data, schema=to_ddl(columns)).write.format("delta")
    if spark.catalog.tableExists(table):
        writer = writer.mode("overwrite").option("replaceWhere", f"_source_file = '{source_file}'")
    else:
        # "error" (e não "errorifexists"): é o único nome aceito pelo Spark Connect.
        writer = writer.mode("error")
    writer.saveAsTable(table)
    return len(data)
