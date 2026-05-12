from __future__ import annotations

import sys
from collections import Counter
from pathlib import Path

try:
    from scripts.revision.revisar_docs import scan_docs
    from scripts.revision.revisar_scripts import scan_scripts
except ModuleNotFoundError:
    # Permite ejecución directa sin depender de paquetes.
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from revisar_docs import scan_docs
    from revisar_scripts import scan_scripts


def _severity_rank(s: str) -> int:
    return {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3, "INFO": 4}.get(s, 9)


def _render_report(findings) -> str:
    findings_sorted = sorted(findings, key=lambda f: (_severity_rank(f.severity), f.category, f.file))

    sev = Counter(f.severity for f in findings_sorted)
    cat = Counter(f.category for f in findings_sorted)

    out: list[str] = []
    out.append("# INFORME DE REVISION - Materiales educativos")
    out.append("")
    out.append("## Resumen ejecutivo")
    out.append("")
    out.append(f"- **CRITICAL**: {sev.get('CRITICAL', 0)}")
    out.append(f"- **HIGH**: {sev.get('HIGH', 0)}")
    out.append(f"- **MEDIUM**: {sev.get('MEDIUM', 0)}")
    out.append(f"- **LOW**: {sev.get('LOW', 0)}")
    out.append(f"- **INFO**: {sev.get('INFO', 0)}")
    out.append("")
    out.append("## KPIs (repo)")
    out.append("")
    out.append(f"- **Enlaces internos rotos**: {cat.get('broken-link', 0)}")
    out.append(f"- **Placeholders pendientes**: {cat.get('placeholders', 0)}")
    out.append(f"- **Scripts no compilables**: {cat.get('py-compile', 0)}")
    out.append("")

    def section(title: str, level: str) -> None:
        items = [f for f in findings_sorted if f.severity == level]
        out.append(f"## {title}")
        out.append("")
        if not items:
            out.append("- (sin hallazgos)")
            out.append("")
            return
        for f in items:
            out.append(f"- **[{f.category}]** `{f.file}` - {f.message}")
            if f.hint:
                out.append(f"  - hint: {f.hint}")
        out.append("")

    section("Hallazgos criticos", "CRITICAL")
    section("Hallazgos altos", "HIGH")
    section("Hallazgos medios", "MEDIUM")
    section("Hallazgos bajos", "LOW")
    section("Notas informativas", "INFO")

    return "\n".join(out)


def main() -> int:
    # Evita problemas de encoding en Windows/PowerShell (cp1252).
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

    findings = scan_docs() + scan_scripts()
    report = _render_report(findings)

    output_path: Path | None = None
    args = sys.argv[1:]
    if "--output" in args:
        idx = args.index("--output")
        if idx + 1 < len(args):
            output_path = Path(args[idx + 1])

    if output_path:
        output_path.write_text(report, encoding="utf-8")
    else:
        print(report)

    sev = Counter(f.severity for f in findings)
    return 2 if sev.get("CRITICAL", 0) else 0


if __name__ == "__main__":
    raise SystemExit(main())

