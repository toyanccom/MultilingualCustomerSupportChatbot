# Chatbot Critique

This document highlights key weaknesses in the current Multilingual Customer Support Chatbot implementation.

## Language detection accuracy

- Detection relies on counting a handful of static keywords per language, which means a single borrowed English term can outweigh the actual language used and force the bot to answer in the wrong locale.【F:src/mcs_chatbot/language_detection.py†L34-L166】
- When no keywords are matched, the detector still defaults to English with a non-zero confidence of 0.2, so the bot rarely admits uncertainty and keeps replying in English even for unsupported inputs.【F:src/mcs_chatbot/language_detection.py†L150-L166】

## Intent matching and knowledge base coverage

- Message matching is a Jaccard comparison over whitespace-delimited tokens, so any language that does not use spaces (e.g., Mandarin) effectively compares whole strings and will miss even minor variations.【F:src/mcs_chatbot/knowledge_base.py†L20-L35】【F:src/mcs_chatbot/knowledge_base.py†L360-L377】
- Responses only trigger when the best similarity score crosses 0.6, which many inflected forms or typos in supported languages fail to hit, causing frequent fallback messages despite relevant training data.【F:src/mcs_chatbot/knowledge_base.py†L49-L68】

## HTTP bridge robustness

- Sessions live in an in-memory dictionary with no expiry or maximum size, so a production deployment can leak memory or mix conversations across processes when scaled out.【F:src/mcs_chatbot/server.py†L35-L156】
- The server emits permissive CORS headers and even substitutes the first allowed origin for disallowed callers, which can unintentionally expose the API to origins that were not explicitly whitelisted.【F:src/mcs_chatbot/server.py†L63-L75】
- There is no authentication, rate limiting, or abuse protection, making the `/chat` endpoint vulnerable to automated spam or enumeration attacks.【F:src/mcs_chatbot/server.py†L101-L152】

## WordPress widget limitations

- The front-end blindly trusts a global `MCSChatbot` object supplied through localization, so a misconfigured page fails silently with no diagnostic messaging or progressive enhancement.【F:integrations/wordpress/assets/widget.js†L30-L114】
- Requests post directly to the configured endpoint without nonce protection or origin checks, leaving the widget exposed to cross-site request forgery if the chatbot server performs privileged actions beyond chat replies.【F:integrations/wordpress/assets/widget.js†L62-L102】

## Shopify snippet gaps

- Accessibility strings are hard-coded to English both in the snippet markup and the JavaScript defaults, so stores cannot localize the widget without editing theme code.【F:integrations/shopify/snippets/mcs-chatbot-widget.liquid†L17-L43】【F:integrations/shopify/assets/mcs-chatbot.js†L13-L104】
- The script looks for a `.visually-hidden` label span, but the snippet renders that class only once and never updates the visible heading, so language overrides from `window.MCSChatbotConfig` do not reach assistive technologies when multiple widgets are present.【F:integrations/shopify/assets/mcs-chatbot.js†L44-L70】
