import React, { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import axios from "axios";
import "./BillingDashboard.css";

const API_BASE = process.env.REACT_APP_API_BASE || "";

function BillingDashboard() {
  const navigate = useNavigate();
  const [invoices, setInvoices] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    axios
      .get(`${API_BASE}/billing/facturacion`)
      .then((res) => setInvoices(Array.isArray(res.data) ? res.data : []))
      .catch((err) => setError(err.message || "Error al cargar facturación"))
      .finally(() => setLoading(false));
  }, []);

  const totalMes = invoices.reduce((sum, inv) => sum + (inv.total_eur || 0), 0);
  const coopNames = { 1: "Sabionda Educa SAT", 2: "Cooperativa #2", 3: "Cooperativa #3" };

  return (
    <div className="billing-dashboard">
      <nav className="billing-nav">
        <button type="button" onClick={() => navigate("/")}>
          ← Dashboard
        </button>
      </nav>
      <h2>Facturación</h2>
      <p className="billing-date">{new Date().toLocaleDateString("es-ES", { dateStyle: "long" })}</p>
      <h3 className="billing-total">Total: €{totalMes.toFixed(0)}/mes</h3>

      {loading && <p>Cargando facturación...</p>}
      {error && <p className="billing-error">{error}</p>}
      {!loading && !error && (
        <table className="billing-table">
          <thead>
            <tr>
              <th>Cooperativa</th>
              <th>Hectáreas</th>
              <th>Importe</th>
              <th>Estado</th>
              <th>Fecha</th>
            </tr>
          </thead>
          <tbody>
            {invoices.map((inv) => (
              <tr key={inv.id}>
                <td>{coopNames[inv.coop_id] || `Coop #${inv.coop_id}`}</td>
                <td>{inv.hectareas} ha</td>
                <td>€{Number(inv.total_eur).toFixed(2)}</td>
                <td>{inv.estado}</td>
                <td>{inv.created_at ? new Date(inv.created_at).toLocaleDateString("es-ES") : "—"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
      {!loading && invoices.length === 0 && !error && (
        <p className="billing-empty">No hay facturas en el último mes. Genera facturas desde el API: POST /billing/invoice/1, /2, /3</p>
      )}
    </div>
  );
}

export default BillingDashboard;
