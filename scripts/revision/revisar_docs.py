from __future__ import annotations

import re
import sys
from pathlib import Path

try:
    from scripts.revision._common import Finding, as_posix_rel, is_markdown, workspace_root
except ModuleNotFoundError:
    # Permite ejecución directa sin depender de paquetes.
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from _common import Finding, as_posix_rel, is_markdown, workspace_root


MD_LINK_RE = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")


def _is_external_link(target: str) -> bool:
    t = target.strip().lower()
    return t.startswith(("http://", "https://", "mailto:", "tel:"))


def _normalize_md_target(target: str) -> str:
    t = target.strip()
    if "#" in t:
        t = t.split("#", 1)[0]
    return t.strip()


def _target_to_path(md_file: Path, target: str) -> Path | None:
    t = _normalize_md_target(target)
    if not t or _is_external_link(t):
        return None
    if t.startswith("PLACEHOLDER:"):
        return None
    if t.startswith("/"):
        return None
    return (md_file.parent / t).resolve()


def scan_docs() -> list[Finding]:
    root = workspace_root()
    findings: list[Finding] = []

    docs_root = root / "docs"
    if not docs_root.exists():
        return [
            Finding(
                severity="CRITICAL",
                category="docs",
                file="(repo)",
                message="No existe carpeta docs/ en el workspace.",
                hint="Verifica que estás en la raíz del repositorio correcto.",
            )
        ]

    # Alcance educativo (evita ruido de docs técnicas no relacionadas).
    targets = [
        docs_root / "cuento-castuo-sabionda",
        docs_root / "lengua-comun",
        docs_root / "castuo-educacion-2040",
        docs_root / "legal",
    ]
    md_files: list[Path] = []
    for t in targets:
        if t.exists():
            md_files.extend([p for p in t.rglob("*") if p.is_file() and is_markdown(p)])

    for md in md_files:
        rel = as_posix_rel(md, root)
        try:
            text = md.read_text(encoding="utf-8", errors="replace")
        except Exception as e:
            findings.append(
                Finding(
                    severity="HIGH",
                    category="docs",
                    file=rel,
                    message=f"No se pudo leer el archivo: {e}",
                )
            )
            continue

        if "PLACEHOLDER:" in text:
            findings.append(
                Finding(
                    severity="INFO",
                    category="placeholders",
                    file=rel,
                    message="Contiene PLACEHOLDER: pendiente de despliegue o decisión.",
                    hint="Sustituye PLACEHOLDER: por una URL real cuando exista.",
                )
            )

        for _, target in MD_LINK_RE.findall(text):
            p = _target_to_path(md, target)
            if p is None:
                continue

            # If target points to a folder, accept if it exists.
            if not p.exists():
                findings.append(
                    Finding(
                        severity="CRITICAL",
                        category="broken-link",
                        file=rel,
                        message=f"Enlace interno roto: ({target})",
                        hint="Revisa la ruta relativa o crea el archivo referido.",
                    )
                )

    return findings


def main() -> int:
    findings = scan_docs()
    print("Revision docs - alcance: docs/cuento-castuo-sabionda, docs/lengua-comun, docs/castuo-educacion-2040")
    print(f"Findings: {len(findings)}")
    for f in findings:
        print(f"[{f.severity}] {f.category} {f.file} - {f.message}")
        if f.hint:
            print(f"  hint: {f.hint}")
    return 2 if any(f.severity == "CRITICAL" for f in findings) else 0


if __name__ == "__main__":
    raise SystemExit(main())

