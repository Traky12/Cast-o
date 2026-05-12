/**
 * Panel admin water/ctaex — claves solo en localStorage (no hardcode).
 * Requiere CORS permitido en el API (main.py ya incluye localhost:3000 y *).
 */
(function () {
  "use strict";

  const LS = {
    apiBase: "CASTUO_ADMIN_API_BASE",
    usageKey: "CASTUO_ADMIN_USAGE_REPORT_KEY",
    aiKey: "CASTUO_ADMIN_AI_KEY",
  };

  function defaultApiBase() {
    if (typeof window === "undefined" || !window.location || !window.location.origin) {
      return "http://127.0.0.1:8000";
    }
    const port = window.location.port;
    const sameHostAsApi =
      port === "8000" ||
      port === "" ||
      port === "80" ||
      port === "443";
    if (sameHostAsApi) {
      return String(window.location.origin).replace(/\/$/, "");
    }
    return "http://127.0.0.1:8000";
  }

  function getConfig() {
    const stored = (localStorage.getItem(LS.apiBase) || "").trim().replace(/\/$/, "");
    return {
      apiBase: stored || defaultApiBase(),
      usageKey: localStorage.getItem(LS.usageKey) || "",
      aiKey: localStorage.getItem(LS.aiKey) || "",
    };
  }

  function saveConfig(apiBase, usageKey, aiKey) {
    localStorage.setItem(LS.apiBase, (apiBase || "").trim().replace(/\/$/, ""));
    localStorage.setItem(LS.usageKey, (usageKey || "").trim());
    localStorage.setItem(LS.aiKey, (aiKey || "").trim());
  }

  async function api(path, { method = "GET", headers = {}, body, usage = true, ai = false } = {}) {
    const c = getConfig();
    const url = `${c.apiBase}${path.startsWith("/") ? path : "/" + path}`;
    const h = { ...headers };
    if (ai && c.aiKey) h["X-AI-KEY"] = c.aiKey;
    else if (usage && c.usageKey) h["X-USAGE-REPORT-KEY"] = c.usageKey;
    const res = await fetch(url, { method, headers: h, body });
    const text = await res.text();
    let data;
    try {
      data = text ? JSON.parse(text) : null;
    } catch {
      data = { _raw: text };
    }
    if (!res.ok) {
      const err = new Error(data?.detail || data?.message || res.statusText || String(res.status));
      err.status = res.status;
      err.body = data;
      throw err;
    }
    return data;
  }

  function esc(s) {
    if (s == null) return "";
    return String(s)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  function ymNow() {
    const d = new Date();
    return { year: d.getFullYear(), month: d.getMonth() + 1 };
  }

  async function loadDashboard() {
    const { year, month } = ymNow();
    const elClients = document.getElementById("active-clients");
    const elRev = document.getElementById("monthly-revenue");
    const elReq = document.getElementById("total-requests");
    const elAct = document.getElementById("recent-activity");
    elAct.innerHTML = '<p class="text-gray-500">Cargando…</p>';

    try {
      const summary = await api(
        `/water/ctaex/subscription/billing-summary?year=${year}&month=${month}`,
        { usage: true },
      );
      const customers = summary.customers || [];
      const inv = summary.invoices || {};
      let reqSum = 0;
      for (const row of customers) {
        reqSum += Number(row.requests_in_period || 0);
      }
      elClients.textContent = String(customers.length);
      elRev.textContent = "€" + Number(inv.total_eur || 0).toFixed(2);
      elReq.textContent = String(reqSum);

      const usage = await api(`/water/ctaex/subscription/usage-report?limit=8`, { usage: true });
      const items = usage.items || usage.report || [];
      if (!items.length) {
        elAct.innerHTML = '<p class="text-gray-500">Sin trazas recientes.</p>';
        return;
      }
      elAct.innerHTML = items
        .map(
          (it) => `
        <div class="mb-3 pb-3 border-b border-gray-100 last:border-0">
          <p class="font-mono text-xs text-gray-600">${esc(it.key_hash?.slice(0, 16))}…</p>
          <p class="text-sm"><span class="font-semibold">${esc(it.plan_id)}</span> · ${esc(it.endpoint)}</p>
          <p class="text-xs text-gray-500">${esc(it.request_timestamp)} · period ${esc(it.period)}</p>
        </div>`,
        )
        .join("");
    } catch (e) {
      elAct.innerHTML = `<p class="text-red-600 text-sm">Error: ${esc(e.message)}</p>`;
      elClients.textContent = "—";
      elRev.textContent = "—";
      elReq.textContent = "—";
    }
  }

  async function loadClients() {
    const box = document.getElementById("clients-list");
    box.innerHTML = '<p class="text-gray-500">Cargando…</p>';
    try {
      const { year, month } = ymNow();
      const summary = await api(
        `/water/ctaex/subscription/billing-summary?year=${year}&month=${month}`,
        { usage: true },
      );
      const customers = summary.customers || [];
      if (!customers.length) {
        box.innerHTML = '<p class="text-gray-500">No hay filas en billing_customers para este período.</p>';
        return;
      }
      box.innerHTML = customers
        .map((c) => {
          const pct =
            c.max_requests && c.requests_in_period != null
              ? Math.min(100, Math.round((100 * Number(c.requests_in_period)) / Number(c.max_requests)))
              : "—";
          return `
        <div class="p-4 border-b border-gray-100 last:border-b-0">
          <div class="flex justify-between gap-2">
            <div>
              <p class="font-semibold">${esc(c.customer_name)}</p>
              <p class="text-sm text-gray-500">${esc(c.customer_email)}</p>
              <p class="text-xs font-mono text-gray-400 mt-1">${esc(c.key_hash?.slice(0, 12))}…</p>
            </div>
            <span class="px-2 py-1 bg-green-100 text-green-800 rounded h-fit">${esc(c.plan_name || c.plan_id)}</span>
          </div>
          <div class="mt-2 flex justify-between text-sm text-gray-600">
            <span>Requests período: ${esc(c.requests_in_period)}</span>
            <span>${pct === "—" ? "—" : pct + "% cuota (ver plan en API)"}</span>
          </div>
        </div>`;
        })
        .join("");
    } catch (e) {
      box.innerHTML = `<p class="text-red-600 text-sm">Error: ${esc(e.message)}</p>`;
    }
  }

  async function loadInvoices() {
    const box = document.getElementById("invoices-list");
    box.innerHTML = '<p class="text-gray-500">Cargando…</p>';
    try {
      const { year, month } = ymNow();
      const data = await api(
        `/water/ctaex/subscription/certification?year=${year}&month=${month}`,
        { usage: true },
      );
      const invs = data.invoices || [];
      if (!invs.length) {
        box.innerHTML =
          '<p class="text-gray-500">Sin facturas en SQLite para este mes (genera con “Generar facturas”).</p>';
        return;
      }
      box.innerHTML = `
      <div class="overflow-x-auto">
        <table class="min-w-full text-sm">
          <thead><tr class="border-b text-left">
            <th class="px-3 py-2">Número</th>
            <th class="px-3 py-2">Cliente</th>
            <th class="px-3 py-2">Total</th>
            <th class="px-3 py-2">Estado</th>
          </tr></thead>
          <tbody>
            ${invs
              .map(
                (inv) => `
              <tr class="border-b">
                <td class="px-3 py-2 font-mono text-xs">${esc(inv.invoice_number)}</td>
                <td class="px-3 py-2">${esc(inv.customer_name)}</td>
                <td class="px-3 py-2">€${Number(inv.total_eur ?? (inv.total_cents || 0) / 100).toFixed(2)}</td>
                <td class="px-3 py-2"><span class="px-2 py-0.5 rounded bg-yellow-100 text-yellow-900">${esc(inv.status)}</span></td>
              </tr>`,
              )
              .join("")}
          </tbody>
        </table>
      </div>`;
    } catch (e) {
      box.innerHTML = `<p class="text-red-600 text-sm">Error: ${esc(e.message)}</p>`;
    }
  }

  async function generateInvoices() {
    const { year, month } = ymNow();
    try {
      const data = await api(
        `/water/ctaex/subscription/generate-invoices?year=${year}&month=${month}`,
        { method: "POST", usage: true },
      );
      alert(`Generadas: ${data.invoices_generated ?? data.generated ?? 0} factura(s) nuevas.`);
      await loadInvoices();
    } catch (e) {
      alert("Error: " + e.message);
    }
  }

  async function loadReport() {
    const month = document.getElementById("report-month").value;
    const year = document.getElementById("report-year").value || String(new Date().getFullYear());
    const box = document.getElementById("monthly-report");
    box.innerHTML = '<p class="text-gray-500">Cargando…</p>';
    try {
      const data = await api(`/water/ctaex/subscription/certification?year=${year}&month=${parseInt(month, 10)}`, {
        usage: true,
      });
      box.innerHTML = `<pre class="json-out">${esc(JSON.stringify(data, null, 2))}</pre>`;
    } catch (e) {
      box.innerHTML = `<p class="text-red-600 text-sm">Error: ${esc(e.message)}</p>`;
    }
  }

  async function loadAiMonitoring() {
    const out = document.getElementById("ai-monitoring-out");
    out.innerHTML = '<p class="text-gray-500">Cargando…</p>';
    try {
      const data = await api(`/water/ctaex/subscription/ai/monitoring`, { usage: false, ai: true });
      out.innerHTML = `<pre class="json-out">${esc(JSON.stringify(data, null, 2))}</pre>`;
    } catch (e) {
      out.innerHTML = `<p class="text-red-600 text-sm">Error: ${esc(e.message)}</p>`;
    }
  }

  async function loadAiHealth() {
    const out = document.getElementById("ai-health-out");
    out.innerHTML = '<p class="text-gray-500">Cargando…</p>';
    try {
      const data = await api(`/water/ctaex/subscription/ai/health`, { usage: false, ai: true });
      out.innerHTML = `<pre class="json-out">${esc(JSON.stringify(data, null, 2))}</pre>`;
    } catch (e) {
      out.innerHTML = `<p class="text-red-600 text-sm">Error: ${esc(e.message)}</p>`;
    }
  }

  async function loadAiBlueprint() {
    const out = document.getElementById("ai-blueprint-out");
    out.innerHTML = '<p class="text-gray-500">Cargando…</p>';
    try {
      const data = await api(`/water/ctaex/subscription/ai/enterprise-blueprint`, { usage: false, ai: true });
      out.innerHTML = `<pre class="json-out">${esc(JSON.stringify(data, null, 2))}</pre>`;
    } catch (e) {
      out.innerHTML = `<p class="text-red-600 text-sm">Error: ${esc(e.message)}</p>`;
    }
  }

  function syncHtmxHealthUrl() {
    const c = getConfig();
    const btn = document.getElementById("htmx-health-btn");
    if (btn) {
      btn.setAttribute("hx-get", `${c.apiBase}/water/ctaex/health`);
      if (window.htmx) window.htmx.process(btn);
    }
  }

  function bindSettingsForm() {
    document.getElementById("cfg-api-base").value = localStorage.getItem(LS.apiBase) || "";
    document.getElementById("cfg-usage-key").value = localStorage.getItem(LS.usageKey) || "";
    document.getElementById("cfg-ai-key").value = localStorage.getItem(LS.aiKey) || "";

    const ry = document.getElementById("report-year");
    if (ry && !ry.value) ry.value = String(new Date().getFullYear());

    document.getElementById("save-settings").addEventListener("click", () => {
      saveConfig(
        document.getElementById("cfg-api-base").value,
        document.getElementById("cfg-usage-key").value,
        document.getElementById("cfg-ai-key").value,
      );
      syncHtmxHealthUrl();
      alert("Configuración guardada en este navegador (localStorage).");
    });

    document.getElementById("btn-health-public")?.addEventListener("click", async () => {
      const base = getConfig().apiBase;
      try {
        const r = await fetch(`${base}/water/ctaex/health`);
        const j = await r.json();
        alert(JSON.stringify(j, null, 2));
      } catch (e) {
        alert("Error: " + e.message);
      }
    });
  }

  function bindNav() {
    document.getElementById("refresh-dashboard").addEventListener("click", loadDashboard);
    document.getElementById("refresh-clients").addEventListener("click", loadClients);
    document.getElementById("refresh-invoices").addEventListener("click", loadInvoices);
    document.getElementById("generate-invoices").addEventListener("click", generateInvoices);
    document.getElementById("generate-report").addEventListener("click", loadReport);
    document.getElementById("btn-ai-monitoring").addEventListener("click", loadAiMonitoring);
    document.getElementById("btn-ai-health").addEventListener("click", loadAiHealth);
    document.getElementById("btn-ai-blueprint").addEventListener("click", loadAiBlueprint);
  }

  document.addEventListener("DOMContentLoaded", () => {
    bindSettingsForm();
    bindNav();
    syncHtmxHealthUrl();
    loadDashboard();
  });
})();
