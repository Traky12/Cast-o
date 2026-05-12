# Guía de Agentes Personalizables SABIONDA

Sistema de agentes personalizables con ética (AI Act UE), perfiles adaptables, accesibilidad y especialización agritech.

---

## 1. Modelo de datos

- **AgentEthics:** equidad, igualdad, transparencia, privacidad, sostenibilidad (0.0–1.0) y lista de cumplimiento (AI_Act_UE_2024_1689, GDPR, ISO_9001, ISO_27001).
- **AgentProfile:** agent_id, name, description, type (assistant|bot|expert|farmer|psychologist), ethics, capabilities, knowledge_areas, personality, accessibility, progress, custom_fields.
- **CustomAgent:** perfil + config (modelo, temperature, max_tokens, tools, security_level), user_relations, improvement_history, achievements, version, status (draft|active|deprecated).
- **AgritechAgent:** subclase de CustomAgent con knowledge_areas y ethics por defecto orientados a hidroponía, microgreens, blockchain e IoT; métodos `analyze_environment(sensor_data)` y `generate_certificate(batch_data)`.

---

## 2. API (prefijo `/agents`)

| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | `/agents/` | Lista todos los agentes |
| POST | `/agents/` | Crea un agente (body: name, description, type, ethics, personality, knowledge_areas, accessibility, etc.) |
| GET | `/agents/{agent_id}` | Obtiene un agente |
| PUT | `/agents/{agent_id}/config` | Actualiza configuración técnica |
| PUT | `/agents/{agent_id}/ethics` | Actualiza ética |
| PUT | `/agents/{agent_id}/personality` | Actualiza personalidad |
| POST | `/agents/{agent_id}/interact` | Registra interacción (body: user_id, feedback opcional) |
| POST | `/agents/{agent_id}/chat` | Respuesta adaptada (body: user_input, user_profile) |
| GET | `/agents/{agent_id}/progress` | Progreso (training, effectiveness, user_satisfaction) |
| POST | `/agents/{agent_id}/adapt` | Adapta con feedback y preferencias (body: feedback, user_preferences) |
| GET | `/agents/{agent_id}/improvements` | Historial de mejoras |
| POST | `/agents/{agent_id}/improvements` | Registra mejora (ImprovementTrack) |
| GET | `/agents/{agent_id}/achievements` | Logros |
| POST | `/agents/{agent_id}/achievements` | Añade logro (Achievement) |
| GET | `/agents/{agent_id}/ethics/validate` | Valida ética (valid, errors, suggestions) |
| POST | `/agents/{agent_id}/equity/check` | Evalúa equidad (body: user_profile) |
| POST | `/agents/{agent_id}/accessibility/adjust` | Ajusta accesibilidad (body: user_needs) |
| DELETE | `/agents/{agent_id}` | Elimina agente |
| POST | `/agents/agritech/create` | Crea agente agritech |
| POST | `/agents/{agent_id}/agritech/analyze` | Analiza ambiente (body: sensor_data) |
| POST | `/agents/{agent_id}/agritech/certificate` | Genera certificado (body: batch_data) |

---

## 3. Ejemplo de uso (curl)

```bash
# Crear agente
curl -X POST http://localhost:8000/agents/ \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Asistente Personal de María",
    "description": "Agente para agricultora con discapacidad visual",
    "type": "assistant",
    "ethics": {"equity": 1.0, "equality": 1.0, "sustainability": 0.9},
    "personality": {"empathy": 0.9, "patience": 0.9},
    "knowledge_areas": ["hydroponics", "accessibility"]
  }'

# Guardar agent_id de la respuesta (ej: "abc-123")

# Ajustar accesibilidad
curl -X POST http://localhost:8000/agents/abc-123/accessibility/adjust \
  -H "Content-Type: application/json" \
  -d '{"visual_impairment": true}'

# Adaptar con feedback
curl -X POST http://localhost:8000/agents/abc-123/adapt \
  -H "Content-Type: application/json" \
  -d '{
    "feedback": "Muy claro y útil, pero más detalle en explicaciones.",
    "user_preferences": {"empathy": 0.95, "precision": 0.9}
  }'

# Chat
curl -X POST http://localhost:8000/agents/abc-123/chat \
  -H "Content-Type: application/json" \
  -d '{
    "user_input": "¿Cómo ajusto el pH en microgreens de rábano?",
    "user_profile": {"accessibility_needs": {"visual_impairment": true}, "experience_level": "intermediate"}
  }'

# Validar ética
curl http://localhost:8000/agents/abc-123/ethics/validate
```

---

## 4. Frontend

- **Página:** `frontend/public/agent-creator.html`. Formulario para nombre, descripción, tipo, sliders de ética y personalidad, áreas de conocimiento y opciones de accesibilidad. Botones "Crear Agente" y "Crear Agente Agritech".
- **API base:** En local (puerto 3000) se usa `http://localhost:8000`; en producción, misma origen (proxy `/api` si aplica).

---

## 5. Servicios backend

- **AdaptabilityEngine:** Ajusta ética y personalidad según feedback (sentimiento simple) y preferencias; actualiza progreso (effectiveness, training).
- **EthicsValidator:** Comprueba umbrales mínimos de ética y normativas requeridas; sugiere mejoras.
- **EquityEngine:** Evalúa equidad (score y sugerencias); ajusta accesibilidad (visual_impairment, hearing_impairment, etc.).
- **SabiondaMaster:** Registra agentes y genera respuestas adaptadas (texto con perfil del agente y del usuario).

---

## 6. Checklist de implementación

| Paso | Acción | Verificación |
|------|--------|---------------|
| 1 | Modelos en `backend/models/agent.py` | `from backend.models.agent import CustomAgent` |
| 2 | Router en `backend/routers/agents.py` | `curl http://localhost:8000/agents/` → lista (vacía o con datos) |
| 3 | Router incluido en `main.py` | `app.include_router(agents_router)` |
| 4 | Crear agente | POST `/agents/` con body JSON → respuesta con `agent_id` |
| 5 | Adaptar | POST `/agents/{id}/adapt` con feedback y user_preferences |
| 6 | Validar ética | GET `/agents/{id}/ethics/validate` → `valid`, `errors`, `suggestions` |
| 7 | Frontend | Abrir `agent-creator.html` y crear agente |
| 8 | Agritech | POST `/agents/agritech/create` y POST `/{id}/agritech/analyze` con sensor_data |

---

## 7. Buenas prácticas

- Revisar ética con `GET /agents/{id}/ethics/validate` antes de activar.
- Ajustar accesibilidad con `POST /agents/{id}/accessibility/adjust` según necesidades del usuario.
- Monitorear progreso con `GET /agents/{id}/progress`.
- Usar `POST /agents/{id}/equity/check` para comprobar equidad en el trato.
- Documentar adaptaciones en `improvement_history` para auditoría.
