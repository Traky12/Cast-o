# GUÍA DE BOTS COMERCIALES PARA FORESTOWNERSHIPTOKEN

## 1. Arquitectura

Los bots comerciales se integran con Sabionda Omega para:

- Generar ofertas personalizadas (madera, carbono, subvenciones).
- Optimizar negociaciones usando aprendizaje reforzado.
- Fidelizar clientes con recomendaciones basadas en datos.

## 2. Bots implementados

### 2.1. Bot de Ofertas

- Endpoint: `POST /generate-offer`
- Entrada:

```json
{
  "token_id": 1,
  "parcel_data": {
    "area": 10000,
    "certifications": ["PEFC", "FSC"],
    "tree_species": ["Quercus ilex"],
    "carbon_sequestered": 5000
  }
}
```

- Salida (ejemplo):

```json
{
  "carbon_credit_offer": {"tonnes": 5, "total_value": 250},
  "wood_sale_offer": {"species_offers": {}, "total_wood_value": 1200},
  "subsidy_optimization": {"total_value": 650},
  "confidence": 0.95
}
```

### 2.2. Bot de Negociación

- Endpoint: `POST /negotiate`
- Modelo: aprendizaje reforzado (Q-Learning) sobre precios de madera.
- Feedback: `POST /update-negotiation-knowledge` para ajustar la exploración y aprender de negociaciones reales.

### 2.3. Bot de Fidelización

- Endpoint: `POST /recommend-actions`
- Modelo: clustering (K-Means) para segmentar clientes.
- Feedback: `POST /update-loyalty-model` para reentrenar segmentos periódicamente.

## 3. Integración con Sabionda Omega

- Orquestador: `sabionda_integration/commercial_bots.py`
- Endpoint principal: `POST /orchestrate/commercial-offer`
- Feedback unificado: `POST /update-commercial-knowledge`

## 4. Despliegue

### 4.1. Requisitos

| Componente   | Versión  |
|-------------|----------|
| Python      | 3.8+     |
| FastAPI     | 0.95.0   |
| Docker      | 20.10+   |
| scikit-learn| 1.0.2    |
| numpy       | 1.22.0   |

### 4.2. Pasos

1. Construir imágenes Docker:

```bash
docker build -t registry.castuo-system.com/forestownershiptoken/offer-bot:latest -f bots/Dockerfile.offer .
```

2. Desplegar con Ansible:

```bash
ansible-playbook -i inventory/production.ini production_deploy.yml --vault-password-file ~/.vault_pass
```

3. Verificar servicios:

```bash
curl https://api.juntaextremadura.es/commercial/orchestrate/commercial-offer
```

## 5. Aprendizaje continuo

- Feedback de usuarios registrado en JSON (`feedback_log.json`, `negotiation_feedback.json`, `loyalty_feedback.json`).
- Reentrenamiento de modelos cada cierto número de feedbacks o de forma mensual (job programado).
- Métricas clave:
  - Tasa de aceptación de ofertas.
  - Ingresos adicionales por cliente.
  - Retención de clientes.

## 6. Ejemplo de uso

```python
import httpx
import asyncio


async def get_commercial_offer():
  async with httpx.AsyncClient() as client:
    response = await client.post(
      "https://api.juntaextremadura.es/commercial/orchestrate/commercial-offer",
      json={
        "token_id": 1,
        "parcel_data": {
          "area": 10000,
          "certifications": ["PEFC"],
          "tree_species": ["Quercus ilex"],
          "carbon_sequestered": 5000
        },
        "client_id": "CLI-001",
        "buyer_profile": "equilibrado"
      },
    )
    print(response.json())


if __name__ == "__main__":
  asyncio.run(get_commercial_offer())
```

