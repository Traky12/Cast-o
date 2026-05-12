from __future__ import annotations

import ast
import py_compile
import sys
from pathlib import Path

try:
    from scripts.revision._common import Finding, as_posix_rel, workspace_root
except ModuleNotFoundError:
    # Permite ejecución directa sin depender de paquetes.
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from _common import Finding, as_posix_rel, workspace_root


def _uses_input_without_guard(tree: ast.AST) -> bool:
    # Heurística: presencia de input() sin try/except cercano no es detectable fácil sin CFG.
    # Señalamos solo si hay input() y no hay ningún Try en el módulo.
    has_input = False
    has_try = False
    for node in ast.walk(tree):
        if isinstance(node, ast.Try):
            has_try = True
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "input":
            has_input = True
    return has_input and not has_try


def scan_scripts() -> list[Finding]:
    root = workspace_root()
    findings: list[Finding] = []

    scripts_root = root / "scripts"
    educ_root = scripts_root / "educacion"
    dash_root = scripts_root / "dashboard"
    seg_root = scripts_root / "seguridad"
    if not educ_root.exists():
        return [
            Finding(
                severity="CRITICAL",
                category="scripts",
                file="scripts/educacion",
                message="No existe carpeta scripts/educacion en el workspace.",
                hint="Verifica que el bloque educativo esté presente.",
            )
        ]

    py_files = [p for p in educ_root.rglob("*.py") if p.is_file()]
    if dash_root.exists():
        py_files.extend([p for p in dash_root.rglob("*.py") if p.is_file()])
    if seg_root.exists():
        py_files.extend([p for p in seg_root.rglob("*.py") if p.is_file()])

    for py in py_files:
        rel = as_posix_rel(py, root)

        try:
            py_compile.compile(str(py), doraise=True)
        except Exception as e:
            findings.append(
                Finding(
                    severity="CRITICAL",
                    category="py-compile",
                    file=rel,
                    message=f"No compila: {e}",
                    hint="Corrige sintaxis/imports para mantener el ecosistema ejecutable.",
                )
            )
            continue

        try:
            text = py.read_text(encoding="utf-8", errors="replace")
            tree = ast.parse(text)
        except Exception as e:
            findings.append(
                Finding(
                    severity="HIGH",
                    category="py-parse",
                    file=rel,
                    message=f"No se pudo analizar AST: {e}",
                )
            )
            continue

        if "requests.get(" in text or "requests.post(" in text:
            findings.append(
                Finding(
                    severity="MEDIUM",
                    category="network-default",
                    file=rel,
                    message="Detectada posible llamada de red (requests.*).",
                    hint="Evita red por defecto en scripts educativos; usa modo simulado o flags explícitos.",
                )
            )

        if _uses_input_without_guard(tree):
            findings.append(
                Finding(
                    severity="LOW",
                    category="input-guard",
                    file=rel,
                    message="Usa input() sin detectar try/except en el módulo (heurística).",
                    hint="Añade validación/manejo de error para entradas vacías o inesperadas.",
                )
            )

    return findings


def main() -> int:
    findings = scan_scripts()
    print("Revision scripts - alcance: scripts/educacion (+ scripts/dashboard si existe)")
    print(f"Findings: {len(findings)}")
    for f in findings:
        print(f"[{f.severity}] {f.category} {f.file} - {f.message}")
        if f.hint:
            print(f"  hint: {f.hint}")
    return 2 if any(f.severity == "CRITICAL" for f in findings) else 0


if __name__ == "__main__":
    raise SystemExit(main())

