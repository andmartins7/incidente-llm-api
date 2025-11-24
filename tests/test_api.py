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


def test_extract_respects_relative_day_with_time():
    payload = {
        "texto": "Ontem às 14h houve falha no servidor principal que impactou clientes corporativos.",
        "referencia_datahora": "2024-08-10T10:00:00-03:00",
    }
    r = client.post("/extract", json=payload)
    assert r.status_code == 200
    data = r.json()
    # Ontem relativo à referência 2024-08-10 deve ser 2024-08-09.
    assert data["data_ocorrencia"] == "2024-08-09 14:00"
