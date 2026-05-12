// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

interface IERC20 {
    function transferFrom(address from, address to, uint256 amount) external returns (bool);
    function approve(address spender, uint256 amount) external returns (bool);
    function balanceOf(address account) external view returns (uint256);
}

contract BioCoinCarbonMarket {
    IERC20 public bioCoin;
    address public owner;
    uint256 public pricePerKgCO2;

    event CreditSold(address indexed buyer, uint256 kgCO2, uint256 bioCoinAmount);

    constructor(address _bioCoinAddress) {
        bioCoin = IERC20(_bioCoinAddress);
        owner = msg.sender;
        pricePerKgCO2 = 1 * (10 ** 18);
    }

    function buyCarbonCredits(uint256 kgCO2) external {
        require(kgCO2 > 0, "Amount must be greater than 0");
        uint256 totalBioCoin = kgCO2 * pricePerKgCO2;
        require(bioCoin.transferFrom(msg.sender, owner, totalBioCoin), "BioCoin transfer failed");
        emit CreditSold(msg.sender, kgCO2, totalBioCoin);
    }

    function setPricePerKgCO2(uint256 newPrice) external {
        require(msg.sender == owner, "Only owner can set price");
        pricePerKgCO2 = newPrice;
    }
}
