"""Command-line interface for the Multilingual Customer Support Bot."""

from __future__ import annotations

import argparse

from mcs_chatbot import MultilingualCustomerSupportBot


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Chat with the Multilingual Customer Support Assistant. "
            "Enter customer questions in English, Spanish, Mandarin, French, "
            "or German and receive localized replies."
        )
    )
    parser.add_argument(
        "--turns",
        type=int,
        default=5,
        help="Number of conversational turns to simulate before exiting.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    bot = MultilingualCustomerSupportBot()

    print("Multilingual Customer Support Assistant")
    print("Type 'exit' to leave the conversation.\n")

    turns = 0
    while turns < args.turns:
        user_message = input("You: ")
        if user_message.strip().lower() in {"exit", "quit"}:
            break

        response = bot.reply(user_message)
        print(f"Bot: {response}\n")
        turns += 1

    print("Conversation summary:")
    print(bot.conversation_summary())


if __name__ == "__main__":
    main()
