const hre = require("hardhat");

async function main() {
  const ForestOwnershipToken = await hre.ethers.getContractFactory("ForestOwnershipToken");
  const contract = await ForestOwnershipToken.deploy();
  await contract.waitForDeployment();
  const addr = await contract.getAddress();
  console.log("ForestOwnershipToken desplegado en:", addr);
  console.log('Export: export FOREST_OWNERSHIP_TOKEN_ADDRESS="' + addr + '"');
  return addr;
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
