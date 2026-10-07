#!/usr/bin/env python3
"""Act as an IDE for Claude Code, backed by SilverBullet's editor.

Writes ~/.claude/ide/PORT.lock and accepts Claude Code's WebSocket connection
(MCP over JSON-RPC). SilverBullet reports the current page and selection, and
receives files Claude Code asks to open:

    POST /ide/state     JSON body {"page", "text", "start": [line, char], "end": [line, char]}
    GET  /ide/events    text/event-stream; each event's data is JSON with a "type":
                        open {"page", "startText"}, diff {"id", "page", "tab", "old", "new"}, closeDiff {"id"}
    POST /ide/diff      JSON body {"id", "accepted"}, the answer to a diff event
    POST /shutdown      stops the server and removes the lock file

Claude Code finds the server when started with CLAUDE_CODE_SSE_PORT=PORT and
ENABLE_IDE_INTEGRATION=true, or through /ide.

Listens on 127.0.0.1 only. Meant to sit behind SilverBullet's /.proxy, which
supplies authentication. HTTP requests also need the bridge's bearer token from
.bridge-token in --cwd; Claude Code's WebSocket uses the lock file's token.
"""

import argparse
import atexit
import base64
import hashlib
import hmac
import json
import os
import queue
import secrets
import signal
import struct
import sys
import threading
import time
from http.server import ThreadingHTTPServer

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "Terminal"))
from bridge import BridgeHandler, load_token

WEBSOCKET_GUID = "258EAFA5-E914-47DA-95CA-C5AB0DC85B11"


def schema(*required, **properties):
    return {"type": "object", "properties": properties, "required": list(required)}


FILE_PATH = {"type": "string", "description": "Absolute path of the file"}

TOOLS = [
    {"name": "getCurrentSelection", "description": "Get the current text selection in the editor", "inputSchema": schema()},
    {"name": "getLatestSelection", "description": "Get the most recent text selection", "inputSchema": schema()},
    {"name": "getOpenEditors", "description": "Get list of currently open files", "inputSchema": schema()},
    {"name": "getWorkspaceFolders", "description": "Get all workspace folders currently open in the IDE", "inputSchema": schema()},
    {"name": "openFile", "description": "Open a file in the editor, optionally positioned at some text", "inputSchema": schema(
        "filePath",
        filePath=FILE_PATH,
        startText={"type": "string", "description": "Text to position the editor at"},
    )},
    {"name": "openDiff", "description": "Show a diff of proposed changes and wait for the user to accept or reject it", "inputSchema": schema(
        "old_file_path", "new_file_path", "new_file_contents", "tab_name",
        old_file_path={"type": "string"}, new_file_path={"type": "string"},
        new_file_contents={"type": "string"}, tab_name={"type": "string"},
    )},
    {"name": "getDiagnostics", "description": "Get language diagnostics", "inputSchema": schema(uri={"type": "string"})},
    {"name": "checkDocumentDirty", "description": "Check if a document has unsaved changes", "inputSchema": schema("filePath", filePath=FILE_PATH)},
    {"name": "saveDocument", "description": "Save a document with unsaved changes", "inputSchema": schema("filePath", filePath=FILE_PATH)},
    {"name": "close_tab", "description": "Close a tab", "inputSchema": schema(tab_name={"type": "string"})},
    {"name": "closeAllDiffTabs", "description": "Close all diff tabs in the editor", "inputSchema": schema()},
]


