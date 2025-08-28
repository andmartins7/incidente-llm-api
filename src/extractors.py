from __future__ import annotations
import re, datetime, zoneinfo
from typing import Optional, Dict
import dateparser
from .settings import TZ

def _now_tz() -> datetime.datetime:
    try:
        return datetime.datetime.now(zoneinfo.ZoneInfo(TZ))
    except Exception:
        return datetime.datetime.now(zoneinfo.ZoneInfo("America/Sao_Paulo"))

def parse_datetime_pt(texto: str, referencia_iso: Optional[str] = None) -> Optional[datetime.datetime]:
    settings = {"PREFER_DATES_FROM": "past", "RELATIVE_BASE": None, "TIMEZONE": TZ, "RETURN_AS_TIMEZONE_AWARE": True, "DATE_ORDER": "DMY", "LANGUAGE_DETECTION_CONFIDENCE_THRESHOLD": 0.0}
    if referencia_iso:
        try:
            ref = dateparser.parse(referencia_iso)
            if ref:
                settings["RELATIVE_BASE"] = ref
        except Exception:
            pass
    return dateparser.parse(texto, languages=["pt"], settings=settings)

def normalize_dt(dt: datetime.datetime) -> str:
    # Retorna "YYYY-MM-DD HH:MM"
    dt = dt.astimezone(zoneinfo.ZoneInfo(TZ))
    return dt.strftime("%Y-%m-%d %H:%M")

def fallback_extract(texto: str, referencia_iso: Optional[str] = None) -> Dict[str, str]:
    '''
    Heurísticas simples para extrair campos quando o LLM falhar ou vier incompleto.
    '''
    t = texto

    # === data/hora ===
    dt = None
    # procura por padrões explícitos: "às 14h30", "14:00", "14h"
    m_time = re.search(r"\b(\d{1,2}):(\d{2})\b", t)
    if m_time:
        horas, mins = int(m_time.group(1)), int(m_time.group(2))
        base = parse_datetime_pt("hoje", referencia_iso) or _now_tz()
        dt = base.replace(hour=horas, minute=mins, second=0, microsecond=0)
    else:
        m_h = re.search(r"\b(\d{1,2})h\b", t, re.IGNORECASE)
        if m_h:
            horas = int(m_h.group(1))
            base = parse_datetime_pt("hoje", referencia_iso) or _now_tz()
            dt = base.replace(hour=horas, minute=0, second=0, microsecond=0)

    # procura datas explícitas dd/mm/aaaa
    m_date = re.search(r"\b(\d{1,2})[/-](\d{1,2})[/-](\d{2,4})\b", t)
    if m_date:
        d, m, y = int(m_date.group(1)), int(m_date.group(2)), int(m_date.group(3))
        if y < 100: y += 2000
        try:
            if dt:
                dt = dt.replace(year=y, month=m, day=d)
            else:
                dt = datetime.datetime(y, m, d, tzinfo=zoneinfo.ZoneInfo(TZ))
        except Exception:
            dt = None

    # termos relativos: hoje, ontem, anteontem
    if not dt:
        for palavra in ["anteontem", "ontem", "hoje"]:
            if re.search(rf"\b{palavra}\b", t, re.IGNORECASE):
                dt = parse_datetime_pt(palavra, referencia_iso)
                break

    data_ocorrencia = normalize_dt(dt) if dt else ""

    # === local ===
    local = ""
    # heurística: após "no|na|em|no escritório de" capturar sequência até vírgula/ponto/ "houve"
    m_loc = re.search(r"\b(?:no|na|em)\s+(?:escritório\s+de\s+)?([A-ZÁÉÍÓÚÂÊÔÃÕÇ][^,.;]*?)(?=,|\s+houve|\s+ocorreu|\.|$)", t)
    if m_loc:
        local = m_loc.group(1).strip()
        # limpar sufixos comuns
        local = re.sub(r"\b(da|de|do)\b\s*$", "", local).strip()

    # === tipo_incidente ===
    tipo_incidente = ""
    CANDIDATOS = [
        r"falha no servidor", r"falha (?:geral|total)",
        r"queda de energia", r"pane elétrica", r"intermitência",
        r"incêndio", r"vazamento", r"ataque ddos", r"ataque de ddos",
        r"indisponibilidade", r"erro de aplicação", r"parada programada",
        r"problema de rede", r"congestionamento de rede", r"falha de banco de dados"
    ]
    for pat in CANDIDATOS:
        m = re.search(pat, t, re.IGNORECASE)
        if m:
            tipo_incidente = m.group(0).strip().capitalize()
            break
    if not tipo_incidente:
        # fallback genérico
        if "houve" in t.lower() or "ocorreu" in t.lower():
            tipo_incidente = "Incidente reportado"

    # === impacto ===
    impacto = ""
    # após "que" ou "afetou" capturar até ponto final
    m_imp = re.search(r"\b(?:que\s+)?(?:afetou|impactou|deixou)\s+(.*?)(?:\.\s*|$)", t, re.IGNORECASE)
    if m_imp:
        impacto = m_imp.group(1).strip().capitalize()

    return {
        "data_ocorrencia": data_ocorrencia,
        "local": local,
        "tipo_incidente": tipo_incidente,
        "impacto": impacto
    }

def merge_dicts(primary: Dict[str, str], fallback: Dict[str, str]) -> Dict[str, str]:
    out = {}
    for k in ["data_ocorrencia", "local", "tipo_incidente", "impacto"]:
        v = (primary or {}).get(k, "") if primary else ""
        if not v or not str(v).strip():
            v = fallback.get(k, "")
        out[k] = v or ""
    return out
