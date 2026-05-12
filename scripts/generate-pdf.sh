#!/usr/bin/env bash
set -euo pipefail

INPUT_FILE="${1:-}"
OUTPUT_FILE="${2:-}"

if [[ -z "$INPUT_FILE" || -z "$OUTPUT_FILE" ]]; then
  echo "Usage: $0 <input.md> <output.pdf>"
  exit 1
fi

if [[ ! -f "$INPUT_FILE" ]]; then
  echo "Input file not found: $INPUT_FILE"
  exit 1
fi

python3 - "$INPUT_FILE" "$OUTPUT_FILE" <<'PY'
import re
import sys
from pathlib import Path

input_path = Path(sys.argv[1])
output_path = Path(sys.argv[2])

try:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
except Exception as exc:
    raise SystemExit(f"reportlab is required: {exc}")

text = input_path.read_text(encoding="utf-8")
styles = getSampleStyleSheet()
doc = SimpleDocTemplate(str(output_path), pagesize=A4)
story = []

for raw_line in text.splitlines():
    line = raw_line.strip()
    if not line:
        story.append(Spacer(1, 8))
        continue
    if line.startswith("# "):
        story.append(Paragraph(re.sub(r'^#\s+', '', line), styles["Title"]))
    elif line.startswith("## "):
        story.append(Paragraph(re.sub(r'^##\s+', '', line), styles["Heading2"]))
    elif line.startswith("### "):
        story.append(Paragraph(re.sub(r'^###\s+', '', line), styles["Heading3"]))
    else:
        safe = (
            line.replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
        )
        story.append(Paragraph(safe, styles["BodyText"]))
    story.append(Spacer(1, 4))

doc.build(story)
print(f"Generated {output_path}")
PY
