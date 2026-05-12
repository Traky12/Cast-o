from __future__ import annotations

from pathlib import Path


SENSITIVE_BOOL_FLAGS = {
    "ENABLE_GITHUB_INTEGRATION": "false",
    "ENABLE_TRACES_SUBMIT": "false",
    "ENABLE_CLAUDE_INTEGRATION": "false",
    "ENABLE_MISTRAL_INTEGRATION": "false",
}


def _parse_env_template(content: str) -> dict[str, str]:
    values: dict[str, str] = {}
    for raw_line in content.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip()
    return values


def test_env_production_template_keeps_sensitive_flags_disabled_by_default() -> None:
    env_template = Path(__file__).resolve().parent.parent / ".env.production.example"
    assert env_template.exists(), ".env.production.example must exist"

    content = env_template.read_text(encoding="utf-8")
    values = _parse_env_template(content)

    for key, expected in SENSITIVE_BOOL_FLAGS.items():
        assert key in values, f"Missing {key} in .env.production.example"
        assert values[key].lower() == expected, (
            f"{key} must default to {expected} in .env.production.example"
        )