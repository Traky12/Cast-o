// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/token/ERC721/ERC721.sol";
import "@openzeppelin/contracts/utils/Counters.sol";

/**
 * DynamicCropNFT: NFT que refleja el crecimiento en tiempo real (growthStage 0-100).
 * Metadatos actualizables en IPFS. Soporta lechuga, cannabis medicinal y fresas.
 */
contract DynamicCropNFT is ERC721 {
    using Counters for Counters.Counter;
    Counters.Counter private _tokenIds;

    struct CropMetadata {
        string cropType;
        string farmId;
        uint256 plantDate;
        uint256 lastUpdate;
        string ipfsHash;
        uint256 growthStage; // 0-100
        string strain;      // cannabis: "Amnesia Haze"
        uint256 thcCbdRatio; // cannabis: 2000 = 20.00% THC
        uint256 brixLevel;   // fresas: nivel de azúcar
    }

    mapping(uint256 => CropMetadata) private _tokenIdToMetadata;

    constructor() ERC721("DynamicCropNFT", "DCNFT") {}

    function mintNFT(
        address to,
        string memory cropType,
        string memory farmId,
        string memory initialIpfsHash,
        string memory strain,
        uint256 thcCbdRatio,
        uint256 brixLevel
    ) public returns (uint256) {
        _tokenIds.increment();
        uint256 newTokenId = _tokenIds.current();

        _mint(to, newTokenId);
        _tokenIdToMetadata[newTokenId] = CropMetadata({
            cropType: cropType,
            farmId: farmId,
            plantDate: block.timestamp,
            lastUpdate: block.timestamp,
            ipfsHash: initialIpfsHash,
            growthStage: 0,
            strain: strain,
            thcCbdRatio: thcCbdRatio,
            brixLevel: brixLevel
        });

        return newTokenId;
    }

    function updateGrowthStage(
        uint256 tokenId,
        uint256 newGrowthStage,
        string memory newIpfsHash
    ) public {
        require(ownerOf(tokenId) != address(0), "Token does not exist");
        require(newGrowthStage <= 100, "Growth stage cannot exceed 100");

        CropMetadata storage metadata = _tokenIdToMetadata[tokenId];
        metadata.growthStage = newGrowthStage;
        metadata.ipfsHash = newIpfsHash;
        metadata.lastUpdate = block.timestamp;
    }

    function getMetadata(uint256 tokenId) public view returns (CropMetadata memory) {
        require(ownerOf(tokenId) != address(0), "Token does not exist");
        return _tokenIdToMetadata[tokenId];
    }

    function tokenURI(uint256 tokenId) public view override returns (string memory) {
        require(ownerOf(tokenId) != address(0), "Token does not exist");
        return string(
            abi.encodePacked("https://ipfs.io/ipfs/", _tokenIdToMetadata[tokenId].ipfsHash)
        );
    }
}
