import React from "react";
import "./AuditTrail.css";

const AuditTrail = ({ entries }) => {
  if (!entries || entries.length === 0) {
    return <p>No hay registros de auditoría para este token.</p>;
  }

  return (
    <div className="audit-trail">
      <table>
        <thead>
          <tr>
            <th>Fecha/Hora</th>
            <th>Acción</th>
            <th>Estado</th>
            <th>Detalles</th>
            <th>Verificación</th>
          </tr>
        </thead>
        <tbody>
          {entries.map((entry, index) => (
            <tr key={index}>
              <td>{new Date(entry.timestamp).toLocaleString()}</td>
              <td>
                {entry.action === "erasure_request" && "Solicitud de Borrado (GDPR Art. 17)"}
                {entry.action === "subsidy_claim" && "Reclamación de Subvención"}
                {entry.action === "carbon_mint" && "Tokenización de Carbono"}
                {!["erasure_request", "subsidy_claim", "carbon_mint"].includes(entry.action) &&
                  entry.action}
              </td>
              <td className={`status-${entry.status}`}>
                {entry.status === "completed" && "✅ Completado"}
                {entry.status === "failed" && "❌ Fallido"}
                {entry.status === "pending" && "⏳ Pendiente"}
              </td>
              <td>
                {entry.transactionHash && (
                  <a
                    href={`https://explorer.gaiachain.castuo-system.com/tx/${entry.transactionHash}`}
                    target="_blank"
                    rel="noopener noreferrer"
                  >
                    TX: {entry.transactionHash.slice(0, 6)}...
                  </a>
                )}
                {entry.error && <span className="error-detail">{entry.error}</span>}
                {entry.certificateUrl && (
                  <a href={entry.certificateUrl} target="_blank" rel="noopener noreferrer">
                    Certificado
                  </a>
                )}
              </td>
              <td>
                {entry.transactionHash && (
                  <span className="verification-badge" title="Verificado en GaiaChain">
                    ✅ Blockchain
                  </span>
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </table>

      <div className="audit-notice">
        <p>🔒 Todos los eventos están registrados en <strong>GaiaChain</strong> y son inmutables.</p>
        <p>📄 Cumplimiento con:</p>
        <ul>
          <li>
            <strong>ISO 27001:</strong> Gestión de seguridad de la información.
          </li>
          <li>
            <strong>GDPR Art. 30:</strong> Registro de actividades de tratamiento.
          </li>
          <li>
            <strong>eIDAS:</strong> Autenticación y firma electrónica certificada.
          </li>
        </ul>
      </div>
    </div>
  );
};

export default AuditTrail;

