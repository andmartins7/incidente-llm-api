from fastapi.testclient import TestClient
from src.main import app

client = TestClient(app)

def test_extract_fallback_only():
    payload = {
        "texto": "Ontem às 14h no escritório de Porto Alegre houve queda de energia que afetou a rede interna por 30 minutos."
    }
    r = client.post("/extract", json=payload)
    assert r.status_code == 200
    data = r.json()
    assert set(data.keys()) == {"data_ocorrencia", "local", "tipo_incidente", "impacto"}
    assert data["impacto"] != ""
