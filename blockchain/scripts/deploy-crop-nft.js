const hre = require("hardhat");

async function main() {
  const CropNFT = await hre.ethers.getContractFactory("CropNFT");
  const cropNFT = await CropNFT.deploy();
  await cropNFT.waitForDeployment();
  const addr = await cropNFT.getAddress();
  console.log("CropNFT desplegado en:", addr);
  console.log('Export: export CROP_NFT_ADDRESS="' + addr + '"');
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
