"""Minimal HTTP server for integrating the chatbot with storefronts."""

from __future__ import annotations

import argparse
import json
import os
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Callable, Dict, Iterable, Optional
from urllib.parse import urlparse
from uuid import uuid4

from .chatbot import MultilingualCustomerSupportBot


@dataclass
class ChatRequest:
    """Incoming payload for a chat turn."""

    message: str
    session_id: Optional[str] = None


@dataclass
class ChatResponse:
    """Reply payload returned to channel integrations."""

    reply: str
    detected_language: str
    session_id: str


@dataclass
class _SessionState:
    bot: MultilingualCustomerSupportBot
    last_activity: datetime


class ChatbotHTTPApplication:
    """In-memory HTTP API for storefront integrations."""

    def __init__(
        self,
        *,
        bot_factory: Optional[Callable[[], MultilingualCustomerSupportBot]] = None,
        allowed_origins: Optional[Iterable[str]] = None,
        session_ttl_seconds: Optional[int] = None,
        max_sessions: Optional[int] = None,
        api_keys: Optional[Iterable[str]] = None,
    ) -> None:
        self.bot_factory = bot_factory or MultilingualCustomerSupportBot
        self.sessions: Dict[str, _SessionState] = {}

        env_origins = os.getenv("ALLOWED_ORIGINS")
        if allowed_origins is not None:
            self.allowed_origins = list(allowed_origins)
        elif env_origins:
            self.allowed_origins = [
                origin.strip() for origin in env_origins.split(",") if origin.strip()
            ]
        else:
            self.allowed_origins = ["*"]

        ttl_env = os.getenv("SESSION_TTL_SECONDS")
        max_sessions_env = os.getenv("MAX_SESSIONS")

        ttl_value = session_ttl_seconds
        if ttl_value is None and ttl_env:
            ttl_value = int(ttl_env)
        self.session_ttl = timedelta(seconds=ttl_value if ttl_value is not None else 1800)

        max_sessions_value = max_sessions
        if max_sessions_value is None and max_sessions_env:
            max_sessions_value = int(max_sessions_env)
        self.max_sessions = max_sessions_value if max_sessions_value is not None else 1000

        env_keys = os.getenv("CHATBOT_API_KEYS")
        if api_keys is not None:
            self.api_keys = {key.strip() for key in api_keys if key.strip()}
        elif env_keys:
            self.api_keys = {key.strip() for key in env_keys.split(",") if key.strip()}
        else:
            self.api_keys = set()

    def _create_handler(self):
        application = self

        class Handler(BaseHTTPRequestHandler):
            server_version = "MCSChatbotHTTP/0.2"

            def _origin_allowed(self) -> bool:
                origin = self.headers.get("Origin")
                if not origin or "*" in application.allowed_origins:
                    return True
                return origin in application.allowed_origins

            def _cors_headers(self) -> Dict[str, str]:
                origin = self.headers.get("Origin")
                if origin and self._origin_allowed():
                    allow_origin = origin
                elif "*" in application.allowed_origins:
                    allow_origin = "*"
                else:
                    allow_origin = "null"
                return {
                    "Access-Control-Allow-Origin": allow_origin,
                    "Access-Control-Allow-Methods": "GET, POST, DELETE, OPTIONS",
                    "Access-Control-Allow-Headers": "Content-Type, X-API-Key, X-CSRF-Token",
                }

            def _require_api_key(self) -> bool:
                if not application.api_keys:
                    return True
                supplied = self.headers.get("X-API-Key", "").strip()
                return supplied in application.api_keys

            def _send_json(self, payload: Dict, status: HTTPStatus) -> None:
                body = json.dumps(payload).encode("utf-8")
                self.send_response(status)
                for header, value in self._cors_headers().items():
                    self.send_header(header, value)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

            def _parse_json_body(self) -> Dict:
                length = int(self.headers.get("Content-Length", "0"))
                raw_body = self.rfile.read(length) if length else b"{}"
                try:
                    return json.loads(raw_body.decode("utf-8"))
                except json.JSONDecodeError as exc:
                    raise ValueError("Invalid JSON body") from exc

            def do_OPTIONS(self) -> None:  # noqa: N802 (HTTP verb name)
                if not self._origin_allowed():
                    self.send_response(HTTPStatus.FORBIDDEN)
                    self.end_headers()
                    return

                self.send_response(HTTPStatus.NO_CONTENT)
                for header, value in self._cors_headers().items():
                    self.send_header(header, value)
                self.end_headers()

            def do_GET(self) -> None:  # noqa: N802
                parsed = urlparse(self.path)
                if parsed.path == "/health":
                    self._send_json({"status": "ok"}, HTTPStatus.OK)
                else:
                    self._send_json({"error": "Not found"}, HTTPStatus.NOT_FOUND)

            def do_POST(self) -> None:  # noqa: N802
                parsed = urlparse(self.path)
                if parsed.path != "/chat":
                    self._send_json({"error": "Not found"}, HTTPStatus.NOT_FOUND)
                    return

                if not self._origin_allowed():
                    self._send_json({"error": "Origin not allowed"}, HTTPStatus.FORBIDDEN)
                    return

                if not self._require_api_key():
                    self._send_json({"error": "Invalid API key"}, HTTPStatus.UNAUTHORIZED)
                    return

                try:
                    payload = self._parse_json_body()
                    message = payload.get("message", "").strip()
                    if not message:
                        raise ValueError("'message' field is required")
                    session_id = payload.get("session_id") or str(uuid4())
                    chat_request = ChatRequest(message=message, session_id=session_id)
                    chat_response = application.handle_chat(chat_request)
                    self._send_json(asdict(chat_response), HTTPStatus.OK)
                except ValueError as exc:
                    self._send_json({"error": str(exc)}, HTTPStatus.BAD_REQUEST)

            def do_DELETE(self) -> None:  # noqa: N802
                parsed = urlparse(self.path)
                if not parsed.path.startswith("/sessions/"):
                    self._send_json({"error": "Not found"}, HTTPStatus.NOT_FOUND)
                    return

                if not self._origin_allowed():
                    self._send_json({"error": "Origin not allowed"}, HTTPStatus.FORBIDDEN)
                    return

                if not self._require_api_key():
                    self._send_json({"error": "Invalid API key"}, HTTPStatus.UNAUTHORIZED)
                    return

                session_id = parsed.path.split("/", 2)[-1]
                try:
                    payload = application.reset_session(session_id)
                    self._send_json(payload, HTTPStatus.OK)
                except KeyError:
                    self._send_json({"error": "Unknown session"}, HTTPStatus.NOT_FOUND)

        return Handler

    def handle_chat(self, request: ChatRequest) -> ChatResponse:
        session_id = request.session_id or str(uuid4())
        self._prune_sessions()
        state = self.sessions.get(session_id)
        if state is None:
            bot = self.bot_factory()
            state = _SessionState(bot=bot, last_activity=datetime.utcnow())
            self._enforce_session_limit()
            self.sessions[session_id] = state
        else:
            state.last_activity = datetime.utcnow()

        reply = state.bot.reply(request.message)
        detected = (
            state.bot.last_detection.language.name if state.bot.last_detection else "UNKNOWN"
        )
        return ChatResponse(reply=reply, detected_language=detected, session_id=session_id)

    def reset_session(self, session_id: str) -> Dict[str, str]:
        state = self.sessions.pop(session_id)
        state.bot.reset()
        return {"status": "cleared", "session_id": session_id}

    def _prune_sessions(self) -> None:
        now = datetime.utcnow()
        expired = [
            session_id
            for session_id, state in self.sessions.items()
            if now - state.last_activity > self.session_ttl
        ]
        for session_id in expired:
            state = self.sessions.pop(session_id)
            state.bot.reset()

    def _enforce_session_limit(self) -> None:
        if len(self.sessions) < self.max_sessions:
            return
        # Remove the least recently active sessions until we are under the limit.
        for session_id, state in sorted(
            self.sessions.items(), key=lambda item: item[1].last_activity
        ):
            self.sessions.pop(session_id)
            state.bot.reset()
            if len(self.sessions) < self.max_sessions:
                break

    def serve(self, host: str = "0.0.0.0", port: int = 8000) -> None:
        server = self.build_server(host=host, port=port)
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            pass
        finally:
            server.server_close()

    def build_server(self, host: str = "0.0.0.0", port: int = 8000) -> ThreadingHTTPServer:
        """Return a configured HTTP server instance."""

        return ThreadingHTTPServer((host, port), self._create_handler())


