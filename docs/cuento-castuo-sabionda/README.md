# El Secreto del Olivo Cuántico: Castúo y Sabionda

Cuentos infantiles, relatos para adolescentes y actividades para explicar **CASTÚO-SYSTEM** y **Sabionda** con analogías de la dehesa, tecnología y raíces extremeñas.

**Para poner en marcha el ecosistema sin complicaciones:** [Guía de Instalación Rápida: De la Dehesa al Código](GUIA-INSTALACION-RAPIDA.md) (docentes, padres, dinamizadores Escuela Rural 4.0).

---

## Contenidos principales (guía rápida)

1. **Relato 2040**: `04-castuo-2040-rebelion-datos-verdes.md` (alias editorial: `relato-2040.md`)
2. **Cómic 6 viñetas**: `05-comic-castuo-2040.md`
3. **Lengua Común (bloque editorial)**: `../lengua-comun/README.md`
4. **Scripts Python**: `../../scripts/educacion/README.md`

## Contenido

| Documento | Público | Descripción |
|-----------|---------|-------------|
| [01-el-olivo-que-hablaba-con-las-estrellas.md](01-el-olivo-que-hablaba-con-las-estrellas.md) | Niños | Primera historia: Castúo (olivo cuántico), Sabionda (IA guardiana), certificado, libro de secretos, sello, NFT. |
| [02-el-misterio-del-aceite-cuantico.md](02-el-misterio-del-aceite-cuantico.md) | Niños | Don Braulio, Lucía, Jabalíes Digitales, escudo de encina, jamón ibérico y NFT. |
| [03-mapa-del-tesoro.md](03-mapa-del-tesoro.md) | Niños | Juego de pistas: mapa de la finca, 5 paradas, acertijos, tesoros y diploma de Guardián Cuántico. |
| [04-castuo-2040-rebelion-datos-verdes.md](04-castuo-2040-rebelion-datos-verdes.md) | 12–16 años | Relato cyberpunk rural: Extremadura 2040, resistencia de datos verdes, AgroTech vs. red CASTÚO, hacktivismo ecológico y soberanía tecnológica. |
| [05-comic-castuo-2040.md](05-comic-castuo-2040.md) | 12–16 años | Cómic (portada + 6 viñetas) + actividades para taller + puente a scripts. |
| [relato-2040.md](relato-2040.md) | Editorial | Alias para maquetación del bloque “Lengua Común” (apunta al relato 2040 principal). |
| [Lengua Común (bloque editorial)](../lengua-comun/README.md) | Docentes / comunidades | Plan de maquetación, prólogo/intro, plantilla A4 y guía para talleres/impresión. |

---

## Instrucciones rápidas (acción)

### 1) Ejecutar scripts (local)

```bash
python scripts/educacion/recuperar_nucleo_castuo.py
python scripts/educacion/activar_castuo.py
```

### 2) Copiar la imagen “Copilot” al bloque editorial (Windows PowerShell)

```powershell
Copy-Item "c:\Users\traky\OneDrive - FCI\Castuo-System\Copilot_20250703_222214.png" -Destination "c:\Users\traky\OneDrive - FCI\Castuo-System\docs\lengua-comun\assets\Copilot_20250703_222214.png"
```

### 3) Generar PDF (opcional)

```bash
pandoc docs/lengua-comun/*.md -o lengua-comun-castuo-2040.pdf --pdf-engine=weasyprint
```

## Scripts interactivos

| Script | Uso |
|--------|-----|
| `activar_castuo.py` | Al final del mapa del tesoro: mensaje de victoria, datos del NFT (simulados), mini-juego de preguntas. |
| `sensor_castuo.py` | Simulador de sensor de humedad (Castúo midiendo el agua). |
| `recuperar_nucleo_castuo.py` | Juego de terminal (12–16 años): "recuperar" el núcleo de Castúo en la sala de servidores en 10 min con comandos `infectar`, `copiar`, `escapar`. |

```bash
python scripts/educacion/activar_castuo.py
python scripts/educacion/sensor_castuo.py
python scripts/educacion/recuperar_nucleo_castuo.py
```

Requisitos: **Python 3.x** (sin dependencias extra obligatorias).

---

## Conceptos que aprenden los niños

| Tema | Explicación simple | Referencia en el cuento |
|------|--------------------|--------------------------|
| Blockchain | Un cuaderno mágico que nadie puede borrar. | Certificado de Castúo / NFT. |
| IoT | Objetos que hablan entre sí (olivos, sensores). | Castúo y sus sensores. |
| IA (Sabionda) | Un cerebro amigo que ayuda a tomar decisiones. | Sabionda analizando datos y bugs. |
| NFT | Una medalla única que demuestra que algo es especial. | Cristal dorado / certificado cuántico. |
| Ciberseguridad | Proteger los datos como se protege la finca. | Escudo de encina, seal, jamón ibérico vs Jabalíes Digitales. |
| Sostenibilidad | Cuidar la tierra para el futuro. | Castúo ahorrando agua. |

---

## Referencias al sistema real

| Elemento del cuento | En CASTÚO-SYSTEM |
|---------------------|-------------------|
| Certificado mágico | [SABIONDA-AUTH-V1.cert](../../SABIONDA-AUTH-V1.cert) |
| Libro de los secretos | [SABIONDA_FINAL_RELEASE.log](../../SABIONDA_FINAL_RELEASE.log) |
| Sello de la encina | `python scripts/seal.py --verify` o [sabionda_final_release_seal.py](../../scripts/sabionda_final_release_seal.py) |
| NFT de Castúo | [Estrategia testnet NFT](../NFT-TESTNET-STRATEGY-CASTUO-GOLD-V1.md), [contracts/nft/](../../contracts/nft/), [scripts/nft/](../../scripts/nft/) |

---

## Célula educativa "Raíces y Código"

| Concepto técnico | En el cuento | Valor educativo |
|------------------|--------------|-----------------|
| Blockchain | El Libro de los Secretos | Inmutabilidad y verdad compartida. |
| Ciberseguridad | El Escudo de Don Braulio | Protección de lo que amamos. |
| NFT / Trazabilidad | El Sello de la Bellota de Oro | Origen y autenticidad. |
| IA / Sabionda | El viento que susurra respuestas | Colaboración humano-máquina. |
| Soberanía tecnológica | CASTÚO 2040 vs. AgroTech | Datos como bien común. |

*De la dehesa al universo, con raíces y código.*
