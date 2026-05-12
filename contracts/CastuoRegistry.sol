// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/**
 * @title CastuoRegistry — evidencias gemelo / Ladanum / VERDFIRMA
 * @notice Registro inmutable de evidenceHash + dataRoomId; emite EvidenceSubmitted.
 * @dev Desplegar tras auditoría. Compatible EVM soberanas (Polygon, Base, EBSI-capable).
 */
contract CastuoRegistry {
    mapping(bytes32 => bool) public evidenceSubmitted;
    mapping(bytes32 => string) public dataRoomOf;

    event EvidenceSubmitted(
        bytes32 indexed evidenceHash,
        string dataRoomId,
        address indexed submitter
    );

    error AlreadySubmitted();

    function submitEvidence(bytes32 _evidenceHash, string calldata _dataRoomId) external {
        if (evidenceSubmitted[_evidenceHash]) revert AlreadySubmitted();
        evidenceSubmitted[_evidenceHash] = true;
        dataRoomOf[_evidenceHash] = _dataRoomId;
        emit EvidenceSubmitted(_evidenceHash, _dataRoomId, msg.sender);
    }

    function isEvidenceRegistered(bytes32 h) external view returns (bool) {
        return evidenceSubmitted[h];
    }
}
