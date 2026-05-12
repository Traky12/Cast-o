const hre = require("hardhat");

async function main() {
  const bioCoinAddress = process.env.BIOCOIN_ADDRESS || "0x0000000000000000000000000000000000000000";
  if (bioCoinAddress === "0x0000000000000000000000000000000000000000") {
    console.error("Definir BIOCOIN_ADDRESS");
    process.exit(1);
  }

  const CarbonMarketplace = await hre.ethers.getContractFactory("CarbonMarketplace");
  const marketplace = await CarbonMarketplace.deploy(bioCoinAddress);
  await marketplace.waitForDeployment();
  const addr = await marketplace.getAddress();
  console.log("CarbonMarketplace desplegado en:", addr);
  return addr;
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
