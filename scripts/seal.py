#!/usr/bin/env python3
"""Alias del sello Sabionda (misma lógica que sabionda_final_release_seal.py)."""
import subprocess
import sys
from pathlib import Path

p = Path(__file__).resolve().parent / "sabionda_final_release_seal.py"
raise SystemExit(subprocess.call([sys.executable, str(p), *sys.argv[1:]]))
