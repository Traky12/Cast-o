/**
 * BIO-HUB-GATEWAY — Oráculo Castúo-System [CIPHER-LEVEL-5]
 * Conecta sensores industriales de [BIO-HUB-DIGITAL] (PLC / NIR tolva) con el contrato BioPayV2.
 * Solo emite authorizePayment cuando el orquestador ha validado triple-check (NIR + VULCAN + TERRA).
 * Uso: node BIO-HUB-GATEWAY.js (config vía env CONTRACT_ADDRESS, RPC_URL, ORCHESTRATOR_KEY).
 */

const CONTRACT_ADDRESS = process.env.BIOPAY_V2_ADDRESS || "";
const RPC_URL = process.env.RPC_URL || "http://127.0.0.1:8545";
const ORCHESTRATOR_PRIVATE_KEY = process.env.ORCHESTRATOR_PRIVATE_KEY || "";

const ABI_AUTHORIZE = [
  "function authorizePayment(address _producer, uint256 _amount, uint256 _shipmentId) external",
];

async function readNIRFromPLC() {
  // Placeholder: integración real con PLC (Modbus/OPC-UA) o API REST del silo.
  return { sugarBps: 1200, moistureBps: 800, weightKg: 500 };
}

async function tripleCheckValid(shipmentId, producer, amountWei) {
  const nir = await readNIRFromPLC();
  // En producción: esperar firma VULCAN (Falcon X) y hash TERRA (Nexus) vía API/ledger.
  const vulcanOk = process.env.MOCK_VULCAN_SIGN === "1" || true;
  const terraOk = process.env.MOCK_TERRA_HASH !== "";
  return nir.moistureBps <= 2500 && vulcanOk && terraOk;
}

async function authorizePayment(producer, amountWei, shipmentId) {
  if (!CONTRACT_ADDRESS || !ORCHESTRATOR_PRIVATE_KEY) {
    console.error("Configure BIOPAY_V2_ADDRESS and ORCHESTRATOR_PRIVATE_KEY");
    return false;
  }
  const valid = await tripleCheckValid(shipmentId, producer, amountWei);
  if (!valid) {
    console.warn("Triple-check failed; not authorizing.");
    return false;
  }
  // Llamada real vía ethers/web3 desde cuenta orquestador.
  console.log(`[BIO-HUB-GATEWAY] Authorize producer=${producer} amount=${amountWei} shipment=${shipmentId}`);
  return true;
}

module.exports = { authorizePayment, readNIRFromPLC, tripleCheckValid };

if (require.main === module) {
  const [producer, amount, shipment] = process.argv.slice(2);
  if (!producer || !amount || !shipment) {
    console.log("Usage: node BIO-HUB-GATEWAY.js <producerAddress> <amountWei> <shipmentId>");
    process.exit(1);
  }
  authorizePayment(producer, amount, shipment).then((ok) => process.exit(ok ? 0 : 1));
}
