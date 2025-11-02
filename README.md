# Multilingual Customer Support Chatbot

An offline-friendly prototype of a multilingual customer service assistant. The
bot detects the customer's language, retrieves responses from a localized
knowledge base, and provides 24/7 style support without relying on external
APIs.

## Features

- ✅ Supports English, Spanish, Mandarin, French, and German out of the box.
- ✅ Keyword-based language detection to avoid heavyweight dependencies.
- ✅ Localized answers for common e-commerce scenarios such as order tracking,
  return policies, and product information.
- ✅ CLI demo (`python -m src.main`) that simulates a short conversation and
  prints a transcript at the end.
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
    knowledge_base.py
    language_detection.py
  main.py
```

Tests live under `tests/` and cover language detection, localized responses, and
fallback messaging.

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for
more information.
