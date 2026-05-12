// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract AuditTrail {
    struct AuditEvent {
        uint256 timestamp;
        string action;
        string status;
        string details;
        string compliance;
        address registeredBy;
    }

    mapping(uint256 => AuditEvent[]) private _auditTrails;

    event EventRegistered(
        uint256 indexed tokenId,
        string action,
        string status,
        bytes32 txRef
    );

    function registerEvent(
        uint256 tokenId,
        string memory action,
        string memory status,
        string memory details,
        string memory compliance
    ) public {
        _auditTrails[tokenId].push(
            AuditEvent({
                timestamp: block.timestamp,
                action: action,
                status: status,
                details: details,
                compliance: compliance,
                registeredBy: msg.sender
            })
        );

        emit EventRegistered(tokenId, action, status, blockhash(block.number - 1));
    }

    function getAuditTrail(uint256 tokenId) public view returns (AuditEvent[] memory) {
        return _auditTrails[tokenId];
    }

    function getEventCount(uint256 tokenId) public view returns (uint256) {
        return _auditTrails[tokenId].length;
    }
}

