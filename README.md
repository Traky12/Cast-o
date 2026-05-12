# 🚀 **CASTÚO-SYSTEM™ v3.1   FoodLab Production**
**Plataforma SaaS de agricultura de precisión para CTAEX** | **TRL9 Certificado** | **IA Soberana EU**

---
[![Deploy Status](https://img.shields.io/badge/Deploy-Online-brightgreen)](https://api.castuo-system.cloud/health)
[![CI/CD](https://img.shields.io/badge/CI%2FCD-Passing-brightgreen)](https://github.com/Traky12/Castuo-System/actions)
[![TRL](https://img.shields.io/badge/TRL-9-blue?style=for-the-badge)](https://github.com/Traky12/Castuo-System/wiki/TRL-Certification)
[![License](https://img.shields.io/badge/License-MIT-yellow)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.11-blue)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109.0-green)](https://fastapi.tiangolo.com/)

---

## 📌 **Descripción General**
**CASTÚO-SYSTEM™ v3.1** es una **plataforma SaaS de agricultura de precisión** diseñada para el **programa FoodLab de CTAEX**, especializada en:
- 🌱 **Cultivos hidropónicos agrovoltaicos** (microbrotes, cannabis medicinal regulado por **RD 903/2025**).
- 🤖 **Automatización inteligente** con **SABIONDA + LangGraph** (agente autónomo con rollback Saga).
- 🔗 **Trazabilidad inmutable** mediante **GaiaChain** (blockchain soberana **eIDAS compliant**).
- 📡 **Integración IoT** con **ESP32, Raspberry Pi 4, MQTT y LoRaWAN**.
- ☁️ **Infraestructura cloud** en **Hetzner K8s** (3 réplicas, HPA 3–10, PVC 10Gi).
- 📊 **Monitorización avanzada** con **Prometheus + Grafana** (10 paneles, alertas K8s).

**🔹 Casos de uso principales (FoodLab):**
- Monitoreo en tiempo real de **pH, EC, humedad, temperatura y luminosidad**.
- Control automático de **electroválvulas** para regulación de pH y nutrición.
- Generación de **QR codes con trazabilidad blockchain** para auditorías (AEMPS, CTAEX).
- **Alertas inteligentes** (Telegram/WhatsApp/Email) basadas en umbrales configurables.
- **Misiones de drones** para fotogrametría y monitoreo (Dronica + CASTUO-Gate).
- **Validación de lotes** con **blockchain + PDF + QR** (`/api/v1/skills/validar_lote`).

---

## 🏗️ **Arquitectura Global**
```mermaid
graph TD
    subgraph IoT["🌱 Capa IoT (Finca)"]
        A[ESP32 Sensores] -->|MQTT| B[CASTUO-Gate]
        A2[Drones (Dronica)] -->|MQTT| B
        B -->|MQTT Bridge| C[Mosquitto]
    end
    subgraph Cloud["☁️ Capa Cloud (Hetzner K8s)"]
        C -->|MQTT/HTTP| D[FastAPI Backend]
        D --> E[PostgreSQL + TimescaleDB]
        D --> F[Redis]
        D --> G[LangGraph / SABIONDA]
        D --> H[n8n Workflows]
        H -->|Alertas| I[Telegram/WhatsApp/Email]
        D --> J[Frontend SPA]
        D --> K[WordPress Plugin]
    end
    subgraph Blockchain["🔗 Capa Blockchain"]
        D --> L[GaiaChain]
        L -->|Trazabilidad| M[Smart Contracts]
        M -->|Certificación| N[QR Codes + PDF]
    end
    subgraph Monitoring["📊 Capa Monitoring"]
        D --> O[Prometheus]
        O --> P[Grafana]
    end
    style IoT fill:#e6f7ff
    style Cloud fill:#fff2e6
    style Blockchain fill:#e6ffe6
    style Monitoring fill:#f0fff4
