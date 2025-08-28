import re

def preprocess_text(texto: str) -> str:
    '''
    Normaliza o texto de entrada para reduzir ruído antes do envio ao LLM.
    - Remove espaços duplicados
    - Normaliza padrões de horário (ex.: '14 h' -> '14h')
    - Garante vírgulas simples e pontuação básica
    '''
    if not texto:
        return ""

    t = texto.strip()

    # normaliza múltiplos espaços
    t = re.sub(r"\s+", " ", t)

    # normaliza Horas '14 h' -> '14h', '14 : 30' -> '14:30'
    t = re.sub(r"(\d{1,2})\s*h\b", r"\1h", t, flags=re.IGNORECASE)
    t = re.sub(r"(\d{1,2})\s*:\s*(\d{2})", r"\1:\2", t)

    # remove espaços antes de vírgulas/pontos
    t = re.sub(r"\s+([,.;:])", r"\1", t)

    # corrige vírgula sem espaço após
    t = re.sub(r",(\S)", r", \1", t)

    return t
