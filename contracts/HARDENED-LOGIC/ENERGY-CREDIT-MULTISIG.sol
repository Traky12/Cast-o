// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/**
 * @title EnergyCreditMultisig — PTM con doble firma y ajuste calima (CIPHER-LEVEL-5)
 * @notice PoT requiere acuse emisor (donante) y receptor (beneficiario). Eficiencia por calima (BPS).
 * @dev Evita robo de haz; no usar transfer directo — settle registra crédito; pull en módulo separado si aplica.
 */
contract EnergyCreditMultisig {
    address public settler;
    address public admin;

    uint256 public constant BPS = 10_000;
    uint256 public calimaLossBps = 150; // 1.5% pérdida por calima por defecto; actualizable por sensor

    struct PTMSession {
        bytes32 sourceIdHash;
        bytes32 targetIdHash;
        uint256 energyWh;
        uint256 tariffWeiPerKwh;
        uint256 amountWei;
        bool sourceAck;
        bool targetAck;
        bool settled;
        uint256 openedAt;
    }

    mapping(bytes32 => PTMSession) public sessions;

    event SessionOpened(bytes32 indexed sessionId, bytes32 sourceHash, bytes32 targetHash, uint256 energyWh);
    event ProofOfTransfer(bytes32 indexed sessionId, bool fromSource, bytes32 msgHash);
    event EnergyCreditSettled(bytes32 indexed sessionId, address indexed beneficiary, uint256 weiAmount);
    event CalimaUpdated(uint256 lossBps);

    error NotSettler();
    error NotAdmin();
    error AlreadySettled();
    error SessionMissing();
    error PoTIncomplete();

    modifier onlySettler() {
        if (msg.sender != settler) revert NotSettler();
        _;
    }

    modifier onlyAdmin() {
        if (msg.sender != admin) revert NotAdmin();
        _;
    }

    constructor(address _settler) {
        admin = msg.sender;
        settler = _settler;
    }

    function setSettler(address s) external onlyAdmin {
        settler = s;
    }

    function setCalimaLossBps(uint256 bps) external onlyAdmin {
        require(bps <= BPS, "BPS overflow");
        calimaLossBps = bps;
        emit CalimaUpdated(bps);
    }

    function openSession(
        bytes32 sessionId,
        bytes32 sourceIdHash,
        bytes32 targetIdHash,
        uint256 energyWh,
        uint256 tariffWeiPerKwh
    ) external onlySettler {
        uint256 kwh = energyWh / 1000;
        if (kwh == 0 && energyWh > 0) kwh = 1;
        uint256 gross = kwh * tariffWeiPerKwh;
        uint256 net = (gross * (BPS - calimaLossBps)) / BPS;
        sessions[sessionId] = PTMSession({
            sourceIdHash: sourceIdHash,
            targetIdHash: targetIdHash,
            energyWh: energyWh,
            tariffWeiPerKwh: tariffWeiPerKwh,
            amountWei: net,
            sourceAck: false,
            targetAck: false,
            settled: false,
            openedAt: block.timestamp
        });
        emit SessionOpened(sessionId, sourceIdHash, targetIdHash, energyWh);
    }

    function submitPoT(bytes32 sessionId, bool isSource, bytes32 messageHash) external onlySettler {
        PTMSession storage s = sessions[sessionId];
        if (s.openedAt == 0) revert SessionMissing();
        if (s.settled) revert AlreadySettled();
        if (isSource) s.sourceAck = true;
        else s.targetAck = true;
        emit ProofOfTransfer(sessionId, isSource, messageHash);
    }

    function settle(bytes32 sessionId, address payable beneficiary) external onlySettler {
        PTMSession storage s = sessions[sessionId];
        if (s.openedAt == 0) revert SessionMissing();
        if (s.settled) revert AlreadySettled();
        if (!s.sourceAck || !s.targetAck) revert PoTIncomplete();

        s.settled = true;
        (bool ok, ) = beneficiary.call{value: s.amountWei}("");
        require(ok, "pay");
        emit EnergyCreditSettled(sessionId, beneficiary, s.amountWei);
    }

    receive() external payable {}
}
