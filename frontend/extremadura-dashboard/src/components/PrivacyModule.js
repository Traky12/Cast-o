import React, { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import axios from "axios";
import Web3 from "web3";
import ForestOwnershipTokenABI from "../abis/ForestOwnershipToken.json";
import "./PrivacyModule.css";
import ConfirmationModal from "./ConfirmationModal";
import AuditTrail from "./AuditTrail";

const FOREST_CONTRACT_ADDRESS =
  process.env.REACT_APP_FOREST_OWNERSHIP_TOKEN_ADDRESS ||
  "0x0000000000000000000000000000000000000000";
const API_BASE = process.env.REACT_APP_API_BASE || "";

function PrivacyModule() {
  const navigate = useNavigate();
  const [web3, setWeb3] = useState(null);
  const [account, setAccount] = useState("");
  const [tokenId, setTokenId] = useState("");
  const [propertyData, setPropertyData] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [successData, setSuccessData] = useState(null);
  const [error, setError] = useState(null);
  const [showConfirmation, setShowConfirmation] = useState(false);
  const [auditTrail, setAuditTrail] = useState([]);

  useEffect(() => {
    if (window.ethereum) {
      const w = new Web3(window.ethereum);
      setWeb3(w);
      window.ethereum.request({ method: "eth_requestAccounts" }).then((accounts) => {
        setAccount(accounts[0] || "");
      }).catch(console.error);
    }
  }, []);

  useEffect(() => {
    if (!tokenId) {
      setPropertyData(null);
      setAuditTrail([]);
      return;
    }
    const fetchProperty = async () => {
      try {
        const res = await axios.get(`${API_BASE}/api/property/${tokenId}`);
        setPropertyData(res.data);
        setError(null);
      } catch (err) {
        if (web3 && FOREST_CONTRACT_ADDRESS !== "0x0000000000000000000000000000000000000000") {
          const contract = new web3.eth.Contract(ForestOwnershipTokenABI, FOREST_CONTRACT_ADDRESS);
          try {
            const prop = await contract.methods.getProperty(tokenId).call();
            const certs = await contract.methods.getCertifications(tokenId).call();
            setPropertyData({
              parcelaId: prop[0],
              owner: prop[1],
              area: prop[3].toString(),
              certifications: Array.isArray(certs) ? certs : [],
              ipfsHash: prop[6],
            });
            setError(null);
          } catch (e) {
            setPropertyData(null);
            setError("No se pudo cargar la propiedad. Comprueba el Token ID.");
          }
        } else {
          setPropertyData(null);
          setError("Conecta la wallet o comprueba la configuración del contrato.");
        }
      }
    };
    fetchProperty();
  }, [tokenId, web3]);

  useEffect(() => {
    if (!tokenId) {
      return;
    }
    const fetchAuditTrail = async () => {
      try {
        const res = await axios.get(
          `${API_BASE}/api/audit/trail`,
          {
            params: { tokenId },
            headers: {
              Authorization: `Bearer ${localStorage.getItem("authToken") || ""}`,
            },
          }
        );
        setAuditTrail(res.data || []);
      } catch (e) {
        // no interrumpir la UX por errores de auditoría
        // eslint-disable-next-line no-console
        console.error("Error cargando trail de auditoría", e);
      }
    };
    fetchAuditTrail();
  }, [tokenId]);

  const handleErasureRequest = () => {
    setShowConfirmation(true);
  };

  const confirmErasure = async () => {
    setShowConfirmation(false);
    setIsLoading(true);
    setError(null);
    setSuccessData(null);
    const walletAddress = account || (window.ethereum && (await window.ethereum.request({ method: "eth_requestAccounts" }))?.[0]);
    if (!walletAddress) {
      setError("Conecta tu wallet primero.");
      setIsLoading(false);
      return;
    }

    try {
      const response = await axios.post(
        `${API_BASE}/api/privacy/request-erasure`,
        {
          token_id: parseInt(tokenId, 10),
          wallet_address: walletAddress,
          email: null,
          federation_metadata: {
            jurisdiction: "ES-EX",
            legal_basis: "GDPR Art. 17",
            dpo_contact: "dpo@juntaextremadura.es",
          },
        },
        {
          headers: {
            Authorization: `Bearer ${localStorage.getItem("authToken") || ""}`,
            "X-Federation-Token": localStorage.getItem("federationToken") || "",
          },
        }
      );
      const data = response.data;
      if (data.success) {
        setSuccessData({
          request_id: data.request_id,
          transaction_hash: data.transaction_hash,
          certificate_url: data.certificate_url,
          redacted_fields: data.redacted_fields || [],
        });
        setAuditTrail((prev) => [
          ...prev,
          {
            timestamp: new Date().toISOString(),
            action: "erasure_request",
            status: "completed",
            transactionHash: data.transaction_hash,
            certificateUrl: data.certificate_url,
          },
        ]);
      } else {
        setError(data.detail || data.error || "Error al procesar la solicitud.");
      }
    } catch (err) {
      const detail = err.response?.data?.detail || err.message;
      setError(Array.isArray(detail) ? detail.join(", ") : detail);
      setAuditTrail((prev) => [
        ...prev,
        {
          timestamp: new Date().toISOString(),
          action: "erasure_request",
          status: "failed",
          error: detail,
        },
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  const downloadCertificate = () => {
    if (successData?.certificate_url) {
      window.open(`${API_BASE}${successData.certificate_url}`, "_blank");
    }
  };

  return (
    <div className="privacy-module">
      <button type="button" onClick={() => navigate("/")} className="back-button">
        ← Volver al dashboard
      </button>

      <h2>🔒 Ejercer Derecho al Olvido (GDPR Art. 17)</h2>
      <p className="description">
        Este módulo te permite solicitar la eliminación de tus datos personales
        de los metadatos de tu propiedad forestal, en cumplimiento con el
        Reglamento General de Protección de Datos (GDPR).
      </p>

      <div className="token-selector">
        <label>Selecciona tu Token ID:</label>
        <input
          type="text"
          placeholder="Ej: 1"
          value={tokenId}
          onChange={(e) => setTokenId(e.target.value)}
          disabled={isLoading}
        />
      </div>

      {propertyData && (
        <div className="property-preview">
          <h3>Datos de la Propiedad</h3>
          <p><strong>Parcela ID:</strong> {propertyData.parcelaId}</p>
          <p><strong>Área:</strong> {propertyData.area} m²</p>
          <p><strong>Certificaciones:</strong> {propertyData.certifications?.join(", ") || "Ninguna"}</p>
          <p><strong>Propietario actual:</strong> {propertyData.owner}</p>
          {propertyData.ipfsHash && (
            <button
              type="button"
              onClick={() => window.open(`https://ipfs.io/ipfs/${propertyData.ipfsHash}`, "_blank")}
              className="metadata-button"
            >
              Ver Metadatos Actuales
            </button>
          )}
        </div>
      )}

      {error && <div className="error-message">{error}</div>}

      <button
        type="button"
        onClick={handleErasureRequest}
        disabled={!tokenId || isLoading}
        className="erasure-button"
      >
        {isLoading ? "Procesando…" : "EJERCER DERECHO AL OLVIDO"}
      </button>

      <ConfirmationModal
        isOpen={showConfirmation}
        onClose={() => setShowConfirmation(false)}
        onConfirm={confirmErasure}
        title="Confirmar Borrado de Datos"
        message={
          <div>
            <p>
              Estás a punto de ejercer tu <strong>derecho al olvido</strong>{" "}
              (GDPR Art. 17).
            </p>
            <p>Esta acción:</p>
            <ul>
              <li>
                Borrará tus datos personales de los metadatos de la propiedad en
                GaiaChain/IPFS.
              </li>
              <li>
                Mantendrá la información catastral obligatoria (Ley 3/2023 de
                Montes).
              </li>
              <li>
                Generará un certificado de borrado verificable en blockchain
                para tu registro.
              </li>
            </ul>
            <p>
              <strong>¿Estás seguro de que quieres continuar?</strong>
            </p>
          </div>
        }
      />

      {successData && (
        <div className="success-message">
          <h3>✅ Solicitud procesada con éxito</h3>
          <p><strong>ID de solicitud:</strong> {successData.request_id}</p>
          <p>
            <strong>Transacción:</strong>{" "}
            <a
              href={`https://explorer.gaiachain.castuo-system.com/tx/${successData.transaction_hash}`}
              target="_blank"
              rel="noopener noreferrer"
            >
              {successData.transaction_hash?.slice(0, 10)}...
            </a>
          </p>
          {successData.redacted_fields?.length > 0 && (
            <p><strong>Campos borrados:</strong> {successData.redacted_fields.join(", ")}</p>
          )}
          <button type="button" onClick={downloadCertificate} className="download-button">
            DESCARGAR CERTIFICADO DE BORRADO (PDF)
          </button>
        </div>
      )}

      {tokenId && (
        <div className="audit-section">
          <h3>📜 Trail de Auditoría (GDPR Art. 30)</h3>
          <AuditTrail entries={auditTrail} />
          <div className="federation-notice">
            <p>
              ⚖️ <strong>Federación de Datos:</strong>
            </p>
            <p>
              Esta solicitud se procesa bajo el marco de federación de la UE, en cumplimiento con:
            </p>
            <ul>
              <li>
                <strong>GDPR Art. 45:</strong> Transferencia internacional de datos.
              </li>
              <li>
                <strong>eIDAS:</strong> Identificación electrónica certificada.
              </li>
              <li>
                <strong>Ley 3/2023:</strong> Gestión de montes de Extremadura.
              </li>
            </ul>
            <p>
              Todos los datos se registran en <strong>GaiaChain</strong> para auditoría inmutable.
            </p>
          </div>
        </div>
      )}
    </div>
  );
}

export default PrivacyModule;
