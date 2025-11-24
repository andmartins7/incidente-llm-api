from __future__ import annotations

import re
import unicodedata
from typing import Dict, List, Optional


LOCALITY_DICTIONARY: List[Dict[str, str]] = [
    {"name": "São Paulo", "uf": "SP", "aliases": ["sao paulo", "sp", "sampa"]},
    {"name": "Rio de Janeiro", "uf": "RJ", "aliases": ["rio de janeiro", "rj", "rio"]},
    {"name": "Belo Horizonte", "uf": "MG", "aliases": ["belo horizonte", "bh", "bhz"]},
    {"name": "Brasília", "uf": "DF", "aliases": ["brasilia", "df"]},
    {"name": "Curitiba", "uf": "PR", "aliases": ["curitiba", "ctba"]},
    {"name": "Porto Alegre", "uf": "RS", "aliases": ["porto alegre", "poa"]},
    {"name": "Salvador", "uf": "BA", "aliases": ["salvador", "ssa"]},
    {"name": "Fortaleza", "uf": "CE", "aliases": ["fortaleza"]},
    {"name": "Recife", "uf": "PE", "aliases": ["recife"]},
    {"name": "Manaus", "uf": "AM", "aliases": ["manaus"]},
    {"name": "Campinas", "uf": "SP", "aliases": ["campinas"]},
    {"name": "Florianópolis", "uf": "SC", "aliases": ["florianopolis", "fln"]},
    {"name": "Vitória", "uf": "ES", "aliases": ["vitoria"]},
    {"name": "Goiânia", "uf": "GO", "aliases": ["goiania"]},
    {"name": "Belém", "uf": "PA", "aliases": ["belem"]},
]


def _normalize(text: str) -> str:
    normalized = unicodedata.normalize("NFD", text)
    normalized = "".join(ch for ch in normalized if unicodedata.category(ch) != "Mn")
    return normalized.lower()


def _match_dictionary(texto: str) -> Optional[str]:
    norm = _normalize(texto)
    best_match = None
    for entry in LOCALITY_DICTIONARY:
        for alias in entry["aliases"] + [entry["name"]]:
            alias_norm = _normalize(alias)
            if re.search(rf"\b{re.escape(alias_norm)}\b", norm):
                candidate = f"{entry['name']} ({entry['uf']})"
                if not best_match or len(alias_norm) > len(_normalize(best_match)):
                    best_match = candidate
    return best_match


def _simple_capitalized_entities(texto: str) -> List[str]:
    pattern = re.compile(r"\b(?:[A-ZÁÉÍÓÚÂÊÔÃÕÇ][\wÁÉÍÓÚÂÊÔÃÕÇãõçáéíóúâêôç-]+(?:\s+|$)){1,3}")
    return [m.group(0).strip() for m in pattern.finditer(texto)]


def detect_localidade(texto: str) -> str:
    """
    Detecta localidades usando dicionário estático e um NER leve baseado em padrões
    de palavras capitalizadas. Retorna string vazia se nada for encontrado.
    """
    if not texto:
        return ""

    dic_match = _match_dictionary(texto)
    if dic_match:
        return dic_match

    entities = _simple_capitalized_entities(texto)
    if entities:
        # Prioriza a primeira entidade após preposições comuns.
        for ent in entities:
            if re.search(rf"\b(?:no|na|em)\s+{re.escape(ent)}\b", texto, re.IGNORECASE):
                return ent
        return entities[0]

    return ""

