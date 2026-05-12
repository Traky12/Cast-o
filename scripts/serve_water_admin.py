#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Sirve frontend/public en un puerto local (panel water-admin y estáticos)."""

from __future__ import annotations

import argparse
import http.server
import os
import socketserver
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PUBLIC = ROOT / "frontend" / "public"


class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(PUBLIC), **kwargs)

    def log_message(self, fmt, *args):
        sys.stderr.write("%s - %s\n" % (self.address_string(), fmt % args))


def main() -> None:
    p = argparse.ArgumentParser(description="Static server: frontend/public")
    p.add_argument("--port", type=int, default=3000)
    args = p.parse_args()
    if not PUBLIC.is_dir():
        print("No existe:", PUBLIC, file=sys.stderr)
        sys.exit(1)
    os.chdir(PUBLIC)
    with socketserver.TCPServer(("", args.port), Handler) as httpd:
        print(f"CASTÚO admin estático → http://127.0.0.1:{args.port}/water-admin/")
        print("Configura claves en la pestaña Configuración del panel.")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nDetenido.")


if __name__ == "__main__":
    main()
