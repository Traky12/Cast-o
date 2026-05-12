const hre = require("hardhat");

async function main() {
  const CompostToken = await hre.ethers.getContractFactory("CompostToken");
  const contract = await CompostToken.deploy();
  await contract.waitForDeployment();
  const addr = await contract.getAddress();
  console.log("CompostToken desplegado en:", addr);
  console.log("Export para scripts: export COMPOST_TOKEN_ADDRESS=\"" + addr + "\"");
  return addr;
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
