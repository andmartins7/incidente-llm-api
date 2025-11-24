# API de Extração de Incidentes com LLM Local (Ollama)

Este projeto implementa uma **API em Python (FastAPI)** que recebe uma descrição textual de um incidente,
utiliza um **LLM local via Ollama** para extrair campos estruturados e retorna um **JSON** com as chaves:

- `data_ocorrencia` — data e hora do incidente (se presente)
- `local` — local do incidente
- `tipo_incidente` — tipo/categoria do incidente
- `impacto` — breve descrição do impacto

> **Foco**: boas práticas, organização do código, reprodutibilidade local e integração com LLM **offline** (sem serviços de nuvem).

---

## 🔧 Requisitos

- Python 3.10+
- [Ollama](https://ollama.com/) em execução local
- (Opcional) Docker e Docker Compose

---

## 📦 Instalação (modo local)

1) Crie e ative um ambiente virtual:
```bash
python -m venv .venv
source .venv/bin/activate  # no Windows: .venv\Scripts\activate
```

2) Instale as dependências:
```bash
pip install -r requirements.txt
```

3) Inicie o **Ollama** (em outro terminal):
```bash
ollama serve &
# escolha um modelo pequeno:
ollama pull tinyllama
# ou:
ollama pull llama3.2
```

4) Configure variáveis de ambiente (opcional – podem ser passadas via `.env`):
```bash
export OLLAMA_HOST=http://localhost:11434
export OLLAMA_MODEL=llama3.2  # ou tinyllama
export LOG_LEVEL=INFO
export TZ=America/Sao_Paulo
```

5) Rode a API:
```bash
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

Abra a documentação interativa em: <http://localhost:8000/docs>

---

## ▶️ Exemplos de uso

### cURL (POST /extract)
```bash
curl -s -X POST http://localhost:8000/extract   -H "Content-Type: application/json"   -d '{{
        "texto": "Ontem às 14h, no escritório de São Paulo, houve uma falha no servidor principal que afetou o sistema de faturamento por 2 horas."
      }}' | jq .
```

### Python (requests)
```python
import requests
payload = {{
  "texto": "Ontem às 14h, no escritório de São Paulo, houve uma falha no servidor principal que afetou o sistema de faturamento por 2 horas."
}}
print(requests.post("http://localhost:8000/extract", json=payload).json())
```

Saída **esperada** (exemplo):
```json
{{
  "data_ocorrencia": "2025-08-12 14:00",
  "local": "São Paulo",
  "tipo_incidente": "Falha no servidor",
  "impacto": "Sistema de faturamento indisponível por 2 horas"
}}
```

> Observação: o LLM local pode não acertar todos os campos. A API valida o JSON e
> aplica um **fallback por regras** para preencher o que estiver faltando.

---

## 🧠 Como funciona

1. **Pré-processamento** do texto (`src/preprocess.py`): normaliza espaços, corrige padrões comuns de hora/data etc.
2. **Chamada ao LLM local** (`src/llm_client.py`): usa o endpoint **Ollama** (`/api/chat`) com um prompt **instruído a responder somente JSON**.
3. **Validação e Fallback** (`src/extractors.py`): valida o JSON com um **schema JSON (jsonschema)**; se estiver inválido ou incompleto, usa **expressões regulares**, **dicionário/NER local de localidades** e **heurísticas** (com `dateparser`) para preencher os campos.
4. **API FastAPI** (`src/main.py`): expõe `POST /extract`, `GET /healthz`, `GET /example` e `GET /metrics` (Prometheus). Inclui **logs estruturados** em JSON.

---

## 🧪 Testes

Execute testes básicos (sem LLM, usando fallback):
```bash
pytest -q
```

---

## 🐳 Docker (opcional)

### Executar somente a API (supondo Ollama fora do container)
```bash
docker build -t incidente-llm-api -f docker/Dockerfile .
docker run --rm -p 8000:8000   -e OLLAMA_HOST=http://host.docker.internal:11434   -e OLLAMA_MODEL=llama3.2   incidente-llm-api
```

### Docker Compose (API + Ollama)
> **Atenção**: baixar o modelo pode levar alguns minutos na primeira vez.
```bash
docker compose -f docker/compose.yml up --build
# API: http://localhost:8000/docs
# Ollama: porta 11434 dentro da rede do compose
```

---

## 📁 Estrutura do projeto

```
incidente_llm_api/
├── README.md
├── requirements.txt
├── .env.example
├── src/
│   ├── main.py
│   ├── models.py
│   ├── settings.py
│   ├── preprocess.py
│   ├── llm_client.py
│   └── extractors.py
├── tests/
│   └── test_api.py
├── scripts/
│   ├── curl_example.sh
│   └── install_ollama_linux.sh
├── examples/
│   └── incidento_exemplo.txt
└── docker/
    ├── Dockerfile
    └── compose.yml
```

---

## 📝 Notas

- A API é **100% local** e **não** utiliza provedores de nuvem.
- Use `LLM` **pequeno** (ex.: `tinyllama`, `llama3.2`) apenas para validar a integração.
- Campos ausentes no texto serão retornados como string vazia.
- A API injeta no prompt a data/hora atual (fuso `America/Sao_Paulo`) para ajudar o LLM a resolver textos relativos (ex.: *ontem*, *hoje*).

---

## 🧭 Roadmap (sugestões)
- Melhorar o parser de localidades com dicionário/NER local.
- Adicionar schema JSON com `jsonschema` para validação estrita.
- Expor métricas (Prometheus) e log estruturado.
