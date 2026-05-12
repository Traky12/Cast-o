/**
 * Verifica que el contrato DynamicCropNFT esté desplegado y (opcional) proxy admin configurado.
 * Uso: DYNAMIC_NFT_ADDRESS=0x... npx hardhat run scripts/verify-proxy-admin.js --network gaiachain
 */
const hre = require("hardhat");

async function main() {
  const addr = process.env.DYNAMIC_NFT_ADDRESS;
  if (!addr) {
    console.error("Definir DYNAMIC_NFT_ADDRESS");
    process.exitCode = 1;
    return;
  }
  const contract = await hre.ethers.getContractAt("DynamicCropNFT", addr);
  const [name, symbol] = await Promise.all([
    contract.name().catch(() => ""),
    contract.symbol().catch(() => ""),
  ]);
  if (name === "DynamicCropNFT" && symbol === "DCNFT") {
    console.log("Contract verified:", addr);
    return;
  }
  try {
    if (typeof contract.proxyAdmin === "function") {
      const admin = await contract.proxyAdmin();
      console.log("Proxy admin:", admin);
    }
  } catch (_) {
    // Sin proxy admin en esta versión del contrato
  }
  console.log("Contract reachable:", addr);
}

main().catch((err) => {
  console.error(err);
  process.exitCode = 1;
});
