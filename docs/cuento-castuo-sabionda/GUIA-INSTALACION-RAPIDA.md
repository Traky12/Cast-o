# Guía de Instalación Rápida: De la Dehesa al Código

Para docentes, padres y dinamizadores de la **Escuela Rural 4.0**. Permite ejecutar los cuentos interactivos y simuladores del Castúo-System en cualquier ordenador (Windows, Mac o Linux) sin complicaciones técnicas.

---

## 1. Requisitos previos (El Kit del Guardián)

Solo necesitas **Python**, el lenguaje en el que habla Sabionda.

- **Descarga:** [python.org](https://www.python.org/) — instala la versión más reciente (3.x).
- **Windows:** Durante la instalación, marca la casilla **"Add Python to PATH"** para poder usar `python` desde la terminal.

Comprueba que funciona abriendo una terminal y escribiendo:

```bash
python --version
```

Debe aparecer algo como `Python 3.12.x`.

---

## 2. Preparación del terreno (Descarga)

- Descarga el bundle **CASTUO_GOLD_V1.zip** (o clona/descarga el repositorio Castuo-System).
- Descomprímelo en una carpeta (por ejemplo `Castuo-System`).

Estructura esperada:

```
Castuo-System/
├── scripts/
│   └── educacion/
│       ├── activar_castuo.py
│       ├── sensor_castuo.py
│       └── recuperar_nucleo_castuo.py
└── docs/
    └── cuento-castuo-sabionda/
```

---

## 3. ¡A jugar! (Ejecución de scripts)

Abre una **terminal** (o "Símbolo del sistema" en Windows, "Terminal" en Mac/Linux) y sitúate en la carpeta de los scripts:

```bash
cd Castuo-System/scripts/educacion
```

### A. Activar el tesoro de Castúo

Cuando los niños hayan completado el **Mapa del Tesoro** (juego de pistas físico), ejecuta:

```bash
python activar_castuo.py
```

**Qué pasará:** Sabionda hará 3 preguntas sobre el cuento. Si aciertan, verán el mensaje de victoria y los datos del NFT simulado (en Windows puede sonar un pitido).

### B. Escuchar a la tierra (Simulador de sensor)

Para entender el riego inteligente en el olivar:

```bash
python sensor_castuo.py
```

**Qué pasará:** Aparecerán lecturas de humedad simuladas. Si el valor es bajo, el sistema avisará: *"¡Riega ya!"*.

### C. Recuperar el núcleo (12–16 años)

Para el relato **CASTÚO 2040** (cyberpunk rural), juego de terminal:

```bash
python recuperar_nucleo_castuo.py
```

Comandos: `ayuda`, `infectar`, `copiar` (x5), `escapar`. Objetivo: recuperar el núcleo antes de que se acabe el tiempo.

---

## 4. Arquitectura pedagógica (Flujo del aprendizaje)

El aprendizaje en Castúo-System sigue un flujo circular: la tecnología como extensión de la naturaleza.

| Fase | Actividad | Contenido |
|------|-----------|-----------|
| **Inspiración** | El cuento | Leer sobre Castúo y Sabionda. La tecnología como magia con reglas. |
| **Exploración** | El mapa | Salir al campo a buscar los 5 tesoros (conceptos de ingeniería). |
| **Validación** | El script | Usar el código para confirmar lo aprendido y obtener la recompensa digital. |
| **Aplicación** | El sensor | Entender que los datos ayudan a cuidar el medio ambiente. |

---

## 5. Certificación del Guardián Cuántico

Al finalizar, cada niño habrá interactuado con:

- **Algoritmos:** en las preguntas del quiz (`activar_castuo.py`).
- **Datos:** en las lecturas del sensor (`sensor_castuo.py`).
- **Criptografía:** al entender qué es un NFT y un sello de identidad (certificado, libro de secretos).

---

## 6. Resolución de problemas

| Problema | Solución |
|----------|----------|
| `python` no reconocido (Windows) | Reinstala Python marcando "Add Python to PATH", o usa `py activar_castuo.py`. |
| Error al ejecutar el script | Comprueba que estás en `scripts/educacion` y que el archivo existe. |
| En Mac/Linux: "Permission denied" | Ejecuta `chmod +x activar_castuo.py` si quieres poder lanzarlo con `./activar_castuo.py`. |

---

## Sello de cierre (Sabionda)

*Con esta guía, el ecosistema educativo Castúo-System V1.0 queda enlazado de punta a punta: del cuento al código, del mapa al diploma.*

- **Estado del ecosistema:** TOTAL_HARMONY_V1  
- **Bundle de referencia:** CASTUO_GOLD_V1.zip (raíz del proyecto)

*Que el viento de la dehesa sople siempre a favor de este código.*

> **Última inscripción (Log de Sabionda)**  
> *"El código es libre, la tierra es soberana y el futuro es cuántico. Castúo-System: Despliegue completado."*
