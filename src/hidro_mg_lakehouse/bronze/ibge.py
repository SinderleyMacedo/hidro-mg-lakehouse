"""Bronze do IBGE: municípios e população, do JSON no volume raw para tabelas Delta.

Formato verificado em 18/11/2026 nos arquivos gravados por `01_extract_ibge`:
- Municípios: `id` numérico de 7 dígitos; todos os 853 de MG têm microrregião e região imediata.
- População (agregado 4714, variável 93): `localidade.id` e valores vêm como texto;
  o nome vem com sufixo " - MG".
Conversões aqui: `municipality_code` vira texto de 7 dígitos nas duas tabelas
(docs/naming.md); população vira inteiro e o ano vira INT; o sufixo da UF sai do nome.
"""

import json
import re
from collections.abc import Callable
from typing import Any

from hidro_mg_lakehouse.bronze.control import CONTROL_COLUMNS, add_control_columns
from hidro_mg_lakehouse.bronze.writer import write_bronze
from hidro_mg_lakehouse.config import table
from hidro_mg_lakehouse.extract.volume import list_volume_dir, read_from_volume

SOURCE = "ibge"
UF_SUFFIX = re.compile(r" - [A-Z]{2}$")

MUNICIPALITY_COLUMNS: list[tuple[str, str]] = [
    ("municipality_code", "STRING"),
    ("municipality_name", "STRING"),
    ("microregion_code", "STRING"),
    ("microregion_name", "STRING"),
    ("mesoregion_code", "STRING"),
    ("mesoregion_name", "STRING"),
    ("immediate_region_code", "STRING"),
    ("immediate_region_name", "STRING"),
    ("intermediate_region_code", "STRING"),
    ("intermediate_region_name", "STRING"),
    ("uf_code", "STRING"),
    ("uf_acronym", "STRING"),
]

POPULATION_COLUMNS: list[tuple[str, str]] = [
    ("municipality_code", "STRING"),
    ("municipality_name", "STRING"),
    ("reference_year", "INT"),
    ("population", "BIGINT"),
    ("variable_code", "STRING"),
    ("variable_name", "STRING"),
    ("unit", "STRING"),
]


def municipality_code(value: int | str) -> str:
    """Código IBGE de município como texto de 7 dígitos; erro se não for."""
    code = str(value).strip()
    if not re.fullmatch(r"\d{7}", code):
        raise ValueError(f"Código de município inválido: {value!r}")
    return code


def to_int(value: str | None) -> int | None:
    """Converte texto numérico em inteiro; outro conteúdo vira None.

    TODO(verificar): símbolos especiais do IBGE para valor ausente ou sigiloso
    (não apareceram nos dados de MG de 2022).
    """
    text = (value or "").strip()
    return int(text) if text.isdigit() else None


def _code(value: Any) -> str | None:
    return None if value is None else str(value)


def parse_municipalities(payload: bytes) -> list[dict]:
    rows = []
    for item in json.loads(payload):
        micro = item.get("microrregiao") or {}
        meso = micro.get("mesorregiao") or {}
        immediate = item.get("regiao-imediata") or {}
        intermediate = immediate.get("regiao-intermediaria") or {}
        uf = meso.get("UF") or intermediate.get("UF") or {}
        rows.append(
            {
                "municipality_code": municipality_code(item["id"]),
                "municipality_name": item["nome"],
                "microregion_code": _code(micro.get("id")),
                "microregion_name": micro.get("nome"),
                "mesoregion_code": _code(meso.get("id")),
                "mesoregion_name": meso.get("nome"),
                "immediate_region_code": _code(immediate.get("id")),
                "immediate_region_name": immediate.get("nome"),
                "intermediate_region_code": _code(intermediate.get("id")),
                "intermediate_region_name": intermediate.get("nome"),
                "uf_code": _code(uf.get("id")),
                "uf_acronym": uf.get("sigla"),
            }
        )
    return rows


def parse_population(payload: bytes) -> list[dict]:
    """Uma linha por município e período (variável x resultado x série)."""
    rows = []
    for variable in json.loads(payload):
        for result in variable["resultados"]:
            for item in result["series"]:
                place = item["localidade"]
                for period, value in item["serie"].items():
                    rows.append(
                        {
                            "municipality_code": municipality_code(place["id"]),
                            "municipality_name": UF_SUFFIX.sub("", place["nome"]),
                            "reference_year": int(period),
                            "population": to_int(value),
                            "variable_code": _code(variable["id"]),
                            "variable_name": variable["variavel"],
                            "unit": variable["unidade"],
                        }
                    )
    return rows


ENTITIES: dict[str, tuple[Callable[[bytes], list[dict]], list[tuple[str, str]]]] = {
    "municipality": (parse_municipalities, MUNICIPALITY_COLUMNS),
    "population": (parse_population, POPULATION_COLUMNS),
}


def latest_source_file(root: str, entity: str, list_dir: Callable[[str], list[str]]) -> str:
    """Arquivo da carga mais recente: <root>/ibge/<entity>/load_date=.../<entity>.json."""
    folders = [p.rstrip("/") for p in list_dir(f"{root}/{SOURCE}/{entity}") if "load_date=" in p]
    if not folders:
        raise FileNotFoundError(f"Nenhuma carga encontrada em {root}/{SOURCE}/{entity}")
    latest = max(folders, key=lambda p: p.rsplit("load_date=", 1)[1])
    return f"{latest}/{entity}.json"


def build_rows(entity: str, payload: bytes, source_file: str, **control: Any) -> list[dict]:
    parse, _ = ENTITIES[entity]
    return add_control_columns(parse(payload), SOURCE, source_file, **control)


def load_entity(
    spark: Any,
    entity: str,
    root: str,
    read: Callable[[str], bytes] = read_from_volume,
    list_dir: Callable[[str], list[str]] = list_volume_dir,
) -> tuple[str, int]:
    """Carrega a última extração de `entity` em bronze.ibge_<entity>. Devolve (tabela, linhas)."""
    source_file = latest_source_file(root, entity, list_dir)
    rows = build_rows(entity, read(source_file), source_file)
    _, columns = ENTITIES[entity]
    target = table("bronze", f"{SOURCE}_{entity}")
    return target, write_bronze(spark, target, columns + CONTROL_COLUMNS, rows, source_file)
