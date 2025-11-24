from __future__ import annotations

from jsonschema import Draft202012Validator, ValidationError
from typing import Dict, Any


INCIDENT_SCHEMA: Dict[str, Any] = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "title": "IncidentResponse",
    "type": "object",
    "additionalProperties": False,
    "required": ["data_ocorrencia", "local", "tipo_incidente", "impacto"],
    "properties": {
        "data_ocorrencia": {
            "anyOf": [
                {"type": "string", "const": ""},
                {
                    "type": "string",
                    "pattern": r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2}$",
                    "description": "Data/hora no formato YYYY-MM-DD HH:MM",
                },
            ]
        },
        "local": {"type": "string"},
        "tipo_incidente": {"type": "string"},
        "impacto": {"type": "string"},
    },
}


_validator = Draft202012Validator(INCIDENT_SCHEMA)


def validate_incident_payload(payload: Dict[str, Any]) -> None:
    """Validate incident payload against the strict JSON Schema."""
    errors = list(_validator.iter_errors(payload))
    if errors:
        raise ValidationError(errors[0].message)

