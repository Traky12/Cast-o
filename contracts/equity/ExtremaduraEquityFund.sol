// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

/**
 * @title ExtremaduraEquityFund
 * @notice Fondo de equidad extremeño — 1% de transacciones redistribuido a fincas.
 * @dev Solo la cooperativa puede añadir fondos y distribuir entre fincas.
 */
contract ExtremaduraEquityFund {
    uint256 public totalFunds;
    mapping(address => uint256) public farmContributions;
    address public owner;
    address public cooperativeAddress;

    event FundsAdded(uint256 amount);
    event Distribution(address farm, uint256 amount);

    constructor(address _cooperative) {
        owner = msg.sender;
        cooperativeAddress = _cooperative;
    }

    receive() external payable {
        totalFunds += msg.value;
    }

    function addFunds() public payable {
        require(msg.sender == cooperativeAddress, "Only cooperative can add funds");
        totalFunds += msg.value;
        emit FundsAdded(msg.value);
    }

    function distributeFunds(address[] calldata farms) public {
        require(msg.sender == cooperativeAddress, "Only cooperative can distribute");
        require(farms.length > 0, "No farms");
        uint256 amountPerFarm = totalFunds / farms.length;
        totalFunds = 0;
        for (uint256 i = 0; i < farms.length; i++) {
            farmContributions[farms[i]] += amountPerFarm;
            (bool ok, ) = payable(farms[i]).call{ value: amountPerFarm }("");
            require(ok, "Transfer failed");
            emit Distribution(farms[i], amountPerFarm);
        }
    }

    function getFarmContribution(address farm) public view returns (uint256) {
        return farmContributions[farm];
    }
}
