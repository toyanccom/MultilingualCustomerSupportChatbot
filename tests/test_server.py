"""Tests for the lightweight HTTP server."""

import json
import threading
from http.client import HTTPConnection

from mcs_chatbot import create_app


def start_server():
    app = create_app()
    server = app.build_server(host="127.0.0.1", port=0)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    server.thread = thread  # type: ignore[attr-defined]
    return server


def stop_server(server):
    server.shutdown()
    server.server_close()


def request_json(method: str, port: int, path: str, payload: dict | None = None):
    body = json.dumps(payload or {}).encode("utf-8")
    headers = {"Content-Type": "application/json"}
    conn = HTTPConnection("127.0.0.1", port, timeout=5)
    conn.request(method, path, body=body if method in {"POST", "DELETE"} else None, headers=headers)
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
