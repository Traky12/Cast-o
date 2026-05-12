const hre = require("hardhat");

async function main() {
  const cropNFTAddress = process.env.CROP_NFT_ADDRESS || "";
  if (!cropNFTAddress) {
    console.error("Definir CROP_NFT_ADDRESS (dirección del contrato CropNFT)");
    process.exitCode = 1;
    return;
  }
  const CropNFTMarketplace = await hre.ethers.getContractFactory("CropNFTMarketplace");
  const marketplace = await CropNFTMarketplace.deploy(cropNFTAddress);
  await marketplace.waitForDeployment();
  const addr = await marketplace.getAddress();
  console.log("CropNFTMarketplace desplegado en:", addr);
  console.log('Export: export CROP_NFT_MARKETPLACE_ADDRESS="' + addr + '"');
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
