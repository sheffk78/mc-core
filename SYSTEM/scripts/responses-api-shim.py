#!/usr/bin/env python3
"""
Responses API → Chat Completions Shim
======================================
Translates OpenAI Responses API requests to Chat Completions format,
forwards to the Ollama Cloud proxy, and translates responses back.

Listens on port 11600, forwards to 127.0.0.1:11500 (Ollama Cloud proxy).

Usage:
    python3 responses-api-shim.py [--port 11600] [--upstream http://127.0.0.1:11500]
"""

import argparse
import json
import logging
import os
import sys
import time
import uuid
import http.client
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
log = logging.getLogger("responses-shim")

UPSTREAM_HOST = "127.0.0.1"
UPSTREAM_PORT = 11500


def _make_id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:24]}"


def responses_to_chat_completions(body: bytes) -> bytes:
    """Convert a Responses API request to a Chat Completions request."""
    req = json.loads(body)

    model = req.get("model", "glm-5.2")
    instructions = req.get("instructions", "")
    input_data = req.get("input", "")
    stream = req.get("stream", False)
    tools = req.get("tools", [])
    tool_choice = req.get("tool_choice")
    temperature = req.get("temperature")
    max_output_tokens = req.get("max_output_tokens")

    # Build messages array
    messages = []

    # System instructions
    if instructions:
        messages.append({"role": "system", "content": instructions})

    # Input can be a string or array of message objects
    if isinstance(input_data, str):
        messages.append({"role": "user", "content": input_data})
    elif isinstance(input_data, list):
        for item in input_data:
            if isinstance(item, dict):
                role = item.get("role", "user")
                content = item.get("content", "")
                # Content can be string or array of content parts
                if isinstance(content, list):
                    text_parts = []
                    for part in content:
                        if isinstance(part, dict):
                            if part.get("type") == "text":
                                text_parts.append(part.get("text", ""))
                            elif part.get("type") == "input_text":
                                text_parts.append(part.get("text", ""))
                            elif part.get("type") == "output_text":
                                text_parts.append(part.get("text", ""))
                    content = "\n".join(text_parts)
                elif isinstance(content, str):
                    pass
                messages.append({"role": role, "content": content})
            elif isinstance(item, str):
                messages.append({"role": "user", "content": item})

    # Convert Responses API tools to Chat Completions tools
    chat_tools = []
    for tool in tools:
        if tool.get("type") == "function":
            chat_tools.append(tool)
        elif tool.get("type") == "web_search":
            # Skip web_search - handled separately
            pass
        elif tool.get("type") == "computer_use":
            # Convert computer_use tool to function tool
            pass
        elif tool.get("type") == "browser_use":
            # Convert browser_use tool
            pass
        else:
            # Pass through function-type tools
            if "function" in tool:
                chat_tools.append(tool)

    chat_req = {
        "model": model,
        "messages": messages,
        "stream": stream,
    }

    if chat_tools:
        chat_req["tools"] = chat_tools
    if tool_choice:
        chat_req["tool_choice"] = tool_choice
    if temperature is not None:
        chat_req["temperature"] = temperature
    if max_output_tokens is not None:
        chat_req["max_tokens"] = max_output_tokens

    return json.dumps(chat_req).encode()


def chat_completion_to_response(cc_body: bytes, model: str) -> bytes:
    """Convert a Chat Completions response to a Responses API response."""
    resp = json.loads(cc_body)
    choice = resp.get("choices", [{}])[0]
    msg = choice.get("message", {})
    content = msg.get("content", "")
    tool_calls = msg.get("tool_calls")

    output = []

    # Text output
    if content:
        output.append({
            "type": "message",
            "id": _make_id("msg"),
            "role": "assistant",
            "status": "completed",
            "content": [{"type": "output_text", "text": content}],
        })

    # Tool calls
    if tool_calls:
        for tc in tool_calls:
            func = tc.get("function", {})
            args = func.get("arguments", "{}")
            if isinstance(args, str):
                try:
                    args_parsed = json.loads(args)
                except json.JSONDecodeError:
                    args_parsed = {"_raw": args}
            else:
                args_parsed = args
            output.append({
                "type": "function_call",
                "id": tc.get("id", _make_id("fc")),
                "call_id": tc.get("id", _make_id("call")),
                "name": func.get("name", ""),
                "arguments": json.dumps(args_parsed),
            })

    response = {
        "id": _make_id("resp"),
        "object": "response",
        "created_at": int(time.time()),
        "model": model,
        "status": "completed",
        "output": output,
        "usage": resp.get("usage", {}),
    }

    return json.dumps(response).encode()


