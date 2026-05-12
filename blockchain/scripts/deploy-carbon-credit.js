const hre = require("hardhat");

async function main() {
  const CarbonCredit = await hre.ethers.getContractFactory("CarbonCredit");
  const contract = await CarbonCredit.deploy();
  await contract.waitForDeployment();
  const addr = await contract.getAddress();
  console.log("CarbonCredit desplegado en:", addr);
  return addr;
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
