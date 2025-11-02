"""Core logic for the Multilingual Customer Support Bot."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional

from .knowledge_base import KnowledgeBase, default_knowledge_base
from .language_detection import DetectionResult, SupportedLanguage, detect_language


@dataclass
class Message:
    """Represents a single message in the conversation."""

    sender: str
    text: str
    timestamp: datetime = field(default_factory=datetime.utcnow)


class MultilingualCustomerSupportBot:
    """Lightweight, dependency-free customer support chatbot."""

    def __init__(self, knowledge_base: Optional[KnowledgeBase] = None):
        self.knowledge_base = knowledge_base or default_knowledge_base()
        self.history: List[Message] = []
        self.last_detection: Optional[DetectionResult] = None

    def reply(self, message: str) -> str:
        """Return a localized reply to ``message``."""

        detection: DetectionResult = detect_language(message)
        self.last_detection = detection
        self.history.append(Message(sender="customer", text=message))

        response = self.knowledge_base.best_response(detection.language, message)

        if response is None:
            response = self._fallback_response(detection.language)

        self.history.append(Message(sender="assistant", text=response))
        return response

    def _fallback_response(self, language: SupportedLanguage) -> str:
        """Provide a localized fallback when no answer is found."""

        fallbacks = {
            SupportedLanguage.ENGLISH: (
                "I'm sorry, I didn't quite catch that. Could you share more details about "
                "your question so I can help you faster?"
            ),
            SupportedLanguage.SPANISH: (
                "Lo siento, no entendí completamente. ¿Podrías darme más detalles "
                "para ayudarte mejor?"
            ),
            SupportedLanguage.MANDARIN: (
                "抱歉，我没有完全理解。请提供更多细节，我会尽快协助您。"
            ),
            SupportedLanguage.FRENCH: (
                "Je suis désolé, je n'ai pas bien compris. Pourriez-vous m'en dire plus "
                "afin que je puisse vous aider ?"
            ),
            SupportedLanguage.GERMAN: (
                "Entschuldigung, das habe ich nicht ganz verstanden. Können Sie mir "
                "weitere Details geben, damit ich Ihnen helfen kann?"
            ),
            SupportedLanguage.HINDI: (
                "माफ़ कीजिए, मैं पूरी तरह समझ नहीं पाया। कृपया थोड़ा और बताएँ "
                "ताकि मैं जल्दी मदद कर सकूँ।"
            ),
            SupportedLanguage.ARABIC: (
                "عذراً، لم أفهم ذلك تماماً. هل يمكنك تزويدي بمزيد من التفاصيل "
                "لكي أساعدك بشكل أسرع؟"
            ),
            SupportedLanguage.BENGALI: (
                "দুঃখিত, আমি পুরোপুরি বুঝতে পারিনি। অনুগ্রহ করে আরও কিছু বলুন "
                "যাতে আমি দ্রুত সাহায্য করতে পারি।"
            ),
            SupportedLanguage.PORTUGUESE: (
                "Desculpe, não entendi muito bem. Pode compartilhar mais detalhes "
                "para que eu ajude você mais rápido?"
            ),
            SupportedLanguage.RUSSIAN: (
                "Извините, я не до конца понял. Поделитесь, пожалуйста, подробностями, "
                "чтобы я смог помочь быстрее."
            ),
        }

        return fallbacks.get(language, fallbacks[SupportedLanguage.ENGLISH])

    def conversation_summary(self) -> str:
        """Return a text summary of the conversation history."""

        if not self.history:
            return "No conversation yet."

        lines = []
        for entry in self.history:
            timestamp = entry.timestamp.strftime("%Y-%m-%d %H:%M:%S")
            lines.append(f"[{timestamp}] {entry.sender.capitalize()}: {entry.text}")
        return "\n".join(lines)

    def reset(self) -> None:
        """Clear the conversation history."""

        self.history.clear()
