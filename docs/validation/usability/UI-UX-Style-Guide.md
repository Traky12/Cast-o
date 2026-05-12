# Guía de Estilo UI/UX — CASTÚO Agrovoltaic Tech

**Objetivo**: Colores, tipografía y componentes coherentes (accesibilidad WCAG 2.1 AA).

---

## Principios

- **Claridad**: Información crítica visible (lotes, certificaciones, alertas).
- **Consistencia**: Mismos patrones en web y móvil.
- **Accesibilidad**: Contraste mínimo 4.5:1 (texto normal), 3:1 (texto grande). Navegación por teclado completa.

---

## Colores (paleta base)

| Uso | Token | Hex | Contraste |
|-----|--------|-----|-----------|
| Fondo principal | `--bg-primary` | #FFFFFF | — |
| Fondo secundario | `--bg-secondary` | #F5F5F5 | — |
| Texto principal | `--text-primary` | #1A1A1A | ≥ 4.5:1 sobre #FFF |
| Texto secundario | `--text-secondary` | #5C5C5C | ≥ 4.5:1 |
| Acento / primario | `--accent-primary` | #2E7D32 | Verde (agritech) |
| Acento hover | `--accent-hover` | #1B5E20 | |
| Error / alerta | `--error` | #C62828 | |
| Éxito | `--success` | #2E7D32 | |

---

## Tipografía

- **Títulos**: Sans-serif (ej: Inter, system-ui), pesos 600–700.
- **Cuerpo**: 16px base, line-height 1.5.
- **Etiquetas y formularios**: 14px, peso 500.

---

## Componentes

- **Botón primario**: Fondo `--accent-primary`, texto blanco, padding 12px 24px, border-radius 8px.
- **Inputs**: Borde 1px, focus visible (outline 2px).
- **Tarjetas (lotes, certificados)**: Sombra ligera, border-radius 8px, padding 16px.

---

## Navegación por teclado

- Orden de tabulación lógico (formularios, menús).
- Focus visible en todos los elementos interactivos.
- No trampas de foco en modales.

---

## Referencias

- WCAG 2.1 AA: https://www.w3.org/WAI/WCAG21/quickref/
- axe DevTools para auditoría automática.
