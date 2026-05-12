# El Mapa del Tesoro de Castúo: La Búsqueda de los Datos Perdidos

Juego de pistas interactivas para niños. Los "exploradores cuánticos" siguen el mapa de la finca, resuelven acertijos y recuperan los 5 tesoros.

---

## Introducción: La Carta de Don Braulio

**Querido/a Explorador/a Cuántico/a:**

*"¡Los Jabalíes Digitales han vuelto! Esta mañana, Sabionda detectó que alguien robó los datos más importantes de Castúo: el certificado mágico, el libro de los secretos y el sello de la encina. Sin ellos, las aceitunas dejarán de brillar.*

*Tu misión es: seguir el mapa, resolver los acertijos en cada parada y recuperar los 5 tesoros antes de que los Jabalíes los vendan en el Mercado Negro de Bruselas. ¡Solo tú puedes salvar a Castúo!"*

— Don Braulio (y Sabionda, disfrazada de aceituna en el olivo grande).

---

## Mapa de la Finca

```
        [N]
          🌳
[O] 🏡1 ——→ 2🌱 ——→ 3💧
          |           |
          ↓           ↓
      4📡 ←——← 5🔒
        [S]
```

**Leyenda:**

- **🏡 Parada 1 — La Casa del Abuelo:** Aquí empezó todo.
- **🌳 Olivo de Castúo:** Donde todo cobra vida.
- **🌱 Parada 2 — Junto al olivo:** Raíces y código.
- **💧 Parada 3 — El Pozo de la Encina:** El agua es vida… y datos.
- **📡 Parada 4 — La Torre de las Comunicaciones:** Castúo habla con el cielo.
- **🔒 Parada 5 — El Cobertizo de los Secretos:** El último escondite.

---

## Pistas y Acertijos

### 🏡 Parada 1: La Casa del Abuelo

- **Pista:** *"Don Braulio decía: 'Lo más importante no es lo que ves, sino lo que mides'. Busca donde guardaba sus herramientas de medir."*
- **Acertijo:** *"Si el agua es a la planta lo que el certificado es al olivo, ¿dónde guardaría Don Braulio lo que no puede perder ni un solo dato?"*
- **Respuesta:** En el cajón de las herramientas de medición.
- **Tesoro:** Certificado Mágico (papel con SABIONDA-AUTH-V1.cert o dibujo).

### 🌱 Parada 2: El Olivo de Castúo

- **Pista:** *"Las raíces de Castúo guardan más que agua… ¡busca donde la tierra y el código se abrazan!"*
- **Acertijo:** *"No soy hoja, ni rama, ni aceituna. Soy el libro donde Castúo escribe su historia cada luna. ¿Dónde estoy?"*
- **Respuesta:** Debajo de las raíces del olivo (o en un hueco marcado).
- **Tesoro:** Libro de los Secretos (SABIONDA_FINAL_RELEASE.log en formato cuento o resumen).

### 💧 Parada 3: El Pozo de la Encina

- **Pista:** *"El agua es vida, pero también datos. ¡Busca donde el cubo toca el suelo!"*
- **Acertijo:** *"Si el pozo es un disco duro y el cubo es un USB, ¿dónde escondería Sabionda el backup de Castúo?"*
- **Respuesta:** Dentro del cubo del pozo (o caja con forma de cubo).
- **Tesoro:** USB con forma de aceituna o papel con referencia a seal.py / backup.

### 📡 Parada 4: La Torre de las Comunicaciones

- **Pista:** *"Desde aquí Castúo habla con los satélites. Los Jabalíes cortaron un cable… ¡busca donde la antena apunta al norte!"*
- **Acertijo:** *"No soy pájaro ni estrella, pero sin mí Castúo no transmite. Soy el puente entre la tierra y el cielo. ¿Dónde estoy escondida?"*
- **Respuesta:** Detrás de la antena parabólica (o caja marcada).
- **Tesoro:** Sello de la Encina (código QR que lleva a `scripts/seal.py --verify` o instrucción impresa).

### 🔒 Parada 5: El Cobertizo de los Secretos

- **Pista:** *"Aquí Don Braulio guardaba lo que no quería que nadie viera. ¡Busca donde el candado brilla bajo la luna!"*
- **Acertijo:** *"Si el cobertizo es un servidor y el candado es un firewall, ¿dónde escondería Sabionda el tesoro final?"*
- **Respuesta:** Dentro de una caja de madera con candado.
- **Tesoro:** NFT de Castúo (diploma dorado con el diseño del certificado cuántico).

---

## El Tesoro Final: Activar el NFT

Cuando se recuperen los 5 tesoros, "activar" el NFT leyendo en voz alta:

*"¡Por el aceite de oliva, el jamón ibérico y el código cuántico… declaramos a Castúo a salvo!"*

Luego ejecutar en el ordenador:

```bash
python scripts/educacion/activar_castuo.py
```

Sabionda (en pantalla) dirá: *"¡Lo habéis conseguido! Ahora Castúo está protegido y sus aceitunas volverán a brillar. Sois los nuevos Guardianes Cuánticos de la Dehesa."*

---

## Diploma de Guardián Cuántico

Al finalizar, entregar a cada niño:

**DIPLOMA OFICIAL DE GUARDIÁN CUÁNTICO**  
*Otorgado a:* [Nombre]  
*Por:* Salvar a Castúo de los Jabalíes Digitales  
*Habilidades:* Resolución de acertijos, trabajo en equipo con IA, protección de datos agrícolas  
*Firma:* Don Braulio y Sabionda | *Fecha:* [Día del juego]  

*"Ahora eres parte de la Red Cuántica de la Dehesa. ¡Nunca dejes de explorar!"*

---

## Guía para padres y educadores

- **Preparación:** Imprimir mapa y pistas; esconder los 5 tesoros (papeles, USBs o dibujos).
- **Duración:** 30–45 minutos.
- **Edades:** 6–10 con adulto; 10–12 pueden jugar solos.
- **Extensión:** Hablar de backup (cubo del pozo), certificados (DNI para plantas), NFT (medalla única).

## Referencias reales

| Elemento del juego | Concepto real |
|--------------------|----------------|
| Certificado mágico | SABIONDA-AUTH-V1.cert |
| Libro de los secretos | SABIONDA_FINAL_RELEASE.log |
| Sello de la encina | scripts/seal.py / sabionda_final_release_seal.py |
| USB-Aceituna | Backup de datos |
| NFT de Castúo | Token no fungible / certificado único (contracts/nft, scripts/nft) |

*En Extremadura, los tesoros no son de oro… son de aceite, datos y raíces que hablan con el futuro.*
