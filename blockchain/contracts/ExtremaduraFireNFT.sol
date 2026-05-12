// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/token/ERC721/ERC721.sol";
import "@openzeppelin/contracts/utils/Counters.sol";

/**
 * ExtremaduraFireNFT: partes de incendio forestal BRIF (Ley 6/2022).
 * Ubicación, equipo extintor, hectáreas afectadas y causa.
 */
contract ExtremaduraFireNFT is ERC721 {
    using Counters for Counters.Counter;
    Counters.Counter private _tokenIdCounter;

    struct FireReport {
        string location;
        string extinguishedBy;
        uint256 affectedArea;
        string cause;
        uint256 timestamp;
        string ipfsHash;
    }

    mapping(uint256 => FireReport) private _tokenIdToReport;

    event FireReportMinted(
        uint256 indexed tokenId,
        string location,
        string extinguishedBy,
        uint256 affectedArea
    );

    constructor() ERC721("ExtremaduraFireNFT", "EFNFT") {}

    function mintFireReport(
        address to,
        string memory location,
        string memory extinguishedBy,
        uint256 affectedArea,
        string memory cause,
        string memory ipfsHash
    ) external returns (uint256) {
        _tokenIdCounter.increment();
        uint256 tokenId = _tokenIdCounter.current();
        _mint(to, tokenId);

        _tokenIdToReport[tokenId] = FireReport({
            location: location,
            extinguishedBy: extinguishedBy,
            affectedArea: affectedArea,
            cause: cause,
            timestamp: block.timestamp,
            ipfsHash: ipfsHash
        });

        emit FireReportMinted(tokenId, location, extinguishedBy, affectedArea);
        return tokenId;
    }

    function getFireReport(uint256 tokenId) external view returns (FireReport memory) {
        require(ownerOf(tokenId) != address(0), "Token does not exist");
        return _tokenIdToReport[tokenId];
    }
}
