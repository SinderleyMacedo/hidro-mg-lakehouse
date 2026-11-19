"""Comentários (COMMENT) em português de todos os objetos do Unity Catalog.

Regra do projeto: toda tabela, schema, volume e coluna criados têm COMMENT completo.
Os textos ficam aqui; as funções `*_statements` só montam o SQL (testáveis sem Spark)
e as `apply_*` o executam. COMMENT substitui o texto anterior, então reaplicar é seguro.
"""

from typing import Any

from hidro_mg_lakehouse.config import catalog

CATALOG_COMMENT = (
    "Catálogo do projeto Hidro MG (portfólio de engenharia de dados, só dados públicos): "
    "qualidade da água, vazão e clima em Minas Gerais, com o IBGE como dimensão de município "
    "e população. Fontes: IGAM, ANA, INMET, IBGE e limites legais (CONAMA 357/430, DN "
    "COPAM/CERH). Arquitetura medalhão: raw -> bronze -> silver -> gold, mais ops e dq."
)

SCHEMA_COMMENTS: dict[str, str] = {
    "raw": (
        "Camada raw do medalhão: volumes com os arquivos de origem exatamente como foram "
        "baixados das fontes, sem nenhuma alteração. É a base para reprocessar a bronze."
    ),
    "bronze": (
        "Camada bronze do medalhão: uma tabela Delta por fonte e entidade "
        "(<fonte>_<entidade>), lida só da raw, com tipos convertidos e colunas de controle "
        "de carga (_source, _source_file, _batch_id, _loaded_at, _row_hash). Imutável e "
        "reprocessável: recarregar um arquivo substitui apenas as linhas dele."
    ),
    "silver": (
        "Camada silver do medalhão: dados limpos e padronizados (nomes, unidades, datas em "
        "UTC), lidos só da bronze, com a tabela única de estações (station) ligando cada "
        "estação ao município pelo código IBGE."
    ),
    "gold": (
        "Camada gold do medalhão: modelo dimensional para análise, lido só da silver "
        "(fact_water_quality, fact_flow, fact_weather, fact_limit_violation, dim_station, "
        "dim_municipality, dim_parameter)."
    ),
    "ops": (
        "Schema operacional (fora do medalhão): histórico de execuções de jobs e de lotes "
        "de carga (ex.: job_run, load_batch)."
    ),
    "dq": (
        "Schema de qualidade de dados (fora do medalhão): resultados dos testes do hidrodq "
        "(ex.: test_result)."
    ),
}

VOLUME_COMMENTS: dict[tuple[str, str], str] = {
    ("raw", "arquivos"): (
        "Arquivos de origem sem alteração, organizados em "
        "<fonte>/<entidade>/load_date=AAAA-MM-DD/<arquivo> (ex.: "
        "ibge/municipality/load_date=2026-11-18/municipality.json). Cada pasta load_date= é "
        "uma extração; repetir a extração no mesmo dia sobrescreve o arquivo daquele dia."
    ),
}

CONTROL_COLUMN_COMMENTS: dict[str, str] = {
    "_source": "Controle de carga: fonte de origem dos dados (ex.: 'ibge'), fixa no código.",
    "_source_file": (
        "Controle de carga: caminho completo, no volume raw, do arquivo lido. Recarregar o "
        "mesmo arquivo substitui só as linhas com este valor (replaceWhere)."
    ),
    "_batch_id": (
        "Controle de carga: identificador do lote (UUID4 em hexadecimal, 32 caracteres), "
        "igual para todas as linhas gravadas na mesma execução."
    ),
    "_loaded_at": "Controle de carga: data e hora da gravação na bronze, em UTC.",
    "_row_hash": (
        "Controle de carga: SHA-256 em hexadecimal (64 caracteres) das colunas de negócio "
        "da linha, serializadas em JSON com chaves ordenadas. Não inclui colunas de controle; "
        "serve para detectar mudança de conteúdo entre cargas."
    ),
}

