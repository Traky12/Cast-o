// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

/**
 * @title CASTUO_NFT — Certificación de integridad CASTUO_GOLD_V1 (ERC-721 + cumplimiento EU)
 * @notice Token único por release; metadatos en IPFS; registro de cumplimiento (EU AI Act, GDPR, NIS2, eIDAS2).
 * @dev Desplegar en testnet primero; usar scripts/nft/deploy_castuo_nft_testnet.py
 */
contract CASTUO_NFT {
    string private _name = "CASTUO_GOLD_V1";
    string private _symbol = "CGV1";
    address public owner;
    uint256 private _nextTokenId = 1;

    mapping(uint256 => address) private _owners;
    mapping(address => uint256) private _balances;
    mapping(uint256 => string) private _tokenURIs;
    mapping(uint256 => bool) private _minted;

    struct ComplianceData {
        string standard;
        string complianceHash;
        uint256 timestamp;
    }
    mapping(uint256 => ComplianceData[]) private _complianceData;

    event Transfer(address indexed from, address indexed to, uint256 indexed tokenId);
    event ComplianceRegistered(uint256 indexed tokenId, string complianceStandard, string complianceHash);

    error NotOwner();
    error AlreadyMinted();
    error InvalidToken();

    modifier onlyOwner() {
        if (msg.sender != owner) revert NotOwner();
        _;
    }

    constructor() {
        owner = msg.sender;
    }

    function name() external view returns (string memory) {
        return _name;
    }

    function symbol() external view returns (string memory) {
        return _symbol;
    }

    function mint(address to, string calldata tokenURI) external onlyOwner returns (uint256 tokenId) {
        tokenId = _nextTokenId++;
        if (to == address(0)) revert InvalidToken();
        _owners[tokenId] = to;
        _balances[to]++;
        _tokenURIs[tokenId] = tokenURI;
        _minted[tokenId] = true;
        emit Transfer(address(0), to, tokenId);
        return tokenId;
    }

    function ownerOf(uint256 tokenId) public view returns (address) {
        if (!_minted[tokenId]) revert InvalidToken();
        return _owners[tokenId];
    }

    function tokenURI(uint256 tokenId) external view returns (string memory) {
        if (!_minted[tokenId]) revert InvalidToken();
        return _tokenURIs[tokenId];
    }

    function registerCompliance(
        uint256 tokenId,
        string calldata standard,
        string calldata complianceHash
    ) external onlyOwner {
        if (!_minted[tokenId]) revert InvalidToken();
        _complianceData[tokenId].push(ComplianceData({
            standard: standard,
            complianceHash: complianceHash,
            timestamp: block.timestamp
        }));
        emit ComplianceRegistered(tokenId, standard, complianceHash);
    }

    function getComplianceData(uint256 tokenId) external view returns (
        string[] memory standards,
        string[] memory hashes,
        uint256[] memory timestamps
    ) {
        if (!_minted[tokenId]) revert InvalidToken();
        ComplianceData[] storage data = _complianceData[tokenId];
        uint256 n = data.length;
        standards = new string[](n);
        hashes = new string[](n);
        timestamps = new uint256[](n);
        for (uint256 i = 0; i < n; i++) {
            standards[i] = data[i].standard;
            hashes[i] = data[i].complianceHash;
            timestamps[i] = data[i].timestamp;
        }
    }
}
