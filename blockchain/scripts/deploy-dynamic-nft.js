const hre = require("hardhat");

async function main() {
  const DynamicCropNFT = await hre.ethers.getContractFactory("DynamicCropNFT");
  const contract = await DynamicCropNFT.deploy();
  await contract.waitForDeployment();
  const addr = await contract.getAddress();
  console.log("DynamicCropNFT desplegado en:", addr);
  console.log('Export: export DYNAMIC_NFT_ADDRESS="' + addr + '"');
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