def stream_chat_to_responses(cc_body: bytes, model: str) -> bytes:
    """Convert a streaming chat completion chunk to a Responses API SSE event stream."""
    # For non-streaming, return the full response
    # For streaming, we need to emit SSE events
    # The chat completions response here is non-streaming (we de-stream on our side)
    resp = json.loads(cc_body)
    choice = resp.get("choices", [{}])[0]
    msg = choice.get("message", {})
    content = msg.get("content", "")
    tool_calls = msg.get("tool_calls")

    response_id = _make_id("resp")
    message_id = _make_id("msg")
    events = []

    # response.created
    events.append({
        "type": "response.created",
        "response": {"id": response_id, "object": "response", "status": "in_progress",
                     "model": model, "output": [], "created_at": int(time.time())}
    })

    # response.in_progress
    events.append({
        "type": "response.in_progress",
        "response": {"id": response_id, "object": "response", "status": "in_progress",
                     "model": model, "output": [], "created_at": int(time.time())}
    })

    # output_item.added (message)
    events.append({
        "type": "response.output_item.added",
        "output_index": 0,
        "item": {"type": "message", "id": message_id, "role": "assistant",
                 "status": "in_progress", "content": []}
    })

    # content_part.added
    events.append({
        "type": "response.content_part.added",
        "item_id": message_id,
        "output_index": 0,
        "content_index": 0,
        "part": {"type": "output_text", "text": ""}
    })

    # output_text.delta
    if content:
        events.append({
            "type": "response.output_text.delta",
            "item_id": message_id,
            "output_index": 0,
            "content_index": 0,
            "delta": content
        })

    # output_text.done
    events.append({
        "type": "response.output_text.done",
        "item_id": message_id,
        "output_index": 0,
        "content_index": 0,
        "text": content
    })

    # content_part.done
    events.append({
        "type": "response.content_part.done",
        "item_id": message_id,
        "output_index": 0,
        "content_index": 0,
        "part": {"type": "output_text", "text": content}
    })

    # output_item.done
    events.append({
        "type": "response.output_item.done",
        "output_index": 0,
        "item": {"type": "message", "id": message_id, "role": "assistant",
                 "status": "completed", "content": [{"type": "output_text", "text": content}]}
    })

    # Tool call events
    tool_outputs = []
    if tool_calls:
        for i, tc in enumerate(tool_calls):
            func = tc.get("function", {})
            fc_id = tc.get("id", _make_id("fc"))
            call_id = tc.get("id", _make_id("call"))
            args = func.get("arguments", "{}")
            if isinstance(args, str):
                try:
                    args_parsed = json.loads(args)
                except json.JSONDecodeError:
                    args_parsed = {"_raw": args}
            else:
                args_parsed = args

            fc_item = {
                "type": "function_call",
                "id": fc_id,
                "call_id": call_id,
                "name": func.get("name", ""),
                "arguments": json.dumps(args_parsed),
                "status": "completed"
            }

            events.append({
                "type": "response.output_item.added",
                "output_index": i + 1,
                "item": fc_item
            })
            events.append({
                "type": "response.output_item.done",
                "output_index": i + 1,
                "item": fc_item
            })
            tool_outputs.append(fc_item)

    # response.completed
    all_output = [{"type": "message", "id": message_id, "role": "assistant",
                   "status": "completed", "content": [{"type": "output_text", "text": content}]}]
    all_output.extend(tool_outputs)

    events.append({
        "type": "response.completed",
        "response": {
            "id": response_id,
            "object": "response",
            "status": "completed",
            "model": model,
            "output": all_output,
            "created_at": int(time.time()),
            "usage": resp.get("usage", {})
        }
    })

    # Format as SSE
    sse_lines = []
    for event in events:
        sse_lines.append(f"event: {event['type']}")
        sse_lines.append(f"data: {json.dumps(event)}")
        sse_lines.append("")
    return "\n".join(sse_lines).encode() + b"\n"


