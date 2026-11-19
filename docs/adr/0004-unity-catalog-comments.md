# 0004. Comentários em português em todo objeto do Unity Catalog

Data: 2026-11-18
Status: aceita (pedida pelo usuário como regra nova do projeto)

## Contexto
Quem abre o Catalog Explorer ou consulta uma tabela precisa entender, sem ler o código, o que cada objeto guarda: de onde veio o dado, em que unidade está, que conversões foram feitas e para que servem as colunas de controle. Sem isso, o catálogo vira uma lista de nomes em inglês sem explicação.

## Decisão
- Toda tabela, schema, volume e coluna criados têm COMMENT completo em português.
- Tabela: o que é, fonte e endpoint, granularidade, frequência de carga e camada.
- Coluna: significado, unidade, tipo original na fonte e conversões aplicadas. As colunas de controle (`_source`, `_source_file`, `_batch_id`, `_loaded_at`, `_row_hash`) têm textos únicos, compartilhados por todas as tabelas bronze.
- Os textos ficam no código, em `src/hidro_mg_lakehouse/catalog/comments.py`, e são aplicados por `COMMENT ON` e `ALTER TABLE ... ALTER COLUMN ... COMMENT`. Quem aplica: o `00_setup_catalog` (catálogo, schemas, volume e tabelas existentes) e o notebook de cada camada, depois de gravar.
- Um teste compara as colunas de cada tabela com os comentários cadastrados e falha se faltar ou sobrar algum.

## Consequências
- Os comentários são versionados com o código e reaplicados a cada carga, então não se perdem nem divergem do que foi feito à mão.
- Toda tabela nova (silver, gold, ops, dq) precisa entrar em `TABLE_COMMENTS` junto com o código que a cria; sem isso, o teste de consistência pede o texto.
- Mudar um texto exige commit, como qualquer outra mudança.
