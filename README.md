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
2. Install the free [Code Snippets](https://wordpress.org/plugins/code-snippets/)
   plugin (or add the code to a child theme's `functions.php`).
3. Create a new snippet and paste:

   ```php
   function mcs_chatbot_proxy( $message, $session_id = '' ) {
       $endpoint = 'https://your-api.example.com/chat';
       $body = array(
           'message'    => $message,
           'session_id' => $session_id,
       );

       $response = wp_remote_post( $endpoint, array(
           'headers' => array( 'Content-Type' => 'application/json' ),
           'body'    => wp_json_encode( $body ),
       ) );

       if ( is_wp_error( $response ) ) {
           return array( 'error' => $response->get_error_message() );
       }

       return json_decode( wp_remote_retrieve_body( $response ), true );
   }
   ```

4. You can now call `mcs_chatbot_proxy( 'Hola, ¿dónde está mi pedido?' )` from a
   custom block, support form handler, or a Live Chat plugin hook to pipe
   customer inquiries through the AI assistant.

## Shopify Integration

1. Host the HTTP API and note the public base URL (e.g. using Vercel, Render, or
   a private server).
2. Within the Shopify admin, navigate to **Online Store → Themes → Edit code**.
3. Create a new asset `snippets/mcs-chatbot.js` with:

   ```javascript
   async function askMcsChatbot(message, sessionId) {
     const response = await fetch('https://your-api.example.com/chat', {
       method: 'POST',
       headers: { 'Content-Type': 'application/json' },
       body: JSON.stringify({ message, session_id: sessionId }),
     });

     if (!response.ok) {
       throw new Error('Chatbot request failed');
     }

     return await response.json();
   }
   window.askMcsChatbot = askMcsChatbot;
   ```

4. Include the snippet at the end of `theme.liquid`:

   ```liquid
   {% render 'mcs-chatbot.js' %}
   ```

5. Bind the helper to an existing contact form or floating chat widget. Each
   call returns the assistant reply, detected language, and a `session_id` that
   you reuse for follow-up messages to preserve context.

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
```

Tests live under `tests/` and cover language detection, localized responses, and
fallback messaging.

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for
more information.
