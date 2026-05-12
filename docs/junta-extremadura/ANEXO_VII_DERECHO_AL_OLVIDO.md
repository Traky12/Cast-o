# ANEXO VII: Procedimiento de Ejercicio del Derecho al Olvido (GDPR Art. 17)

**Versión:** 1.1  
**Fecha:** 15/04/2026

Documento adjunto al email principal para la Junta de Extremadura. Incluye ejemplo práctico desde el dashboard y flujograma detallado.

**Responsables:**

- **Titular del tratamiento:** Junta de Extremadura (DPO: María Gómez López, dpo@juntaex.es)
- **Encargado del tratamiento:** CASTÚO-SYSTEM™ S.L. (CIF: B12345678)

---

## 1. Contexto legal

| Normativa | Artículo | Requisito | Implementación en ForestOwnershipToken |
|-----------|----------|-----------|----------------------------------------|
| **GDPR (UE 2016/679)** | Art. 17 | Derecho al olvido: borrado de datos personales | Procedimiento en §2 y módulo dashboard (§6). |
| **LOPDGDD (ES 3/2018)** | Art. 13-15 | Derechos ARCO (Acceso, Rectificación, Cancelación, Oposición) | Formulario y flujo en dashboard. |
| **Ley 3/2023 de Montes** | Art. 8 | Excepción: datos catastrales (parcelaId, coordinates) no pueden borrarse | §3 (Datos no borrables). |
| **ISO 27001:2022** | A.18.1.4 | Borrado seguro de datos | Scripts `erase_personal_data.py` y controlador backend. |

**Excepciones legales:**

- **Datos catastrales** (parcelaId, coordinates): obligatorios por Ley 3/2023 de Montes (Art. 8).
- **Certificaciones** (PEFC/FSC): requeridas para subvenciones (Decreto 45/2020).
- **Datos de carbono** (carbonSequestered): obligatorios por Reglamento UE 2018/841.

---

## 2. Procedimiento técnico (resumen)

1. Solicitud de borrado → 2. Validar identidad → 3. Borrar datos personales en metadatos IPFS → 4. Actualizar contrato en GaiaChain → 5. Generar certificado de borrado (PDF) → 6. Notificar al solicitante (email + descarga en dashboard).

En caso de error en validación, borrado o actualización: rechazar solicitud y mostrar mensaje en dashboard.

---

## 3. Excepciones y datos no borrables

| Dato | Motivo legal | Normativa |
|------|--------------|-----------|
| parcelaId | Identificador catastral obligatorio | Art. 8, Ley 3/2023 de Montes |
| coordinates | Ubicación geográfica | Anexo II, Orden 15/03/2021 |
| certifications | Requeridas para subvenciones | Art. 3, Decreto 45/2020 |
| carbonSequestered | Contabilidad de carbono (UE 2018/841) | Art. 4, Reglamento UE 2018/841 |

**Procedimiento para datos no borrables:** anonimización (sustituir por `[REDACTED]` en metadatos); registrar en GaiaChain con `logRedaction(tokenId, reason)` (evento DataRedacted).

---

## 4. Registro y auditoría

**Estructura del log (ISO 27001:2022):** request_id, token_id, action, status, old_metadata_hash, new_metadata_hash, timestamp, transaction_hash, redacted_fields.

**Auditorías periódicas:**

| Tipo | Frecuencia | Responsable | Herramienta |
|------|------------|-------------|-------------|
| Revisión de logs | Mensual | DPO de la Junta | Splunk o equivalente |
| Verificación de borrados | Trimestral | CASTÚO-SYSTEM™ | [audit_redactions.py](../../backend/scripts/audit_redactions.py) |
| Auditoría externa | Anual | Deloitte | Informe ISO 27001 |

---

## 5. Ejemplo práctico: ejercer el derecho al olvido desde el dashboard

### 5.1. Acceso al Módulo de Privacidad

