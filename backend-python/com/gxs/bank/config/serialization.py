from __future__ import annotations

from dataclasses import asdict, is_dataclass
from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import Any
from uuid import UUID

from sqlalchemy.inspection import inspect as sqla_inspect


def serialize(value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, list):
        return [serialize(item) for item in value]
    if isinstance(value, tuple):
        return [serialize(item) for item in value]
    if isinstance(value, dict):
        return {key: serialize(item) for key, item in value.items()}
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, UUID):
        return str(value)
    if is_dataclass(value):
        return serialize(asdict(value))

    if hasattr(value, "__table__"):
        result: dict[str, Any] = {}
        mapper = sqla_inspect(value.__class__)
        for column in mapper.columns:
            try:
                attr_name = mapper.get_property_by_column(column).key
            except Exception:
                attr_name = column.key
            result[attr_name] = serialize(getattr(value, attr_name, None))
        return result

    return value
