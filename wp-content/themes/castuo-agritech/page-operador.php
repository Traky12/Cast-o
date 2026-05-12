<?php
/**
 * Template Name: Panel Operador
 * Template Post Type: page
 *
 * Dashboard en tiempo real para operadores CASTÚO-SYSTEM™.
 * Muestra: estado de servicios, últimos lotes, alertas activas, métricas clave.
 *
 * Acceso: requiere rol editor o superior (WordPress auth).
 */

if ( ! is_user_logged_in() || ! current_user_can( 'edit_posts' ) ) {
	wp_redirect( wp_login_url( get_permalink() ) );
	exit;
}

get_header();
?>

<main class="castuo-dashboard" role="main">

  <!-- ── Cabecera ──────────────────────────────────────────────── -->
  <header class="dashboard-header">
    <div class="dashboard-header__inner container">
      <div class="dashboard-header__title">
        <h1>Panel Operador</h1>
        <span class="dashboard-header__version">CASTÚO-SYSTEM™ v3.1 · <?php echo esc_html( wp_get_current_user()->display_name ); ?></span>
      </div>
      <div class="dashboard-header__actions">
        <button class="btn btn--ghost btn--sm" id="js-refresh" aria-label="Actualizar dashboard">
          ↻ Actualizar
        </button>
        <span class="dashboard-header__timestamp" id="js-last-update">—</span>
      </div>
    </div>
  </header>

  <div class="container dashboard-grid">

    <!-- ── Tarjetas KPI ─────────────────────────────────────────── -->
    <section class="kpi-row" aria-label="Indicadores clave">
      <article class="kpi-card" id="kpi-chain">
        <span class="kpi-card__label">Blockchain</span>
        <span class="kpi-card__value" id="kpi-chain-val">—</span>
      </article>
      <article class="kpi-card" id="kpi-services">
        <span class="kpi-card__label">Servicios operativos</span>
        <span class="kpi-card__value" id="kpi-services-val">—</span>
      </article>
      <article class="kpi-card" id="kpi-lotes">
        <span class="kpi-card__label">Lotes registrados</span>
        <span class="kpi-card__value" id="kpi-lotes-val">—</span>
      </article>
      <article class="kpi-card" id="kpi-lab">
        <span class="kpi-card__label">Lab Neuromórfico</span>
        <span class="kpi-card__value" id="kpi-lab-val">—</span>
      </article>
    </section>

    <!-- ── Estado de Servicios ──────────────────────────────────── -->
    <section class="dashboard-section" aria-labelledby="services-title">
      <h2 class="section-title" id="services-title">Estado de Servicios</h2>
      <div class="services-grid" id="js-services-grid">
        <div class="services-grid__loading">Cargando servicios…</div>
      </div>
    </section>

    <!-- ── Formulario Verificar Lote ────────────────────────────── -->
    <section class="dashboard-section" aria-labelledby="verify-title">
      <h2 class="section-title" id="verify-title">Verificar Lote</h2>
      <form class="verify-form" id="js-verify-form" novalidate>
        <div class="form-row">
          <label for="op-lote-id">ID de lote</label>
          <input type="text" id="op-lote-id" name="lote_id" placeholder="LOTE-20260401-001"
                 autocomplete="off" required />
        </div>
        <div class="form-row">
          <label for="op-hash">Hash SHA-256</label>
          <input type="text" id="op-hash" name="hash"
                 placeholder="a3f8b2c1…" autocomplete="off" pattern="[a-f0-9]+" />
        </div>
        <button type="submit" class="btn btn--primary">Verificar</button>
      </form>
      <div class="verify-result" id="js-verify-result" aria-live="polite" hidden></div>
    </section>

    <!-- ── Lotes Recientes ──────────────────────────────────────── -->
    <section class="dashboard-section" aria-labelledby="lotes-title">
      <h2 class="section-title" id="lotes-title">Últimas verificaciones</h2>
      <table class="lotes-table" id="js-lotes-table">
        <thead>
          <tr>
            <th>Lote</th><th>Cultivo</th><th>Cosecha</th><th>Estado</th><th>Acción</th>
          </tr>
        </thead>
        <tbody id="js-lotes-body">
          <tr><td colspan="5" class="text-muted">Sin datos en caché local.</td></tr>
        </tbody>
      </table>
    </section>

  </div><!-- /.dashboard-grid -->

</main>

