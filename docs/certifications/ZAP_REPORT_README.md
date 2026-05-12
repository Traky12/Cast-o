# Informe ZAP — Evidencia auditoría ISO 27001

Para generar el reporte HTML de OWASP ZAP (evidencia 0 críticas):

```cmd
REM Con ZAP corriendo en localhost:8080
curl -o docs/certifications/ZAP_REPORT_2026-03-16.html "http://localhost:8080/other/core/other/htmlreport/"
```

O desde la API ZAP (si el endpoint difiere):

```cmd
curl -o docs/certifications/ZAP_REPORT_2026-03-16.html "http://localhost:8080/OTHER/core/other/htmlreport/"
```

Screenshot recomendado: http://localhost:8080 → H10 ✅ (0 críticas) para incluir en paquete Applus+.