_IBGE_MUNICIPALITY_URL = "https://servicodados.ibge.gov.br/api/v1/localidades/estados/31/municipios"
_IBGE_POPULATION_URL = (
    "https://servicodados.ibge.gov.br/api/v3/agregados/4714/periodos/2022/variaveis/93"
    "?localidades=N6[N3[31]]"
)

TABLE_COMMENTS: dict[tuple[str, str], tuple[str, dict[str, str]]] = {
    ("bronze", "ibge_municipality"): (
        "Camada bronze. Municípios de Minas Gerais com a divisão regional do IBGE "
        "(microrregião, mesorregião, região imediata e intermediária). Fonte: IBGE, API de "
        f"Localidades v1, endpoint {_IBGE_MUNICIPALITY_URL}. Arquivo de origem no volume "
        "raw: ibge/municipality/load_date=AAAA-MM-DD/municipality.json. Granularidade: uma "
        "linha por município por arquivo carregado (853 municípios por carga). Frequência: "
        "sob demanda (notebooks 01_extract_ibge e 02_bronze_ibge, ainda sem agendamento); "
        "cadastro que muda raramente.",
        {
            "municipality_code": (
                "Código IBGE do município, 7 dígitos (2 da UF + 4 do município + dígito "
                "verificador). Na API vinha como número (campo id); convertido para texto "
                "e validado com 7 dígitos (docs/naming.md). Chave para cruzar com as demais "
                "fontes."
            ),
            "municipality_name": (
                "Nome oficial do município (campo nome da API, texto). Mantido como veio, "
                "sem correção de grafia."
            ),
            "microregion_code": (
                "Código IBGE da microrregião geográfica (campo microrregiao.id). Vinha como "
                "número; convertido para texto."
            ),
            "microregion_name": "Nome da microrregião geográfica (campo microrregiao.nome, texto).",
            "mesoregion_code": (
                "Código IBGE da mesorregião geográfica (campo microrregiao.mesorregiao.id). "
                "Vinha como número; convertido para texto."
            ),
            "mesoregion_name": (
                "Nome da mesorregião geográfica (campo microrregiao.mesorregiao.nome, texto)."
            ),
            "immediate_region_code": (
                "Código IBGE da região geográfica imediata (divisão de 2017, campo "
                "regiao-imediata.id). Vinha como número; convertido para texto."
            ),
            "immediate_region_name": (
                "Nome da região geográfica imediata (campo regiao-imediata.nome, texto)."
            ),
            "intermediate_region_code": (
                "Código IBGE da região geográfica intermediária (divisão de 2017, campo "
                "regiao-imediata.regiao-intermediaria.id). Vinha como número; convertido "
                "para texto."
            ),
            "intermediate_region_name": (
                "Nome da região geográfica intermediária (campo "
                "regiao-imediata.regiao-intermediaria.nome, texto)."
            ),
            "uf_code": (
                "Código IBGE da unidade da federação (31 = Minas Gerais), do campo "
                "microrregiao.mesorregiao.UF.id. Vinha como número; convertido para texto."
            ),
            "uf_acronym": "Sigla da unidade da federação (campo UF.sigla, texto; ex.: MG).",
            **CONTROL_COLUMN_COMMENTS,
        },
    ),
    ("bronze", "ibge_population"): (
        "Camada bronze. População residente dos municípios de Minas Gerais no Censo "
        "Demográfico 2022. Fonte: IBGE, API de Agregados v3, agregado (tabela) 4714 "
        "(População residente, área territorial e densidade demográfica), variável 93 "
        f"(População residente, em pessoas), período 2022; endpoint {_IBGE_POPULATION_URL}. "
        "Arquivo de origem no volume raw: ibge/population/load_date=AAAA-MM-DD/"
        "population.json. Granularidade: uma linha por município, ano de referência e "
        "arquivo carregado (853 municípios por carga). Frequência: sob demanda (notebooks "
        "01_extract_ibge e 02_bronze_ibge, ainda sem agendamento); o Censo é decenal.",
        {
            "municipality_code": (
                "Código IBGE do município, 7 dígitos. Na API vinha como texto (campo "
                "localidade.id); mantido como texto e validado com 7 dígitos. Chave para "
                "ligar com bronze.ibge_municipality."
            ),
            "municipality_name": (
                "Nome do município (campo localidade.nome, texto). Na API vinha com o sufixo "
                "da UF (ex.: 'Abaeté - MG'); o sufixo ' - MG' foi removido."
            ),
            "reference_year": (
                "Ano de referência do dado (período do agregado; 2022 = Censo 2022). Na API "
                "era a chave de texto do objeto serie; convertido para inteiro."
            ),
            "population": (
                "População residente, em pessoas (variável 93). Na API vinha como texto; "
                "convertido para inteiro (BIGINT). Valor não numérico vira NULL (não ocorreu "
                "na carga de MG 2022)."
            ),
            "variable_code": "Código da variável no agregado 4714 (campo id; texto, '93').",
            "variable_name": (
                "Nome da variável conforme o IBGE (campo variavel, texto: População residente)."
            ),
            "unit": "Unidade de medida da variável (campo unidade, texto: Pessoas).",
            **CONTROL_COLUMN_COMMENTS,
        },
    ),
}