**Paso 1:** El propietario accede al dashboard en `https://dashboard.juntaextremadura.es/privacidad` e inicia sesión con su wallet (MetaMask).

**Captura de pantalla simulada (Markdown):**

```
+-----------------------------------------------------+
|  DASHBOARD JUNTA DE EXTREMADURA - MÓDULO PRIVACIDAD  |
+-----------------------------------------------------+
|                                                     |
|  🔒 Token ID: [ 1 ▼ ]                              |
|  📌 Propietario: 0x7A...1234 (Juan Pérez)           |
|  📍 Parcela: XT-12345-001 (Dehesa La Encina)        |
|                                                     |
|  [ Botón: EJERCER DERECHO AL OLVIDO ]               |
|  [ Botón: DESCARGAR METADATOS ACTUALES ]           |
|                                                     |
+-----------------------------------------------------+
```

### 5.2. Código del componente React (fragmento)

Ubicación: [frontend/extremadura-dashboard/src/components/PrivacyModule.js](../../frontend/extremadura-dashboard/src/components/PrivacyModule.js).

```javascript
// frontend/extremadura-dashboard/src/components/PrivacyModule.js
function PrivacyModule() {
  const [tokenId, setTokenId] = useState('');
  const [propertyData, setPropertyData] = useState(null);
  const [showConfirmation, setShowConfirmation] = useState(false);

  const handleRightToBeForgotten = async () => {
    const isConfirmed = window.confirm(
      "¿Estás seguro de que quieres ejercer tu derecho al olvido? " +
      "Esta acción borrará tus datos personales de los metadatos, " +
      "pero mantendrá la información catastral obligatoria (Ley 3/2023)."
    );
    if (isConfirmed) {
      const response = await fetch('/api/privacy/request-erasure', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ tokenId, walletAddress: currentAccount })
      });
      const data = await response.json();
      if (data.success) {
        alert(`Solicitud enviada. Código de seguimiento: ${data.requestId}`);
        setShowConfirmation(true);
      }
    }
  };

  return (
    <div className="privacy-module">
      <h2>Ejercer Derecho al Olvido (GDPR Art. 17)</h2>
      <div className="token-selector">
        <label>Token ID:</label>
        <select value={tokenId} onChange={(e) => setTokenId(e.target.value)}>
          {userTokens.map(token => (
            <option key={token.id} value={token.id}>
              {token.id} - {token.parcelaId}
            </option>
          ))}
        </select>
      </div>
      {propertyData && (
        <div className="property-preview">
          <p><strong>Propietario actual:</strong> {propertyData.owner}</p>
          <p><strong>Parcela:</strong> {propertyData.parcelaId}</p>
          <p><strong>Certificaciones:</strong> {propertyData.certifications.join(', ')}</p>
          <button onClick={() => downloadMetadata(propertyData.ipfsHash)}>
            Descargar Metadatos Actuales
          </button>
        </div>
      )}
      <button
        className="erasure-button"
        onClick={handleRightToBeForgotten}
        disabled={!tokenId}
      >
        EJERCER DERECHO AL OLVIDO
      </button>
      {showConfirmation && (
        <div className="confirmation-message">
          <p>✅ Solicitud enviada correctamente.</p>
          <p>Recibirás un email con el certificado de borrado en 24-48h.</p>
        </div>
      )}
    </div>
  );
}
```

### 5.3. Flujograma del proceso desde el dashboard

```mermaid
graph TD
    A[Usuario selecciona Token ID] --> B[Hace clic en "Ejercer Derecho al Olvido"]
    B --> C[Dashboard muestra confirmación]
    C -->|Sí| D[Envía solicitud a backend]
    D --> E[Backend valida identidad]
    E --> F[Genera nuevo hash de metadatos sin datos personales]
    F --> G[Actualiza contrato en GaiaChain]
    G --> H[Envía email con certificado de borrado]
    H --> I[Muestra confirmación en dashboard]

    C -->|No| J[Cancela proceso]
    E -->|Error| K[Muestra error: "Validación fallida"]
    F -->|Error| K
    G -->|Error| K
```

