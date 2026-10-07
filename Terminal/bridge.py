#!/usr/bin/env python3
"""Serve named terminal sessions over plain HTTP: SSE for output, POST for input.

    GET  /NAME/stream   text/event-stream; each event's data is base64 terminal output
    POST /NAME/input    request body is written to the terminal as-is
    POST /NAME/resize   JSON body {"cols": N, "rows": N}
    POST /shutdown      stops the bridge and every session

Each session runs its own command through /bin/sh, fixed when the bridge starts.

Listens on 127.0.0.1 only. Meant to sit behind SilverBullet's /.proxy, which
supplies authentication. Every request also needs "Authorization: Bearer TOKEN",
where TOKEN is read from .bridge-token in --cwd (created with mode 600 if missing).
"""

import argparse
import base64
import fcntl
import hmac
import json
import os
import pty
import queue
import secrets
import signal
import struct
import termios
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

SCROLLBACK_BYTES = 256 * 1024
TOKEN_FILE = ".bridge-token"


def load_token(cwd):
    """The token in cwd/.bridge-token, writing a new one if the file is missing or empty."""
    path = os.path.join(cwd, TOKEN_FILE)
    try:
        with open(path) as f:
            token = f.read().strip()
    except FileNotFoundError:
        token = ""
    if not token:
        tmp = f"{path}.{os.getpid()}"
        fd = os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(fd, "w") as f:
            f.write(secrets.token_hex(32))
        os.replace(tmp, path)
        with open(path) as f:
            token = f.read().strip()
    if not token:
        raise SystemExit(f"{path} is empty")
    return token


class Session:
    def __init__(self, command, cwd):
        self.argv, self.cwd = ["/bin/sh", "-c", command], cwd
        self.lock = threading.Lock()
        self.listeners = set()
        self.scrollback = bytearray()
        self.pid = self.fd = None

    def ensure_running(self):
        with self.lock:
            if self.pid is not None:
                return
            pid, fd = pty.fork()
            if pid == 0:
                os.chdir(self.cwd)
                os.environ.update(TERM="xterm-256color", COLORTERM="truecolor")
                os.execvp(self.argv[0], self.argv)
            self.pid, self.fd = pid, fd
            self.scrollback.clear()
            threading.Thread(target=self._read, daemon=True).start()

    def _read(self):
        while True:
            try:
                data = os.read(self.fd, 65536)
            except OSError:
                break
            if not data:
                break
            with self.lock:
                self.scrollback += data
                del self.scrollback[:-SCROLLBACK_BYTES]
                for q in self.listeners:
                    q.put(base64.b64encode(data))
        os.waitpid(self.pid, 0)
        with self.lock:
            os.close(self.fd)
            self.pid = self.fd = None
            for q in self.listeners:
                q.put(None)

    def subscribe(self):
        q = queue.Queue()
        with self.lock:
            if self.scrollback:
                q.put(base64.b64encode(bytes(self.scrollback)))
            self.listeners.add(q)
        return q

    def unsubscribe(self, q):
        with self.lock:
            self.listeners.discard(q)

    def write(self, data):
        self.ensure_running()
        os.write(self.fd, data)

    def resize(self, cols, rows):
        self.ensure_running()
        fcntl.ioctl(self.fd, termios.TIOCSWINSZ, struct.pack("HHHH", rows, cols, 0, 0))
        os.kill(self.pid, signal.SIGWINCH)


class BridgeHandler(BaseHTTPRequestHandler):
    """Request helpers shared by the bridge and servers built on it."""

    token = None

    def parse_request(self):
        """Reject requests with a foreign Host (DNS rebinding) or that fail authorized()."""
        if not super().parse_request():
            return False
        host = self.headers.get("Host", "").rsplit(":", 1)[0]
        if host not in ("127.0.0.1", "localhost") or not self.authorized():
            self.send_error(403)
            return False
        return True

    def authorized(self):
        """The bearer token, and no Origin, since SilverBullet's /.proxy sends none and browsers do."""
        auth = self.headers.get("Authorization", "")
        return "Origin" not in self.headers and hmac.compare_digest(auth, f"Bearer {self.token}")

    def serve_events(self, source):
        """Send each item from source.subscribe() as an SSE event until None arrives or the client goes away."""
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")
        self.send_header("Cache-Control", "no-cache")
        self.send_header("X-Accel-Buffering", "no")
        self.end_headers()
        q = source.subscribe()
        try:
            while True:
                try:
                    data = q.get(timeout=15)
                except queue.Empty:
                    self.wfile.write(b": keepalive\n\n")
                else:
                    if data is None:
                        self.wfile.write(b"event: exit\ndata:\n\n")
                        self.wfile.flush()
                        return
                    self.wfile.write(b"data: " + data + b"\n\n")
                self.wfile.flush()
        except (BrokenPipeError, ConnectionResetError):
            pass
        finally:
            source.unsubscribe(q)

    def read_body(self):
        # SilverBullet's /.proxy streams request bodies with chunked encoding.
        if self.headers.get("Transfer-Encoding", "").lower() != "chunked":
            return self.rfile.read(int(self.headers.get("Content-Length", 0)))
        body = bytearray()
        while size := int(self.rfile.readline().split(b";")[0], 16):
            body += self.rfile.read(size)
            self.rfile.readline()
        self.rfile.readline()
        return bytes(body)

    def do_POST(self):
        body = self.read_body()
        shutdown = self.path == "/shutdown"
        if not shutdown and not self.post(body):
            return self.send_error(404)
        self.send_response(204)
        self.end_headers()
        if shutdown:
            os.kill(os.getpid(), signal.SIGTERM)

    def post(self, body):
        """Handle a POST other than /shutdown. Returns False for an unknown path."""
        return False

    def log_message(self, *args):
        pass


class Handler(BridgeHandler):
    sessions = {}

    def route(self):
        """The session and action for a /NAME/ACTION path, or (None, None)."""
        parts = self.path.strip("/").split("/")
        if len(parts) != 2 or parts[0] not in self.sessions:
            return None, None
        return self.sessions[parts[0]], parts[1]

    def do_GET(self):
        session, action = self.route()
        if action != "stream":
            return self.send_error(404)
        session.ensure_running()
        self.serve_events(session)

    def post(self, body):
        session, action = self.route()
        if action == "input":
            session.write(body)
        elif action == "resize":
            size = json.loads(body)
            session.resize(int(size["cols"]), int(size["rows"]))
        else:
            return False
        return True


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--port", type=int, default=7681)
    parser.add_argument("--cwd", default=os.getcwd())
    parser.add_argument("--session", action="append", metavar="NAME=COMMAND", help="a named session and its command, e.g. claude=claude; repeatable (default: shell=$SHELL)")
    parser.add_argument("--print-token", action="store_true", help="print the token, creating it if needed, and exit")
    args = parser.parse_args()
    cwd = os.path.abspath(os.path.expanduser(args.cwd))
    BridgeHandler.token = load_token(cwd)
    if args.print_token:
        return print(BridgeHandler.token)
    for spec in args.session or ["shell=" + os.environ.get("SHELL", "bash")]:
        name, _, command = spec.partition("=")
        Handler.sessions[name] = Session(command, cwd)
    ThreadingHTTPServer(("127.0.0.1", args.port), Handler).serve_forever()


if __name__ == "__main__":
    main()
