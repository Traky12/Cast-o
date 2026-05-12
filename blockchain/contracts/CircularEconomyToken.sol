// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/token/ERC1155/ERC1155.sol";

/**
 * CircularEconomyToken: batches de residuos agrícolas reutilizados y compost generado.
 * Decreto 123/2023 (Economía Circular) — Junta de Extremadura.
 */
contract CircularEconomyToken is ERC1155 {
    struct ResidueBatch {
        string farmId;
        uint256 residueKg;
        uint256 compostKg;
        uint256 co2Saved;
        string ipfsHash;
    }

    uint256 private _nextTokenId;
    mapping(uint256 => ResidueBatch) private _tokenIdToBatch;

    event ResidueBatchMinted(uint256 indexed tokenId, string farmId, uint256 compostKg, address indexed minter);

    constructor() ERC1155("https://gaiachain.castuo-system.com/circular-economy/{id}") {
        _nextTokenId = 1;
    }

    function mintResidueBatch(
        address to,
        string memory farmId,
        uint256 residueKg,
        uint256 compostKg,
        uint256 co2Saved,
        string memory ipfsHash
    ) external returns (uint256) {
        require(bytes(farmId).length > 0, "farmId required");
        require(bytes(ipfsHash).length > 0, "ipfsHash required");

        uint256 tokenId = _nextTokenId++;
        _mint(to, tokenId, 1, "");

        _tokenIdToBatch[tokenId] = ResidueBatch({
            farmId: farmId,
            residueKg: residueKg,
            compostKg: compostKg,
            co2Saved: co2Saved,
            ipfsHash: ipfsHash
        });

        emit ResidueBatchMinted(tokenId, farmId, compostKg, msg.sender);
        return tokenId;
    }

    function getBatch(uint256 tokenId) external view returns (ResidueBatch memory) {
        require(bytes(_tokenIdToBatch[tokenId].ipfsHash).length > 0, "Token does not exist");
        return _tokenIdToBatch[tokenId];
    }
}