class Ide:
    """SilverBullet's editor state, served to Claude Code over its IDE protocol (MCP over WebSocket)."""

    def __init__(self, cwd, port, bridge_token):
        self.cwd, self.port = cwd, port
        # Stable across restarts. Claude Code reconnects with the token it read first.
        self.ws_token = hmac.new(bridge_token.encode(), b"claude-code-ide", hashlib.sha256).hexdigest()
        self.lock = threading.Lock()
        self.clients = set()
        self.listeners = set()
        self.selection = None
        self.diffs = {}

    def keep_lockfile(self):
        """Write ~/.claude/ide/PORT.lock, and write it again whenever it goes missing.

        Claude Code deletes lock files whose pid it can't see. Inside a flatpak the pid is
        in the sandbox's PID namespace, so Claude Code running outside deletes the file.
        """
        folder = os.path.expanduser("~/.claude/ide")
        path = os.path.join(folder, f"{self.port}.lock")
        atexit.register(lambda: os.path.exists(path) and os.remove(path))
        while True:
            if not os.path.exists(path):
                os.makedirs(folder, exist_ok=True)
                with open(path, "w") as f:
                    json.dump({"pid": os.getpid(), "workspaceFolders": [self.cwd], "ideName": "SilverBullet",
                               "transport": "ws", "authToken": self.ws_token}, f)
            time.sleep(2)

    def set_state(self, page, text, start, end):
        path = os.path.join(self.cwd, page + ".md")
        selection = {
            "text": text, "filePath": path, "fileUrl": "file://" + path,
            "selection": {"start": {"line": start[0], "character": start[1]},
                          "end": {"line": end[0], "character": end[1]}, "isEmpty": not text},
        }
        with self.lock:
            self.selection = selection
            clients = list(self.clients)
        for client in clients:
            client.send_json({"jsonrpc": "2.0", "method": "selection_changed", "params": selection})

    def page(self, path):
        """The page or document name for path, or None outside the space."""
        rel = os.path.relpath(path, self.cwd)
        if rel.startswith(".."):
            return None
        return rel[:-3] if rel.endswith(".md") else rel

    def subscribe(self):
        """A queue of events for one SilverBullet window, starting with the diffs still waiting."""
        q = queue.Queue()
        with self.lock:
            self.listeners.add(q)
            for event, _ in self.diffs.values():
                q.put(json.dumps(event).encode())
        return q

    def unsubscribe(self, q):
        with self.lock:
            self.listeners.discard(q)

    def broadcast(self, event):
        """Send event to every connected SilverBullet window and return how many there are."""
        with self.lock:
            listeners = list(self.listeners)
        for q in listeners:
            q.put(json.dumps(event).encode())
        return len(listeners)

    def open_file(self, path, start_text):
        page = self.page(path)
        if page is None:
            return f"Not in the SilverBullet space: {path}"
        if not self.broadcast({"type": "open", "page": page, "startText": start_text}):
            return "SilverBullet is not connected"
        return f"Opened file: {path}"

    def open_diff(self, path, new, tab):
        """Show the diff in SilverBullet and block until it is answered or closed."""
        page = self.page(path)
        if page is None:
            raise ValueError(f"Not in the SilverBullet space: {path}")
        try:
            with open(path) as f:
                old = f.read()
        except FileNotFoundError:
            old = ""
        event = {"type": "diff", "id": secrets.token_hex(8), "page": page, "tab": tab, "old": old, "new": new}
        answer = queue.Queue(1)
        with self.lock:
            self.diffs[event["id"]] = event, answer
        if not self.broadcast(event):
            with self.lock:
                del self.diffs[event["id"]]
            raise RuntimeError("SilverBullet is not connected")
        return answer.get()

    def resolve_diff(self, diff_id, answer):
        """Answer a waiting openDiff with FILE_SAVED, DIFF_REJECTED or TAB_CLOSED."""
        with self.lock:
            diff = self.diffs.pop(diff_id, None)
        if diff:
            event, answers = diff
            answers.put((answer, event["new"]) if answer == "FILE_SAVED" else (answer,))
            self.broadcast({"type": "closeDiff", "id": diff_id})
        return diff is not None

    def close_diffs(self, tab=None):
        """Close the diffs for tab, or all of them, and return how many were open."""
        with self.lock:
            ids = [e["id"] for e, _ in self.diffs.values() if tab is None or e["tab"] == tab]
        for diff_id in ids:
            self.resolve_diff(diff_id, "TAB_CLOSED")
        return len(ids)

    def call_tool(self, name, args):
        selection = self.selection
        if name in ("getCurrentSelection", "getLatestSelection"):
            if not selection:
                return {"success": False, "message": "No active editor found"}
            return {**selection, "success": True}
        if name == "getOpenEditors":
            tabs = [{"uri": selection["fileUrl"], "isActive": True, "isPinned": False, "isPreview": False,
                     "isDirty": False, "label": os.path.basename(selection["filePath"]), "languageId": "markdown"}] if selection else []
            return {"tabs": tabs}
        if name == "getWorkspaceFolders":
            return {"success": True, "rootPath": self.cwd,
                    "folders": [{"name": os.path.basename(self.cwd), "uri": "file://" + self.cwd, "path": self.cwd}]}
        if name == "openFile":
            return self.open_file(args["filePath"], args.get("startText"))
        if name == "openDiff":
            return self.open_diff(args["new_file_path"], args["new_file_contents"], args["tab_name"])
        if name == "getDiagnostics":
            return []
        if name == "checkDocumentDirty":
            return {"success": True, "filePath": args["filePath"], "isDirty": False, "isUntitled": False}
        if name == "saveDocument":
            return {"success": True, "filePath": args["filePath"], "saved": True, "message": "Document saved"}
        if name == "close_tab":
            self.close_diffs(args.get("tab_name"))
            return "TAB_CLOSED"
        if name == "closeAllDiffTabs":
            return f"CLOSED_{self.close_diffs()}_DIFF_TABS"

    def handle(self, message):
        """The JSON-RPC response to message, or None for a notification."""
        method, params = message.get("method"), message.get("params") or {}
        if "id" not in message:
            return None
        if method == "initialize":
            result = {"protocolVersion": "2024-11-05",
                      "capabilities": {"logging": {}, "prompts": {"listChanged": True}, "tools": {"listChanged": True}},
                      "serverInfo": {"name": "silverbullet", "version": "1"}}
        elif method == "tools/list":
            result = {"tools": TOOLS}
        elif method == "prompts/list":
            result = {"prompts": []}
        elif method == "ping":
            result = {}
        elif method == "tools/call" and params.get("name") in {t["name"] for t in TOOLS}:
            try:
                output = self.call_tool(params["name"], params.get("arguments") or {})
            except (ValueError, RuntimeError) as e:
                return {"jsonrpc": "2.0", "id": message["id"], "error": {"code": -32000, "message": str(e)}}
            texts = output if isinstance(output, tuple) else [output if isinstance(output, str) else json.dumps(output)]
            result = {"content": [{"type": "text", "text": text} for text in texts]}
        else:
            return {"jsonrpc": "2.0", "id": message["id"], "error": {"code": -32601, "message": f"Unknown method: {method}"}}
        return {"jsonrpc": "2.0", "id": message["id"], "result": result}


