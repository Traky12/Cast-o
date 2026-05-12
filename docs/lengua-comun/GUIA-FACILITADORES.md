# 🎓 GUÍA PARA FACILITADORES — Talleres Lengua Común + Castúo 2040

Guía práctica para educadores, dinamizadores comunitarios y facilitadores de aula. Diseñada para funcionar **con y sin Internet**, y para sostener el aprendizaje en el territorio (agua, suelo, comunidad).

---

## 1) Preparación del taller

### Materiales

| Tipo | Descripción | Cantidad |
|------|-------------|----------|
| **Impresos** | Cómic A4 (o B/N), hoja de proyecto, certificados | 1 por participante |
| **Digitales** | Un portátil + proyector (opcional), USB con `scripts/educacion/` | 1 por taller |
| **Arte** | lápices, rotuladores, papel continuo | según grupo |
| **Opcional** | sensor de humedad (simulado o real), recipiente medidor | 1 por grupo |

### Espacio

- **Presencial**: mesas en círculo o bajo un olivo (si es posible).
- **Virtual**: una sala + pizarra colaborativa (si hay conectividad).

### Antes de empezar (checklist)

- [ ] Llevo el cómic y la plantilla imprimible.
- [ ] Tengo un plan B sin dispositivos (ver `KIT-EMERGENCIA.md`).
- [ ] He probado al menos un script:
  - [ ] `python scripts/educacion/recuperar_nucleo_castuo.py`
  - [ ] `python scripts/educacion/activar_castuo.py`

---

## 2) Dinámicas por edad (recomendación)

| Grupo | Duración | Enfoque | Actividades |
|------|----------|---------|-------------|
| **8–10** | 45 min | narrativa + arte | leer cómic + dibujar “Sabionda” + mapa de finca |
| **11–14** | 60 min | tecnología básica | ejecutar 1 script + debate “¿qué protegemos?” |
| **15+** | 90 min | ética + modificación | cambiar un `print()`/mensaje + reflexión sesgos |
| **Adultos** | 120 min | proyecto comunitario | hoja de proyecto + decisión de acción local |

---

## 3) Guion de sesión (60 min)

### 0–10 min — Apertura

- Pregunta: *“¿Qué dato de tu territorio no debería perderse nunca?”*
- Regla: la tecnología es una herramienta, no un fin.

### 10–30 min — Relato + cómic (lectura guiada)

- Lee un fragmento del relato 2040.
- Muestra viñetas 1–3.
- Identifica el conflicto: **soberanía de datos**, **agua**, **decisión comunitaria**.

### 30–45 min — Acción (script)

Ejecuta:

```bash
python scripts/educacion/recuperar_nucleo_castuo.py
```

Si no hay dispositivos: usa la versión de papel del kit emergencia.

### 45–60 min — Cierre (proyecto)

Hoja de proyecto (5 líneas):

- Objetivo
- Territorio
- Dato mínimo
- Cómo se mide sin invadir
- Primer paso esta semana

---

## 4) Evaluación (rúbrica simple)

| Criterio | 3 (Excelente) | 2 (Bien) | 1 (En desarrollo) |
|---------|----------------|----------|-------------------|
| Participación | todas las voces aparecen | participa la mayoría | participan pocos |
| Comprensión | explican con ejemplos propios | responden básico | dudas constantes |
| Aplicación | proponen un paso real | siguen instrucciones | necesitan guía total |
| Impacto | conectan con agua/suelo/comunidad | conectan parcialmente | no conectan |

---

## 5) Problemas comunes (y recuperación)

| Problema | Causa probable | Recuperación (resiliente) |
|---------|-----------------|---------------------------|
| “No funciona Python” | versión / PATH | usar kit emergencia + planificar actualización |
| “No hay internet” | conectividad | no usar red; solo material local |
| “Se pierde el hilo” | demasiada técnica | volver a metáfora: agua, suelo, comunidad |
| “Grupo tímido” | dinámica frontal | círculo + turnos cortos (30–60 s) |

---

## 6) Ejemplos de piloto (plantilla de caso)

### Cáceres (plantilla)

- Grupo: __________
- Duración: _______
- Qué funcionó: ____
- Qué ajustar: _____
- Resultado: _______

### Oaxaca (plantilla)

- Idioma(s): _______
- Material usado (kit emergencia / digital): _______
- Resultado comunitario: _______

