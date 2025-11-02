"""Utilities for detecting supported languages."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Dict, Iterable
import unicodedata


class SupportedLanguage(str, Enum):
    """Enumeration of languages supported by the chatbot."""

    ENGLISH = "en"
    SPANISH = "es"
    MANDARIN = "zh"
    FRENCH = "fr"
    GERMAN = "de"


@dataclass(frozen=True)
class DetectionResult:
    """Outcome from the language detector."""

    language: SupportedLanguage
    confidence: float


_KEYWORD_DICTIONARY: Dict[SupportedLanguage, Iterable[str]] = {
    SupportedLanguage.ENGLISH: (
        "hello",
        "help",
        "order",
        "product",
        "refund",
        "shipping",
        "where",
    ),
    SupportedLanguage.SPANISH: (
        "hola",
        "ayuda",
        "pedido",
        "producto",
        "reembolso",
        "envio",
        "donde",
        "politica",
        "devolucion",
        "devoluciones",
        "pregunta",
    ),
    SupportedLanguage.MANDARIN: (
        "你好",  # hello
        "帮助",  # help
        "订单",  # order
        "产品",  # product
        "退款",  # refund
        "配送",  # shipping
    ),
    SupportedLanguage.FRENCH: (
        "bonjour",
        "aide",
        "commande",
        "produit",
        "remboursement",
        "livraison",
        "ou",
    ),
    SupportedLanguage.GERMAN: (
        "hallo",
        "hilfe",
        "bestellung",
        "produkt",
        "ruckerstattung",
        "versand",
        "wo",
    ),
}


def detect_language(message: str) -> DetectionResult:
    """Detect the language of ``message`` based on keyword occurrence.

    The heuristic is intentionally simple but highly deterministic, making it
    suitable for environments where we want to avoid heavyweight dependencies.
    The function scans the incoming text for known keywords in each supported
    language and returns the language with the highest hit count.
    """

    normalized = _strip_accents(message.lower())
    best_language = SupportedLanguage.ENGLISH
    best_score = 0

    for language, keywords in _KEYWORD_DICTIONARY.items():
        score = sum(normalized.count(keyword) for keyword in keywords)

        # Mandarin queries may consist solely of Han characters, so we boost the
        # score if the message contains any character in that range.
        if language is SupportedLanguage.MANDARIN and _contains_han_characters(message):
            score += 1

        if score > best_score:
            best_language = language
            best_score = score

    confidence = 1.0 if best_score else 0.2
    return DetectionResult(language=best_language, confidence=confidence)


def _contains_han_characters(text: str) -> bool:
    """Return ``True`` if *text* includes CJK Unified Ideographs."""

    for char in text:
        if "\u4e00" <= char <= "\u9fff":
            return True
    return False


def _strip_accents(text: str) -> str:
    """Remove diacritics from ``text`` for easier keyword comparison."""

    normalized = unicodedata.normalize("NFD", text)
    return "".join(char for char in normalized if unicodedata.category(char) != "Mn")
