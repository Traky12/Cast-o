// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/token/ERC721/IERC721.sol";

/**
 * Marketplace para NFTs de cultivos. El vendedor debe aprobar este contrato
 * (approve o setApprovalForAll) antes de createListing.
 */
contract CropNFTMarketplace {
    IERC721 public cropNFT;
    address public owner;
    uint256 public platformFee = 250; // 2.5% (250/10000)

    struct Listing {
        address seller;
        uint256 tokenId;
        uint256 price;
        bool sold;
    }

    mapping(uint256 => Listing) private _listings;
    mapping(uint256 => uint256) private _tokenIdToListingId;
    uint256 public listingCount;

    event ListingCreated(uint256 listingId, address seller, uint256 tokenId, uint256 price);
    event ListingSold(uint256 listingId, address buyer, uint256 price);

    constructor(address _cropNFTAddress) {
        cropNFT = IERC721(_cropNFTAddress);
        owner = msg.sender;
    }

    function createListing(uint256 tokenId, uint256 price) public {
        require(cropNFT.ownerOf(tokenId) == msg.sender, "Not the owner");
        require(price > 0, "Price must be > 0");
        uint256 existingId = _tokenIdToListingId[tokenId];
        require(
            existingId == 0 || _listings[existingId].sold,
            "Token already listed"
        );

        listingCount++;
        _listings[listingCount] = Listing({
            seller: msg.sender,
            tokenId: tokenId,
            price: price,
            sold: false
        });
        _tokenIdToListingId[tokenId] = listingCount;

        emit ListingCreated(listingCount, msg.sender, tokenId, price);
    }

    function buyListing(uint256 listingId) public payable {
        Listing storage listing = _listings[listingId];
        require(listing.seller != address(0), "Listing does not exist");
        require(!listing.sold, "Already sold");
        require(msg.value >= listing.price, "Incorrect price");

        listing.sold = true;
        _tokenIdToListingId[listing.tokenId] = 0;

        cropNFT.transferFrom(listing.seller, msg.sender, listing.tokenId);

        uint256 fee = (listing.price * platformFee) / 10000;
        uint256 toSeller = listing.price - fee;
        (bool okSeller,) = payable(listing.seller).call{value: toSeller}("");
        require(okSeller, "Transfer to seller failed");
        if (fee > 0) {
            (bool okOwner,) = payable(owner).call{value: fee}("");
            require(okOwner, "Transfer fee failed");
        }
        if (msg.value > listing.price) {
            (bool okRefund,) = payable(msg.sender).call{value: msg.value - listing.price}("");
            require(okRefund, "Refund failed");
        }

        emit ListingSold(listingId, msg.sender, listing.price);
    }

    function getListing(uint256 listingId) public view returns (Listing memory) {
        return _listings[listingId];
    }

    function getAllListings() public view returns (Listing[] memory) {
        Listing[] memory allListings = new Listing[](listingCount);
        for (uint256 i = 1; i <= listingCount; i++) {
            allListings[i - 1] = _listings[i];
        }
        return allListings;
    }
}
