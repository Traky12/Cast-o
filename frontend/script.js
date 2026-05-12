const apiBase =
  (window.location.hostname === "localhost" ||
    window.location.hostname === "127.0.0.1")
    ? "http://127.0.0.1:8000"
    : `${window.location.protocol}//${window.location.hostname}:8000`;

document.getElementById("apiBase").textContent = apiBase;

document.getElementById("ejecutar").addEventListener("click", async () => {
  const crop = document.getElementById("crop").value;
  const biomasa = parseFloat(document.getElementById("biomasa").value || "0");
  const amount = parseFloat(document.getElementById("amount").value || "0");
  const texto_psicologo = document.getElementById("texto_psicologo").value || "";

  const response = await fetch(`${apiBase}/ecosistema/B001`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      biomasa_kg: biomasa,
      crop,
      texto_psicologo,
      amount,
    }),
  });

  const data = await response.json();
  mostrarResultados(data);
});

function mostrarResultados(data) {
  document.getElementById("resultados").classList.remove("hidden");

  // Bioeconomía
  if (data.bioeconomia) {
    document.getElementById("bioeconomia_result").innerHTML = `
      <h3>Bioeconomía</h3>
      <div class="muted small">${data.bioeconomia.product}</div>
      <div><strong>${data.bioeconomia.quantity}</strong> ${data.bioeconomia.unit}</div>
      <div class="muted small">Valor: ${Number(data.bioeconomia.market_value_eur).toFixed(2)}€</div>
      <div class="muted small">Biocoin: ${data.bioeconomia.biocoin}</div>
      <div class="muted small">CO₂ evitado: ${data.bioeconomia.co2_saved_kg} kg</div>
    `;
  }

  // MONEI
  if (data.monei) {
    document.getElementById("monei_result").innerHTML = `
      <h3>MONEI</h3>
      <div class="muted small">IBAN</div>
      <div><code>${data.monei.iban}</code></div>
      <div class="muted small">Amount: ${data.monei.amount}€</div>
      <div class="muted small">Carbon credit: ${data.monei.carbon_credit}</div>
    `;
  } else {
    document.getElementById("monei_result").innerHTML = `
      <h3>MONEI</h3>
      <div class="muted small">Sin transacción (amount=0)</div>
    `;
  }

  // Psicólogo
  if (data.psicologo) {
    document.getElementById("psicologo_result").innerHTML = `
      <h3>Psicólogo Digital</h3>
      <div class="muted small">Emoción: ${data.psicologo.emocion}</div>
      <div>${escapeHtml(data.psicologo.respuesta)}</div>
      <div class="muted small">Biocoin reward: ${data.psicologo.biocoin_reward}</div>
    `;
  } else {
    document.getElementById("psicologo_result").innerHTML = `
      <h3>Psicólogo Digital</h3>
      <div class="muted small">Sin sesión (texto vacío)</div>
    `;
  }

  document.getElementById("total_value").textContent = `${Number(
    data.total_value_eur
  ).toFixed(2)}€`;
  document.getElementById("total_biocoin").textContent = `${data.total_biocoin}`;

  const tx = data.vechain_tx || "";
  const link = document.getElementById("vechain_tx_link");
  link.href = `https://explore.vechain.org/transactions/${tx}`;
  link.textContent = tx;
}

function escapeHtml(str) {
  return String(str)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;");
}

