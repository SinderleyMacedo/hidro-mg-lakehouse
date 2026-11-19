import pytest

from hidro_mg_lakehouse.bronze.writer import to_ddl, write_bronze

COLUMNS = [("code", "STRING"), ("value", "BIGINT"), ("_source_file", "STRING")]
ROWS = [{"value": 10, "code": "a", "_source_file": "f.json"}]


class FakeWriter:
    def __init__(self, calls):
        self.calls = calls

    def format(self, fmt):
        self.calls.append(("format", fmt))
        return self

    def mode(self, mode):
        self.calls.append(("mode", mode))
        return self

    def option(self, key, value):
        self.calls.append(("option", key, value))
        return self

    def saveAsTable(self, name):  # noqa: N802 (nome da API do Spark)
        self.calls.append(("saveAsTable", name))


class FakeSpark:
    def __init__(self, table_exists):
        self.calls = []
        self.catalog = self
        self._exists = table_exists

    def tableExists(self, name):  # noqa: N802 (nome da API do Spark)
        return self._exists

    def createDataFrame(self, data, schema):  # noqa: N802 (nome da API do Spark)
        self.calls.append(("createDataFrame", data, schema))
        self.write = FakeWriter(self.calls)
        return self


def test_to_ddl():
    assert to_ddl(COLUMNS) == "code STRING, value BIGINT, _source_file STRING"


def test_first_load_creates_table_with_columns_in_order():
    spark = FakeSpark(table_exists=False)

    assert write_bronze(spark, "c.bronze.t", COLUMNS, ROWS, "f.json") == 1
    assert spark.calls == [
        ("createDataFrame", [("a", 10, "f.json")], to_ddl(COLUMNS)),
        ("format", "delta"),
        ("mode", "error"),
        ("saveAsTable", "c.bronze.t"),
    ]


def test_reload_replaces_only_rows_of_same_file():
    spark = FakeSpark(table_exists=True)

    write_bronze(spark, "c.bronze.t", COLUMNS, ROWS, "f.json")

    assert ("mode", "overwrite") in spark.calls
    assert ("option", "replaceWhere", "_source_file = 'f.json'") in spark.calls


def test_rejects_path_with_quote():
    with pytest.raises(ValueError):
        write_bronze(FakeSpark(True), "c.bronze.t", COLUMNS, ROWS, "f'.json")
