"""Tests for the Multilingual Customer Support Bot."""

from mcs_chatbot import MultilingualCustomerSupportBot, SupportedLanguage, detect_language


def test_language_detection_spanish():
    detection = detect_language("Hola, necesito ayuda con mi pedido")
    assert detection.language is SupportedLanguage.SPANISH
    assert detection.confidence >= 0.6


def test_language_detection_mandarin():
    detection = detect_language("我的订单在哪里？")
    assert detection.language is SupportedLanguage.MANDARIN
    assert detection.confidence >= 0.6


def test_language_detection_portuguese():
    detection = detect_language("Olá, preciso de ajuda com meu pedido")
    assert detection.language is SupportedLanguage.PORTUGUESE
    assert detection.confidence >= 0.6


def test_language_detection_unknown():
    detection = detect_language("Sveiki, tai nėra palaikoma kalba")
    assert detection.language is SupportedLanguage.UNKNOWN
    assert detection.confidence == 0


def test_returns_localized_responses():
    bot = MultilingualCustomerSupportBot()
    response = bot.reply("¿Cuál es su política de devoluciones?")
    assert "devoluciones" in response.lower()
    assert bot.last_detection is not None
    assert bot.last_detection.language is SupportedLanguage.SPANISH


def test_returns_localized_responses_portuguese():
    bot = MultilingualCustomerSupportBot()
    response = bot.reply("Qual é a política de devolução?")
    assert "devolu" in response.lower()


def test_fallback_response_for_unknown_question():
    bot = MultilingualCustomerSupportBot()
    response = bot.reply("Esto es una pregunta desconocida")
    assert "lo siento" in response.lower()
    assert len(bot.history) == 2


def test_fallback_response_for_unknown_question_hindi():
    bot = MultilingualCustomerSupportBot()
    response = bot.reply("यह एक अज्ञात प्रश्न है")
    assert "माफ़" in response
    assert len(bot.history) == 2


def test_unknown_language_fallback_message_mentions_recognition_issue():
    bot = MultilingualCustomerSupportBot()
    response = bot.reply("Sveiki, kur yra mano užsakymas?")
    assert "recognise" in response.lower()
    assert bot.last_detection is not None
    assert bot.last_detection.language is SupportedLanguage.UNKNOWN


def test_mandarin_similarity_handles_variations():
    bot = MultilingualCustomerSupportBot()
    response = bot.reply("订单状态如何更新？")
    assert "订单" in response
