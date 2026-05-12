// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/**
 * @title EnergyCredit — liquidación PTM (Aetheris / Remolque XXL)
 * @notice Registro sesiones transferencia láser; PoT = firma receptor confirma kWh.
 * @dev DID/HSM off-chain; on-chain hashes de identidad y mensajes PoT.
 */
contract EnergyCredit {
    address public settler;
    address public admin;

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
    mapping(bytes32 => int256) public creditBalanceWei;

    event SessionOpened(bytes32 indexed sessionId, bytes32 sourceHash, bytes32 targetHash, uint256 energyWh);
    event ProofOfTransfer(bytes32 indexed sessionId, bool fromSource, bytes32 msgHash);
    event EnergyCreditSettled(bytes32 indexed sessionId, address indexed beneficiary, uint256 weiAmount);

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

    function openSession(
        bytes32 sessionId,
        bytes32 sourceIdHash,
        bytes32 targetIdHash,
        uint256 energyWh,
        uint256 tariffWeiPerKwh
    ) external onlySettler {
        uint256 kwh = energyWh / 1000;
        if (kwh == 0 && energyWh > 0) kwh = 1;
        uint256 amt = (kwh * tariffWeiPerKwh * 85) / 100;
        sessions[sessionId] = PTMSession({
            sourceIdHash: sourceIdHash,
            targetIdHash: targetIdHash,
            energyWh: energyWh,
            tariffWeiPerKwh: tariffWeiPerKwh,
            amountWei: amt,
            sourceAck: false,
            targetAck: false,
            settled: false,
            openedAt: block.timestamp
        });
        emit SessionOpened(sessionId, sourceIdHash, targetIdHash, energyWh);
    }

    function submitPoT(bytes32 sessionId, bool isSource, bytes32 messageHash) external onlySettler {
        PTMSession storage s = sessions[sessionId];
        if (s.openedAt == 0) revert AlreadySettled();
        if (isSource) s.sourceAck = true;
        else s.targetAck = true;
        emit ProofOfTransfer(sessionId, isSource, messageHash);
    }

    function settle(bytes32 sessionId, address payable beneficiary) external onlySettler {
        PTMSession storage s = sessions[sessionId];
        if (s.settled) revert AlreadySettled();
        if (!s.sourceAck || !s.targetAck) revert PoTIncomplete();
        s.settled = true;
        creditBalanceWei[s.sourceIdHash] += int256(s.amountWei);
        creditBalanceWei[s.targetIdHash] -= int256(s.amountWei);
        (bool ok,) = beneficiary.call{value: s.amountWei}("");
        require(ok, "pay");
        emit EnergyCreditSettled(sessionId, beneficiary, s.amountWei);
    }

    receive() external payable {}
}
