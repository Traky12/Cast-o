# CASTÚO-SYSTEM™ v2.0 — Política de cumplimiento OPA
package castuo.compliance

default allow = false

# Acciones deben tener metadatos de cumplimiento
allow {
    input.action.type != ""
    input.metadata.normative != ""
    input.metadata.timestamp != ""
}

# Despliegue: solo staging si no es producción
allow {
    input.action.type == "deployment"
    input.metadata.normative == "ISO_27001:A.12.5.1"
    input.action.environment != "production"
}

# Auto-reparación: solo para incidentes críticos
allow {
    input.action.type == "self_healing"
    input.metadata.normative == "ISO_27001:A.16.1.1"
    input.action.severity == "critical"
}

# Actualización de modelo: debe incluir hash y score
allow {
    input.action.type == "model_update"
    input.metadata.normative == "EU_AI_Act:Anexo_IV"
    input.action.validation.hash != ""
    input.action.validation.compliance_score > 0.95
}

# Rotación de claves: solo algoritmos aprobados
allow {
    input.action.type == "key_rotation"
    input.metadata.normative == "ISO_27001:A.10.1.1"
    input.action.new_key.algorithm == "Kyber1024"
}
