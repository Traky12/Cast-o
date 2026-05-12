// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

interface AggregatorV3Interface {
    function latestRoundData()
        external
        view
        returns (
            uint80 roundId,
            int256 answer,
            uint256 startedAt,
            uint256 updatedAt,
            uint80 answeredInRound
        );
}

contract BioCoinPriceConsumer {
    AggregatorV3Interface internal priceFeed;
    address public bioCoinAddress;
    uint256 public bioCoinPriceUSD;

    event PriceUpdated(uint256 newPrice);

    constructor(address _bioCoinAddress, address _priceFeedAddress) {
        bioCoinAddress = _bioCoinAddress;
        priceFeed = AggregatorV3Interface(_priceFeedAddress);
    }

    function getLatestPrice() public returns (int256) {
        (, int256 price, , , ) = priceFeed.latestRoundData();
        bioCoinPriceUSD = uint256(price) / 1e8;
        emit PriceUpdated(bioCoinPriceUSD);
        return price;
    }

    function getBioCoinPriceUSD() public view returns (uint256) {
        return bioCoinPriceUSD;
    }
}
