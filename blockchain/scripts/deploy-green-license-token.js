const hre = require("hardhat");

async function main() {
  const GreenLicenseToken = await hre.ethers.getContractFactory("GreenLicenseToken");
  const contract = await GreenLicenseToken.deploy();
  await contract.waitForDeployment();
  const addr = await contract.getAddress();
  console.log("GreenLicenseToken desplegado en:", addr);
  console.log('Export: export DOCUMENT_TOKEN_ADDRESS="' + addr + '"');
  return addr;
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
