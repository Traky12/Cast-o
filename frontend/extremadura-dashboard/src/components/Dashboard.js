import React, { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import Web3 from "web3";
import ForestOwnershipTokenABI from "../abis/ForestOwnershipToken.json";

const FOREST_CONTRACT_ADDRESS =
  process.env.REACT_APP_FOREST_OWNERSHIP_TOKEN_ADDRESS ||
  "0x0000000000000000000000000000000000000000";

function Dashboard() {
  const navigate = useNavigate();
  const [web3, setWeb3] = useState(null);
  const [account, setAccount] = useState("");
  const [tokenId, setTokenId] = useState("");
  const [propertyData, setPropertyData] = useState(null);
  const [subsidyAmount, setSubsidyAmount] = useState(null);
  const [subsidyCodes, setSubsidyCodes] = useState([]);
  const [certifications, setCertifications] = useState([]);

  useEffect(() => {
    const init = async () => {
      if (window.ethereum) {
        const w = new Web3(window.ethereum);
        setWeb3(w);
        try {
          const accounts = await window.ethereum.request({ method: "eth_requestAccounts" });
          setAccount(accounts[0] || "");
        } catch (e) {
          console.error(e);
        }
      }
    };
    init();
  }, []);

  const loadPropertyData = async () => {
    if (!web3 || FOREST_CONTRACT_ADDRESS === "0x0000000000000000000000000000000000000000") return;
    const contract = new web3.eth.Contract(ForestOwnershipTokenABI, FOREST_CONTRACT_ADDRESS);
    try {
      const prop = await contract.methods.getProperty(tokenId).call();
      const [parcelaId, owner, coordinates, area, treeSpecies, carbonSequestered, ipfsHash, isProtected] = prop;
      setPropertyData({
        parcelaId,
        owner,
        coordinates,
        area: area.toString(),
        treeSpecies,
        carbonSequestered: carbonSequestered.toString(),
        ipfsHash,
        isProtected,
      });
      const amount = await contract.methods.calculateSubsidies(tokenId).call();
      setSubsidyAmount(amount.toString());
      const codes = await contract.methods.getEligibleSubsidies(tokenId).call();
      setSubsidyCodes(Array.isArray(codes) ? codes : []);
      const certs = await contract.methods.getCertifications(tokenId).call();
      setCertifications(Array.isArray(certs) ? certs : []);
    } catch (e) {
      console.error(e);
      setPropertyData(null);
      setSubsidyAmount(null);
      setSubsidyCodes([]);
      setCertifications([]);
    }
  };

  return (
    <div style={{ padding: "2rem", fontFamily: "sans-serif", maxWidth: 720 }}>
      <nav style={{ marginBottom: "1rem" }}>
        <button
          type="button"
          className="nav-link"
          onClick={() => navigate("/privacidad")}
          style={{ background: "none", border: "none", cursor: "pointer", color: "#007bff", textDecoration: "underline", marginRight: "1rem" }}
        >
          🔒 Módulo de privacidad (Derecho al olvido)
        </button>
        <button
          type="button"
          className="nav-link"
          onClick={() => navigate("/facturacion")}
          style={{ background: "none", border: "none", cursor: "pointer", color: "#007bff", textDecoration: "underline" }}
        >
          📊 Facturación
        </button>
      </nav>
      <h1>Dashboard de Gestión Forestal (Junta de Extremadura)</h1>
      <p>CASTÚO-SYSTEM™ — ForestOwnershipToken</p>
      <p>Cuenta: {account || "—"}</p>

      <div style={{ marginTop: "1rem" }}>
        <input
          type="text"
          placeholder="Token ID (ej: 1)"
          value={tokenId}
          onChange={(e) => setTokenId(e.target.value)}
        />
        <button onClick={loadPropertyData}>Cargar datos</button>
      </div>

      {propertyData && (
        <div style={{ marginTop: "1.5rem", fontSize: "0.95rem" }}>
          <h2>Datos de la propiedad</h2>
          <p><strong>Parcela ID:</strong> {propertyData.parcelaId}</p>
          <p><strong>Área:</strong> {propertyData.area} m²</p>
          <p><strong>Coordenadas:</strong> {propertyData.coordinates}</p>
          <p><strong>Especies:</strong> {propertyData.treeSpecies}</p>
          <p><strong>CO₂ secuestrado:</strong> {propertyData.carbonSequestered} kg/año</p>
          <p><strong>Protegida:</strong> {propertyData.isProtected ? "Sí" : "No"}</p>
          <p><strong>Certificaciones:</strong> {certifications.length ? certifications.join(", ") : "Ninguna"}</p>
          <p><strong>Subvenciones calculadas:</strong> €{subsidyAmount}/año</p>
          {subsidyCodes.length > 0 && (
            <p><strong>Códigos elegibles:</strong> {subsidyCodes.join(", ")}</p>
          )}
          {propertyData.ipfsHash && (
            <a href={`https://ipfs.io/ipfs/${propertyData.ipfsHash}`} target="_blank" rel="noopener noreferrer">
              Ver metadatos en IPFS
            </a>
          )}
        </div>
      )}
    </div>
  );
}

export default Dashboard;
