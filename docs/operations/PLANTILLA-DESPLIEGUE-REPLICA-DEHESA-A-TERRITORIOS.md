# Plantilla de Despliegue — Protocolo de Replica (Dehesa -> Territorios)

**Uso:** documento maestro para llevar el modelo Castuo-System desde la Dehesa a otros territorios (Valles, Zonas Costeras, Alta Montaña) manteniendo invariantes de soberania (vida -> agua -> datos) y adaptando solo lo ambiental/operativo.

---

## 0) Invariantes del sistema (NO se tocan)

Estas piezas se consideran **constitucion tecnica y etica**, por lo que deben permanecer coherentes en cualquier territorio:

- **Custodia tripartita** (Custodio de la Tierra + Guardian del Silicio + Auditor Etico).
- **Protocolo de Despertar TRL9** como secuencia formal de arranque y validacion.
- **Manual de Crisis “Tierra Firme”** como respaldo analogo/resistente.
- **Cripto-Fortaleza del repositorio**: cifrado en reposo de documentos criticos y lacre digital.
- **Principio de continuidad**: si falla lo digital, debe existir ruta analoga (sin interrumpir la vida del territorio).

---

## 1) Variables de territorio (SI se adaptan)

Cada territorio debe rellenar su **Ficha de Territorio** para parametrizar:

- **Energia disponible y estrategia de resiliencia** (primaria/respaldo/emergencia).
- **Gestion de agua y riesgos hidrologicos** (inundacion, salinidad, congelacion, humedad excesiva).
- **Condiciones de comunicaciones** (linea de vista, interferencias, clima, potreto de saltos).
- **Ecosistema de hardware y materiales** (corrosion salina, microclimas, temperatura).
- **Marco legal aplicable y requisitos de cumplimiento** (proteccion de datos, consentimientos, seguridad).

---

## 2) Ficha de Territorio (rellenar antes de cualquier despliegue)

Completar y archivar (cifrar si contiene detalles sensibles):

| Campo | Valles | Zonas costeras | Alta montana | Valor real (a rellenar) |
|------|---------|----------------|---------------|---------------------------|
| Tipo de clima | | | | |
| Altitud (m) | | | | |
| Riesgo principal | inundacion | salinidad/corrosion | congelacion/heladas | |
| Agua | rios/escorrentia | humedad + salobre | nieve + deshielo | |
| Energia primaria | | | | |
| Energia respaldo | | | | |
| Energia emergencia | | | | |
| Conectividad | | | | |
| Linea de vista para enlaces | | | | |
| Stakeholders (custodios locales) | | | | |
| Pais / marco legal | | | | |
| Ubicacion de caja fuerte externa | | | | |

**Entregable recomendado:** `docs/territorios/<TIPO>/FICHA-TERRITORIO-<NOMBRE>.md` (cifrada si aplica).

---

## 3) Adaptaciones por tipologia

### 3.1 Valles (altas posibilidades hidricas, riesgo de inundacion)

**Objetivo:** priorizar drenaje, control de humedad y comunicaciones robustas en sombras orograficas.

- Energia: revisar viabilidad de fuentes hidrogeno/biomasa con redundancia; asegurar transiciones de energia sin microcortes.
- Agua: instalar barreras contra anegamiento y definir estrategia de purga/aislamiento para sensores.
- Comunicaciones: planificar rutas de salto (mesh) para superar sombras del valle y mantener handshake cifrado.
- Hardware: evitar puntos de corrosion por condensacion; controlar punto de rocio en gabinetes.

### 3.2 Zonas costeras (sal, humedad, corrosion y agresividad atmosferica)

**Objetivo:** blindar contra atmosfera marina y asegurar continuidad operacional.

- Agua: definir control de salinidad (evitar acumulacion en intercambiadores y lineas).
- Energia: priorizar almacenamiento y protecciones anti-corrosion; garantizar aislamiento de componentes sensibles.
- Comunicaciones: aprovechar mayor linealidad hacia el mar (si existe), pero preparar contingencia por bruma/condensacion.
- Hardware: recubrimientos anticorrosion; juntas selladas; inspeccion programada.

### 3.3 Alta montana (temperatura extrema, nieve/hielo, mas necesidad de aislamiento)

**Objetivo:** proteger energia, almacenamiento y sensores frente a congelacion y variaciones extremas.

- Energia: asegurar resistencia a frio en baterias/emergencia; prever aislamiento termico adicional.
- Agua: gestionar deshielo y posibles variaciones de caudal; definir estrategia para evitar cristalizacion en conducciones.
- Comunicaciones: aprovechar vistas altas para line-of-sight, pero planificar relays por tormenta/nieve.
- Hardware: encapsulado resistente; calor pasivo donde sea posible; mantenimiento mas frecuente.

