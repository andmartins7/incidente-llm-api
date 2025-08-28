from __future__ import annotations
import asyncio
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from .models import IncidentRequest, IncidentResponse
from .preprocess import preprocess_text
from .llm_client import extract_with_llm
from .extractors import fallback_extract, merge_dicts
from .settings import APP_PORT, TZ

app = FastAPI(title="Incidente LLM API", version="1.0.0")

@app.get("/healthz")
async def healthz():
    return {"status": "ok", "tz": TZ, "app_port": APP_PORT}

@app.get("/example")
async def example():
    texto = "Ontem às 14h, no escritório de São Paulo, houve uma falha no servidor principal que afetou o sistema de faturamento por 2 horas."
    return {"texto": texto}

@app.post("/extract", response_model=IncidentResponse)
async def extract(payload: IncidentRequest):
    # 1) Preprocess
    texto = preprocess_text(payload.texto)

    # 2) LLM
    llm_task = extract_with_llm(texto, payload.referencia_datahora)

    # 3) Fallback por regras
    rb = fallback_extract(texto, payload.referencia_datahora)

    # 4) Tenta primeiro o LLM (com timeout)
    try:
        llm = await asyncio.wait_for(llm_task, timeout=35.0)
    except asyncio.TimeoutError:
        llm = None

    final = merge_dicts(llm or {}, rb or {})

    # Garante chaves esperadas
    resp = IncidentResponse(**final)
    return JSONResponse(content=resp.model_dump(), status_code=200)
