"""Domain knowledge for the Multilingual Customer Support Bot."""

from __future__ import annotations

from dataclasses import dataclass
from difflib import SequenceMatcher
from typing import Dict, Iterable, List, Optional
import unicodedata

from .language_detection import SupportedLanguage


@dataclass(frozen=True)
class KnowledgeBaseEntry:
    """Represents a single intent and localized responses."""

    intent_id: str
    utterances: Dict[SupportedLanguage, Iterable[str]]
    responses: Dict[SupportedLanguage, str]

    def match_score(self, language: SupportedLanguage, message: str) -> float:
        """Return a similarity score for ``message`` in ``language``."""

        candidates = self.utterances.get(language, ())
        if not candidates:
            return 0.0

        message_norm = _normalize(message)
        best_ratio = 0.0

        for utterance in candidates:
            ratio = _similarity(message_norm, _normalize(utterance))
            if ratio > best_ratio:
                best_ratio = ratio

        return best_ratio

    def localized_response(self, language: SupportedLanguage) -> Optional[str]:
        """Return the localized response if available."""

        return self.responses.get(language)


class KnowledgeBase:
    """In-memory storage of intents and responses."""

    def __init__(self, entries: Iterable[KnowledgeBaseEntry]):
        self._entries: List[KnowledgeBaseEntry] = list(entries)

    def best_response(self, language: SupportedLanguage, message: str) -> Optional[str]:
        """Return the best matching response for ``message`` in ``language``."""

        best_entry = None
        best_score = 0.0

        for entry in self._entries:
            score = entry.match_score(language, message)
            if score > best_score:
                best_entry = entry
                best_score = score

        if best_entry and best_score >= 0.5:
            response = best_entry.localized_response(language)
            if response:
                return response

            # Fallback to English if the requested language lacks a response.
            return best_entry.localized_response(SupportedLanguage.ENGLISH)
        return None


