# Políticas de cumplimiento v2.1 — CASTÚO-SYSTEM™

## 1. Políticas de seguridad

### 1.1. Rotación de claves

- **Frecuencia**: Mensual (configurable en `rotate_pqc_keys.py`).
- **Algoritmos**: Kyber-1024 (KEM) + Dilithium-5 (firmas).
- **Registro**: Eventos en GaiaChain con:
  - Timestamp.
  - Hash de claves antiguas/nuevas.
  - Firma digital del agente.

### 1.2. Matriz de riesgos actualizada

| Riesgo                          | Impacto | Probabilidad | Control mitigante                 | Normativa relacionada   |
|---------------------------------|---------|--------------|-----------------------------------|--------------------------|
| Compromiso de claves PQC        | Alto    | Bajo         | Rotación automática + HSM         | ISO 27001:A.10.1.1       |
| Ataque a Federated Learning     | Alto    | Medio        | Validación de hash + Z-score      | EU AI Act:Anexo IV       |
| Incumplimiento normativo        | Alto    | Medio        | OPA + registros en GaiaChain      | GDPR:Art.30              |

## 3. Políticas de Federated Learning con Cifrado Homomórfico (HE)

### 3.1. Cifrado homomórfico

- **Esquema**: CKKS (TenSEAL) con `poly_modulus_degree=8192` y `coeff_mod_bit_sizes=[60,40,40,60]`.
- **Nivel de seguridad**: 128 bits (post-cuántico).
- **Validación**: Modelos cifrados se verifican con hash (integridad), detección de outliers (DBSCAN) y registro en GaiaChain.

### 3.2. Proceso de agregación

1. **Cifrado**: Cada nodo cifra sus pesos locales con CKKS.
2. **Agregación**: Suma de vectores cifrados en el coordinador.
3. **Promedio**: División cifrada por número de participantes.
4. **Descifrado**: Solo el coordinador descifra el resultado final.
5. **Registro**: Pasos registrados en GaiaChain (timestamp, hash, firma del coordinador).

### 3.3. Métricas de rendimiento

| Métrica             | Objetivo | Alerta   |
|---------------------|----------|----------|
| Tiempo de agregación| &lt;50 ms | &gt;100 ms |
| Uso de memoria      | &lt;200 MB | &gt;500 MB |
| Precisión           | &gt;99,9 % | &lt;99,5 % |
| Tasa de outliers    | &lt;0,1 % | &gt;0,5 % |

### 3.4. Cumplimiento normativo

| Requisito           | Normativa          | Implementación                    |
|---------------------|--------------------|-----------------------------------|
| Protección de datos | GDPR:Art.25        | Cifrado homomórfico + DBSCAN     |
| Transparencia       | EU AI Act:Anexo IV | Registros en GaiaChain           |
| Control de acceso   | ISO 27001:A.9.1.1  | Autenticación mútua TLS 1.3       |
| Registro actividades| GDPR:Art.30        | Eventos en GaiaChain              |
