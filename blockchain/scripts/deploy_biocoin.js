const hre = require("hardhat");

async function main() {
  const initialSupply = process.env.INITIAL_SUPPLY || "1000000";
  const BioCoinCastuo = await hre.ethers.getContractFactory("BioCoinCastuo");
  const token = await BioCoinCastuo.deploy(initialSupply);
  await token.waitForDeployment();
  const addr = await token.getAddress();
  console.log("BioCoin Castúo (BIOCAST) desplegado en:", addr);
  return addr;
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
