from __future__ import annotations

"""
Pequena implementação local do subset necessário da biblioteca `jsonschema` para
validar o payload de resposta. A API expõe as classes ``ValidationError`` e
``Draft202012Validator`` com a interface mínima usada neste projeto.
"""

import re
from typing import Any, Dict, Iterable, List

__all__ = ["ValidationError", "Draft202012Validator"]


class ValidationError(Exception):
    pass


class Draft202012Validator:
    def __init__(self, schema: Dict[str, Any]):
        self.schema = schema

    def iter_errors(self, instance: Dict[str, Any]) -> Iterable[ValidationError]:
        errors: List[ValidationError] = []
        if not isinstance(instance, dict):
            errors.append(ValidationError("payload deve ser um objeto"))
            return errors

        required = self.schema.get("required", [])
        for key in required:
            if key not in instance:
                errors.append(ValidationError(f"campo obrigatório ausente: {key}"))

        allowed_keys = set(self.schema.get("properties", {}).keys())
        for key in instance.keys():
            if key not in allowed_keys:
                errors.append(ValidationError(f"chave não permitida: {key}"))

        properties: Dict[str, Dict[str, Any]] = self.schema.get("properties", {})
        for key, constraints in properties.items():
            value = instance.get(key)
            if not isinstance(value, str):
                errors.append(ValidationError(f"{key} deve ser string"))
                continue

            if "anyOf" in constraints:
                if not any(self._matches_schema(value, opt) for opt in constraints["anyOf"]):
                    errors.append(ValidationError(f"{key} não corresponde ao formato permitido"))
            else:
                if not self._matches_schema(value, constraints):
                    errors.append(ValidationError(f"{key} não corresponde ao formato permitido"))

        return errors

    @staticmethod
    def _matches_schema(value: str, schema: Dict[str, Any]) -> bool:
        if schema.get("type") != "string":
            return False
        if "const" in schema:
            return value == schema["const"]
        pattern = schema.get("pattern")
        if pattern and not re.match(pattern, value):
            return False
        return True

