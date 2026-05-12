const hre = require("hardhat");

async function main() {
  const ExtremaduraFireNFT = await hre.ethers.getContractFactory("ExtremaduraFireNFT");
  const contract = await ExtremaduraFireNFT.deploy();
  await contract.waitForDeployment();
  const addr = await contract.getAddress();
  console.log("ExtremaduraFireNFT desplegado en:", addr);
  console.log('Export: export EXTREMADURA_FIRE_NFT_ADDRESS="' + addr + '"');
  return addr;
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
