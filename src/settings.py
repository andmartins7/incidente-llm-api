import os

def getenv(key: str, default: str | None = None) -> str | None:
    val = os.getenv(key, default)
    return val

OLLAMA_HOST = getenv("OLLAMA_HOST", "http://localhost:11434")
OLLAMA_MODEL = getenv("OLLAMA_MODEL", "llama3.2")
TZ = getenv("TZ", "America/Sao_Paulo")
APP_PORT = int(getenv("APP_PORT", "8000") or 8000)
