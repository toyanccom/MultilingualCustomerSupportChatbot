"""Utilities for detecting supported languages."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Callable, Dict, Iterable
import unicodedata


class SupportedLanguage(str, Enum):
    """Enumeration of languages supported by the chatbot."""

    UNKNOWN = "und"
    ENGLISH = "en"
    SPANISH = "es"
    MANDARIN = "zh"
    FRENCH = "fr"
    GERMAN = "de"
    HINDI = "hi"
    ARABIC = "ar"
    BENGALI = "bn"
    PORTUGUESE = "pt"
    RUSSIAN = "ru"


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
    SupportedLanguage.HINDI: (
        "नमस्ते",
        "मदद",
        "ऑर्डर",
        "उत्पाद",
        "रिफंड",
        "शिपिंग",
        "कहाँ",
        "नीति",
        "वापसी",
    ),
    SupportedLanguage.ARABIC: (
        "مرحبا",
        "مساعدة",
        "طلب",
        "منتج",
        "استرداد",
        "شحن",
        "أين",
        "سياسة",
        "إرجاع",
    ),
    SupportedLanguage.BENGALI: (
        "হ্যালো",
        "সাহায্য",
        "অর্ডার",
        "পণ্য",
        "রিফান্ড",
        "শিপিং",
        "কোথায়",
        "নীতি",
        "ফেরত",
    ),
    SupportedLanguage.PORTUGUESE: (
        "ola",
        "ajuda",
        "pedido",
        "produto",
        "reembolso",
        "envio",
        "onde",
        "politica",
        "devolucao",
    ),
    SupportedLanguage.RUSSIAN: (
        "привет",
        "помощь",
        "заказ",
        "товар",
        "возврат",
        "доставка",
        "где",
        "политика",
        "возврата",
    ),
}


_STOPWORDS: Dict[SupportedLanguage, Iterable[str]] = {
    SupportedLanguage.ENGLISH: (
        "the",
        "and",
        "you",
        "your",
        "please",
        "where",
        "what",
        "is",
    ),
    SupportedLanguage.SPANISH: (
        "el",
        "la",
        "de",
        "y",
        "por",
        "donde",
        "cual",
        "mi",
    ),
    SupportedLanguage.MANDARIN: (
        "请问",
        "我的",
        "在哪里",
        "订单",
        "状态",
        "如何",
    ),
    SupportedLanguage.FRENCH: (
        "le",
        "la",
        "ou",
        "de",
        "est",
        "ma",
    ),
    SupportedLanguage.GERMAN: (
        "der",
        "die",
        "und",
        "wo",
        "mein",
        "bestellung",
    ),
    SupportedLanguage.HINDI: (
        "क्या",
        "कहाँ",
        "मेरा",
        "आप",
        "कृपया",
        "स्थिति",
    ),
    SupportedLanguage.ARABIC: (
        "ما",
        "أين",
        "طلب",
        "من",
        "يمكن",
        "رجاء",
    ),
    SupportedLanguage.BENGALI: (
        "কি",
        "কোথায়",
        "আমার",
        "আপনি",
        "ফেরত",
        "অর্ডার",
    ),
    SupportedLanguage.PORTUGUESE: (
        "onde",
        "meu",
        "pedido",
        "qual",
        "por",
        "favor",
    ),
    SupportedLanguage.RUSSIAN: (
        "мой",
        "заказ",
        "где",
        "что",
        "пожалуйста",
        "статус",
    ),
}

_EMPTY_STOPWORDS: frozenset[str] = frozenset()
_STOPWORD_SETS: Dict[SupportedLanguage, frozenset[str]] = {
    language: frozenset(words) for language, words in _STOPWORDS.items()
}


def detect_language(message: str) -> DetectionResult:
    """Detect the language of ``message`` based on keyword occurrence.

    The heuristic is intentionally simple but highly deterministic, making it
    suitable for environments where we want to avoid heavyweight dependencies.
    The function scans the incoming text for known keywords in each supported
    language and returns the language with the highest hit count.
    """

    normalized = _strip_accents(message.lower())
    tokens = list(_tokenize(normalized))
    best_language = SupportedLanguage.UNKNOWN
    best_score = 0.0
    best_script_bonus = 0

    for language, keywords in _KEYWORD_DICTIONARY.items():
        keyword_score = sum(normalized.count(keyword) for keyword in keywords)
        stopword_set = _STOPWORD_SETS.get(language, _EMPTY_STOPWORDS)
        stopword_score = sum(1 for token in tokens if token in stopword_set)

        script_detector = _SCRIPT_DETECTORS.get(language)
        script_bonus = 0
        if script_detector and script_detector(message):
            script_bonus = 2

        score = keyword_score + stopword_score + script_bonus

        if score > best_score:
            best_language = language
            best_score = score
            best_script_bonus = script_bonus

    if best_language is SupportedLanguage.UNKNOWN or best_score == 0:
        return DetectionResult(language=SupportedLanguage.UNKNOWN, confidence=0.0)

    max_tokens = max(len(tokens), 3)
    confidence = min(1.0, best_score / max_tokens)
    if confidence < 0.6 and best_script_bonus:
        confidence = 0.6
    return DetectionResult(language=best_language, confidence=confidence)


def _contains_han_characters(text: str) -> bool:
    """Return ``True`` if *text* includes CJK Unified Ideographs."""

    for char in text:
        if "\u4e00" <= char <= "\u9fff":
            return True
    return False


def _contains_characters_in_range(text: str, start: str, end: str) -> bool:
    """Return ``True`` if *text* includes characters between ``start`` and ``end``."""

    for char in text:
        if start <= char <= end:
            return True
    return False


def _strip_accents(text: str) -> str:
    """Remove diacritics from ``text`` for easier keyword comparison."""

    normalized = unicodedata.normalize("NFD", text)
    return "".join(char for char in normalized if unicodedata.category(char) != "Mn")


def _tokenize(text: str) -> Iterable[str]:
    token = []
    for char in text:
        if char.isalpha():
            token.append(char)
        elif token:
            yield "".join(token)
            token = []
    if token:
        yield "".join(token)


_SCRIPT_DETECTORS: Dict[SupportedLanguage, Callable[[str], bool]] = {
    SupportedLanguage.MANDARIN: lambda text: _contains_han_characters(text),
    SupportedLanguage.HINDI: lambda text: _contains_characters_in_range(text, "\u0900", "\u097F"),
    SupportedLanguage.ARABIC: lambda text: _contains_characters_in_range(text, "\u0600", "\u06FF"),
    SupportedLanguage.BENGALI: lambda text: _contains_characters_in_range(text, "\u0980", "\u09FF"),
    SupportedLanguage.RUSSIAN: lambda text: _contains_characters_in_range(text, "\u0400", "\u04FF"),
}
