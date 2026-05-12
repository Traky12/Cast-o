import React, { useState } from "react";
import Web3 from "web3";
import GreenLicenseTokenABI from "./abis/GreenLicenseToken.json";

const CONTRACT_ADDRESS =
  process.env.REACT_APP_DOCUMENT_TOKEN_ADDRESS ||
  "0x0000000000000000000000000000000000000000";

function App() {
  const [web3, setWeb3] = useState(null);
  const [account, setAccount] = useState("");
  const [documentHash, setDocumentHash] = useState("");
  const [tokenId, setTokenId] = useState("");
  const [isValid, setIsValid] = useState(null);
  const [metadata, setMetadata] = useState(null);
  const [ipfsData, setIpfsData] = useState(null);

  const connectWallet = async () => {
    if (window.ethereum) {
      const web3Instance = new Web3(window.ethereum);
      setWeb3(web3Instance);
      try {
        const accounts = await window.ethereum.request({ method: "eth_requestAccounts" });
        setAccount(accounts[0] || "");
      } catch (err) {
        console.error(err);
      }
    }
  };

  const verifyDocument = async () => {
    if (!web3 || CONTRACT_ADDRESS === "0x0000000000000000000000000000000000000000") {
      setIsValid(false);
      setMetadata(null);
      return;
    }
    const contract = new web3.eth.Contract(GreenLicenseTokenABI, CONTRACT_ADDRESS);
    try {
      const valid = await contract.methods.verifyDocument(tokenId, documentHash).call();
      setIsValid(valid);
      if (valid) {
        const meta = await contract.methods.getDocumentMetadata(tokenId).call();
        const [docHash, docType, ipfsHash, timestamp, responsible] = meta;
        setMetadata({
          documentHash: docHash,
          documentType: docType,
          ipfsHash,
          timestamp: timestamp.toString(),
          responsible,
        });
        if (ipfsHash) {
          try {
            const res = await fetch(`https://ipfs.io/ipfs/${ipfsHash}`);
            if (res.ok) {
              const json = await res.json();
              setIpfsData(json);
            } else {
              setIpfsData(null);
            }
          } catch {
            setIpfsData(null);
          }
        } else {
          setIpfsData(null);
        }
      } else {
        setMetadata(null);
        setIpfsData(null);
      }
    } catch (err) {
      console.error(err);
      setIsValid(false);
      setMetadata(null);
      setIpfsData(null);
    }
  };

  return (
    <div style={{ padding: "2rem", fontFamily: "sans-serif", maxWidth: 640 }}>
      <h1>Verificación de Documentos (Junta de Extremadura)</h1>
      <p>CASTÚO-SYSTEM™ — GaiaChain 2.0</p>
      <button onClick={connectWallet}>Conectar Wallet</button>
      <p>Cuenta: {account || "—"}</p>

      <div style={{ marginTop: "1.5rem" }}>
        <h2>Verificar documento</h2>
        <div style={{ display: "flex", flexDirection: "column", gap: "0.5rem" }}>
          <input
            type="text"
            placeholder="Token ID (ej: 1)"
            value={tokenId}
            onChange={(e) => setTokenId(e.target.value)}
          />
          <input
            type="text"
            placeholder="SHA-512 del documento (hex)"
            value={documentHash}
            onChange={(e) => setDocumentHash(e.target.value)}
            style={{ width: "100%" }}
          />
          <button onClick={verifyDocument}>Verificar</button>
        </div>

        {isValid !== null && (
          <div style={{ marginTop: "1rem" }}>
            <h3>Resultado: {isValid ? "✅ VÁLIDO" : "❌ INVÁLIDO"}</h3>
            {metadata && (
              <div style={{ fontSize: "0.9rem" }}>
                <p>Tipo: {metadata.documentType}</p>
                <p>Responsable: {metadata.responsible}</p>
                <p>Fecha: {metadata.timestamp ? new Date(Number(metadata.timestamp) * 1000).toLocaleString() : "—"}</p>
                {metadata.ipfsHash && (
                  <a href={`https://ipfs.io/ipfs/${metadata.ipfsHash}`} target="_blank" rel="noopener noreferrer">
                    Ver metadatos en IPFS
                  </a>
                )}
                {ipfsData && (
                  <pre style={{ background: "#f0f0f0", padding: "0.5rem", overflow: "auto" }}>
                    {JSON.stringify(ipfsData, null, 2)}
                  </pre>
                )}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

export default App;
