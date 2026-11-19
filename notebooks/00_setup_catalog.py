# Databricks notebook source
# MAGIC %md
# MAGIC # 00_setup_catalog
# MAGIC Confere o catálogo: cria schemas e volume que faltarem (sem apagar nada) e aplica os
# MAGIC comentários em português do catálogo, schemas, volume e tabelas já existentes.
# MAGIC A lógica e os textos ficam em `src/hidro_mg_lakehouse/catalog/comments.py`.

# COMMAND ----------

from hidro_mg_lakehouse.catalog import comments
from hidro_mg_lakehouse.session import get_spark

spark = get_spark()

# COMMAND ----------

print(f"{comments.apply_catalog_comments(spark)} comandos executados")