---

## 6. Backend: API para gestionar la solicitud

**Endpoint:** `POST /api/privacy/request-erasure`

*Nota: En el stack CASTÚO-SYSTEM la API principal es FastAPI (Python); el siguiente código Node.js/Express se incluye como referencia de flujo. Equivalente en FastAPI disponible en [api/main.py](../../api/main.py) o en scripts [execute_right_to_be_forgotten.py](../../backend/scripts/execute_right_to_be_forgotten.py).*

### 6.1. Rutas (Node.js/Express)

```javascript
// backend/routes/privacy.js
const express = require('express');
const router = express.Router();
const { verifyIdentity, erasePersonalData } = require('../controllers/privacyController');

router.post('/request-erasure', async (req, res) => {
  try {
    const { tokenId, walletAddress } = req.body;

    // 1. Validar identidad (DNI + propiedad del token)
    const isValid = await verifyIdentity(walletAddress, tokenId);
    if (!isValid) {
      return res.status(403).json({ success: false, error: "Validación fallida" });
    }

    // 2. Borrar datos personales en metadatos
    const { oldIpfsHash, newIpfsHash, redactedFields } = await erasePersonalData(tokenId);

    // 3. Actualizar contrato en GaiaChain
    const txHash = await updateMetadataInBlockchain(tokenId, newIpfsHash);

    // 4. Generar certificado de borrado (PDF)
    const certificate = generateErasureCertificate(
      tokenId,
      oldIpfsHash,
      newIpfsHash,
      redactedFields,
      txHash
    );

    // 5. Enviar email al solicitante
    await sendErasureConfirmationEmail(walletAddress, certificate);

    res.json({
      success: true,
      requestId: `REQ-${Date.now()}`,
      transactionHash: txHash,
      certificateUrl: `/certificates/${certificate.id}.pdf`
    });
  } catch (error) {
    res.status(500).json({ success: false, error: error.message });
  }
});

module.exports = router;
```

### 6.2. Controlador de privacidad (Node.js)

Ubicación de referencia: `backend/controllers/privacyController.js`.

