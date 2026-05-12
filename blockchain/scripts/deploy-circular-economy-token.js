const hre = require("hardhat");

async function main() {
  const CircularEconomyToken = await hre.ethers.getContractFactory("CircularEconomyToken");
  const contract = await CircularEconomyToken.deploy();
  await contract.waitForDeployment();
  const addr = await contract.getAddress();
  console.log("CircularEconomyToken desplegado en:", addr);
  console.log('Export: export CIRCULAR_ECONOMY_TOKEN_ADDRESS="' + addr + '"');
  return addr;
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
