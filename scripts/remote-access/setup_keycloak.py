#!/usr/bin/env python3
"""
Bootstrap mínimo de realm/cliente/roles en Keycloak (laboratorio CTAEX).
Requiere: pip install -r scripts/remote-access/requirements.txt
"""
from __future__ import annotations
import os
import sys

try:
    from keycloak import KeycloakAdmin
except ImportError:
    print("Instala dependencias: pip install -r scripts/remote-access/requirements.txt", file=sys.stderr)
    raise

REALM = os.getenv("KEYCLOAK_REALM", "castuo-system") /-*/
ADMIN_USER = os.getenv("KEYCLOAK_BOOTSTRAP_ADMIN", "admin")
ADMIN_PASS = os.getenv("KEYCLOAK_ADMIN_PASSWORD", "")
SERVER = os.getenv("KEYCLOAK_SERVER_URL", "http://localhost:8090").rstrip("/")


def _ignore_exists(fn, label: str) -> None:
    try:
        fn()
    except Exception as e:
        if "409" in str(e) or "already exists" in str(e).lower():
            print(f"{label}: ya existía")
        else:
            print(f"{label}: {e}")


def main() -> None:
    if not ADMIN_PASS:
        print("KEYCLOAK_ADMIN_PASSWORD no definido", file=sys.stderr)
        sys.exit(1)

    admin = KeycloakAdmin(
        server_url=f"{SERVER}/",
        username=ADMIN_USER,
        password=ADMIN_PASS,
        realm_name="master",
        verify=True,
    )

    _ignore_exists(
        lambda: admin.create_realm(
            payload={
                "realm": REALM,
                "enabled": True,
                "displayName": "CASTÚO System",
                "sslRequired": "external",
            }
        ),
        "Realm",
    )

    client_secret = os.getenv("KEYCLOAK_GATEWAY_CLIENT_SECRET", "change-me-gateway-secret")
    _ignore_exists(
        lambda: admin.create_client(
            payload={
                "clientId": "api-gateway",
                "name": "CASTÚO API Gateway",
                "enabled": True,
                "publicClient": False,
                "secret": client_secret,
                "directAccessGrantsEnabled": True,
                "serviceAccountsEnabled": True,
                "standardFlowEnabled": True,
                "redirectUris": ["*"],
                "webOrigins": ["*"],
            },
            realm_name=REALM,
        ),
        "Cliente api-gateway",
    )

    for role in (
        {"name": "admin", "description": "Administración"},
        {"name": "technician", "description": "Técnico operación"},
        {"name": "viewer", "description": "Solo lectura"},
        {"name": "owner", "description": "Propietario tratamiento (backend)"},
        {"name": "dpo", "description": "DPO (backend)"},
    ):
        _ignore_exists(
            lambda r=role: admin.create_realm_role(payload=r, realm_name=REALM),
            f"Rol {role['name']}",
        )

    tech_pass = os.getenv("KEYCLOAK_TECH_USER_PASSWORD", "")
    if tech_pass:
        users = admin.get_users(query={"username": "tecnico1"}, realm_name=REALM)
        if users:
            uid = users[0]["id"]
            print("Usuario tecnico1 ya existe")
        else:
            uid = admin.create_user(
                payload={
                    "username": "tecnico1",
                    "email": "tecnico1@example.local",
                    "enabled": True,
                    "credentials": [
                        {
                            "type": "password",
                            "value": tech_pass,
                            "temporary": False,
                        }
                    ],
                },
                realm_name=REALM,
            )
            print("Usuario tecnico1 creado")
        role = admin.get_realm_role(role_name="technician", realm_name=REALM)
        admin.assign_realm_roles(user_id=uid, roles=[role], realm_name=REALM)

    print("Hecho. Ajusta secretos en Keycloak y sincroniza .env.remote-access.")


if __name__ == "__main__":
    main()