def default_knowledge_base() -> KnowledgeBase:
    """Return a pre-configured knowledge base covering common scenarios."""

    entries = [
        KnowledgeBaseEntry(
            intent_id="order_status",
            utterances={
                SupportedLanguage.ENGLISH: (
                    "where is my order",
                    "order status",
                    "track my order",
                ),
                SupportedLanguage.SPANISH: (
                    "estado de mi pedido",
                    "donde esta mi pedido",
                    "seguimiento de pedido",
                ),
                SupportedLanguage.MANDARIN: (
                    "我的订单在哪",
                    "订单状态",
                    "跟踪我的订单",
                ),
                SupportedLanguage.FRENCH: (
                    "ou est ma commande",
                    "statut de ma commande",
                    "suivre ma commande",
                ),
                SupportedLanguage.GERMAN: (
                    "wo ist meine bestellung",
                    "bestellstatus",
                    "verfolge meine bestellung",
                ),
                SupportedLanguage.HINDI: (
                    "मेरा ऑर्डर कहाँ है",
                    "ऑर्डर की स्थिति",
                    "मेरा ऑर्डर ट्रैक करें",
                ),
                SupportedLanguage.ARABIC: (
                    "أين طلبي",
                    "حالة الطلب",
                    "تتبع طلبي",
                ),
                SupportedLanguage.BENGALI: (
                    "আমার অর্ডার কোথায়",
                    "অর্ডারের অবস্থা",
                    "আমার অর্ডার ট্র্যাক করুন",
                ),
                SupportedLanguage.PORTUGUESE: (
                    "onde está meu pedido",
                    "status do pedido",
                    "rastrear meu pedido",
                ),
                SupportedLanguage.RUSSIAN: (
                    "где мой заказ",
                    "статус заказа",
                    "отследить мой заказ",
                ),
            },
            responses={
                SupportedLanguage.ENGLISH: (
                    "You can follow your order from the tracking link we sent "
                    "via email. Let me know if you want me to resend it."
                ),
                SupportedLanguage.SPANISH: (
                    "Puedes seguir tu pedido desde el enlace de seguimiento "
                    "que te enviamos por correo electrónico. Avísame si quieres que lo reenvíe."
                ),
                SupportedLanguage.MANDARIN: (
                    "您可以通过我们发送给您的邮件中的追踪链接查看订单。需要我重新发送吗？"
                ),
                SupportedLanguage.FRENCH: (
                    "Vous pouvez suivre votre commande grâce au lien de suivi "
                    "reçu par e-mail. Dites-moi si vous souhaitez que je vous le renvoie."
                ),
                SupportedLanguage.GERMAN: (
                    "Sie können Ihre Bestellung über den Sendungsverfolgungslink "
                    "in unserer E-Mail verfolgen. Soll ich ihn erneut senden?"
                ),
                SupportedLanguage.HINDI: (
                    "आप अपने आदेश को हमारे ईमेल में भेजे गए ट्रैकिंग लिंक से देख सकते हैं। "
                    "क्या आप चाहते हैं कि मैं इसे फिर से भेजूँ?"
                ),
                SupportedLanguage.ARABIC: (
                    "يمكنك متابعة طلبك عبر رابط التتبع الذي أرسلناه إلى بريدك الإلكتروني. "
                    "أخبرني إذا كنت تريد أن أعيد إرساله."
                ),
                SupportedLanguage.BENGALI: (
                    "আপনি আমাদের পাঠানো ইমেইলের ট্র্যাকিং লিংক থেকে আপনার অর্ডার অনুসরণ করতে পারেন। "
                    "আবার পাঠাতে হলে জানাবেন।"
                ),
                SupportedLanguage.PORTUGUESE: (
                    "Você pode acompanhar o pedido pelo link de rastreamento que enviamos por e-mail. "
                    "Quer que eu o envie novamente?"
                ),
                SupportedLanguage.RUSSIAN: (
                    "Вы можете отслеживать заказ по ссылке из письма. Сообщите, если нужно отправить её снова."
                ),
            },
        ),
        KnowledgeBaseEntry(
            intent_id="return_policy",
            utterances={
                SupportedLanguage.ENGLISH: (
                    "what is your return policy",
                    "how do i return",
                    "can i get a refund",
                ),
                SupportedLanguage.SPANISH: (
                    "cual es su politica de devoluciones",
                    "como devuelvo",
                    "puedo obtener un reembolso",
                ),
                SupportedLanguage.MANDARIN: (
                    "你们的退货政策是什么",
                    "我可以退款吗",
                    "如何退货",
                ),
                SupportedLanguage.FRENCH: (
                    "quelle est votre politique de retour",
                    "comment effectuer un retour",
                    "puis je obtenir un remboursement",
                ),
                SupportedLanguage.GERMAN: (
                    "wie ist eure rückgaberegelung",
                    "wie kann ich zurücksenden",
                    "kann ich eine rückerstattung bekommen",
                ),
                SupportedLanguage.HINDI: (
                    "आपकी रिटर्न नीति क्या है",
                    "मैं वापसी कैसे करूं",
                    "क्या मुझे रिफंड मिल सकता है",
                ),
                SupportedLanguage.ARABIC: (
                    "ما هي سياسة الإرجاع",
                    "كيف أعيد المنتج",
                    "هل يمكنني استرجاع المال",
                ),
                SupportedLanguage.BENGALI: (
                    "আপনাদের রিটার্ন নীতি কী",
                    "কীভাবে আমি রিটার্ন করব",
                    "আমি কি রিফান্ড পেতে পারি",
                ),
                SupportedLanguage.PORTUGUESE: (
                    "qual é a política de devolução",
                    "como faço para devolver",
                    "posso receber um reembolso",
                ),
                SupportedLanguage.RUSSIAN: (
                    "какова ваша политика возврата",
                    "как мне вернуть товар",
                    "могу ли я получить возврат средств",
                ),
            },
            responses={
                SupportedLanguage.ENGLISH: (
                    "Returns are accepted within 30 days in original condition. "
                    "I can guide you through the prepaid label process."
                ),
                SupportedLanguage.SPANISH: (
                    "Aceptamos devoluciones dentro de los 30 días y en perfecto "
                    "estado. Puedo ayudarte a generar la etiqueta prepagada."
                ),
                SupportedLanguage.MANDARIN: (
                    "商品自收到之日起30天内可在保持完好情况下退货。我可以协助您生成预付费退货标签。"
                ),
                SupportedLanguage.FRENCH: (
                    "Les retours sont possibles sous 30 jours si l'article est "
                    "comme neuf. Je peux vous aider à générer l'étiquette prépayée."
                ),
                SupportedLanguage.GERMAN: (
                    "Rücksendungen sind innerhalb von 30 Tagen im Originalzustand möglich. "
                    "Ich helfe Ihnen gern beim Erstellen des Rücksendeetiketts."
                ),
                SupportedLanguage.HINDI: (
                    "मूल स्थिति में 30 दिनों के भीतर रिटर्न स्वीकार किए जाते हैं। "
                    "मैं आपको प्रीपेड लेबल प्रक्रिया में मदद कर सकता हूँ।"
                ),
                SupportedLanguage.ARABIC: (
                    "نقبل الإرجاع خلال 30 يوماً مع الحفاظ على حالة المنتج الأصلية. "
                    "يمكنني مساعدتك في الحصول على بطاقة الشحن المسبقة."
                ),
                SupportedLanguage.BENGALI: (
                    "আমরা ৩০ দিনের মধ্যে আসল অবস্থায় রিটার্ন গ্রহণ করি। "
                    "প্রিপেইড লেবেল প্রক্রিয়ায় আমি আপনাকে সাহায্য করতে পারি।"
                ),
                SupportedLanguage.PORTUGUESE: (
                    "Aceitamos devoluções em até 30 dias com o produto em perfeitas condições. "
                    "Posso ajudar a gerar a etiqueta pré-paga."
                ),
                SupportedLanguage.RUSSIAN: (
                    "Возврат возможен в течение 30 дней при сохранении товара в исходном состоянии. "
                    "Я могу помочь оформить предоплаченный ярлык."
                ),
            },
        ),
        KnowledgeBaseEntry(
            intent_id="product_information",
            utterances={
                SupportedLanguage.ENGLISH: (
                    "tell me about this product",
                    "does it have a warranty",
                    "product details",
                ),
                SupportedLanguage.SPANISH: (
                    "cuentame sobre este producto",
                    "tiene garantia",
                    "detalles del producto",
                ),
                SupportedLanguage.MANDARIN: (
                    "告诉我这个产品",
                    "有保修吗",
                    "产品详情",
                ),
                SupportedLanguage.FRENCH: (
                    "parlez moi de ce produit",
                    "a t il une garantie",
                    "details du produit",
                ),
                SupportedLanguage.GERMAN: (
                    "erzähl mir von diesem produkt",
                    "hat es eine garantie",
                    "produktdetails",
                ),
                SupportedLanguage.HINDI: (
                    "मुझे इस उत्पाद के बारे में बताएं",
                    "क्या इसमें वारंटी है",
                    "उत्पाद विवरण",
                ),
                SupportedLanguage.ARABIC: (
                    "أخبرني عن هذا المنتج",
                    "هل لديه ضمان",
                    "معلومات المنتج",
                ),
                SupportedLanguage.BENGALI: (
                    "এই পণ্য সম্পর্কে বলুন",
                    "এতে কি ওয়ারেন্টি আছে",
                    "পণ্যের বিবরণ",
                ),
                SupportedLanguage.PORTUGUESE: (
                    "fale sobre este produto",
                    "ele tem garantia",
                    "detalhes do produto",
                ),
                SupportedLanguage.RUSSIAN: (
                    "расскажите об этом товаре",
                    "есть ли гарантия",
                    "информация о товаре",
                ),
            },
            responses={
                SupportedLanguage.ENGLISH: (
                    "This item includes a one-year warranty and detailed specs "
                    "on the product page. I can send the link if you need it."
                ),
                SupportedLanguage.SPANISH: (
                    "Este artículo incluye una garantía de un año y las "
                    "especificaciones completas en la página del producto. ¿Quieres el enlace?"
                ),
                SupportedLanguage.MANDARIN: (
                    "该商品提供一年保修，详细规格可在产品页面查看。需要链接吗？"
                ),
                SupportedLanguage.FRENCH: (
                    "Cet article est couvert par une garantie d'un an et toutes les "
                    "spécifications sont disponibles sur la page produit. Souhaitez-vous le lien ?"
                ),
                SupportedLanguage.GERMAN: (
                    "Dieser Artikel bietet eine einjährige Garantie. Die kompletten "
                    "Spezifikationen finden Sie auf der Produktseite. Soll ich den Link senden?"
                ),
                SupportedLanguage.HINDI: (
                    "इस आइटम में एक साल की वारंटी शामिल है और विस्तृत विवरण उत्पाद पृष्ठ पर उपलब्ध हैं। "
                    "क्या आपको लिंक चाहिए?"
                ),
                SupportedLanguage.ARABIC: (
                    "يتضمن هذا المنتج ضماناً لمدة عام، وجميع التفاصيل متاحة في صفحة المنتج. "
                    "هل ترغب بالرابط؟"
                ),
                SupportedLanguage.BENGALI: (
                    "এই পণ্যে এক বছরের ওয়ারেন্টি রয়েছে এবং বিস্তারিত তথ্য পণ্য পাতায় আছে। "
                    "লিংকটি কি লাগবে?"
                ),
                SupportedLanguage.PORTUGUESE: (
                    "Este item inclui garantia de um ano e as especificações completas estão na página do produto. "
                    "Quer o link?"
                ),
                SupportedLanguage.RUSSIAN: (
                    "Этот товар имеет годовую гарантию, а подробные характеристики доступны на странице товара. "
                    "Нужна ссылка?"
                ),
            },
        ),
    ]

    return KnowledgeBase(entries)


def _normalize(text: str) -> str:
    text = _strip_accents(text.lower())
    return "".join(ch for ch in text if ch.isalnum() or ch.isspace())


def _similarity(first: str, second: str) -> float:
    if not first or not second:
        return 0.0

    sequence_ratio = SequenceMatcher(None, first, second).ratio()

    first_tokens = set(first.split())
    second_tokens = set(second.split())
    if first_tokens and second_tokens:
        intersection = first_tokens & second_tokens
        union = first_tokens | second_tokens
        token_ratio = len(intersection) / len(union)
    else:
        token_ratio = 0.0

    return max(sequence_ratio, token_ratio)


def _strip_accents(text: str) -> str:
    normalized = unicodedata.normalize("NFD", text)
    return "".join(char for char in normalized if unicodedata.category(char) != "Mn")
