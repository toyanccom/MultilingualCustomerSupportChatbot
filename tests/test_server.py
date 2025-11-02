"""Tests for the lightweight HTTP server."""

import json
import threading
import time
from http.client import HTTPConnection

from mcs_chatbot import ChatRequest, ChatbotHTTPApplication, create_app


def start_server(**create_kwargs):
    app = create_app(**create_kwargs)
    server = app.build_server(host="127.0.0.1", port=0)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    server.thread = thread  # type: ignore[attr-defined]
    server.app = app  # type: ignore[attr-defined]
    return server


def stop_server(server):
    server.shutdown()
    server.server_close()


def request_json(
    method: str,
    port: int,
    path: str,
    payload: dict | None = None,
    *,
    headers: dict[str, str] | None = None,
):
    body = json.dumps(payload or {}).encode("utf-8")
    request_headers = {"Content-Type": "application/json"}
    if headers:
        request_headers.update(headers)
    conn = HTTPConnection("127.0.0.1", port, timeout=5)
    conn.request(
        method,
        path,
        body=body if method in {"POST", "DELETE"} else None,
        headers=request_headers,
    )
    response = conn.getresponse()
    data = json.loads(response.read().decode("utf-8"))
    conn.close()
    return response.status, data


def test_chat_endpoint_returns_response():
    server = start_server()
    port = server.server_address[1]

    status, payload = request_json("POST", port, "/chat", {"message": "Hello"})
    assert status == 200
    assert payload["reply"]
    assert payload["session_id"]

    follow_status, follow_payload = request_json(
        "POST",
        port,
        "/chat",
        {"message": "Where is my order?", "session_id": payload["session_id"]},
    )
    assert follow_status == 200
    assert follow_payload["session_id"] == payload["session_id"]

    stop_server(server)


def test_reset_endpoint_clears_session():
    server = start_server()
    port = server.server_address[1]

    _, chat_payload = request_json("POST", port, "/chat", {"message": "Bonjour"})
    status, _ = request_json("DELETE", port, f"/sessions/{chat_payload['session_id']}")
    assert status == 200

    missing_status, missing_payload = request_json(
        "DELETE", port, f"/sessions/{chat_payload['session_id']}"
    )
    assert missing_status == 404
    assert missing_payload["error"] == "Unknown session"

    stop_server(server)


def test_origin_restrictions_block_disallowed_hosts():
    server = start_server(allowed_origins=["https://example.com"])
    port = server.server_address[1]

    status, payload = request_json(
        "POST",
        port,
        "/chat",
        {"message": "Hola"},
        headers={"Origin": "https://malicious.example"},
    )
    assert status == 403
    assert payload["error"] == "Origin not allowed"

    stop_server(server)


def test_api_key_is_required_when_configured():
    server = start_server(api_keys={"secret"}, allowed_origins=["https://example.com"])
    port = server.server_address[1]

    missing_status, missing_payload = request_json(
        "POST",
        port,
        "/chat",
        {"message": "Hola"},
        headers={"Origin": "https://example.com"},
    )
    assert missing_status == 401
    assert missing_payload["error"] == "Invalid API key"

    ok_status, ok_payload = request_json(
        "POST",
        port,
        "/chat",
        {"message": "Hola"},
        headers={"Origin": "https://example.com", "X-API-Key": "secret"},
    )
    assert ok_status == 200
    assert ok_payload["reply"]

    stop_server(server)


def test_sessions_expire_after_ttl():
    app: ChatbotHTTPApplication = create_app(session_ttl_seconds=0)
    first = app.handle_chat(ChatRequest(message="Hello"))
    initial_state = app.sessions[first.session_id]
    time.sleep(0.01)
    second = app.handle_chat(ChatRequest(message="Hi again", session_id=first.session_id))
    renewed_state = app.sessions[second.session_id]
    assert renewed_state.bot is not initial_state.bot
    assert len(renewed_state.bot.history) == 2