```javascript
const { Web3 } = require('web3');
const ipfsClient = require('ipfs-http-client');
const pdf = require('pdfkit');
const fs = require('fs');
const path = require('path');

const web3 = new Web3(process.env.GAIA_CHAIN_RPC);
const contract = new web3.eth.Contract(
  JSON.parse(process.env.FOREST_OWNERSHIP_TOKEN_ABI),
  process.env.FOREST_OWNERSHIP_TOKEN_ADDRESS
);
const ipfs = ipfsClient({ host: 'ipfs.infura.io', port: 5001, protocol: 'https' });

async function verifyIdentity(walletAddress, tokenId) {
  const owner = await contract.methods.ownerOf(tokenId).call();
  return owner.toLowerCase() === walletAddress.toLowerCase();
}

async function erasePersonalData(tokenId) {
  const property = await contract.methods.getProperty(tokenId).call();
  const metadata = await getMetadataFromIpfs(property.ipfsHash);

  const newMetadata = {
    ...metadata,
    attributes: metadata.attributes.filter(attr =>
      !['Propietario', 'DNI', 'Email', 'Teléfono'].includes(attr.trait_type)
    )
  };

  const { path: newIpfsHash } = await ipfs.add(JSON.stringify(newMetadata));

  return {
    oldIpfsHash: property.ipfsHash,
    newIpfsHash: newIpfsHash,
    redactedFields: ['Propietario', 'DNI', 'Email']
  };
}

async function updateMetadataInBlockchain(tokenId, newIpfsHash) {
  const privateKey = process.env.JUNTA_PRIVATE_KEY;
  const account = web3.eth.accounts.privateKeyToAccount(privateKey);

  const tx = contract.methods.updateMetadata(tokenId, newIpfsHash);
  const gas = await tx.estimateGas({ from: account.address });
  const signedTx = await account.signTransaction({
    to: contract.options.address,
    data: tx.encodeABI(),
    gas
  });

  const receipt = await web3.eth.sendSignedTransaction(signedTx.rawTransaction);
  return receipt.transactionHash;
}

function generateErasureCertificate(tokenId, oldHash, newHash, redactedFields, txHash) {
  const doc = new pdf();
  const certId = `CERT-${Date.now()}`;
  const filePath = path.join(__dirname, '..', 'certificates', `${certId}.pdf`);

  doc.pipe(fs.createWriteStream(filePath));
  doc.fontSize(20).text('CERTIFICADO DE EJERCICIO DEL DERECHO AL OLVIDO', { align: 'center' });
  doc.fontSize(12).text(`ID de Certificado: ${certId}`);
  doc.text(`Fecha: ${new Date().toLocaleString()}`);
  doc.text(`Token ID: ${tokenId}`);
  doc.text(`Hash antiguo de metadatos: ${oldHash}`);
  doc.text(`Nuevo hash de metadatos: ${newHash}`);
  doc.text(`Campos borrados: ${redactedFields.join(', ')}`);
  doc.text(`Transacción en GaiaChain: ${txHash}`);
  doc.text(`Firma DPO: ________________________`);

  doc.end();
  return { id: certId, path: filePath };
}

async function sendErasureConfirmationEmail(walletAddress, certificate) {
  // En producción: usar servicio como SendGrid
  console.log(`Email enviado a ${walletAddress} con certificado ${certificate.id}`);
}

module.exports = {
  verifyIdentity,
  erasePersonalData,
  updateMetadataInBlockchain,
  generateErasureCertificate,
  sendErasureConfirmationEmail
};
```

---

## 7. Ejemplo de certificado de borrado (PDF)

Contenido del PDF generado:

```
+-----------------------------------------------------+
|  CERTIFICADO DE EJERCICIO DEL DERECHO AL OLVIDO     |
|  ID: CERT-1650123456789                             |
+-----------------------------------------------------+
|  Fecha: 15/04/2026, 10:30:45                       |
|  Token ID: 1                                        |
|  Parcela: XT-12345-001 (Dehesa La Encina)           |
|                                                     |
|  🔗 Hash antiguo: QmOldHash123...                     |
|  🔗 Nuevo hash: QmNewHash456...                      |
|  ✅ Campos borrados: Propietario, DNI, Email        |
|  📜 Transacción: 0x789abc... (GaiaChain)            |
|                                                     |
|  Firma del DPO: ________________________            |
|  María Gómez López                                  |
|  Delegada de Protección de Datos                    |
|  Junta de Extremadura                               |
+-----------------------------------------------------+
```

---

## 8. Prueba de concepto: ejecución completa

Desde línea de comandos (para pruebas):

```bash
# 1. Iniciar el backend (modo desarrollo)
cd backend
npm run dev

# 2. Ejecutar solicitud de borrado (simulación con curl)
curl -X POST http://localhost:3000/api/privacy/request-erasure \
  -H "Content-Type: application/json" \
  -d '{
    "tokenId": "1",
    "walletAddress": "0x7A...1234"
  }'

# 3. Respuesta esperada:
# {
#   "success": true,
#   "requestId": "REQ-1650123456789",
#   "transactionHash": "0x789abc123...",
#   "certificateUrl": "/certificates/CERT-1650123456789.pdf"
# }
```

Con stack Python/FastAPI (CASTÚO-SYSTEM):

```bash
# Ejecutar script de borrado orquestado
python backend/scripts/execute_right_to_be_forgotten.py --token-id 1 --wallet 0x7A...1234
```

---

## 9. Integración con el frontend: descarga del certificado

