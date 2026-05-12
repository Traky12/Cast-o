const hre = require("hardhat");

async function main() {
  const bioCoinAddress = process.env.BIOCOIN_ADDRESS || "0x0000000000000000000000000000000000000000";
  if (bioCoinAddress === "0x0000000000000000000000000000000000000000") {
    console.error("Definir BIOCOIN_ADDRESS (dirección del contrato BioCoin en GaiaChain)");
    process.exit(1);
  }

  const BioCoinCarbonMarket = await hre.ethers.getContractFactory("BioCoinCarbonMarket");
  const market = await BioCoinCarbonMarket.deploy(bioCoinAddress);
  await market.waitForDeployment();
  const addr = await market.getAddress();
  console.log("BioCoinCarbonMarket desplegado en:", addr);
  return addr;
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
