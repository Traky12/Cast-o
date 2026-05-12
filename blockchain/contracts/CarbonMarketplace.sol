// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

interface IERC20 {
    function transferFrom(address from, address to, uint256 amount) external returns (bool);
}

contract CarbonMarketplace {
    IERC20 public bioCoin;
    address public owner;
    uint256 public platformFee = 5;

    struct Listing {
        address seller;
        uint256 kgCO2;
        uint256 pricePerKgBioCoin;
        bool sold;
    }

    mapping(uint256 => Listing) public listings;
    uint256 public listingCount;

    event ListingCreated(uint256 listingId, address seller, uint256 kgCO2, uint256 pricePerKgBioCoin);
    event ListingSold(uint256 listingId, address buyer, uint256 totalBioCoin);

    constructor(address _bioCoinAddress) {
        bioCoin = IERC20(_bioCoinAddress);
        owner = msg.sender;
    }

    function createListing(uint256 kgCO2, uint256 pricePerKgBioCoin) external {
        listingCount++;
        listings[listingCount] = Listing({
            seller: msg.sender,
            kgCO2: kgCO2,
            pricePerKgBioCoin: pricePerKgBioCoin,
            sold: false
        });
        emit ListingCreated(listingCount, msg.sender, kgCO2, pricePerKgBioCoin);
    }

    function buyListing(uint256 listingId) external {
        Listing storage listing = listings[listingId];
        require(!listing.sold, "Listing already sold");
        uint256 total = listing.kgCO2 * listing.pricePerKgBioCoin;
        uint256 fee = (total * platformFee) / 100;
        uint256 totalAmount = total + fee;
        require(bioCoin.transferFrom(msg.sender, listing.seller, total), "BioCoin transfer to seller failed");
        require(bioCoin.transferFrom(msg.sender, owner, fee), "BioCoin transfer fee failed");
        listing.sold = true;
        emit ListingSold(listingId, msg.sender, total);
    }

    function getListing(uint256 listingId) external view returns (Listing memory) {
        return listings[listingId];
    }
}