---

## 4) Fases de despliegue (checklist de replica)

### Fase 0 — Alineamiento y gobernanza (2-4 semanas)

- Identificar Custodios locales y firmar actas de gobernanza (mismo esquema de custodia tripartita).
- Definir y rellenar la **Ficha de Territorio**.
- Generar plan legal de cumplimiento (proteccion de datos, seguridad, y reglas locales aplicables).
- Asegurar que el **Manual de Crisis** existe en su forma fisica y que la caja fuerte externa esta identificada.

**Criterio de bloqueo:** no iniciar Fase 1 si faltan custodios y ficha basica de territorio.

### Fase 1 — Staging y validacion (auditoria tecnica y Sabionda)

- Desplegar un entorno de staging equivalente (igual arquitectura de kernel, con overlay/parametrizacion del territorio).
- Ejecutar pruebas de seguridad y verificacion de integridad.
- Activar el flujo de sellado de lacre digital: versionar y firmar cambios de documentos criticos.
- Generar evidencias de cumplimiento (documentacion y registros).

**Criterio de bloqueo:** no pasar a piloto si el sistema no supera health-check TRL9 en entorno aislado.

### Fase 2 — Piloto de campo (sensores + demostrador operacional)

- Instalar sensores y nodos segun condiciones del territorio (agua/energia/comunicaciones).
- Realizar calibracion inicial y registro de integridad (sin exponer datos sensibles).
- Ejecutar simulacion gemelo local y validar recomendaciones operativas.
- Empezar formacion de Escuela Rural 4.0 y adaptar contenido educativo a cultura local.

### Fase 3 — Activacion TRL9 y apertura controlada

- Ejecutar el **Protocolo de Despertar TRL9** en modo pilot (custodia tripartita).
- Probar ruta analoga:
  - confirmacion de ubicacion del manual,
  - confirmacion de que existe ejecucion “manual” sin depender de red.
- Activar comunicacion OMEGA-LINK en modo de prueba (handshake cifrado).

**Criterio de bloqueo:** si no hay ruta analoga verificable, no se considera “operacion real”.

### Fase 4 — Operacion continua y escalado

- Activar dashboards y KPIs.
- Programar re-auditoria y rotacion de claves.
- Replicar nodos y ampliar coverage (mesh / sensores / automatizacion).

---

## 5) Entregables por replica (lo que debe terminar existiendo)

- **Ficha de Territorio** (cifrada si contiene detalles sensibles).
- **Plan de despliegue local** (basado en esta plantilla).
- **Evidencias de staging** (pruebas de seguridad + integridad + registros).
- **Activacion TRL9** documentada (log/resumen para Sabionda).
- **Manual de Crisis fisico** en caja fuerte externa + version digital (si aplica, cifrada con Cripto-Fortaleza).
- **Paquete educativo local** (traduccion/adaptacion cultural + guia facilitadores).
- **Registro de lacre digital** (firma de cambios y trazabilidad).
- **KPI report inicial** y plan de auditoria trimestral.

---

## 6) Plantillas a copiar y rellenar (mapa rapido)

- Mantener invariantes (copiar “referencia”, no “cambiar contenido”):
  - `docs/security/PROTOCOLO-DESPERTAR-V2-HARDENED.md`
  - `docs/operations/MANUAL-CRISIS-TIERRA-FIRME.md`
  - `docs/security/REPOSITORIO-CRIPTO-FORTALEZA.md`

- Fichas de territorio iniciales (ya creadas):
  - `docs/territorios/valles/FICHA-TERRITORIO-VALLES.md`
  - `docs/territorios/costa/FICHA-TERRITORIO-COSTA.md`
  - `docs/territorios/alta-montana/FICHA-TERRITORIO-ALTA-MONTAÑA.md`

- Crear variantes territoriales (cambiar parametros):
  - `docs/territorios/<TIPO>/FICHA-TERRITORIO-<NOMBRE>.md`
  - `docs/territorios/<TIPO>/PLAN-TRABAJO-<NOMBRE>.md`
  - `docs/territorios/<TIPO>/RUNBOOK-OPERATIVO-<NOMBRE>.md` (con KPIs locales y calendario de mantenimientos)

---

## 7) Criterios TRL9 de entrada (blockers finales)

No se considera “Replica lista” si falta cualquiera:

- Manual de crisis verificable fisicamente.
- Protocolo de Despertar TRL9 ejecutable con custodia tripartita.
- Evidencia de cifrado en reposo de documentos criticos (Cripto-Fortaleza operativa).
- Plan de comunicaciones OMEGA-LINK adaptado (al menos un modo de contingencia).
- KPI basicos iniciales y calendario de auditoria.

