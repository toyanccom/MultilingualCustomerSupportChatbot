# Chatbot Critique

This document highlights key weaknesses in the current Multilingual Customer Support Chatbot implementation.

## Language detection accuracy

- Although the detector now balances keyword hits, stopword matches, and script cues, the stopword lists remain short and handcrafted. Code-switching phrases with only one or two language-specific terms can still be misclassified because the heuristic weights every hit equally and ignores context or token order.【F:src/mcs_chatbot/language_detection.py†L28-L173】
- Inputs that mix supported and unsupported languages return the dominant supported locale with a seemingly precise confidence score. There is no calibration step, so downstream consumers might over-trust low-information confidences (e.g., a single keyword produces ≥0.6 confidence when a script bonus applies).【F:src/mcs_chatbot/language_detection.py†L128-L167】

## Intent matching and knowledge base coverage

- Sequence-based similarity improves Mandarin handling, but the knowledge base still stores only a handful of hard-coded utterances per intent. Rare synonyms or spelling variants frequently fall below the 0.5 similarity threshold, forcing the fallback despite broadly correct questions.【F:src/mcs_chatbot/knowledge_base.py†L22-L125】【F:src/mcs_chatbot/knowledge_base.py†L51-L86】
- The system strips punctuation and accents before comparison, which can merge otherwise distinct utterances (e.g., product codes with dashes or accents) and return an unrelated answer when two intents share similar tokens.【F:src/mcs_chatbot/knowledge_base.py†L330-L377】

## HTTP bridge robustness

- Sessions now expire and honor a global cap, but they still live purely in memory. A multi-process deployment or pod restart loses every active conversation and cannot share load-balanced traffic without sticky sessions.【F:src/mcs_chatbot/server.py†L38-L210】
- API key checks rely on static secrets passed to the browser. Because the key is embedded in page markup or localized JavaScript, a determined user can extract it and script direct calls, so it should be considered an advisory rather than hard security.【F:src/mcs_chatbot/server.py†L70-L158】【F:integrations/wordpress/mcs-chatbot.php†L104-L152】
- Origin validation returns `403` but still responds with JSON payloads for disallowed callers, which may help attackers enumerate valid endpoints even though the body is generic. Consider dropping CORS headers entirely or responding with an empty body on rejection.【F:src/mcs_chatbot/server.py†L86-L152】

## WordPress widget limitations

- The widget now surfaces configuration issues, yet it permanently disables the form after the first network error. A transient outage blocks further attempts until the page reloads, which can degrade support availability on flaky connections.【F:integrations/wordpress/assets/widget.js†L25-L124】
- API keys entered in the admin UI are rendered into the front-end script as plain text. Without server-side correlation or nonce rotation, any visitor viewing source can extract the key and replay requests outside WordPress.【F:integrations/wordpress/mcs-chatbot.php†L41-L117】【F:integrations/wordpress/assets/widget.js†L13-L129】

## Shopify snippet gaps

- Theme translations feed the widget text, but the snippet still injects an inline `window.MCSChatbotConfig` definition on every render. Stores that place multiple widgets on one page risk overwriting runtime overrides from other sections or apps because the global object is shared.【F:integrations/shopify/snippets/mcs-chatbot-widget.liquid†L1-L52】【F:integrations/shopify/assets/mcs-chatbot.js†L8-L111】
- The JavaScript keeps a single session identifier per widget, yet it never cleans up expired sessions client-side if the API evicts them. Customers who leave the page open for a long time will see silent resets without messaging once the server TTL elapses.【F:integrations/shopify/assets/mcs-chatbot.js†L79-L139】【F:src/mcs_chatbot/server.py†L140-L195】