class Handler(BridgeHandler):
    ide = None

    def websocket(self):
        return self.headers.get("Upgrade", "").lower() == "websocket"

    def authorized(self):
        """Claude Code's WebSocket uses the lock file's token, everything else the bridge's."""
        if self.websocket():
            return hmac.compare_digest(self.headers.get("x-claude-code-ide-authorization", ""), self.ide.ws_token)
        return super().authorized()

    def do_GET(self):
        if self.websocket():
            return self.serve_websocket()
        if self.path != "/ide/events":
            return self.send_error(404)
        self.serve_events(self.ide)

    def serve_websocket(self):
        accept = base64.b64encode(hashlib.sha1((self.headers["Sec-WebSocket-Key"] + WEBSOCKET_GUID).encode()).digest())
        self.send_response(101)
        self.send_header("Upgrade", "websocket")
        self.send_header("Connection", "Upgrade")
        self.send_header("Sec-WebSocket-Accept", accept.decode())
        if protocol := self.headers.get("Sec-WebSocket-Protocol"):
            self.send_header("Sec-WebSocket-Protocol", protocol.split(",")[0].strip())
        self.end_headers()
        self.wfile.flush()
        self.close_connection = True
        self.send_lock = threading.Lock()
        with self.ide.lock:
            self.ide.clients.add(self)
        try:
            message = bytearray()
            while frame := self.read_frame():
                opcode, fin, payload = frame
                if opcode == 8:
                    self.send_frame(8, payload[:2])
                    return
                if opcode == 9:
                    self.send_frame(10, payload)
                    continue
                if opcode in (0, 1, 2):
                    message += payload
                    if fin:
                        threading.Thread(target=self.respond, args=(json.loads(message),), daemon=True).start()
                        message = bytearray()
        except (BrokenPipeError, ConnectionResetError):
            pass
        finally:
            with self.ide.lock:
                self.ide.clients.discard(self)

    def respond(self, message):
        """Answer one JSON-RPC message. Runs in its own thread, since openDiff blocks until it is answered."""
        if response := self.ide.handle(message):
            try:
                self.send_json(response)
            except OSError:
                pass

    def read_frame(self):
        """The next WebSocket frame as (opcode, fin, payload), or None when the connection closes."""
        header = self.rfile.read(2)
        if len(header) < 2:
            return None
        length = header[1] & 0x7F
        if length == 126:
            length = struct.unpack(">H", self.rfile.read(2))[0]
        elif length == 127:
            length = struct.unpack(">Q", self.rfile.read(8))[0]
        mask = self.rfile.read(4) if header[1] & 0x80 else b"\0\0\0\0"
        data = self.rfile.read(length)
        n = len(data)
        payload = (int.from_bytes(data, "little") ^ int.from_bytes((mask * (n // 4 + 1))[:n], "little")).to_bytes(n, "little")
        return header[0] & 0x0F, header[0] & 0x80, payload

    def send_frame(self, opcode, payload):
        length = len(payload)
        if length < 126:
            header = struct.pack(">BB", 0x80 | opcode, length)
        elif length < 65536:
            header = struct.pack(">BBH", 0x80 | opcode, 126, length)
        else:
            header = struct.pack(">BBQ", 0x80 | opcode, 127, length)
        with self.send_lock:
            self.wfile.write(header + payload)
            self.wfile.flush()

    def send_json(self, message):
        self.send_frame(1, json.dumps(message).encode())

    def post(self, body):
        if self.path == "/ide/state":
            state = json.loads(body)
            self.ide.set_state(state["page"], state["text"], state["start"], state["end"])
            return True
        if self.path == "/ide/diff":
            answer = json.loads(body)
            return self.ide.resolve_diff(answer["id"], "FILE_SAVED" if answer["accepted"] else "DIFF_REJECTED")
        return False


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--port", type=int, default=7682)
    parser.add_argument("--cwd", default=os.getcwd())
    args = parser.parse_args()
    cwd = os.path.abspath(os.path.expanduser(args.cwd))
    Handler.token = load_token(cwd)
    Handler.ide = Ide(cwd, args.port, Handler.token)
    threading.Thread(target=Handler.ide.keep_lockfile, daemon=True).start()
    signal.signal(signal.SIGTERM, lambda *_: sys.exit(0))
    ThreadingHTTPServer(("127.0.0.1", args.port), Handler).serve_forever()


if __name__ == "__main__":
    main()
