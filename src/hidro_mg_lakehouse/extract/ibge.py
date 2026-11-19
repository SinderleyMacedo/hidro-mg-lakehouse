"""Extração do IBGE: municípios (API de Localidades v1) e população (API de Agregados v3).

Verificado em 19/11/2026 (consultas reais, HTTP 200):
- Municípios de MG: 853 itens; campo `id` é número de 7 dígitos.
- Tabela 4714 (Censo 2022), variável 93 (população residente): 853 municípios de MG;
  `localidade.id` e os valores vêm como texto.
Esta camada grava o JSON como veio. A conversão de tipos fica para a bronze/silver.
"""

import json
import urllib.request
from collections.abc import Callable
from datetime import date

BASE_URL = "https://servicodados.ibge.gov.br/api"
UF_MG = 31
POPULATION_TABLE = 4714  # População residente, área e densidade (Censo 2022)
POPULATION_VARIABLE = 93  # População residente (pessoas)
POPULATION_PERIOD = 2022
TIMEOUT_SECONDS = 60


def municipality_url(uf_code: int = UF_MG) -> str:
    return f"{BASE_URL}/v1/localidades/estados/{uf_code}/municipios"


def population_url(
    uf_code: int = UF_MG,
    table: int = POPULATION_TABLE,
    period: int = POPULATION_PERIOD,
    variable: int = POPULATION_VARIABLE,
) -> str:
    return (
        f"{BASE_URL}/v3/agregados/{table}/periodos/{period}"
        f"/variaveis/{variable}?localidades=N6[N3[{uf_code}]]"
    )


def raw_path(root: str, entity: str, load_date: date, filename: str) -> str:
    """Caminho no volume: <root>/ibge/<entity>/load_date=AAAA-MM-DD/<filename>."""
    return f"{root}/ibge/{entity}/load_date={load_date.isoformat()}/{filename}"


def fetch_bytes(url: str) -> bytes:
    request = urllib.request.Request(url, headers={"Accept": "application/json"})
    with urllib.request.urlopen(request, timeout=TIMEOUT_SECONDS) as response:  # noqa: S310
        return response.read()


def check_json_list(payload: bytes, expected_min: int = 1) -> int:
    """Confere que o conteúdo é uma lista JSON não vazia e devolve o tamanho."""
    data = json.loads(payload)
    if not isinstance(data, list) or len(data) < expected_min:
        raise ValueError("Resposta inesperada do IBGE: lista JSON vazia ou de outro tipo.")
    return len(data)


def extract_entity(
    entity: str,
    url: str,
    root: str,
    load_date: date,
    write: Callable[[str, bytes], None],
    fetch: Callable[[str], bytes] = fetch_bytes,
) -> str:
    """Baixa `url` e grava o conteúdo original em `raw_path`. Devolve o caminho gravado."""
    payload = fetch(url)
    check_json_list(payload)
    path = raw_path(root, entity, load_date, f"{entity}.json")
    write(path, payload)
    return path


def extract_municipalities(root, load_date, write, uf_code=UF_MG, fetch=fetch_bytes) -> str:
    return extract_entity("municipality", municipality_url(uf_code), root, load_date, write, fetch)


def extract_population(root, load_date, write, uf_code=UF_MG, fetch=fetch_bytes) -> str:
    return extract_entity("population", population_url(uf_code), root, load_date, write, fetch)
