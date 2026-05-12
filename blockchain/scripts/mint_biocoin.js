const hre = require("hardhat");

async function main() {
  const contractAddr = process.env.BIOCAST_ADDRESS;
  if (!contractAddr) {
    console.error("Definir BIOCAST_ADDRESS (dirección del contrato).");
    process.exit(1);
  }
  const gitCommitHash = process.env.GIT_COMMIT_HASH || "unknown";
  const gitTxHash = process.env.GIT_TX_HASH || "00000000000000000000000000000000";

  const BioCoinCastuo = await hre.ethers.getContractFactory("BioCoinCastuo");
  const token = BioCoinCastuo.attach(contractAddr);
  const [signer] = await hre.ethers.getSigners();
  const amount = hre.ethers.parseEther(process.env.MINT_AMOUNT || "1000");

  const tx = await token.mint(signer.address, amount, gitCommitHash, gitTxHash);
  const receipt = await tx.wait();
  console.log("Minted:", amount.toString(), "BIOCAST");
  console.log("TX hash (blockchain):", receipt.hash);
  console.log("gitTxHash (para commit):", gitTxHash);
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