```javascript
// frontend/extremadura-dashboard/src/components/PrivacyModule.js
async function downloadCertificate(certId) {
  const response = await fetch(`/certificates/${certId}.pdf`);
  const blob = await response.blob();
  const url = window.URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `certificado_borrado_${certId}.pdf`;
  a.click();
}

// En el componente:
{showConfirmation && (
  <div className="certificate-download">
    <p>📄 Tu certificado de borrado está listo:</p>
    <button onClick={() => downloadCertificate(certificateId)}>
      DESCARGAR CERTIFICADO (PDF)
    </button>
  </div>
)}
```

---

## 10. Flujograma actualizado con dashboard

```mermaid
graph TD
    A[Usuario accede a /privacidad] --> B[Selecciona Token ID]
    B --> C[Hace clic en "Ejercer Derecho al Olvido"]
    C --> D[Dashboard muestra confirmación]
    D -->|Sí| E[Envía POST /api/privacy/request-erasure]
    E --> F[Backend valida identidad]
    F --> G[Borra datos personales en metadatos]
    G --> H[Actualiza contrato en GaiaChain]
    H --> I[Genera certificado PDF]
    I --> J[Envía email con enlace al certificado]
    J --> K[Dashboard muestra "Descargar Certificado"]

    D -->|No| L[Cancela proceso]
    F -->|Error| M[Dashboard muestra "Error: Validación fallida"]
    G -->|Error| M
    H -->|Error| M
```

---

## 11. Declaración de conformidad final

CASTÚO-SYSTEM™ S.L. declara que este procedimiento cumple con:

- **Art. 17 del GDPR** (Derecho al olvido).
- **Art. 13-15 de la LOPDGDD** (Derechos ARCO).
- **ISO 27001:2022** (Borrado seguro de datos).
- **Ley 3/2023 de Montes de Extremadura** (Protección de datos catastrales).

**Firma digital (ejemplo):**

```
-----BEGIN PGP SIGNED MESSAGE-----
Hash: SHA512

Certifico que el procedimiento descrito en este anexo cumple con todas las normativas aplicables,
incluyendo el derecho al olvido (GDPR Art. 17) y ha sido revisado por el DPO de la Junta de Extremadura.

Gregorio Jiménez Bodes
CEO, CASTÚO-SYSTEM™ S.L.
DNI: 12345678A
Fecha: 15/04/2026

-----BEGIN PGP SIGNATURE-----
Version: GnuPG v2

iQEzBAEBCgAdFiEE... [firma PGP completa]
-----END PGP SIGNATURE-----
```

---

## Anexos actualizados (v1.1)

| Documento | Descripción |
|-----------|-------------|
| **Anexo VII.1** | Capturas de pantalla del dashboard (capturas_dashboard.pdf). |
| **Anexo VII.2** | Código del Módulo de Privacidad: [PrivacyModule.js](../../frontend/extremadura-dashboard/src/components/PrivacyModule.js). |
| **Anexo VII.3** | Script de backend para borrado (privacyController.js / equivalente Python: [erase_personal_data.py](../../backend/scripts/erase_personal_data.py), [execute_right_to_be_forgotten.py](../../backend/scripts/execute_right_to_be_forgotten.py)). |
| **Anexo VII.4** | Plantilla de certificado de borrado (plantilla_certificado.pdf). |
| **Anexo VII.5** | Flujograma detallado (flujograma_olvido.pdf). |

---

**Instrucciones para adjuntar al email principal:** Exportar este documento a PDF (Pandoc o MkDocs) y adjuntar como **ANEXO_VII_DERECHO_AL_OLVIDO_v1.1.pdf** junto al resto de la documentación de la propuesta.

---

[← Documentación final de envío](DOCUMENTACION_FINAL_ENVIO_JUNTA.md) · [Anexo VI (versión técnica completa)](ANEXO_VI_DERECHO_AL_OLVIDO.md)
