// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/token/ERC721/ERC721.sol";
import "@openzeppelin/contracts/utils/Counters.sol";

/**
 * FireReportToken: NFT por parte de incendio forestal (BRIF, extinción).
 * Hash del parte, ubicación, equipo extintor y hectáreas afectadas. Ley 5/2019.
 */
contract FireReportToken is ERC721 {
    using Counters for Counters.Counter;
    Counters.Counter private _tokenIdCounter;

    struct FireReport {
        string reportHash;
        string location;
        uint256 timestamp;
        string extinguishedBy;
        uint256 affectedArea;
    }

    mapping(uint256 => FireReport) private _tokenIdToReport;

    event FireReportMinted(
        uint256 indexed tokenId,
        string location,
        string extinguishedBy,
        uint256 affectedArea
    );

    constructor() ERC721("FireReportToken", "FRT") {}

    function mintFireReport(
        address to,
        string memory reportHash,
        string memory location,
        string memory extinguishedBy,
        uint256 affectedArea
    ) external returns (uint256) {
        require(bytes(reportHash).length > 0, "reportHash required");

        _tokenIdCounter.increment();
        uint256 tokenId = _tokenIdCounter.current();
        _mint(to, tokenId);

        _tokenIdToReport[tokenId] = FireReport({
            reportHash: reportHash,
            location: location,
            timestamp: block.timestamp,
            extinguishedBy: extinguishedBy,
            affectedArea: affectedArea
        });

        emit FireReportMinted(tokenId, location, extinguishedBy, affectedArea);
        return tokenId;
    }

    function getFireReport(uint256 tokenId) external view returns (FireReport memory) {
        require(ownerOf(tokenId) != address(0), "Token does not exist");
        return _tokenIdToReport[tokenId];
    }
}
