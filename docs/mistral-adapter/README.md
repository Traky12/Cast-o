# Mistral-CASTÚO Adapter — Documentación

Documentación pública del adapter para **Mistral AI** integrado en **CASTÚO-SYSTEM™**.

## URLs

- **https://docs.castuo-system.com/mistral-adapter/** ← Cliente-facing (dominio propio)
- **https://castuo-system.github.io/mistral-adapter/** ← Backup listo (GitHub Pages LIVE en ~2 min)

## Estructura

| Archivo | Contenido |
|---------|-----------|
| [index.md](index.md) | Vista general, diagramas Mermaid, casos de uso, badges |
| [features.md](features.md) | Características y tabla resumen |
| [installation.md](installation.md) | Instalación en 2 minutos |
| [usage.md](usage.md) | Uso básico y ejemplos de código |
| [api-reference.md](api-reference.md) | Clases, métodos y configuración |
| [compliance.md](compliance.md) | Cumplimiento normativo (GDPR, AI Act, PAC 2040) |
| [examples.md](examples.md) | Ejemplos para Sabionda Educa |
| [faq.md](faq.md) | Preguntas frecuentes (tokens, errores, rate limit) |
| [roadmap.md](roadmap.md) | Próximos pasos y GaiaChain 2.0 |
| [changelog.md](changelog.md) | Cambios por versión |

Todos los enlaces son **relativos** (`features.md`, `usage.md`, etc.) para evitar 404 entre GitHub Pages y dominio propio.

## Publicar con MkDocs (recomendado)

En la **raíz del repo** está `mkdocs.yml` con:

- `site_name: CASTÚO-Mistral Adapter`
- `site_url: https://docs.castuo-system.com/mistral-adapter/`
- `docs_dir: docs/mistral-adapter`
- Tema **Material** e idioma **es**
- Navegación con todas las secciones (incl. FAQ, Roadmap, Changelog)

**Test local:**

```bash
pip install -r requirements-docs.txt
mkdocs serve
```

**Producción (1 línea):**

```bash
mkdocs gh-deploy --clean --message "Deploy v1.0.0 docs $(git rev-parse --short HEAD)"
```

### Checklist tras `gh-deploy`

1. ✅ Dependencias pip cargadas (`requirements-docs.txt`)
2. ✅ `mkdocs build` → carpeta `site/` generada
3. ✅ Rama `gh-pages` creada/actualizada
4. ✅ Push automático a GitHub
5. ✅ **https://castuo-system.github.io/mistral-adapter/** LIVE en ~1–3 min

### Tiempos

| Etapa | Tiempo |
|-------|--------|
| GitHub Pages live | 1–3 minutos |
| DNS propagación | 5–30 min (Cloudflare), hasta 48 h (otros) |
| HTTPS automático (Enforce HTTPS) | ~1 hora |

### Test enlaces

Usar **siempre enlaces relativos** (nunca `vscode-file://`). Tras publicar, comprobar:

- [Introducción](index.md) ✓
- [Características](features.md) ✓
- [FAQ](faq.md) ✓
- [Changelog](changelog.md) ✓

El plugin `git-revision-date-localized` muestra la fecha de última modificación por archivo. El plugin `search` viene con Material. Para el dominio propio, configura DNS según la sección siguiente.

---

## Configuración DNS recomendada (docs.castuo-system.com)

### Opción 1: CNAME (más simple)

| Campo        | Valor                      |
|-------------|----------------------------|
| **Tipo**    | CNAME                      |
| **Nombre/Host** | docs                    |
| **Valor/Puntos a** | castuo-system.github.io. |
| **TTL**     | 3600 (o automático)        |

### Opción 2: A Records (más robusta)

| Tipo | Nombre/Host | Valor           | TTL  |
|------|-------------|-----------------|------|
| A    | docs        | 185.199.108.153 | 3600 |
| A    | docs        | 185.199.109.153 | 3600 |
| A    | docs        | 185.199.110.153 | 3600 |
| A    | docs        | 185.199.111.153 | 3600 |

### Por proveedor DNS

| Proveedor   | Panel                         | Pasos |
|------------|--------------------------------|-------|
| **Cloudflare** | DNS → Add Record            | Type: CNAME, Name: docs, Target: castuo-system.github.io, Proxy: **DNS only** |
| **Namecheap**  | Domain List → Manage → Advanced DNS | Type: CNAME Record, Host: docs, Value: castuo-system.github.io. |
| **GoDaddy**    | DNS Management                | Type: CNAME, Name: docs, Value: castuo-system.github.io. |
| **OVH / 1&1**  | Zona DNS                     | Sous-domaine: docs, Type: CNAME, Cible: castuo-system.github.io. |
| **Hetzner**    | DNS Console                  | Record Type: CNAME, Name: docs, Value: castuo-system.github.io. |

### GitHub Pages (después del DNS)

1. **Repo → Settings → Pages** → Custom domain: `docs.castuo-system.com`
2. Guardar. **[Enforce HTTPS]** se activa tras ~1 h (automático).

### Resumen: dominio propio en 2 pasos

1. **DNS:** `docs.castuo-system.com` → `castuo-system.github.io.` (CNAME).
2. **Settings → Pages** → Custom domain: `docs.castuo-system.com`.

### Verificación

```bash
# Comprobar DNS
dig docs.castuo-system.com
nslookup docs.castuo-system.com

# Test final
curl -I https://docs.castuo-system.com/mistral-adapter/
```

---

## Deploy + dominio: resumen

**Deploy:**

```bash
mkdocs gh-deploy --clean --message "Deploy v1.0.0 docs $(git rev-parse --short HEAD)"
```

**Dominio propio (2 pasos):**

1. **DNS CNAME:** `docs.castuo-system.com` → `castuo-system.github.io.`
2. **Settings → Pages** → Custom domain: `docs.castuo-system.com`

Tras eso: **https://castuo-system.github.io/mistral-adapter/** listo en ~2 min; dominio propio cuando DNS propague y Enforce HTTPS (~1 h).

---

## Checklist final

| Elemento | Estado |
|----------|--------|
| mkdocs.yml (plugins + nav completa) | ✅ |
| Badges en index.md | ✅ |
| README.md actualizado (comandos + DNS) | ✅ |
| installation.md (sección MkDocs) | ✅ |
| Enlaces relativos (todos funcionales) | ✅ |
| FAQ / Roadmap / Changelog implementados | ✅ |
| requirements-docs.txt | ✅ |
| Enlaces: usar `index.md` (no vscode-file) | ✅ |

## Código del adapter

El código está en el repo principal CASTÚO-SYSTEM:

- **Módulo:** `api/mistral_castuo_adapter.py`
- **Doc técnica:** [docs/ai/Mistral-CASTUO-Adapter.md](../ai/Mistral-CASTUO-Adapter.md)
