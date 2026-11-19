# Databricks notebook source
# MAGIC %md
# MAGIC # 01_extract_ibge
# MAGIC Baixa municípios e população de MG (IBGE) e grava os JSON originais no volume raw.
# MAGIC A lógica fica em `src/hidro_mg_lakehouse/extract/ibge.py`; este notebook só a chama.

# COMMAND ----------

from datetime import date

from hidro_mg_lakehouse.config import raw_volume_root
from hidro_mg_lakehouse.extract import ibge
from hidro_mg_lakehouse.extract.volume import write_to_volume

root = raw_volume_root()
today = date.today()

# COMMAND ----------

print(ibge.extract_municipalities(root, today, write_to_volume))
print(ibge.extract_population(root, today, write_to_volume))
