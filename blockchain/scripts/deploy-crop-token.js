const hre = require("hardhat");

async function main() {
  const CropToken = await hre.ethers.getContractFactory("CropToken");
  const contract = await CropToken.deploy();
  await contract.waitForDeployment();
  const addr = await contract.getAddress();
  console.log("CropToken desplegado en:", addr);
  return addr;
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
