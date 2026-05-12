// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/token/ERC1155/ERC1155.sol";

/**
 * GreenLicenseToken: documentos de Medio Ambiente (licencias, EIAs) con hash SHA-512
 * y metadatos en IPFS. Trazabilidad inmutable para la Junta de Extremadura.
 */
contract GreenLicenseToken is ERC1155 {
    struct DocumentMetadata {
        string documentHash;
        string documentType;
        string ipfsHash;
        uint256 timestamp;
        string responsible;
    }

    uint256 private _nextTokenId;

    mapping(uint256 => DocumentMetadata) private _tokenIdToMetadata;

    event DocumentMinted(
        uint256 indexed tokenId,
        string documentType,
        string documentHash,
        address indexed minter
    );

    constructor() ERC1155("https://gaiachain.castuo-system.com/documents/{id}") {
        _nextTokenId = 1;
    }

    function mintDocument(
        string memory documentHash,
        string memory documentType,
        string memory ipfsHash,
        string memory responsible
    ) external returns (uint256) {
        require(bytes(documentHash).length > 0, "documentHash required");
        require(bytes(documentType).length > 0, "documentType required");

        uint256 tokenId = _nextTokenId++;
        _mint(msg.sender, tokenId, 1, "");

        _tokenIdToMetadata[tokenId] = DocumentMetadata({
            documentHash: documentHash,
            documentType: documentType,
            ipfsHash: ipfsHash,
            timestamp: block.timestamp,
            responsible: responsible
        });

        emit DocumentMinted(tokenId, documentType, documentHash, msg.sender);
        return tokenId;
    }

    function getDocumentMetadata(uint256 tokenId)
        external
        view
        returns (DocumentMetadata memory)
    {
        require(bytes(_tokenIdToMetadata[tokenId].documentHash).length > 0, "Token does not exist");
        return _tokenIdToMetadata[tokenId];
    }

    function verifyDocument(uint256 tokenId, string memory documentHash)
        external
        view
        returns (bool)
    {
        require(bytes(_tokenIdToMetadata[tokenId].documentHash).length > 0, "Token does not exist");
        return
            keccak256(bytes(_tokenIdToMetadata[tokenId].documentHash)) ==
            keccak256(bytes(documentHash));
    }
}
