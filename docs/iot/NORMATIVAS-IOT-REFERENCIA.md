# Normativas y normas citadas en proyectos IoT agrícola (referencia)

**Uso:** mapa orientativo para documentación de proyecto; **no** implica que el repo implemente cada exigencia.

| Ámbito | Referencia típica | Nota en CASTUO-System |
|--------|-------------------|------------------------|
| Datos personales / telemetría | RGPD 2016/679, LOPDGDD | DPIA: `docs/legal/DPIA-CASTUO-SYSTEM.md` |
| MQTT | ISO/IEC 20922 | Cliente opcional en `iot/mqtt_handler.py` |
| Bus de campo (CAN) | ISO 11898 | **No** hay `backend/iot/protocols/modbus.py` genérico en el árbol |
| pH / EC (concepto calidad agua / nutriente) | UNE-EN 12932, RD 506/2013 | Validación en firmware/código **a definir** con hardware real |
| Riego | UNE 50510, RD 169/2021 | Documentación de explotación, no solo software |
| Ozono / biocidas | UNE 400-201-94, RD 106/2022, (UE) 528/2012 | Procedimiento de seguridad y ocupación de espacios |
| Ósmosis inversa | UNE-EN 14898, RD 140/2003 | Membranas y agua: mantenimiento y análisis de laboratorio |
| Fertilizantes / UE 2019/1009 | Reglamento (UE) 2019/1009 | Trazabilidad de aplicación en expediente |
| Agrovoltaica / PAC | (UE) 2021/2115, convocatorias CCAA | Ver `docs/funding/PAC2040-Criterios.md` (narrativo) |

**Enlaces:** EUR-Lex y BOE para textos auténticos; evitar copiar “texto completo” en markdown sin proceso de mantenimiento.

---

**Relación:** [IOT-MARCO-REPOSITORIO.md](./IOT-MARCO-REPOSITORIO.md)
