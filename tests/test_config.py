from hidro_mg_lakehouse.config import raw_volume_root, schema, table


def test_schema_uses_default_catalog(monkeypatch):
    monkeypatch.delenv("UC_CATALOG", raising=False)
    assert schema("bronze") == "hidro_mg.bronze"


def test_schema_uses_env_catalog(monkeypatch):
    monkeypatch.setenv("UC_CATALOG", "outro_catalogo")
    assert schema("gold") == "outro_catalogo.gold"


def test_raw_volume_root_follows_catalog(monkeypatch):
    monkeypatch.delenv("UC_RAW_VOLUME", raising=False)
    monkeypatch.setenv("UC_CATALOG", "hidro_mg")
    assert raw_volume_root() == "/Volumes/hidro_mg/raw/arquivos"


def test_table_is_fully_qualified(monkeypatch):
    monkeypatch.setenv("UC_CATALOG", "hidro_mg")
    assert table("bronze", "ibge_population") == "hidro_mg.bronze.ibge_population"
