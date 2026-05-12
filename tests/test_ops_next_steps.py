from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_sql_persistence_schema_exists_and_has_critical_tables() -> None:
    sql_path = ROOT / "scripts" / "db" / "init_castuo_system_schema.sql"
    assert sql_path.exists(), "Debe existir el SQL de inicializacion de persistencia"

    sql_text = sql_path.read_text(encoding="utf-8").lower()
    assert "create database if not exists castuo_system" in sql_text
    assert "create table if not exists users" in sql_text
    assert "create table if not exists farms" in sql_text
    assert "create table if not exists transactions" in sql_text
    assert "create table if not exists logs" in sql_text


def test_init_persistence_script_exists_and_uses_mariadb_container() -> None:
    script_path = ROOT / "scripts" / "init_castuo_persistence.sh"
    assert script_path.exists(), "Debe existir script para inicializar persistencia"

    script = script_path.read_text(encoding="utf-8")
    assert "castuo-mariadb" in script
    assert "SHOW DATABASES" in script
    assert "SHOW TABLES" in script


def test_verify_operational_stack_script_exists_with_core_checks() -> None:
    script_path = ROOT / "scripts" / "verify_operational_stack.sh"
    assert script_path.exists(), "Debe existir script de verificacion operativa"

    script = script_path.read_text(encoding="utf-8")
    # accepts check_http_ok helper or direct curl calls
    assert "http://localhost:8000" in script
    assert "localhost:5432" in script
    assert "redis-cli ping" in script
    assert "kubectl get certificate -n castuo-system" in script


def test_start_all_services_script_exists_with_recommended_order() -> None:
    script_path = ROOT / "scripts" / "start_all_services.sh"
    assert script_path.exists(), "Debe existir script de inicio recomendado"

    script = script_path.read_text(encoding="utf-8")
    assert "start_frontend_8003.sh" in script
    assert "docker compose" in script
    assert "api" in script
    assert "prometheus" in script
    assert "grafana" in script
