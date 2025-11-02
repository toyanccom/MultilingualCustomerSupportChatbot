# Multilingual Customer Support Chatbot

An offline-friendly prototype of a multilingual customer service assistant. The
bot detects the customer's language, retrieves responses from a localized
knowledge base, and provides 24/7 style support without relying on external
APIs.

## Features

- ✅ Supports ten widely used languages (English, Spanish, Mandarin, French,
  German, Hindi, Arabic, Bengali, Portuguese, and Russian) out of the box.
- ✅ Keyword-based language detection to avoid heavyweight dependencies.
- ✅ Localized answers for common e-commerce scenarios such as order tracking,
  return policies, and product information.
- ✅ CLI demo (`python -m src.main`) that simulates a short conversation and
  prints a transcript at the end.
- ✅ Zero-dependency HTTP bridge (`python -m src.mcs_chatbot.server`) for
  drop-in integration with storefront platforms such as WordPress and Shopify.
- ✅ Ready-to-use WordPress plugin and Shopify snippet assets under
  `integrations/` so you can embed the widget without writing glue code.
- ✅ Easily extendable knowledge base stored as Python data structures.

## Getting Started

1. Ensure you have Python 3.9 or above installed.
2. (Optional) Create and activate a virtual environment.
3. Install development requirements:

   ```bash
   pip install -r requirements-dev.txt
   ```

   This repository does not require third-party runtime dependencies.

4. Run the automated tests:

   ```bash
   pytest
   ```

5. Start a sample conversation:

   ```bash
   python -m src.main --turns 3
   ```

6. Expose the chatbot over HTTP for web platforms:

   ```bash
   python -m src.mcs_chatbot.server --host 0.0.0.0 --port 8000
   ```

   This starts an HTTP service that provides `/chat`, `/sessions/{id}`, and
   `/health` endpoints used by the integration snippets below. By default the
   server allows cross-origin requests from any domain; set the
   `ALLOWED_ORIGINS` environment variable (comma separated) to restrict this in
   production deployments.

## WordPress Integration

1. Deploy the HTTP service somewhere accessible to your WordPress instance.
2. Copy the `integrations/wordpress` directory into
   `wp-content/plugins/multilingual-cs-chatbot/` on your site and activate the
   **Multilingual CS Chatbot Widget** plugin.
3. In **Settings → Multilingual CS Chatbot**, paste the base URL where the HTTP
   bridge is running (for example `https://support.example.com`). The plugin
   automatically calls `/chat` and `/sessions/{id}` under that base URL.
4. Add the shortcode `[mcs_chatbot]` anywhere you want the chatbox to appear:

   ```wordpress
   [mcs_chatbot]
   ```

   The plugin ships with a minimal UI, handles session persistence, and exposes
   a reset button that clears the server-side conversation.

## Shopify Integration

1. Host the HTTP API and note the public base URL (e.g. using Vercel, Render, or
   a private server).
2. Upload the files in `integrations/shopify/assets` to your theme assets.
3. Add the provided `integrations/shopify/snippets/mcs-chatbot-widget.liquid`
   snippet to your theme and render it where you want the assistant to live
   (e.g. within `sections/footer.liquid`).
4. In `config/settings_schema.json` add a new text field setting with the ID
   `mcs_chatbot_endpoint` so editors can paste the API base URL (without trailing
   slash). The snippet automatically derives `/chat` and `/sessions/{id}`.
5. Render the snippet and the widget script:

   ```liquid
   {% render 'mcs-chatbot-widget' %}
   ```

   The bundled JavaScript manages session IDs, streams responses into the chat
   history, and exposes a clear button that calls the reset endpoint.

## Extending the Bot

- Add new intents by appending `KnowledgeBaseEntry` instances to
  `default_knowledge_base` in `src/mcs_chatbot/knowledge_base.py`.
- To support additional languages, extend `SupportedLanguage`, update the
  keyword dictionary in `src/mcs_chatbot/language_detection.py`, and provide new
  localized utterances and responses.
- Integrate with existing systems by importing
  `MultilingualCustomerSupportBot` from the package and calling `reply()` with
  customer messages.

## Project Structure

```
src/
  mcs_chatbot/
    __init__.py
    chatbot.py
    server.py
    knowledge_base.py
    language_detection.py
  main.py
integrations/
  wordpress/
    mcs-chatbot.php
    assets/
  shopify/
    assets/
    snippets/
```

Tests live under `tests/` and cover language detection, localized responses, and
fallback messaging.

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for
more information.
