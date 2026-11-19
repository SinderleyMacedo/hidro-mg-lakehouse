import json
from pathlib import Path

import pytest

from hidro_mg_lakehouse.bronze import ibge
from hidro_mg_lakehouse.bronze.control import CONTROL_COLUMNS

DATA = Path(__file__).parent / "data"
MUNICIPALITY = (DATA / "ibge_municipality_sample.json").read_bytes()
POPULATION = (DATA / "ibge_population_sample.json").read_bytes()


def test_parse_municipalities_flattens_and_converts_codes_to_text():
    rows = ibge.parse_municipalities(MUNICIPALITY)

    assert len(rows) == 2
    assert rows[0] == {
        "municipality_code": "3100104",
        "municipality_name": "Abadia dos Dourados",
        "microregion_code": "31019",
        "microregion_name": "Patrocínio",
        "mesoregion_code": "3105",
        "mesoregion_name": "Triângulo Mineiro/Alto Paranaíba",
        "immediate_region_code": "310061",
        "immediate_region_name": "Monte Carmelo",
        "intermediate_region_code": "3111",
        "intermediate_region_name": "Uberlândia",
        "uf_code": "31",
        "uf_acronym": "MG",
    }


def test_parse_population_converts_types_and_strips_uf_suffix():
    rows = ibge.parse_population(POPULATION)

    assert [r["municipality_name"] for r in rows] == [
        "Abadia dos Dourados",
        "Abaeté",
        "Abre Campo",
    ]
    assert rows[0] == {
        "municipality_code": "3100104",
        "municipality_name": "Abadia dos Dourados",
        "reference_year": 2022,
        "population": 6272,
        "variable_code": "93",
        "variable_name": "População residente",
        "unit": "Pessoas",
    }


def test_parse_population_keeps_non_numeric_value_as_null():
    data = json.loads(POPULATION)
    data[0]["resultados"][0]["series"][0]["serie"]["2022"] = "-"

    rows = ibge.parse_population(json.dumps(data).encode())

    assert rows[0]["population"] is None


@pytest.mark.parametrize("value", ["310010", "31001045", "abc1234", ""])
def test_municipality_code_rejects_invalid(value):
    with pytest.raises(ValueError):
        ibge.municipality_code(value)


def test_columns_match_parsed_rows():
    for entity, (parse, columns) in ibge.ENTITIES.items():
        payload = MUNICIPALITY if entity == "municipality" else POPULATION
        assert list(parse(payload)[0]) == [name for name, _ in columns]


def test_latest_source_file_picks_most_recent_load_date():
    listing = [
        "/V/ibge/population/load_date=2026-11-18/",
        "/V/ibge/population/load_date=2026-12-01/",
        "/V/ibge/population/README.txt",
    ]

    path = ibge.latest_source_file("/V", "population", lambda p: listing)

    assert path == "/V/ibge/population/load_date=2026-12-01/population.json"


def test_latest_source_file_fails_without_loads():
    with pytest.raises(FileNotFoundError):
        ibge.latest_source_file("/V", "population", lambda p: [])


def test_load_entity_writes_to_bronze_table(monkeypatch):
    monkeypatch.setenv("UC_CATALOG", "hidro_mg")
    calls = {}

    def fake_write(spark, table, columns, rows, source_file):
        calls.update(table=table, columns=columns, rows=rows, source_file=source_file)
        return len(rows)

    monkeypatch.setattr(ibge, "write_bronze", fake_write)
    folder = "/V/ibge/population/load_date=2026-11-18"

    result = ibge.load_entity(
        spark=None,
        entity="population",
        root="/V",
        read=lambda p: POPULATION,
        list_dir=lambda p: [folder],
    )

    assert result == ("hidro_mg.bronze.ibge_population", 3)
    assert calls["source_file"] == f"{folder}/population.json"
    assert calls["columns"] == ibge.POPULATION_COLUMNS + CONTROL_COLUMNS
    assert {r["_source"] for r in calls["rows"]} == {"ibge"}
