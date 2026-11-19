import pytest

from hidro_mg_lakehouse.bronze import ibge
from hidro_mg_lakehouse.bronze.control import CONTROL_COLUMNS
from hidro_mg_lakehouse.catalog import comments

BRONZE_COLUMNS = {
    ("bronze", f"{ibge.SOURCE}_{entity}"): columns + CONTROL_COLUMNS
    for entity, (_, columns) in ibge.ENTITIES.items()
}


@pytest.fixture(autouse=True)
def default_catalog(monkeypatch):
    monkeypatch.setenv("UC_CATALOG", "hidro_mg")


@pytest.mark.parametrize("key", list(BRONZE_COLUMNS))
def test_every_bronze_column_has_comment(key):
    """A regra do projeto: nenhuma coluna sem COMMENT, e nenhum COMMENT sobrando."""
    _, column_comments = comments.TABLE_COMMENTS[key]
    assert list(column_comments) == [name for name, _ in BRONZE_COLUMNS[key]]


def test_all_comments_are_filled():
    texts = [comments.CATALOG_COMMENT, *comments.SCHEMA_COMMENTS.values()]
    texts += comments.VOLUME_COMMENTS.values()
    for table_comment, column_comments in comments.TABLE_COMMENTS.values():
        texts += [table_comment, *column_comments.values()]
    assert all(len(text.strip()) >= 20 for text in texts)


def test_schemas_cover_medallion_layers():
    assert set(comments.SCHEMA_COMMENTS) == {"raw", "bronze", "silver", "gold", "ops", "dq"}


def test_sql_string_escapes_quotes_and_backslashes():
    assert comments.sql_string("a 'b' \\c") == "'a \\'b\\' \\\\c'"


def test_catalog_statements_use_configured_catalog(monkeypatch):
    monkeypatch.setenv("UC_CATALOG", "outro")
    statements = comments.catalog_statements()

    assert statements[0].startswith("COMMENT ON CATALOG `outro` IS '")
    assert any(s.startswith("COMMENT ON SCHEMA `outro`.`bronze` IS") for s in statements)
    assert any(s.startswith("COMMENT ON VOLUME `outro`.`raw`.`arquivos` IS") for s in statements)


def test_table_statements_comment_table_and_each_column():
    statements = comments.table_statements("bronze", "ibge_population")

    assert statements[0].startswith("COMMENT ON TABLE `hidro_mg`.`bronze`.`ibge_population` IS")
    assert len(statements) == 1 + len(BRONZE_COLUMNS[("bronze", "ibge_population")])
    assert statements[1].startswith(
        "ALTER TABLE `hidro_mg`.`bronze`.`ibge_population` "
        "ALTER COLUMN `municipality_code` COMMENT '"
    )


class FakeSpark:
    def __init__(self, existing_tables):
        self.executed = []
        self.catalog = self
        self._existing = existing_tables

    def sql(self, statement):
        self.executed.append(statement)

    def tableExists(self, name):  # noqa: N802 (nome da API do Spark)
        return name in self._existing


def test_apply_catalog_comments_skips_missing_tables():
    spark = FakeSpark({"hidro_mg.bronze.ibge_population"})

    count = comments.apply_catalog_comments(spark)

    assert count == len(spark.executed)
    assert spark.executed[0] == "CREATE SCHEMA IF NOT EXISTS `hidro_mg`.`raw`"
    assert any("`ibge_population`" in s for s in spark.executed)
    assert not any("`ibge_municipality`" in s for s in spark.executed)
