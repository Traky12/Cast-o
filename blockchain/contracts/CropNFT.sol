// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/token/ERC721/ERC721.sol";
import "@openzeppelin/contracts/utils/Counters.sol";
import "@openzeppelin/contracts/utils/Strings.sol";

/**
 * CropNFT: NFT único por cultivo (lechuga, cannabis, tomate) con metadatos inmutables en GaiaChain 2.0.
 */
contract CropNFT is ERC721 {
    using Counters for Counters.Counter;
    Counters.Counter private _tokenIds;

    struct CropMetadata {
        string cropType;
        string farmId;
        uint256 harvestDate;
        string location;
        uint256 co2Saved;
        string ipfsHash;
    }

    mapping(uint256 => CropMetadata) private _tokenIdToMetadata;

    constructor() ERC721("CropNFT", "CRP") {}

    function mintNFT(
        address to,
        string memory cropType,
        string memory farmId,
        string memory location,
        uint256 co2Saved,
        string memory ipfsHash
    ) public returns (uint256) {
        _tokenIds.increment();
        uint256 newTokenId = _tokenIds.current();

        _mint(to, newTokenId);
        _tokenIdToMetadata[newTokenId] = CropMetadata({
            cropType: cropType,
            farmId: farmId,
            harvestDate: block.timestamp,
            location: location,
            co2Saved: co2Saved,
            ipfsHash: ipfsHash
        });

        return newTokenId;
    }

    function getMetadata(uint256 tokenId) public view returns (CropMetadata memory) {
        require(ownerOf(tokenId) != address(0), "Token does not exist");
        return _tokenIdToMetadata[tokenId];
    }

    function tokenURI(uint256 tokenId) public view override returns (string memory) {
        require(ownerOf(tokenId) != address(0), "Token does not exist");
        CropMetadata memory metadata = _tokenIdToMetadata[tokenId];
        return string(
            abi.encodePacked("https://ipfs.io/ipfs/", metadata.ipfsHash, "/", Strings.toString(tokenId))
        );
    }
}
