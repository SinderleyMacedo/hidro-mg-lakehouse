# 0003. Convenção de nomes (tabelas, colunas, volumes, notebooks)

Data: 2026-11-18
Status: aceita (aprovada pelo usuário na conversa; detalhes completos em `docs/naming.md`)

## Contexto
Antes de escrever os notebooks de extração, tratamento e gold, precisamos de nomes estáveis para tabelas, colunas, caminhos de volume e notebooks.

## Decisão
- Tabelas, colunas e notebooks em inglês, `snake_case`; documentação em português.
- Catálogo `hidro_mg`; schemas `raw`, `bronze`, `silver`, `gold`, `ops`, `dq`.
- Volume: `/Volumes/hidro_mg/raw/arquivos/<source>/<entity>/load_date=AAAA-MM-DD/<arquivo>`.
- Bronze: `<source>_<entity>` (ex.: `bronze.ana_flow`), com colunas de controle `_source`, `_source_file`, `_batch_id`, `_loaded_at`, `_row_hash`.
- Silver: `water_quality`, `daily_flow`, `daily_rainfall`, `hourly_weather`, `station`, `municipality`, `population`, `parameter`, `legal_limit`.
- Gold: `fact_water_quality`, `fact_flow`, `fact_weather`, `fact_limit_violation`, `dim_station`, `dim_municipality`, `dim_parameter`, `dim_date` (opcional).
- Station única: `silver.station`, uma linha por estação real, com `station_id`, `data_source` (valor único), `igam_code`, `ana_code`, `inmet_code`, `match_method`. Prioridade de origem: ana > igam > inmet. Regra de junção por coordenadas definida no P1.
- Notebooks: `00_setup_catalog`, `01_extract_<source>`, `02_bronze_<source>`, `03_silver_<entity>`, `03_silver_station`, `04_gold_*`, `05_data_quality`, `90_explore_*`. Notebooks só chamam funções de `src/hidro_mg_lakehouse/`.

## Consequências
- Nomes previsíveis por camada; um único lugar para identificar estações.
- Pendentes: colunas da bronze IGAM (formato não confirmado), tudo de `ana_*` (API não liberada), `inmet_*` (token a verificar), regra de junção de estações, `dim_date`.
