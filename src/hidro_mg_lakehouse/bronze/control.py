"""Colunas de controle comuns a toda tabela bronze (ADR 0003)."""

import hashlib
import json
import uuid
from datetime import UTC, datetime

CONTROL_COLUMNS: list[tuple[str, str]] = [
    ("_source", "STRING"),
    ("_source_file", "STRING"),
    ("_batch_id", "STRING"),
    ("_loaded_at", "TIMESTAMP"),
    ("_row_hash", "STRING"),
]


def row_hash(row: dict) -> str:
    """SHA-256 das colunas de negócio; não depende da ordem das chaves."""
    payload = json.dumps(row, sort_keys=True, ensure_ascii=False, default=str)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def new_batch_id() -> str:
    return uuid.uuid4().hex


def add_control_columns(
    rows: list[dict],
    source: str,
    source_file: str,
    batch_id: str | None = None,
    loaded_at: datetime | None = None,
) -> list[dict]:
    """Acrescenta as colunas de controle a cada linha (mesmo lote e horário para todas)."""
    batch_id = batch_id or new_batch_id()
    loaded_at = loaded_at or datetime.now(UTC)
    return [
        {
            **row,
            "_source": source,
            "_source_file": source_file,
            "_batch_id": batch_id,
            "_loaded_at": loaded_at,
            "_row_hash": row_hash(row),
        }
        for row in rows
    ]
