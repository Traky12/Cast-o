const hre = require("hardhat");

async function main() {
  const FireReportToken = await hre.ethers.getContractFactory("FireReportToken");
  const contract = await FireReportToken.deploy();
  await contract.waitForDeployment();
  const addr = await contract.getAddress();
  console.log("FireReportToken desplegado en:", addr);
  console.log('Export: export FIRE_REPORT_TOKEN_ADDRESS="' + addr + '"');
  return addr;
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