def sql_string(text: str) -> str:
    """Literal de texto SQL com aspas simples e barras invertidas escapadas."""
    return "'" + text.replace("\\", "\\\\").replace("'", "\\'") + "'"


def quote(*parts: str) -> str:
    """Identificador qualificado com crases (`a`.`b`.`c`)."""
    return ".".join(f"`{part}`" for part in parts)


def catalog_statements() -> list[str]:
    """COMMENT do catálogo, dos schemas e dos volumes."""
    cat = catalog()
    statements = [f"COMMENT ON CATALOG {quote(cat)} IS {sql_string(CATALOG_COMMENT)}"]
    statements += [
        f"COMMENT ON SCHEMA {quote(cat, name)} IS {sql_string(text)}"
        for name, text in SCHEMA_COMMENTS.items()
    ]
    statements += [
        f"COMMENT ON VOLUME {quote(cat, layer, name)} IS {sql_string(text)}"
        for (layer, name), text in VOLUME_COMMENTS.items()
    ]
    return statements


def table_statements(layer: str, name: str) -> list[str]:
    """COMMENT da tabela e de cada coluna."""
    table_comment, columns = TABLE_COMMENTS[(layer, name)]
    target = quote(catalog(), layer, name)
    statements = [f"COMMENT ON TABLE {target} IS {sql_string(table_comment)}"]
    statements += [
        f"ALTER TABLE {target} ALTER COLUMN {quote(column)} COMMENT {sql_string(text)}"
        for column, text in columns.items()
    ]
    return statements


def setup_statements() -> list[str]:
    """Garante que schemas e volumes existam (sem apagar nada)."""
    cat = catalog()
    statements = [f"CREATE SCHEMA IF NOT EXISTS {quote(cat, name)}" for name in SCHEMA_COMMENTS]
    statements += [
        f"CREATE VOLUME IF NOT EXISTS {quote(cat, layer, name)}" for layer, name in VOLUME_COMMENTS
    ]
    return statements


def _run(spark: Any, statements: list[str]) -> int:
    for statement in statements:
        spark.sql(statement)
    return len(statements)


def apply_table_comments(spark: Any, layer: str, name: str) -> int:
    """Aplica os comentários de uma tabela. Devolve o número de comandos executados."""
    return _run(spark, table_statements(layer, name))


def apply_catalog_comments(spark: Any) -> int:
    """Cria schemas e volumes que faltarem e aplica os comentários deles e do catálogo.

    Também comenta as tabelas conhecidas que já existirem.
    """
    count = _run(spark, setup_statements() + catalog_statements())
    for layer, name in TABLE_COMMENTS:
        if spark.catalog.tableExists(f"{catalog()}.{layer}.{name}"):
            count += apply_table_comments(spark, layer, name)
    return count
