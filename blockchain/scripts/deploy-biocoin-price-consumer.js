const hre = require("hardhat");

async function main() {
  const bioCoinAddress = process.env.BIOCOIN_ADDRESS || "0x0000000000000000000000000000000000000000";
  const priceFeedAddress = process.env.CHAINLINK_PRICE_FEED_ADDRESS || "0x0000000000000000000000000000000000000000";
  if (bioCoinAddress === "0x0000000000000000000000000000000000000000" || priceFeedAddress === "0x0000000000000000000000000000000000000000") {
    console.error("Definir BIOCOIN_ADDRESS y CHAINLINK_PRICE_FEED_ADDRESS");
    process.exit(1);
  }

  const BioCoinPriceConsumer = await hre.ethers.getContractFactory("BioCoinPriceConsumer");
  const consumer = await BioCoinPriceConsumer.deploy(bioCoinAddress, priceFeedAddress);
  await consumer.waitForDeployment();
  const addr = await consumer.getAddress();
  console.log("BioCoinPriceConsumer desplegado en:", addr);
  return addr;
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
