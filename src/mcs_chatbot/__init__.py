"""Multilingual Customer Support Chatbot package."""

from .chatbot import MultilingualCustomerSupportBot
from .language_detection import detect_language, SupportedLanguage
from .knowledge_base import KnowledgeBase

__all__ = [
    "MultilingualCustomerSupportBot",
    "detect_language",
    "KnowledgeBase",
    "SupportedLanguage",
]
