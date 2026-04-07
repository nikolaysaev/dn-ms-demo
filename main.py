import os
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import sys


DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8000
ROOT = Path(__file__).resolve().parent


class DemoRequestHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT), **kwargs)

    def guess_type(self, path: str) -> str:
        content_type = super().guess_type(path)
        if content_type == "text/html":
            return "text/html; charset=utf-8"
        return content_type


def resolve_port() -> int:
    if len(sys.argv) > 1:
        return int(sys.argv[1])
    return int(os.environ.get("PORT", DEFAULT_PORT))


def resolve_host() -> str:
    return os.environ.get("HOST", DEFAULT_HOST)


def run() -> None:
    host = resolve_host()
    port = resolve_port()
    server = ThreadingHTTPServer((host, port), DemoRequestHandler)
    print(f"Serving demo at http://{host}:{port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping server.")
    finally:
        server.server_close()


if __name__ == "__main__":
    run()
