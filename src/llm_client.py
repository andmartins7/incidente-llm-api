from __future__ import annotations
import httpx, json, datetime, zoneinfo
from typing import Optional
from .settings import OLLAMA_HOST, OLLAMA_MODEL, TZ

SYS_PROMPT = (
    "Você é um extrator de informações. "
    "Sua tarefa é ler uma descrição de incidente em português e extrair EXATAMENTE os campos: "
    "data_ocorrencia, local, tipo_incidente, impacto. "
    "Responda SOMENTE um objeto JSON válido, sem comentários, sem texto extra."
)

def now_tz() -> datetime.datetime:
    try:
        tz = zoneinfo.ZoneInfo(TZ)
    except Exception:
        tz = zoneinfo.ZoneInfo("America/Sao_Paulo")
    return datetime.datetime.now(tz)

async def extract_with_llm(texto: str, referencia_iso: Optional[str] = None) -> dict | None:
    '''
    Usa Ollama /api/chat com format=json para extrair os campos.
    Retorna dict (se JSON válido) ou None se falhar.
    '''
    ref = referencia_iso or now_tz().isoformat()
    user_prompt = (
        f"Hoje é {ref}. Leia a descrição e extraia os 4 campos. "
        "Se um campo não existir no texto, retorne string vazia para ele.\n\n"
        "Descrição:\n"
        f"{texto}\n\n"
        "Formato de saída estrito:\n"
        '{'
        '"data_ocorrencia": "YYYY-MM-DD HH:MM", '
        '"local": "string", '
        '"tipo_incidente": "string", '
        '"impacto": "string"'
        '}'
    )

    payload = {
        "model": OLLAMA_MODEL,
        "format": "json",
        "messages": [
            {"role": "system", "content": SYS_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        "options": {"temperature": 0},
        "stream": False,
    }

    url = f"{OLLAMA_HOST}/api/chat"
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            r = await client.post(url, json=payload)
            r.raise_for_status()
            data = r.json()
            content = data.get("message", {}).get("content") or data.get("response")
            if not content:
                return None
            # tentar parsear JSON diretamente (format=json deve garantir)
            try:
                return json.loads(content)
            except json.JSONDecodeError:
                # fallback: tentar encontrar um bloco JSON
                import re
                m = re.search(r"\{.*\}", content, re.DOTALL)
                if m:
                    return json.loads(m.group(0))
                return None
    except Exception:
        return None