<style>
/* ── Dashboard styles ─────────────────────────────────────────────────────── */
.castuo-dashboard { background: var(--cream, #F7F3EE); min-height: 100vh; }

.dashboard-header {
  background: var(--forest, #0D2818);
  color: #fff;
  padding: 1rem 0;
  position: sticky;
  top: 0;
  z-index: 100;
  box-shadow: 0 2px 8px rgba(0,0,0,.25);
}
.dashboard-header__inner {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
}
.dashboard-header__title h1 { font-size: 1.25rem; margin: 0; color: #fff; }
.dashboard-header__version { font-size: .75rem; opacity: .7; }
.dashboard-header__timestamp { font-size: .75rem; opacity: .6; }

.dashboard-grid {
  display: grid;
  gap: 1.5rem;
  padding: 1.5rem 1rem;
  max-width: 1200px;
  margin: 0 auto;
}

/* KPI cards */
.kpi-row {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
  gap: 1rem;
}
.kpi-card {
  background: #fff;
  border-radius: 10px;
  padding: 1.25rem;
  box-shadow: 0 1px 4px rgba(0,0,0,.08);
  display: flex;
  flex-direction: column;
  gap: .5rem;
}
.kpi-card__label { font-size: .75rem; font-weight: 600; text-transform: uppercase;
  letter-spacing: .05em; color: var(--sage, #4A7C59); }
.kpi-card__value { font-size: 1.5rem; font-weight: 700; color: var(--forest, #0D2818); }

/* Sections */
.dashboard-section {
  background: #fff;
  border-radius: 10px;
  padding: 1.5rem;
  box-shadow: 0 1px 4px rgba(0,0,0,.08);
}
.section-title { font-size: 1rem; font-weight: 700; margin: 0 0 1rem; color: var(--forest,#0D2818); }

/* Services grid */
.services-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: .75rem;
}
.service-card {
  border-radius: 8px;
  padding: .75rem 1rem;
  font-size: .85rem;
  display: flex;
  flex-direction: column;
  gap: .25rem;
  border: 1px solid #e5e7eb;
}
.service-card__name { font-weight: 600; }
.service-card__latency { color: #6b7280; font-size: .75rem; }
.service-card[data-status="healthy"]       { background: #f0fdf4; border-color: #86efac; }
.service-card[data-status="degraded"]      { background: #fffbeb; border-color: #fcd34d; }
.service-card[data-status="unavailable"]   { background: #fef2f2; border-color: #fca5a5; }
.service-card[data-status="unknown"]       { background: #f9fafb; border-color: #d1d5db; }
.status-dot { display: inline-block; width: 8px; height: 8px; border-radius: 50%; margin-right: .4em; }
.status-dot--healthy     { background: #22c55e; }
.status-dot--degraded    { background: #f59e0b; }
.status-dot--unavailable { background: #ef4444; }
.status-dot--unknown     { background: #9ca3af; }

/* Verify form */
.verify-form { display: flex; flex-wrap: wrap; gap: 1rem; align-items: flex-end; }
.form-row { display: flex; flex-direction: column; gap: .35rem; min-width: 200px; flex: 1; }
.form-row label { font-size: .8rem; font-weight: 600; color: #374151; }
.form-row input {
  border: 1px solid #d1d5db;
  border-radius: 6px;
  padding: .5rem .75rem;
  font-size: .9rem;
  width: 100%;
}
.verify-result {
  margin-top: 1rem;
  padding: 1rem;
  border-radius: 8px;
  font-size: .9rem;
}
.verify-result--ok     { background: #f0fdf4; border: 1px solid #86efac; }
.verify-result--fail   { background: #fef2f2; border: 1px solid #fca5a5; }
.verify-result__badge  { font-weight: 700; font-size: 1.1rem; margin-bottom: .5rem; }
.verify-result__table  { width: 100%; border-collapse: collapse; font-size: .82rem; }
.verify-result__table th, .verify-result__table td { padding: .35rem .6rem; text-align: left; border-bottom: 1px solid #e5e7eb; }
.verify-result__table th { font-weight: 600; color: #4b5563; }

/* Lotes table */
.lotes-table { width: 100%; border-collapse: collapse; font-size: .85rem; }
.lotes-table th { padding: .5rem .75rem; text-align: left; border-bottom: 2px solid #e5e7eb;
  font-weight: 600; color: var(--forest, #0D2818); }
.lotes-table td { padding: .5rem .75rem; border-bottom: 1px solid #f3f4f6; }
.lotes-table tbody tr:hover { background: #f9fafb; }

/* Utilities */
.text-muted { color: #9ca3af; text-align: center; padding: 1rem 0; }
.btn--sm { padding: .35rem .75rem; font-size: .8rem; }
.btn--ghost {
  background: transparent;
  border: 1px solid rgba(255,255,255,.4);
  color: #fff;
  border-radius: 6px;
  cursor: pointer;
  padding: .4rem .9rem;
  transition: background .2s;
}
.btn--ghost:hover { background: rgba(255,255,255,.12); }
</style>

<script>
(function () {
  'use strict';

  /* ─── Config ──────────────────────────────────────────────────────────── */
  const API_BASE    = '<?php echo esc_js( rtrim( get_option('castuo_api_base', '' ), '/' ) ); ?>';
  const VERIFY_REST = '<?php echo esc_js( rest_url('castuo/v1/verify') ); ?>';
  const NONCE       = '<?php echo esc_js( wp_create_nonce('wp_rest') ); ?>';

  /* ─── DOM refs ─────────────────────────────────────────────────────────── */
  const $ = id => document.getElementById(id);
  const el = (tag, attrs = {}, ...children) => {
    const e = document.createElement(tag);
    Object.entries(attrs).forEach(([k, v]) => {
      if (k.startsWith('data-')) e.dataset[k.slice(5)] = v;
      else e.setAttribute(k, v);
    });
    children.forEach(c => e.append(typeof c === 'string' ? document.createTextNode(c) : c));
    return e;
  };

  /* ─── Helpers ──────────────────────────────────────────────────────────── */
  function esc(str) {
    return String(str)
      .replace(/&/g, '&amp;').replace(/</g, '&lt;')
      .replace(/>/g, '&gt;').replace(/"/g, '&quot;');
  }

  function statusDot(s) {
    return el('span', { class: `status-dot status-dot--${s}` });
  }

  function setKPI(id, val, cls) {
    const el = $(id);
    if (el) { el.textContent = val; if (cls) el.className = `kpi-card__value ${cls}`; }
  }

  /* ─── Load health ──────────────────────────────────────────────────────── */
  async function loadHealth() {
    if (!API_BASE) return;
    try {
      const r = await fetch(`${API_BASE}/health`, { cache: 'no-store' });
      if (!r.ok) throw new Error(r.status);
      const d = await r.json();
      setKPI('kpi-chain-val', d.chain_status || '—');
      setKPI('kpi-lab-val', d.neuromorphic_lab ? 'Activo' : 'Inactivo');
      $('js-last-update').textContent = 'Actualizado: ' + new Date().toLocaleTimeString('es-ES');
    } catch (e) {
      setKPI('kpi-chain-val', 'Error');
    }
  }

  /* ─── Load orchestrator status ─────────────────────────────────────────── */
  async function loadServices() {
    if (!API_BASE) { $('js-services-grid').innerHTML = '<p class="text-muted">API_BASE no configurado.</p>'; return; }
    try {
      const r = await fetch(`${API_BASE}/api/v1/orchestrator/status`, { cache: 'no-store' });
      const d = await r.json();
      const grid = $('js-services-grid');
      grid.innerHTML = '';

      const services = d.services || {};
      const count = Object.values(services).filter(s => s.status === 'healthy').length;
      setKPI('kpi-services-val', `${count} / ${Object.keys(services).length}`);

      Object.entries(services).forEach(([name, info]) => {
        const card = el('div', { class: 'service-card', 'data-status': info.status });
        const nameRow = el('div', { class: 'service-card__name' });
        nameRow.append(statusDot(info.status), esc(name));
        const latency = el('div', { class: 'service-card__latency' },
          info.latency_ms != null ? `${info.latency_ms} ms` : (info.error || 'sin datos'));
        card.append(nameRow, latency);
        grid.append(card);
      });
      if (!Object.keys(services).length) {
        grid.innerHTML = '<p class="text-muted">Sin servicios registrados o API no alcanzable.</p>';
      }
    } catch (e) {
      $('js-services-grid').innerHTML = '<p class="text-muted">No se pudo conectar con el orquestador.</p>';
    }
  }

  /* ─── Verify form ──────────────────────────────────────────────────────── */
  $('js-verify-form').addEventListener('submit', async function (ev) {
    ev.preventDefault();
    const lote_id = $('op-lote-id').value.trim();
    const hash    = $('op-hash').value.trim();
    const result  = $('js-verify-result');
    if (!lote_id) { alert('Introduce el ID de lote.'); return; }

    result.removeAttribute('hidden');
    result.className = 'verify-result';
    result.innerHTML = '<em>Verificando…</em>';

    try {
      const body = { lote_id };
      if (hash) body.hash = hash;

      const r = await fetch(VERIFY_REST, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'X-WP-Nonce': NONCE },
        body: JSON.stringify(body),
      });
      const d = await r.json();

      // Support both direct FastAPI response and WP proxy wrapping
      const autentico = d.autentico ?? (d.data && d.data.autentico);
      const lote      = d.datos_lote ?? (d.data && d.data.datos_lote) ?? {};
      const msg       = d.mensaje_consumidor ?? (d.data && d.data.mensaje_consumidor) ?? d.detail ?? 'Sin respuesta';

      result.className = `verify-result verify-result--${autentico ? 'ok' : 'fail'}`;
      let html = `<div class="verify-result__badge">${autentico ? '✓ Lote auténtico' : '⚠ No verificado'}</div>`;
      html += `<p>${esc(msg)}</p>`;

      if (autentico && lote.producto) {
        html += '<table class="verify-result__table"><tbody>';
        const rows = [
          ['Producto', lote.producto],
          ['Cosecha', lote.fecha_cosecha],
          ['Kg', lote.cantidad_kg],
          ['Eco', lote.certificaciones?.eco_certificado ? 'Sí' : 'No'],
          ['Sin pesticidas', lote.certificaciones?.sin_pesticidas_sinteticos ? 'Sí' : 'No'],
        ];
        rows.forEach(([k, v]) => {
          html += `<tr><th>${esc(k)}</th><td>${esc(String(v ?? '—'))}</td></tr>`;
        });
        html += '</tbody></table>';
        // Cache in localStorage for the lotes table
        try {
          const cache = JSON.parse(localStorage.getItem('castuo_lotes') || '[]');
          if (!cache.find(c => c.lote_id === lote_id)) {
            cache.unshift({ lote_id, cultivo: lote.producto, fecha: lote.fecha_cosecha, autentico });
            localStorage.setItem('castuo_lotes', JSON.stringify(cache.slice(0, 20)));
            renderLotesTable(cache);
          }
        } catch (_) {}
      }
      result.innerHTML = html;
    } catch (e) {
      result.className = 'verify-result verify-result--fail';
      result.innerHTML = `<p>Error de red: ${esc(e.message)}</p>`;
    }
  });

  /* ─── Lotes table (localStorage cache) ────────────────────────────────── */
  function renderLotesTable(rows) {
    const tbody = $('js-lotes-body');
    if (!rows || !rows.length) return;
    tbody.innerHTML = rows.map(r => `
      <tr>
        <td>${esc(r.lote_id)}</td>
        <td>${esc(r.cultivo || '—')}</td>
        <td>${esc(r.fecha || '—')}</td>
        <td>${r.autentico ? '<span style="color:#16a34a">✓ auténtico</span>' : '<span style="color:#dc2626">⚠ no verificado</span>'}</td>
        <td><button class="btn btn--ghost btn--sm" style="color:var(--sage,#4A7C59);border-color:var(--sage,#4A7C59)"
            onclick="document.getElementById('op-lote-id').value='${esc(r.lote_id)}';document.getElementById('js-verify-form').dispatchEvent(new Event('submit'))">
          Reverificar
        </button></td>
      </tr>`).join('');
  }

  /* ─── Refresh ──────────────────────────────────────────────────────────── */
  async function refresh() {
    await Promise.all([ loadHealth(), loadServices() ]);
    // Lotes from localStorage
    try {
      renderLotesTable(JSON.parse(localStorage.getItem('castuo_lotes') || '[]'));
    } catch (_) {}
  }

  $('js-refresh').addEventListener('click', refresh);

  // Load lote count from localStorage
  try {
    const c = JSON.parse(localStorage.getItem('castuo_lotes') || '[]');
    setKPI('kpi-lotes-val', c.length);
  } catch (_) {}

  // Auto-refresh on load
  refresh();

})();
</script>

<?php get_footer(); ?>
