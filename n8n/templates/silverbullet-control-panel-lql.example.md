# Panel de control — alertas IA (SilverBullet)

> **Aviso:** sintaxis de consultas depende de la **versión** de SilverBullet. Valida en https://silverbullet.md/ antes de producción.
>
> El Trillizo escribe `#ia-decision` y, si el payload trae `tags`, una línea **Etiquetas:** con `#sector-…` para filtrado por texto.

## Vista global sugerida (ajustar a tu build)

```query
# Ejemplo orientativo — puede requerir cambios según SB
page
where contains(text, "#ia-decision") and contains(text, "CRITICAL")
render each "snippets/alerta-agro"
order by lastModified desc
limit 20
```

Copia a tu space (p. ej. `Control-Panel.md` en `cerebros/auditoria/`).
