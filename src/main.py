from __future__ import annotations

import asyncio
import time
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse, PlainTextResponse
from jsonschema import ValidationError
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
from starlette.requests import Request

from .models import IncidentRequest, IncidentResponse
from .preprocess import preprocess_text
from .llm_client import extract_with_llm
from .extractors import fallback_extract, merge_dicts
from .settings import APP_PORT, TZ
from .schema import validate_incident_payload
from .logging_utils import configure_logging

logger = configure_logging()

REQUEST_COUNT = Counter(
    "incidente_llm_api_requests_total",
    "Total de requisições HTTP",
    labelnames=("method", "path", "status"),
)
REQUEST_LATENCY = Histogram(
    "incidente_llm_api_request_duration_seconds",
    "Duração das requisições HTTP",
    labelnames=("method", "path"),
)

app = FastAPI(title="Incidente LLM API", version="1.1.0")


@app.middleware("http")
async def metrics_and_logging(request: Request, call_next):
    start = time.perf_counter()
    path = request.url.path
    method = request.method
    try:
        response = await call_next(request)
        status = response.status_code
    except Exception:
        status = 500
        REQUEST_COUNT.labels(method, path, str(status)).inc()
        logger.exception("request_error", extra={"path": path, "method": method})
        raise

    duration = time.perf_counter() - start
    REQUEST_COUNT.labels(method, path, str(status)).inc()
    REQUEST_LATENCY.labels(method, path).observe(duration)
    logger.info(
        "request_completed",
        extra={
            "path": path,
            "method": method,
            "status": status,
            "duration_ms": round(duration * 1000, 2),
        },
    )
    return response


@app.get("/healthz")
async def healthz():
    return {"status": "ok", "tz": TZ, "app_port": APP_PORT}


@app.get("/metrics")
async def metrics():
    return PlainTextResponse(generate_latest(), media_type=CONTENT_TYPE_LATEST)


@app.get("/example")
async def example():
    texto = (
        "Ontem às 14h, no escritório de São Paulo, houve uma falha no servidor principal que "
        "afetou o sistema de faturamento por 2 horas."
    )
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

    try:
        validate_incident_payload(final)
    except ValidationError as exc:
        logger.warning("schema_validation_failed", extra={"error": str(exc), "payload": final})
        raise HTTPException(status_code=422, detail="Resposta não atende ao schema JSON")

    # Garante chaves esperadas
    resp = IncidentResponse(**final)
    logger.info("extraction_completed", extra={"has_llm": bool(llm), "payload": resp.model_dump()})
    return JSONResponse(content=resp.model_dump(), status_code=200)