class ShimHandler(BaseHTTPRequestHandler):
    def _read_body(self) -> bytes:
        content_length = int(self.headers.get("Content-Length", 0))
        if content_length > 0:
            return self.rfile.read(content_length)
        return b""

    def do_GET(self):
        # Forward GET requests (e.g., /v1/models) to upstream
        conn = http.client.HTTPConnection(UPSTREAM_HOST, UPSTREAM_PORT, timeout=30)
        try:
            conn.request("GET", self.path, headers={
                "Content-Type": "application/json",
                "Authorization": self.headers.get("Authorization", ""),
            })
            resp = conn.getresponse()
            body = resp.read()
            self.send_response(resp.status)
            self.send_header("Content-Type", resp.getheader("Content-Type", "application/json"))
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(body)
        except Exception as e:
            log.error(f"GET proxy error: {e}")
            self.send_response(502)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"error": {"message": str(e)}}).encode())
        finally:
            conn.close()

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
        self.end_headers()

    def do_POST(self):
        body = self._read_body()

        if self.path == "/v1/responses":
            self._handle_responses(body)
        elif self.path == "/v1/chat/completions":
            self._forward_chat(body)
        else:
            # Forward other POST requests to upstream
            self._forward_raw(body)

    def _handle_responses(self, body: bytes):
        """Translate Responses API request to chat completions, forward to upstream."""
        try:
            req = json.loads(body)
        except json.JSONDecodeError:
            self.send_response(400)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"error": {"message": "Invalid JSON"}}).encode())
            return

        model = req.get("model", "glm-5.2")
        stream = req.get("stream", False)
        auth = self.headers.get("Authorization", "")

        # Convert to chat completions format
        try:
            chat_body = responses_to_chat_completions(body)
        except Exception as e:
            log.error(f"Translation error: {e}")
            self.send_response(400)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"error": {"message": f"Translation error: {e}"}}).encode())
            return

        log.info(f"Translated /v1/responses → /v1/chat/completions (model={model}, stream={stream})")

        # Forward to upstream Ollama Cloud proxy
        conn = http.client.HTTPConnection(UPSTREAM_HOST, UPSTREAM_PORT, timeout=120)
        try:
            # Always request non-streaming from upstream for simplicity
            # We'll convert to SSE events ourselves if Codex wants streaming
            chat_req = json.loads(chat_body)
            chat_req["stream"] = False
            chat_body_nonstream = json.dumps(chat_req).encode()

            conn.request("POST", "/v1/chat/completions", body=chat_body_nonstream, headers={
                "Content-Type": "application/json",
                "Authorization": auth,
            })
            resp = conn.getresponse()
            cc_body = resp.read()

            if resp.status != 200:
                log.error(f"Upstream error {resp.status}: {cc_body[:500]}")
                self.send_response(resp.status)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(cc_body)
                return

            # Convert response back to Responses API format
            if stream:
                response_body = stream_chat_to_responses(cc_body, model)
                self.send_response(200)
                self.send_header("Content-Type", "text/event-stream")
                self.send_header("Cache-Control", "no-cache")
                self.send_header("Connection", "keep-alive")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                self.wfile.write(response_body)
            else:
                response_body = chat_completion_to_response(cc_body, model)
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                self.wfile.write(response_body)

        except Exception as e:
            log.error(f"Forwarding error: {e}")
            self.send_response(502)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"error": {"message": str(e)}}).encode())
        finally:
            conn.close()

    def _forward_chat(self, body: bytes):
        """Forward chat completions requests directly to upstream."""
        conn = http.client.HTTPConnection(UPSTREAM_HOST, UPSTREAM_PORT, timeout=120)
        try:
            conn.request("POST", "/v1/chat/completions", body=body, headers={
                "Content-Type": "application/json",
                "Authorization": self.headers.get("Authorization", ""),
            })
            resp = conn.getresponse()
            cc_body = resp.read()
            self.send_response(resp.status)
            self.send_header("Content-Type", resp.getheader("Content-Type", "application/json"))
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(cc_body)
        except Exception as e:
            log.error(f"Chat forward error: {e}")
            self.send_response(502)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"error": {"message": str(e)}}).encode())
        finally:
            conn.close()

    def _forward_raw(self, body: bytes):
        """Forward any other POST request to upstream."""
        conn = http.client.HTTPConnection(UPSTREAM_HOST, UPSTREAM_PORT, timeout=120)
        try:
            conn.request("POST", self.path, body=body, headers={
                "Content-Type": "application/json",
                "Authorization": self.headers.get("Authorization", ""),
            })
            resp = conn.getresponse()
            cc_body = resp.read()
            self.send_response(resp.status)
            self.send_header("Content-Type", resp.getheader("Content-Type", "application/json"))
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(cc_body)
        except Exception as e:
            log.error(f"Raw forward error: {e}")
            self.send_response(502)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"error": {"message": str(e)}}).encode())
        finally:
            conn.close()

    def log_message(self, format, *args):
        log.info(f"{self.client_address[0]} - {format % args}")


def main():
    parser = argparse.ArgumentParser(description="Responses API → Chat Completions Shim")
    parser.add_argument("--port", type=int, default=11600)
    parser.add_argument("--upstream", type=str, default="http://127.0.0.1:11500")
    args = parser.parse_args()

    global UPSTREAM_HOST, UPSTREAM_PORT
    parsed = urlparse(args.upstream)
    UPSTREAM_HOST = parsed.hostname
    UPSTREAM_PORT = parsed.port

    server = ThreadingHTTPServer(("127.0.0.1", args.port), ShimHandler)
    log.info(f"Responses API shim listening on 127.0.0.1:{args.port}")
    log.info(f"Forwarding to {UPSTREAM_HOST}:{UPSTREAM_PORT}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        log.info("Shutting down...")
        server.shutdown()


if __name__ == "__main__":
    main()