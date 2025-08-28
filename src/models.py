from pydantic import BaseModel, Field
from typing import Optional

class IncidentRequest(BaseModel):
    texto: str = Field(..., description="Descrição textual do incidente")
    referencia_datahora: Optional[str] = Field(
        default=None,
        description="Referência temporal ISO-8601 para resolver 'hoje/ontem' (ex.: 2025-08-13T10:00:00-03:00)"
    )

class IncidentResponse(BaseModel):
    data_ocorrencia: str = ""
    local: str = ""
    tipo_incidente: str = ""
    impacto: str = ""