def create_app(
    *,
    bot_factory: Optional[Callable[[], MultilingualCustomerSupportBot]] = None,
    allowed_origins: Optional[Iterable[str]] = None,
    session_ttl_seconds: Optional[int] = None,
    max_sessions: Optional[int] = None,
    api_keys: Optional[Iterable[str]] = None,
) -> ChatbotHTTPApplication:
    """Factory used by tests and scripts."""

    return ChatbotHTTPApplication(
        bot_factory=bot_factory,
        allowed_origins=allowed_origins,
        session_ttl_seconds=session_ttl_seconds,
        max_sessions=max_sessions,
        api_keys=api_keys,
    )


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Run a lightweight HTTP API that exposes the Multilingual Customer "
            "Support Chatbot for WordPress, Shopify, or any webhook-capable "
            "platform."
        )
    )
    parser.add_argument("--host", default="0.0.0.0", help="Host interface to bind")
    parser.add_argument("--port", type=int, default=8000, help="Port to bind")
    args = parser.parse_args()

    app = create_app()
    print(f"Starting chatbot server on http://{args.host}:{args.port}")
    app.serve(host=args.host, port=args.port)


if __name__ == "__main__":
    main()


__all__ = ["ChatRequest", "ChatResponse", "ChatbotHTTPApplication", "create_app", "main"]
