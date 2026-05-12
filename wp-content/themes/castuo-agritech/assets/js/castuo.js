/**
 * CASTÚO Agritech — castuo.js
 * Header scroll · mobile menu · QR verification
 */

(function () {
  'use strict';

  // ─── Header scroll shadow ──────────────────────────────────
  const header = document.getElementById('site-header');
  if (header) {
    const onScroll = () =>
      header.classList.toggle('scrolled', window.scrollY > 10);
    window.addEventListener('scroll', onScroll, { passive: true });
  }

  // ─── Mobile menu toggle ────────────────────────────────────
  const toggle = document.querySelector('.menu-toggle');
  const nav    = document.getElementById('primary-menu');
  if (toggle && nav) {
    toggle.addEventListener('click', () => {
      const open = nav.classList.toggle('open');
      toggle.setAttribute('aria-expanded', String(open));
      // Animate hamburger → X
      toggle.querySelectorAll('span').forEach((s, i) => {
        if (open) {
          if (i === 0) s.style.transform = 'translateY(7px) rotate(45deg)';
          if (i === 1) s.style.opacity = '0';
          if (i === 2) s.style.transform = 'translateY(-7px) rotate(-45deg)';
        } else {
          s.style.transform = '';
          s.style.opacity   = '';
        }
      });
    });
    // Close on outside click
    document.addEventListener('click', (e) => {
      if (!header.contains(e.target)) {
        nav.classList.remove('open');
        toggle.setAttribute('aria-expanded', 'false');
        toggle.querySelectorAll('span').forEach((s) => {
          s.style.transform = '';
          s.style.opacity   = '';
        });
      }
    });
  }

  // ─── Active nav link on scroll ────────────────────────────
  const sections = document.querySelectorAll('section[id]');
  const navLinks = document.querySelectorAll('.site-nav a[href^="#"]');
  if (sections.length && navLinks.length) {
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            navLinks.forEach((a) => {
              a.classList.toggle('active', a.getAttribute('href') === '#' + entry.target.id);
            });
          }
        });
      },
      { rootMargin: '-40% 0px -55% 0px' }
    );
    sections.forEach((s) => observer.observe(s));
  }

  // ─── QR Verification ──────────────────────────────────────
  const verifyForm   = document.getElementById('verify-form');
  const loteInput    = document.getElementById('lote-input');
  const hashInput    = document.getElementById('hash-input');
  const verifyBtn    = document.getElementById('verify-btn');
  const resultArea   = document.getElementById('verify-result');
  const statusBadge  = document.getElementById('verify-status-badge');
  const dataArea     = document.getElementById('verify-data');

  if (!verifyForm) return;

  // Pre-fill from URL params: ?lote=X&hash=Y
  const params = new URLSearchParams(window.location.search);
  if (params.get('lote')) loteInput.value = params.get('lote');
  if (params.get('hash')) hashInput.value = params.get('hash');
  if (params.get('lote')) verifyForm.requestSubmit?.();

  verifyForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const loteId = loteInput.value.trim().toUpperCase();
    const hash   = hashInput.value.trim().toLowerCase();

    if (!loteId) {
      loteInput.focus();
      return;
    }

    verifyBtn.disabled   = true;
    verifyBtn.textContent = typeof CASTUO !== 'undefined' ? '…' : 'Verificando…';
    resultArea.classList.remove('visible');

    try {
      const verifyUrl = (typeof CASTUO !== 'undefined' && CASTUO.verify_url)
        ? CASTUO.verify_url
        : '/wp-json/castuo/v1/verify';

      const url = new URL(verifyUrl, window.location.origin);
      url.searchParams.set('lote_id', loteId);
      if (hash) url.searchParams.set('hash', hash);

      const headers = { 'Accept': 'application/json' };
      if (typeof CASTUO !== 'undefined' && CASTUO.nonce) {
        headers['X-WP-Nonce'] = CASTUO.nonce;
      }

      const res  = await fetch(url.toString(), { headers });
      const data = await res.json();

      renderResult(res.ok && !data.error, data);
    } catch (err) {
      renderResult(false, { error: 'Error de red. Inténtalo de nuevo.' });
    } finally {
      verifyBtn.disabled   = false;
      verifyBtn.textContent = 'Verificar';
    }
  });

  /**
   * @param {boolean}  valid
   * @param {Object}   data  — backend response
   */
  function renderResult(valid, data) {
    resultArea.classList.add('visible');

    if (valid) {
      statusBadge.className    = 'verify-status ok';
      statusBadge.innerHTML    =
        '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" aria-hidden="true"><polyline points="20 6 9 17 4 12"/></svg>'
        + ' Lote verificado — integridad confirmada en blockchain';
    } else {
      statusBadge.className    = 'verify-status error';
      statusBadge.innerHTML    =
        '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" aria-hidden="true"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>'
        + ' ' + escHtml(data.error || 'Verificación fallida');
    }

    const rows = valid ? buildDataRows(data) : [];
    dataArea.innerHTML = rows.map(([k, v]) =>
      `<div class="verify-row"><span class="verify-key">${escHtml(k)}</span><span class="verify-val">${escHtml(v)}</span></div>`
    ).join('');
  }

  function buildDataRows(data) {
    const rows = [];
    const add  = (k, v) => v !== undefined && v !== null && v !== '' && rows.push([k, String(v)]);

    add('Lote ID',         data.lote_id);
    add('Cultivo',         data.cultivo || data.producto);
    add('Variedad',        data.variedad);
    add('Fecha cosecha',   data.fecha_cosecha);
    add('Kg cosechados',   data.kg_cosechados ? data.kg_cosechados + ' kg' : null);
    add('pH medio',        data.ph_medio);
    add('CE (mS/cm)',      data.ce_ms_cm);
    add('Energía solar',   data.energia_solar_pct ? data.energia_solar_pct + ' %' : null);
    add('IPFS CID',        data.ipfs_cid);
    add('Blockchain TX',   data.gaiachain_tx);
    add('TRACES cert.',    data.traces_cert_id);
    add('Eco certificado', data.eco_certificado ? 'Sí' : data.eco_certificado === false ? 'No' : null);
    add('Sin pesticidas',  data.sin_pesticidas_sinteticos ? 'Sí' : data.sin_pesticidas_sinteticos === false ? 'No' : null);
    add('Hash cadena',     data.hash_cadena);
    return rows;
  }

  function escHtml(str) {
    return String(str)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;');
  }

})();
