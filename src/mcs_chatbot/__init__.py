"""Multilingual Customer Support Chatbot package."""

from .chatbot import MultilingualCustomerSupportBot
from .language_detection import detect_language, SupportedLanguage
from .knowledge_base import KnowledgeBase
from .server import ChatRequest, ChatResponse, ChatbotHTTPApplication, create_app

__all__ = [
    "MultilingualCustomerSupportBot",
    "detect_language",
    "KnowledgeBase",
    "SupportedLanguage",
    "ChatRequest",
    "ChatResponse",
    "ChatbotHTTPApplication",
    "create_app",
]
