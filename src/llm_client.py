from __future__ import annotations
import httpx, json, datetime, zoneinfo
from typing import Optional
from .settings import OLLAMA_HOST, OLLAMA_MODEL, TZ

SYS_PROMPT = (
    "Você é um extrator de informações especializado em incidentes. Siga estritamente as regras abaixo:\n"
    "1) Trabalhe APENAS com o texto fornecido na solicitação. Não invente, traduza ou enriqueça dados externos.\n"
    "2) Extraia exclusivamente os campos data_ocorrencia, local, tipo_incidente e impacto.\n"
    "3) Responda sempre um único objeto JSON válido, sem Markdown, sem comentários, sem explicações.\n"
    "4) Utilize string vazia (\"\") quando um campo estiver ausente ou não puder ser determinado.\n"
    "5) Preserve o idioma original do texto ao preencher campos."
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
        f"Data/hora de referência: {ref}.\n"
        "Leia a descrição delimitada e devolva somente o JSON especificado.\n"
        "Descrição do incidente (não resuma, não reformule):\n"
        "<<<\n"
        f"{texto}\n"
        ">>>\n"
        "Formato de saída obrigatório (ordem fixa das chaves):\n"
        '{\n'
        '  "data_ocorrencia": "YYYY-MM-DD HH:MM",\n'
        '  "local": "string",\n'
        '  "tipo_incidente": "string",\n'
        '  "impacto": "string"\n'
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
