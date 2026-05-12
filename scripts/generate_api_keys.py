#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Genera claves API aleatorias para asignar en WATER_API_KEY_TO_PLAN (no las guarda)."""

from __future__ import annotations

import argparse
import secrets
import string

_ALPHABET = string.ascii_letters + string.digits


def generate_api_key(length: int = 32) -> str:
    return "".join(secrets.choice(_ALPHABET) for _ in range(length))


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("-n", "--count", type=int, default=5, help="Cuántas claves generar")
    p.add_argument("-l", "--length", type=int, default=32, help="Longitud de cada clave")
    args = p.parse_args()
    for i in range(1, max(1, args.count) + 1):
        print(f"Cliente {i}: {generate_api_key(args.length)}")


if __name__ == "__main__":
    main()
