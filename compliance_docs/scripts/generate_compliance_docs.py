#!/usr/bin/env python3
# compliance_docs/scripts/generate_compliance_docs.py
"""Generador de documentación de cumplimiento (GDPR, Ley 3/2023, AI Act, ISO 27001, SIGPAC, contratos, checklists)."""
from __future__ import annotations

import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

from jinja2 import Environment, FileSystemLoader

BASE_DIR = Path(__file__).resolve().parents[1]
TEMPLATES_DIR = BASE_DIR / "templates"
OUTPUT_DIR = BASE_DIR / "generated"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


class ComplianceDocGenerator:
    def __init__(self, region: str = "extremadura") -> None:
        self.env = Environment(
            loader=FileSystemLoader(str(TEMPLATES_DIR)),
            autoescape=False,
        )
        self.region = region
        self._load_context_data()

    def _get_regional_scope(self) -> Dict[str, Any]:
        regions = {
            "extremadura": {
                "name": "Extremadura",
                "normatives": [
                    "Ley 3/2023 de Montes de Extremadura",
                    "Decreto 45/2020 de Subvenciones Forestales",
                    "Orden de 12 de marzo de 2021 (SIGPAC-Extremadura)",
                ],
                "sigpac_url": "https://sigpac.mapa.gob.es/sigpac/",
                "competent_authority": "Consejería de Agricultura, Desarrollo Rural, Población y Territorio",
            },
            "andalucia": {
                "name": "Andalucía",
                "normatives": [
                    "Ley 2/2021 de Montes de Andalucía",
                    "Decreto 16/2022 de Ayudas Forestales",
                    "Orden AAA/2023 de SIGPAC-Andalucía",
                ],
                "sigpac_url": "https://sigpac.juntadeandalucia.es/",
                "competent_authority": "Consejería de Agricultura, Ganadería, Pesca y Desarrollo Sostenible",
            },
            "portugal": {
                "name": "Portugal",
                "normatives": [
                    "Decreto-Lei n.º 96/2019 (Gestão Florestal)",
                    "Portaria n.º 142/2021 (SIGIF)",
                    "Regulamento (UE) 2018/841 (LULUCF)",
                ],
                "sigpac_url": "https://sigif.icnf.pt/",
                "competent_authority": "Instituto da Conservação da Natureza e das Florestas (ICNF)",
            },
        }
        return regions.get(self.region, regions["extremadura"])

    def _load_context_data(self) -> None:
        dpo = {"name": "María Gómez López", "email": "dpo@castuo-system.eu", "phone": "+34 927 00 00 00"}
        generated_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        regional_scope = self._get_regional_scope()

        self.context = {
            "system": {
                "name": "CASTÚO-SYSTEM™",
                "version": "1.3",
                "environment": os.getenv("ENVIRONMENT", "production"),
                "dpo": dpo,
                "generated_at": generated_at,
                "regional_scope": regional_scope,
            },
            "gdpr": self._get_gdpr_data(dpo, generated_at, regional_scope),
            "ai_act": self._get_ai_act_data(dpo, generated_at),
            "ley_3_2023": self._get_ley3_data(dpo, generated_at),
            "iso_27001": self._get_iso27001_data(dpo, generated_at),
            "sigpac": self._get_sigpac_data(generated_at),
            "contracts": self._get_contracts_data(regional_scope),
            "audit": self._get_audit_data(),
        }

    def _get_gdpr_data(
        self, dpo: Dict[str, str], generated_at: str, regional_scope: Dict[str, Any]
    ) -> Dict[str, Any]:
        return {
            "dpo": dpo,
            "generated_at": generated_at,
            "treatments": [
                {
                    "id": 1,
                    "name": "Gestión de Consentimientos",
                    "legal_basis": ["GDPR:6.1(a)", "Ley_3_2023:8"],
                    "data_categories": ["Datos personales", "Información de parcelas", "Datos catastrales"],
                    "recipients": ["Propietario", "DPO", regional_scope["competent_authority"]],
                    "retention": "5 años (GDPR Art. 5.1.e)",
                    "security_measures": [
                        "Cifrado AES-256 (MinIO)",
                        "Registro en GaiaChain (Art. 30)",
                        "Autenticación OIDC (Keycloak)",
                        "Audit logs (Wazuh/OpenSearch)",
                    ],
                    "evidence": {
                        "code": "backend/api/services/consent_service.py (Líneas 45-60)",
                        "gaiachain": "https://explorer.gaiachain.es/address/0xCASTUO...",
                    },
                },
                {
                    "id": 2,
                    "name": "Generación de Media Educativa",
                    "legal_basis": ["GDPR:6.1(a)", "AI_Act:52", "Ley_3_2023:18"],
                    "data_categories": ["Prompts", "Metadatos técnicos", "Vídeos generados"],
                    "recipients": ["Propietario", "DPO"],
                    "retention": "5 años",
                    "security_measures": [
                        "Sandbox EU (Stable Diffusion/SadTalker)",
                        "Registro en GaiaChain por media_id",
                        "Logs en Wazuh con metadatos de compliance",
                        "Cifrado en tránsito (TLS 1.2+)",
                    ],
                    "evidence": {
                        "code": "backend/api/services/media_service.py",
                        "example_media": "sd-eu-20260315-12345-67890",
                    },
                },
                {
                    "id": 3,
                    "name": "Gestión de Subvenciones",
                    "legal_basis": ["Ley_3_2023:12", "Decreto_45_2020:3"],
                    "data_categories": ["Datos catastrales", "Información económica"],
                    "recipients": ["Junta de Extremadura", "Propietario", "DPO"],
                    "retention": "10 años (Ley 3/2023 Art. 22)",
                    "security_measures": [
                        "Validación con SIGPAC",
                        "Firma digital (Vault Transit)",
                        "Registro en GaiaChain",
                    ],
                    "evidence": {
                        "code": "backend/api/routes/subsidies.py",
                        "sigpac_integration": "Pendiente (Hoja de Ruta 2026)",
                    },
                },
            ],
        }

    def _get_ai_act_data(self, dpo: Dict[str, str], generated_at: str) -> Dict[str, Any]:
        return {
            "system_name": "CASTÚO-SYSTEM™ Media Engine",
            "risk_level": "Low",
            "dpo": dpo,
            "generated_at": generated_at,
            "use_cases": [
                {
                    "name": "Generación de vídeos educativos forestales",
                    "ai_models": [
                        {"name": "Stable Diffusion EU", "license": "EUPL-1.2", "hosting": "OVH Cloud (Francia)", "compliance": ["GDPR", "AI Act Art. 52"]},
                        {"name": "SadTalker EU", "license": "MIT", "hosting": "Hetzner (Alemania)", "compliance": ["GDPR", "AI Act Art. 52"]},
                    ],
                    "risk_mitigation": [
                        "Aislamiento en red interna (media_network)",
                        "Registro en GaiaChain de cada media_id",
                        "Consentimiento explícito (GDPR Art. 6.1(a)) antes de generación",
                        "Sanitización de prompts para evitar inyecciones",
                    ],
                    "evidence": {
                        "sandbox_config": "docker-compose.eu-oss.yml (líneas 80-100)",
                        "audit_trail": "backend/api/security/audit.py",
                    },
                },
            ],
            "compliance": {
                "transparency": {"article": "52", "implementation": "Metadatos de compliance en cada respuesta"},
                "risk_management": {"annex": "III", "implementation": "Evaluación documentada en 02.03.02_Evaluacion_Riesgos.xlsx"},
                "copyright": {"article": "53", "implementation": "Uso de modelos con licencia EUPL/MIT"},
            },
        }

    def _get_ley3_data(self, dpo: Dict[str, str], generated_at: str) -> Dict[str, Any]:
        if self.region == "andalucia":
            articles = {
                "7": {
                    "description": "Consentimientos para gestión forestal",
                    "implementation": [
                        "Endpoint POST /api/consents/{token_id} con validación de roles",
                        "Interfaz en frontend/src/components/Legal/ConsentManager.js",
                    ],
                    "evidence": ["backend/api/routes/consents.py", "Capturas en 03_Evidencias_Tecnicas/03.04_Capturas_Pantalla/"],
                },
            }
        elif self.region == "portugal":
            articles = {
                "9": {
                    "description": "Gestão florestal sustentável",
                    "implementation": [
                        "Validação de práticas florestais no backend",
                        "Integração com SIGIF",
                    ],
                    "evidence": ["backend/api/services/consent_service.py", "Acordo com ICNF"],
                },
            }
        else:
            articles = {
                "5": {
                    "description": "Gestión sostenible de montes",
                    "implementation": [
                        "Backend forestal con validación de prácticas sostenibles",
                        "Integración con SIGPAC-Extremadura (Orden de 12 de marzo de 2021)",
                    ],
                    "evidence": ["backend/api/services/consent_service.py", "Acuerdo con Junta de Extremadura (04.02_Acuerdo_Junta.pdf)"],
                },
                "8": {
                    "description": "Consentimientos para gestión forestal",
                    "implementation": [
                        "Endpoint POST /api/consents/{token_id} con validación de roles",
                        "Interfaz en frontend/src/components/Legal/ConsentManager.js",
                    ],
                    "evidence": ["backend/api/routes/consents.py", "Capturas en 03_Evidencias_Tecnicas/03.04_Capturas_Pantalla/dashboard_consent_manager.png"],
                },
                "12": {
                    "description": "Subvenciones y ayudas",
                    "implementation": [
                        "Endpoint POST /api/subsidies/claim con validación contra SIGPAC",
                        "Registro en GaiaChain de cada solicitud",
                    ],
                    "evidence": ["backend/api/routes/subsidies.py (en desarrollo)", "Diagrama en 01_Architectura_Seguridad/01.03_Flujo_Datos_Personales.md"],
                },
                "18": {
                    "description": "Educación y formación forestal",
                    "implementation": [
                        "Servicio media_service.generate_educational_video()",
                        "Vídeos generados con Stable Diffusion EU (licencia EUPL-1.2)",
                    ],
                    "evidence": ["backend/api/services/media_service.py", "Ejemplo: compliance_report_sd-eu-20260315-12345-67890.md"],
                },
                "22": {
                    "description": "Conservación de documentos",
                    "implementation": [
                        "Política de retención de 5 años en MinIO (OVH)",
                        "Backups diarios con cifrado AES-256",
                    ],
                    "evidence": ["Configuración MinIO en docker-compose.eu-oss.yml", "Política en 02.04_ISO_27001/02.04.02_Politicas_Seguridad.md"],
                },
            }
        return {"articles": articles, "dpo": dpo, "generated_at": generated_at}

    def _get_iso27001_data(self, dpo: Dict[str, str], generated_at: str) -> Dict[str, Any]:
        return {
            "dpo": dpo,
            "generated_at": generated_at,
            "controls": {
                "A.5.1.1": {
                    "name": "Políticas de seguridad de la información",
                    "implementation": [
                        "Documentadas en compliance_docs/02.04_ISO_27001/02.04.02_Politicas_Seguridad.md",
                        "Revisión anual por DPO",
                    ],
                    "evidence": ["backend/config/security.md", "Acta de revisión 2026-03-15 (en generated/)"],
                },
                "A.9.1.1": {
                    "name": "Control de acceso a la información",
                    "implementation": [
                        "RBAC con Keycloak (roles: owner, dpo, admin, auditor)",
                        "Autenticación OIDC en todos los endpoints",
                    ],
                    "evidence": ["backend/api/security/keycloak.py", "Configuración en docker-compose.eu-oss.yml (Keycloak)"],
                },
                "A.10.1.1": {
                    "name": "Gestión de claves criptográficas",
                    "implementation": [
                        "HashiCorp Vault con Shamir 5/3",
                        "Transit Engine para firmas",
                        "Rotación cada 90 días (script rotate_keys.sh)",
                    ],
                    "evidence": ["backend/security/master_key.md", "backend/scripts/init_vault.sh"],
                },
                "A.12.4.1": {
                    "name": "Registro de eventos",
                    "implementation": [
                        "AuditLogger (backend/api/security/audit.py)",
                        "Integración con Wazuh/OpenSearch",
                        "Registro en GaiaChain de eventos críticos",
                    ],
                    "evidence": ["backend/api/security/audit.py", "Logs en generated/03_Evidencias_Tecnicas/"],
                },
                "A.12.6.1": {
                    "name": "Restricciones en el uso de servicios en la nube",
                    "implementation": [
                        "Traefik con CORS estricto (solo dominios EU)",
                        "mTLS para comunicación interna",
                        "Hosting en OVH/Hetzner (UE)",
                    ],
                    "evidence": ["deploy/traefik.yml", "deploy/dynamic.yml (middlewares)"],
                },
                "A.18.1.4": {
                    "name": "Protección de datos personales",
                    "implementation": [
                        "Cifrado AES-256 en MinIO",
                        "Vault para gestión de secretos",
                        "Sanitización de inputs (GDPR Art. 32)",
                    ],
                    "evidence": ["docker-compose.eu-oss.yml (volúmenes MinIO)", "backend/api/services/media_service.py (_sanitize_prompt)"],
                },
            },
        }

    def _get_sigpac_data(self, generated_at: str) -> Dict[str, Any]:
        if self.region == "andalucia":
            procedure = {
                "name": "Validación con SIGPAC-Andalucía",
                "legal_basis": ["Orden AAA/2023 de SIGPAC-Andalucía", "Ley 2/2021 de Montes de Andalucía"],
                "steps": [
                    {"name": "Solicitud de validación", "description": "El propietario solicita validación de prácticas forestales.", "implementation": "Endpoint POST /api/sigpac/validate", "evidence": "backend/api/routes/sigpac.py (en desarrollo)"},
                    {"name": "Consulta a SIGPAC", "description": "El sistema consulta SIGPAC-Andalucía.", "implementation": "Integración con API de SIGPAC-Andalucía", "evidence": "backend/api/services/sigpac_service.py (stub)"},
                    {"name": "Registro del resultado", "description": "El resultado se registra en GaiaChain.", "implementation": "Evento en GaiaChain con sigpac_validation_result", "evidence": "Transacción de ejemplo: 0xSIGPAC..."},
                ],
                "technical_details": {
                    "api_endpoint": "https://sigpac.juntadeandalucia.es/api/v1/validate",
                    "auth_method": "API Key (Junta de Andalucía)",
                    "data_format": "GeoJSON con propiedades de la parcela",
                    "validation_criteria": ["Coherencia con usos del suelo", "Cumplimiento de densidades de arbolado", "Alineación con planes de ordenación forestal"],
                },
                "compliance": {"ley_2_2021": ["Art. 12", "Art. 15"], "gdpr": ["Art. 6.1(e)"]},
            }
        elif self.region == "portugal":
            procedure = {
                "name": "Validação com SIGIF",
                "legal_basis": ["Decreto-Lei n.º 96/2019", "Portaria n.º 142/2021"],
                "steps": [
                    {"name": "Pedido de validação", "description": "O proprietário solicita validação das práticas florestais.", "implementation": "Endpoint POST /api/sigif/validate", "evidence": "backend/api/routes/sigif.py"},
                    {"name": "Consulta ao SIGIF", "description": "O sistema consulta o SIGIF.", "implementation": "Integração com API do ICNF", "evidence": "backend/api/services/sigif_service.py"},
                    {"name": "Registo do resultado", "description": "O resultado é registado na GaiaChain.", "implementation": "Evento na GaiaChain com sigif_validation_result", "evidence": "Transação de exemplo: 0xSIGIF..."},
                ],
                "technical_details": {
                    "api_endpoint": "https://sigif.icnf.pt/api/v1/validate",
                    "auth_method": "OAuth2 (ICNF)",
                    "data_format": "GeoJSON com propriedades da parcela",
                    "validation_criteria": ["Coerência com usos do solo", "Cumprimento das densidades", "Alineação com planos de ordenamento"],
                },
                "compliance": {"decreto_lei_96_2019": ["Art. 15", "Art. 22"], "rgpd": ["Art. 6.1(e)"]},
            }
        else:
            procedure = {
                "name": "Validación con SIGPAC-Extremadura",
                "legal_basis": ["Orden de 12 de marzo de 2021", "Ley 3/2023 de Montes de Extremadura"],
                "steps": [
                    {"name": "Solicitud de validación", "description": "El propietario solicita validación de prácticas forestales en su parcela.", "implementation": "Endpoint POST /api/sigpac/validate", "evidence": "backend/api/routes/sigpac.py (en desarrollo)"},
                    {"name": "Consulta a SIGPAC", "description": "El sistema consulta el SIGPAC para validar prácticas.", "implementation": "Integración con API de SIGPAC (https://sigpac.mapa.gob.es/sigpac/api)", "evidence": "backend/api/services/sigpac_service.py (stub)"},
                    {"name": "Registro del resultado", "description": "El resultado se registra en GaiaChain y se notifica al propietario.", "implementation": "Evento en GaiaChain con sigpac_validation_result", "evidence": "Transacción de ejemplo: 0xSIGPAC..."},
                ],
                "technical_details": {
                    "api_endpoint": "https://sigpac.mapa.gob.es/sigpac/api/v1/validate",
                    "auth_method": "Certificado digital (FNMT)",
                    "data_format": "GeoJSON con propiedades de la parcela (código SIGPAC, uso, superficie)",
                    "validation_criteria": [
                        "Coherencia con PORN de Extremadura",
                        "Cumplimiento de densidades de arbolado (Orden 12/03/2021)",
                        "Alineación con usos del suelo declarados en SIGPAC",
                        "Validación de prácticas de poda según Ley 3/2023 Art. 12",
                    ],
                },
                "compliance": {"ley_3_2023": ["Art. 12", "Art. 15"], "gdpr": ["Art. 6.1(e)"], "decreto_45_2020": ["Art. 3"]},
            }
        return {"procedure": procedure, "generated_at": generated_at}

    def _get_contracts_data(self, regional_scope: Dict[str, Any]) -> Dict[str, Any]:
        if self.region == "andalucia":
            owner_contract = {
                "title": "Contrato de Prestación de Servicios Forestales (Andalucía)",
                "parties": {
                    "provider": {"name": "CASTÚO-SYSTEM™ S.L.", "cif": "B10XXXXXX", "address": "C/ Tecnología, 1, 41092 Sevilla", "representative": "Carlos Martínez (Administrador)"},
                    "owner": {"name": "[NOMBRE_PROPIETARIO]", "nif": "[NIF_PROPIETARIO]", "address": "[DIRECCIÓN_PROPIETARIO]"},
                },
                "services": [
                    {"name": "Gestión de consentimientos para subvenciones forestales", "description": "Registro y gestión según Ley 2/2021 de Montes de Andalucía.", "legal_basis": ["Ley 2/2021 Art. 7", "RGPD Art. 6.1(a)"]},
                    {"name": "Generación de material educativo forestal", "description": "Creación de vídeos y documentos educativos.", "legal_basis": ["Ley 2/2021 Art. 18", "AI Act Art. 52"]},
                    {"name": "Validación con SIGPAC-Andalucía", "description": "Integración con SIGPAC para validación de prácticas.", "legal_basis": ["Orden AAA/2023 Art. 5", "Ley 2/2021 Art. 15"]},
                ],
                "obligations": {
                    "provider": ["Garantizar cumplimiento Ley 2/2021 y RGPD.", "Proporcionar acceso a los datos según Ley 2/2021 Art. 12.", "Mantener datos durante 10 años (Ley 2/2021 Art. 22)."],
                    "owner": ["Proporcionar información veraz sobre parcelas.", "Notificar cambios en 15 días.", "Cumplir prácticas validadas por SIGPAC."],
                },
                "data_protection": {"responsible": "CASTÚO-SYSTEM™", "purposes": ["Gestión subvenciones (Ley 2/2021 Art. 12).", "Material educativo (Ley 2/2021 Art. 18).", "Validación SIGPAC (Orden AAA/2023)."], "retention": "10 años (Ley 2/2021 Art. 22).", "rights": ["Acceso (RGPD Art. 15).", "Rectificación (RGPD Art. 16).", "Supresión (RGPD Art. 17).", "Portabilidad (RGPD Art. 20)."]},
                "termination": {"conditions": ["Incumplimiento.", "Finalización del plazo de 5 años (renovable).", "Decisión unilateral con 30 días de preaviso."], "data_deletion": "Datos eliminados en 30 días tras finalización, salvo obligación legal."},
                "jurisdiction": "Tribunales de Sevilla (España).",
                "applicable_law": ["Ley 2/2021 de Montes de Andalucía.", "Reglamento (UE) 2016/679 (RGPD).", "Ley Orgánica 3/2018 (LOPDGDD)."],
            }
        elif self.region == "portugal":
            owner_contract = {
                "title": "Contrato de Prestação de Serviços Florestais (Portugal)",
                "parties": {
                    "provider": {"name": "CASTÚO-SYSTEM™ Unipessoal Lda.", "cif": "5XXXXXXXX", "address": "Rua da Tecnologia, 1, 1000-001 Lisboa", "representative": "Carlos Martínez (Gerente)"},
                    "owner": {"name": "[NOME_PROPRIETÁRIO]", "nif": "[NIF_PROPRIETÁRIO]", "address": "[MORADA_PROPRIETÁRIO]"},
                },
                "services": [
                    {"name": "Gestão de consentimentos para subsídios florestais", "description": "Registo segundo Decreto-Lei n.º 96/2019.", "legal_basis": ["Decreto-Lei n.º 96/2019 Art. 8", "RGPD Art. 6.1(a)"]},
                    {"name": "Geração de material educativo florestal", "description": "Criação de vídeos e documentos educativos.", "legal_basis": ["Decreto-Lei n.º 96/2019 Art. 18", "AI Act Art. 52"]},
                    {"name": "Validação com SIGIF", "description": "Integração com SIGIF (Portaria n.º 142/2021).", "legal_basis": ["Portaria n.º 142/2021 Art. 5", "Decreto-Lei n.º 96/2019 Art. 15"]},
                ],
                "obligations": {
                    "provider": ["Garantir cumprimento do Decreto-Lei n.º 96/2019 e RGPD.", "Fornecer acesso aos dados.", "Manter dados durante 10 anos."],
                    "owner": ["Fornecer informação verídica.", "Notificar alterações em 15 dias.", "Cumprir práticas validadas pelo SIGIF."],
                },
                "data_protection": {"responsible": "CASTÚO-SYSTEM™", "purposes": ["Gestão de subsídios.", "Material educativo.", "Validação SIGIF."], "retention": "10 anos.", "rights": ["Acesso (RGPD Art. 15).", "Retificação (RGPD Art. 16).", "Apagamento (RGPD Art. 17).", "Portabilidade (RGPD Art. 20)."]},
                "termination": {"conditions": ["Incumprimento.", "Finalização do prazo de 5 anos.", "Decisão unilateral com 30 dias de pré-aviso."], "data_deletion": "Dados eliminados em 30 dias, salvo obrigação legal."},
                "jurisdiction": "Tribunais de Lisboa (Portugal).",
                "applicable_law": ["Decreto-Lei n.º 96/2019.", "Regulamento (UE) 2016/679 (RGPD).", "Lei n.º 58/2019."],
            }
        else:
            owner_contract = {
                "title": "Contrato de Prestación de Servicios Forestales (Extremadura)",
                "parties": {
                    "provider": {"name": "CASTÚO-SYSTEM™ S.L.", "cif": "B10XXXXXX", "address": "Av. de la Innovación, 1, 06800 Mérida (Badajoz)", "representative": "Carlos Martínez (Administrador)"},
                    "owner": {"name": "[NOMBRE_PROPIETARIO]", "nif": "[NIF_PROPIETARIO]", "address": "[DIRECCIÓN_PROPIETARIO]"},
                },
                "services": [
                    {"name": "Gestión de consentimientos para subvenciones forestales", "description": "Registro y gestión según Ley 3/2023 de Montes de Extremadura.", "legal_basis": ["Ley 3/2023 Art. 8", "RGPD Art. 6.1(a)"]},
                    {"name": "Generación de material educativo forestal", "description": "Creación de vídeos y documentos según Decreto 45/2020.", "legal_basis": ["Ley 3/2023 Art. 18", "AI Act Art. 52"]},
                    {"name": "Validación con SIGPAC-Extremadura", "description": "Integración con SIGPAC (Orden de 12 de marzo de 2021).", "legal_basis": ["Orden 12/03/2021 Art. 3", "Ley 3/2023 Art. 15"]},
                ],
                "obligations": {
                    "provider": ["Garantizar cumplimiento Ley 3/2023 y RGPD.", "Proporcionar acceso a los datos según Ley 3/2023 Art. 12.", "Mantener datos durante 10 años (Ley 3/2023 Art. 22)."],
                    "owner": ["Proporcionar información veraz.", "Notificar cambios en 15 días.", "Cumplir prácticas validadas por SIGPAC."],
                },
                "data_protection": {"responsible": "CASTÚO-SYSTEM™", "purposes": ["Gestión subvenciones (Ley 3/2023 Art. 12).", "Material educativo (Ley 3/2023 Art. 18).", "Validación SIGPAC (Orden 12/03/2021)."], "retention": "10 años (Ley 3/2023 Art. 22).", "rights": ["Acceso (RGPD Art. 15).", "Rectificación (RGPD Art. 16).", "Supresión (RGPD Art. 17).", "Portabilidad (RGPD Art. 20)."]},
                "termination": {"conditions": ["Incumplimiento.", "Finalización del plazo de 5 años (renovable).", "Decisión unilateral con 30 días de preaviso."], "data_deletion": "Datos eliminados en 30 días, salvo obligación legal."},
                "jurisdiction": "Tribunales de Badajoz (España).",
                "applicable_law": ["Ley 3/2023 de Montes de Extremadura.", "Reglamento (UE) 2016/679 (RGPD).", "Ley Orgánica 3/2018 (LOPDGDD).", "Decreto 45/2020."],
            }
        return {"owner_contract": owner_contract}

    def _get_audit_data(self) -> Dict[str, Any]:
        return {
            "checklists": {
                "monthly": {
                    "name": "Checklist de Auditoría Mensual",
                    "items": [
                        {"id": "AUD-001", "description": "Verificar que todos los consentimientos están registrados en GaiaChain.", "procedure": ["Consultar GaiaChain.", "Comparar con usuarios activos en Keycloak."], "evidence": ["Transacciones GaiaChain.", "Logs Wazuh (event_type:consent_update)."], "compliance": ["GDPR Art. 30", "Ley 3/2023 Art. 8"]},
                        {"id": "AUD-002", "description": "Revisar logs de acceso no autorizado (403/401).", "procedure": ["Consultar Wazuh: status_code:403 OR 401.", "Verificar justificación."], "evidence": ["Logs Wazuh/OpenSearch."], "compliance": ["ISO 27001 A.12.4.1", "GDPR Art. 32"]},
                        {"id": "AUD-003", "description": "Validar que los vídeos generados incluyen metadatos de compliance.", "procedure": ["Seleccionar 5 vídeos aleatorios de MinIO.", "Verificar compliance.gdpr y compliance.ai_act."], "evidence": ["Metadatos en MinIO.", "Transacciones GaiaChain."], "compliance": ["AI Act Art. 52", "Ley 3/2023 Art. 18"]},
                        {"id": "AUD-004", "description": "Comprobar rotación de claves en Vault.", "procedure": ["Verificar vault kv get secret/consent_service.", "Confirmar última rotación <90 días."], "evidence": ["vault_audit.log.", "backend/scripts/rotate_keys.sh"], "compliance": ["ISO 27001 A.10.1.1"]},
                        {"id": "AUD-005", "description": "Revisar integración con SIGPAC (si aplica).", "procedure": ["Verificar validaciones en GaiaChain (sigpac_validation_result).", "Validar 3 parcelas aleatorias."], "evidence": ["Transacciones GaiaChain.", "Logs Wazuh (event_type:sigpac_validation)."], "compliance": ["Ley 3/2023 Art. 15"]},
                    ],
                },
                "quarterly": {
                    "name": "Checklist de Auditoría Trimestral",
                    "items": [
                        {"id": "AUD-101", "description": "Revisión de la evaluación de riesgos AI Act.", "procedure": ["Actualizar 02.03.02_Evaluacion_Riesgos.xlsx.", "Verificar medidas de mitigación."], "evidence": ["Documento en 02.03_AI_Act_EU/.", "Acta firmada por DPO."], "compliance": ["AI Act Anexo III"]},
                        {"id": "AUD-102", "description": "Auditoría de cumplimiento con Ley 3/2023 (o equivalente regional).", "procedure": ["Revisar consentimientos con referencia a ley autonómica.", "Verificar prácticas forestales."], "evidence": ["Transacciones GaiaChain.", "Informe generate_compliance_docs.py."], "compliance": ["Ley 3/2023"]},
                        {"id": "AUD-103", "description": "Prueba de restauración de backups.", "procedure": ["Restaurar backup de MinIO en staging.", "Verificar integridad (checksums)."], "evidence": ["backup_restore.log.", "Informe de verificación."], "compliance": ["ISO 27001 A.12.3.1"]},
                        {"id": "AUD-104", "description": "Revisión de acceso a datos personales.", "procedure": ["Verificar que solo dpo y admin acceden a datos personales.", "Auditar logs de /api/consents/*."], "evidence": ["Logs Wazuh.", "Configuración Keycloak."], "compliance": ["GDPR Art. 9", "ISO 27001 A.9.1.1"]},
                    ],
                },
            },
        }

    def generate_gdpr_register(self) -> None:
        tpl = self.env.get_template("gdpr_register_template.md")
        out = tpl.render(data=self.context["gdpr"])
        (OUTPUT_DIR / "02.01.01_Registro_Actividades_Tratamiento.md").write_text(out, encoding="utf-8")
        print("[OK] Generado: 02.01.01_Registro_Actividades_Tratamiento.md")

    def generate_ai_act_assessment(self) -> None:
        tpl = self.env.get_template("ai_act_assessment_template.md")
        out = tpl.render(data=self.context["ai_act"])
        (OUTPUT_DIR / "02.03.03_AI_Act_Self-Assessment.md").write_text(out, encoding="utf-8")
        print("[OK] Generado: 02.03.03_AI_Act_Self-Assessment.md")

    def generate_ley3_compliance(self) -> None:
        tpl = self.env.get_template("ley3_compliance_template.md")
        out = tpl.render(data=self.context["ley_3_2023"])
        suffix = {"extremadura": "Ley_3_2023_Extremadura", "andalucia": "Ley_2_2021_Andalucia", "portugal": "Decreto_Lei_96_2019_Portugal"}.get(self.region, "Ley_3_2023_Extremadura")
        (OUTPUT_DIR / f"02.02.03_Gestion_Consentimientos_{suffix}.md").write_text(out, encoding="utf-8")
        print(f"[OK] Generado: 02.02.03_Gestion_Consentimientos_{suffix}.md")

    def generate_iso27001_declaration(self) -> None:
        tpl = self.env.get_template("iso27001_declaration_template.md")
        out = tpl.render(data=self.context["iso_27001"])
        (OUTPUT_DIR / "02.04.01_Declaracion_Aplicabilidad_ISO27001.md").write_text(out, encoding="utf-8")
        print("[OK] Generado: 02.04.01_Declaracion_Aplicabilidad_ISO27001.md")

    def generate_sigpac_procedure(self) -> None:
        tpl = self.env.get_template("sigpac_procedure_template.md")
        out = tpl.render(data=self.context["sigpac"], system=self.context["system"], region=self.region)
        suffix = {"extremadura": "Extremadura", "andalucia": "Andalucia", "portugal": "Portugal"}.get(self.region, "Extremadura")
        (OUTPUT_DIR / f"02.05.01_Procedimiento_SIGPAC_{suffix}.md").write_text(out, encoding="utf-8")
        print(f"[OK] Generado: 02.05.01_Procedimiento_SIGPAC_{suffix}.md")

    def generate_contracts(self) -> None:
        tpl = self.env.get_template("forest_owner_contract_template.md")
        out = tpl.render(data=self.context["contracts"], system=self.context["system"], generated_at=self.context["system"]["generated_at"])
        suffix = {"extremadura": "ES_Extremadura", "andalucia": "ES_Andalucia", "portugal": "PT"}.get(self.region, "ES_Extremadura")
        (OUTPUT_DIR / f"04.03.01_Contrato_Propietario_Forestal_{suffix}.md").write_text(out, encoding="utf-8")
        print(f"[OK] Generado: 04.03.01_Contrato_Propietario_Forestal_{suffix}.md")

    def generate_audit_checklists(self) -> None:
        tpl = self.env.get_template("audit_checklist_template.md")
        for checklist_type, checklist in self.context["audit"]["checklists"].items():
            out = tpl.render(checklist=checklist, region=self.region, generated_at=self.context["system"]["generated_at"], system=self.context["system"])
            (OUTPUT_DIR / f"06.01.01_Checklist_Auditoria_{checklist_type.capitalize()}_{self.region}.md").write_text(out, encoding="utf-8")
            print(f"[OK] Generado: 06.01.01_Checklist_Auditoria_{checklist_type.capitalize()}_{self.region}.md")

    def generate_compliance_report(self, media_id: str) -> None:
        media_data = {
            "media_id": media_id,
            "generated_at": self.context["system"]["generated_at"],
            "system": self.context["system"],
            "compliance": {"gdpr": ["Art. 6.1(a)", "Art. 30"], "ai_act": ["Art. 52"], "ley_3_2023": ["Art. 18"], "iso_27001": ["A.12.4.1"]},
            "evidence": {
                "gaiachain_tx": f"0x{media_id[:10]}...{media_id[-10:]}" if len(media_id) >= 20 else f"0x{media_id}",
                "wazuh_query": f"event_type:media_generation_* AND media_id:{media_id}",
                "storage": {"bucket": "castuo-media-eu", "object_key": f"videos/{media_id}.mp4"},
            },
        }
        tpl = self.env.get_template("compliance_report_template.md")
        out = tpl.render(**media_data)
        (OUTPUT_DIR / f"compliance_report_{media_id}.md").write_text(out, encoding="utf-8")
        print(f"[OK] Generado: compliance_report_{media_id}.md")

    def generate_all(self, media_id: str = "sd-eu-20260315-12345-67890") -> None:
        print(f"[*] Generando documentacion para {self.context['system']['regional_scope']['name']} en {OUTPUT_DIR}/")
        self.generate_gdpr_register()
        self.generate_ai_act_assessment()
        self.generate_ley3_compliance()
        self.generate_iso27001_declaration()
        self.generate_sigpac_procedure()
        self.generate_contracts()
        self.generate_audit_checklists()
        self.generate_compliance_report(media_id)
        print("\n[OK] Documentacion generada correctamente.")
        print(f"Archivos en: {OUTPUT_DIR.absolute()}")


if __name__ == "__main__":
    import sys
    region = sys.argv[1] if len(sys.argv) > 1 else "extremadura"
    media_id = sys.argv[2] if len(sys.argv) > 2 else "sd-eu-20260315-12345-67890"
    gen = ComplianceDocGenerator(region=region)
    gen.generate_all(media_id)
