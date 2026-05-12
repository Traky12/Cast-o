// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/**
 * @title BioCoinVault — CASTUO Serie Premium (Génesis 10.000)
 * @notice ERC-1155 simplificado: tokenId 1..10000 = moneda numerada única (balance 1).
 *         mintWithEvidence: requiere firma oráculo (HSM). 10% → bioReserveFund.
 *         clausulaExpansion: nueva serie solo si daoApproved + evidenceScore estable (gobernanza off-chain).
 *         EmergencyPause + Timelock 48h en parámetros económicos.
 * @dev Desplegar con auditoría externa. Compatible EVM (Polygon, Base, etc.).
 */
contract BioCoinVault {
    uint256 public constant GENESIS_SERIES_ID = 1;
    uint256 public constant GENESIS_MIN_ID = 1;
    uint256 public constant GENESIS_MAX_ID = 10_000;
    uint256 public constant BPS_DENOM = 10_000;
    uint256 public constant TIMELOCK_DELAY = 48 hours;

    address public owner;
    address public pendingOwner;
    address public oracleSigner;
    bool public paused;
    uint256 public reserveRateBps = 1000;
    uint256 public bioReserveWei;
    uint256 public mintPriceWei;
    bool public daoExpansionApproved;
    uint256 public evidenceScoreThresholdBps = 9900;
    bool public evidenceScoreStable;

    mapping(uint256 => mapping(address => uint256)) private _balances;
    mapping(uint256 => bool) public tokenMinted;
    mapping(uint256 => bytes32) public evidenceOfToken;
    mapping(uint256 => uint256) public qualityScoreOfToken;
    mapping(uint256 => bool) public doubleCountProtected;

    uint256 private _scheduledReserveBps;
    uint256 private _scheduledMintPrice;
    uint256 public reserveChangeUnlockTime;
    uint256 public priceChangeUnlockTime;

    string private _uri;

    event MintWithEvidence(address indexed to, uint256 indexed tokenId, bytes32 evidenceHash, bytes32 manifestHash);
    event BioReserveAccrued(uint256 amount);
    event EmergencyPauseSet(bool paused);
    event OracleRotated(address indexed newOracle);
    event ExpansionClauseTriggered(bool approved);
    event TimelockReserveScheduled(uint256 newBps, uint256 unlockTime);
    event TimelockPriceScheduled(uint256 newPrice, uint256 unlockTime);

    error Paused();
    error InvalidToken();
    error AlreadyMinted();
    error BadOracleSig();
    error TimelockActive();
    error TimelockNotReady();

    modifier onlyOwner() {
        require(msg.sender == owner, "not owner");
        _;
    }

    modifier whenNotPaused() {
        if (paused) revert Paused();
        _;
    }

    /// @notice mintPriceWei arranca en 0; subir precio solo vía scheduleMintPriceChange + 48h (anti flash governance).
    constructor(address _oracleSigner, string memory uri_) {
        owner = msg.sender;
        oracleSigner = _oracleSigner;
        _uri = uri_;
        evidenceScoreStable = true;
        mintPriceWei = 0;
    }

    function uri(uint256) external view returns (string memory) {
        return _uri;
    }

    function balanceOf(address account, uint256 id) external view returns (uint256) {
        return _balances[id][account];
    }

    function setPaused(bool p) external onlyOwner {
        paused = p;
        emit EmergencyPauseSet(p);
    }

    function setOracle(address o) external onlyOwner {
        oracleSigner = o;
        emit OracleRotated(o);
    }

    function setEvidenceScoreStable(bool stable) external onlyOwner {
        evidenceScoreStable = stable;
    }

    function setDaoExpansionApproved(bool approved) external onlyOwner {
        daoExpansionApproved = approved;
        emit ExpansionClauseTriggered(approved);
    }

    function scheduleReserveRateChange(uint256 newBps) external onlyOwner {
        require(newBps <= 2000, "max 20%");
        if (reserveChangeUnlockTime > block.timestamp) revert TimelockActive();
        _scheduledReserveBps = newBps;
        reserveChangeUnlockTime = block.timestamp + TIMELOCK_DELAY;
        emit TimelockReserveScheduled(newBps, reserveChangeUnlockTime);
    }

    function executeReserveRateChange() external onlyOwner {
        if (block.timestamp < reserveChangeUnlockTime) revert TimelockNotReady();
        reserveRateBps = _scheduledReserveBps;
        reserveChangeUnlockTime = 0;
    }

    function scheduleMintPriceChange(uint256 newPriceWei) external onlyOwner {
        if (priceChangeUnlockTime > block.timestamp) revert TimelockActive();
        _scheduledMintPrice = newPriceWei;
        priceChangeUnlockTime = block.timestamp + TIMELOCK_DELAY;
        emit TimelockPriceScheduled(newPriceWei, priceChangeUnlockTime);
    }

    function executeMintPriceChange() external onlyOwner {
        if (block.timestamp < priceChangeUnlockTime) revert TimelockNotReady();
        mintPriceWei = _scheduledMintPrice;
        priceChangeUnlockTime = 0;
    }

    function clausulaExpansion(uint256 newSeriesId, uint256 maxSupply) external onlyOwner whenNotPaused {
        require(daoExpansionApproved, "DAO");
        require(evidenceScoreStable, "evidence unstable");
        require(newSeriesId > GENESIS_SERIES_ID && maxSupply > 0, "params");
        daoExpansionApproved = false;
    }

    function withdrawBioReserve(address payable to, uint256 amountWei) external onlyOwner {
        require(amountWei <= bioReserveWei, "insufficient reserve");
        bioReserveWei -= amountWei;
        (bool ok,) = to.call{value: amountWei}("");
        require(ok, "transfer fail");
    }

    function mintWithEvidence(
        address to,
        uint256 tokenId,
        bytes32 evidenceHash,
        bytes32 manifestHash,
        uint256 qualityScore,
        bool isDoubleCountedProtected_,
        uint8 v,
        bytes32 r,
        bytes32 s
    ) external payable whenNotPaused {
        if (tokenId < GENESIS_MIN_ID || tokenId > GENESIS_MAX_ID) revert InvalidToken();
        if (tokenMinted[tokenId]) revert AlreadyMinted();
        if (msg.value < mintPriceWei) revert("price");
        bytes32 msgHash = keccak256(abi.encodePacked(evidenceHash, manifestHash, tokenId, to, address(this), block.chainid));
        bytes32 ethSigned = keccak256(abi.encodePacked("\x19Ethereum Signed Message:\n32", msgHash));
        address signer = ecrecover(ethSigned, v, r, s);
        if (signer != oracleSigner) revert BadOracleSig();

        uint256 toReserve = (msg.value * reserveRateBps) / BPS_DENOM;
        bioReserveWei += toReserve;
        emit BioReserveAccrued(toReserve);

        tokenMinted[tokenId] = true;
        _balances[tokenId][to] = 1;
        evidenceOfToken[tokenId] = evidenceHash;
        qualityScoreOfToken[tokenId] = qualityScore;
        doubleCountProtected[tokenId] = isDoubleCountedProtected_;

        emit MintWithEvidence(to, tokenId, evidenceHash, manifestHash);
    }

    function safeTransferFrom(address from, address to, uint256 id, uint256 amount, bytes calldata) external whenNotPaused {
        require(from == msg.sender || _balances[id][from] >= amount, "auth");
        require(_balances[id][from] >= amount, "bal");
        _balances[id][from] -= amount;
        _balances[id][to] += amount;
    }

    function bioReserveFund() external view returns (uint256) {
        return bioReserveWei;
    }

    receive() external payable {
        bioReserveWei += msg.value;
        emit BioReserveAccrued(msg.value);
    }
}
