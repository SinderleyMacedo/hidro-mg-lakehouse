# Databricks notebook source
# MAGIC %md
# MAGIC # 02_bronze_ibge
# MAGIC Lê a última extração do IBGE no volume raw e grava `bronze.ibge_municipality` e
# MAGIC `bronze.ibge_population` (Delta, com as colunas de controle do ADR 0003).
# MAGIC A lógica fica em `src/hidro_mg_lakehouse/bronze/ibge.py`; este notebook só a chama.

# COMMAND ----------

from hidro_mg_lakehouse.bronze import ibge
from hidro_mg_lakehouse.catalog import comments
from hidro_mg_lakehouse.config import raw_volume_root
from hidro_mg_lakehouse.session import get_spark

spark = get_spark()
root = raw_volume_root()

# COMMAND ----------

for entity in ibge.ENTITIES:
    target, count = ibge.load_entity(spark, entity, root)
    comments.apply_table_comments(spark, "bronze", f"{ibge.SOURCE}_{entity}")
    print(f"{target}: {count} linhas gravadas, comentários aplicados")
