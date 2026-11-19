import json
from datetime import date

import pytest

from hidro_mg_lakehouse.extract import ibge


def test_municipality_url_for_mg():
    assert ibge.municipality_url() == (
        "https://servicodados.ibge.gov.br/api/v1/localidades/estados/31/municipios"
    )


def test_population_url_for_mg():
    assert ibge.population_url() == (
        "https://servicodados.ibge.gov.br/api/v3/agregados/4714/periodos/2022"
        "/variaveis/93?localidades=N6[N3[31]]"
    )


def test_raw_path_follows_adr_0003():
    path = ibge.raw_path(
        "/Volumes/hidro_mg/raw/arquivos", "municipality", date(2026, 12, 1), "a.json"
    )
    assert path == ("/Volumes/hidro_mg/raw/arquivos/ibge/municipality/load_date=2026-12-01/a.json")


def test_extract_writes_original_payload_without_network():
    payload = json.dumps([{"id": 3100104, "nome": "Abadia dos Dourados"}]).encode()
    written = {}

    path = ibge.extract_municipalities(
        "/Volumes/x/raw/arquivos",
        date(2026, 12, 1),
        write=lambda p, c: written.update({p: c}),
        fetch=lambda url: payload,
    )

    assert written == {path: payload}
    assert path.endswith("/ibge/municipality/load_date=2026-12-01/municipality.json")


def test_extract_rejects_empty_response():
    with pytest.raises(ValueError):
        ibge.extract_population(
            "/Volumes/x/raw/arquivos",
            date(2026, 12, 1),
            write=lambda p, c: None,
            fetch=lambda u: b"[]",
        )
