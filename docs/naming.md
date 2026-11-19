# Proposta v2: convenção de nomes (hidro-mg-lakehouse)

Status: aprovada (ver ADR 0003).
Mudanças da v1: nomes em inglês; tabela única de `station`, independente da origem.

## 1. Regras gerais
- Tabelas, colunas e notebooks em inglês, minúsculas, `snake_case` (ex.: `daily_flow`, `municipality_code`). Documentação continua em português.
- Catálogo `hidro_mg`; catálogo e schema vêm de variáveis de ambiente.
- Tabelas no singular (`station`, `municipality`); fatos descrevem o evento (`fact_water_quality`).
- Datas: `measurement_date` (dia) e `measurement_datetime` (hora, em UTC no bronze e silver). Valor em `value`, com `unit` ao lado.
- Chaves: `station_id` (chave nossa, única), `municipality_code` (7 dígitos IBGE, texto), `parameter_code`.

## 2. Caminhos no volume (raw)
`/Volumes/hidro_mg/raw/arquivos/<source>/<entity>/load_date=AAAA-MM-DD/<original_file>`
Ex.: `igam/water_quality/load_date=2026-12-01/...`, `ana/flow/...`, `inmet/hourly_weather/...`, `ibge/municipality/...`, `legal/limits/...`.
(O nome do volume `arquivos` já existe e fica como está.)

## 3. A tabela única de station
Problema: IGAM chama de "ponto de monitoramento", ANA de "estação", INMET de "estação meteorológica", e cada uma usa um código próprio. Solução: UMA tabela só, `silver.station`, com uma linha por estação real:

- `station_id` (chave nossa, única), `station_name`, `latitude`, `longitude`, `municipality_code`, `basin`.
- `data_source` (um valor só: `ana`, `igam` ou `inmet`): a origem escolhida para essa estação. Se a mesma estação vier de duas origens, fica uma linha só, com uma origem.
- Regra de prioridade (proposta): `ana` > `igam` > `inmet`. A origem de maior prioridade fornece nome e coordenadas. Motivo: o cadastro da ANA é o mais padronizado; INMET fica por último porque é dado bruto sem validação.
- `igam_code`, `ana_code`, `inmet_code`: o código da estação em cada origem (vazio quando não existe). Ficam mesmo com uma única `data_source`, senão os dados da origem "perdedora" não achariam a estação para ligar com `station_id`.
- `match_method`: como juntamos (`coordinates`, `manual`, `single_source`).

Cada origem entra primeiro em `bronze.<source>_station` como veio. Na silver, `03_silver_station` junta as três na tabela única: se a coordenada indica a mesma estação, vira uma linha só com os dois códigos preenchidos; se não, vira uma linha com uma origem só. A regra exata de junção (distância máxima, revisão manual) decidimos no P1, vendo as coordenadas reais, sem juntar por chute. Os fatos usam só `station_id`.

## 4. Tabelas por camada

### bronze (uma por fonte/entidade, como veio + metadados)
| Tabela | Origem | Depende de |
| --- | --- | --- |
| `bronze.igam_water_quality` | IGAM | formato do arquivo (a confirmar) |
| `bronze.igam_station` | IGAM | formato do arquivo (a confirmar) |
| `bronze.ana_station` | ANA | acesso à API (pendente) |
| `bronze.ana_flow` | ANA | acesso à API (pendente) |
| `bronze.ana_rainfall` | ANA | acesso à API (pendente) |
| `bronze.inmet_station` | INMET | token da API (a verificar) |
| `bronze.inmet_hourly_weather` | INMET | token da API (a verificar) |
| `bronze.ibge_municipality` | IBGE | nada |
| `bronze.ibge_population` | IBGE | nada |
| `bronze.legal_limit` | tabela manual CONAMA/COPAM | versão vigente da DN estadual |

Colunas de controle em toda bronze: `_source`, `_source_file`, `_batch_id`, `_loaded_at`, `_row_hash`.

### silver
`silver.water_quality`, `silver.daily_flow`, `silver.daily_rainfall`, `silver.hourly_weather`, `silver.station`, `silver.municipality`, `silver.population`, `silver.parameter`, `silver.legal_limit`.

### gold
`gold.fact_water_quality`, `gold.fact_flow`, `gold.fact_weather`, `gold.fact_limit_violation`, `gold.dim_station`, `gold.dim_municipality`, `gold.dim_parameter`, `gold.dim_date` (opcional, decidimos no P1).

### ops e dq
`ops.job_run`, `ops.load_batch`, `dq.test_result`.

## 5. Notebooks (`notebooks/`) e módulos (`src/hidro_mg_lakehouse/`)
Notebook só chama funções de `src/`.

| Notebook | Faz | Módulo |
| --- | --- | --- |
| `00_setup_catalog` | confere catálogo, schemas, volume | `config.py`, `session.py` |
| `01_extract_ibge` | municípios e população para o volume | `extract/ibge.py` |
| `01_extract_inmet` | estações e clima horário | `extract/inmet.py` |
| `01_extract_igam` | arquivos de qualidade da água | `extract/igam.py` |
| `01_extract_ana` | estações, vazão, chuva (bloqueado até liberar a API) | `extract/ana.py` |
| `02_bronze_<source>` | volume para bronze + metadados | `bronze/<source>.py` |
| `03_silver_<entity>` | limpeza, tipos, unidades | `silver/<entity>.py` |
| `03_silver_station` | unifica as três origens na tabela única `station` | `silver/station.py` |
| `04_gold_dimensions` | dim_station, dim_municipality, dim_parameter | `gold/dimensions.py` |
| `04_gold_facts` | os três fatos | `gold/facts.py` |
| `04_gold_violations` | qualidade x limites legais | `gold/violations.py` |
| `05_data_quality` | testes e gravação em `dq` | `dq/` |
| `90_explore_*` | exploração livre | nenhum |

Prefixo numérico = camada/ordem. Jobs em `pipelines/`: `job_<layer>_<source>` (ex.: `job_bronze_ibge`).

## 6. Pendências
- Colunas da bronze IGAM: dependem do formato real.
- Tudo de `ana_*`: depende da API.
- `inmet_*`: confirmar token.
- Regra de junção de estações entre origens (distância máxima, revisão manual): definir no P1 depois de ver as coordenadas reais.
- `dim_date`: decidir no P1.
