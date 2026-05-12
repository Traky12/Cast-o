// SPDX-License-Identifier: MIT
// CASTÚO Federated v3.0 — Smart contract GDPR consents (Ethereum Sepolia)
pragma solidity ^0.8.19;

contract GDPRConsent {
    event ConsentRecorded(address indexed subject, bytes32 consentHash, uint256 timestamp);
    event ConsentRevoked(address indexed subject, uint256 timestamp);

    mapping(address => bytes32) public consentHashOf;
    mapping(address => uint256) public consentedAt;

    function recordConsent(bytes32 _consentHash) external {
        require(_consentHash != bytes32(0), "Empty hash");
        consentHashOf[msg.sender] = _consentHash;
        consentedAt[msg.sender] = block.timestamp;
        emit ConsentRecorded(msg.sender, _consentHash, block.timestamp);
    }

    function revokeConsent() external {
        delete consentHashOf[msg.sender];
        delete consentedAt[msg.sender];
        emit ConsentRevoked(msg.sender, block.timestamp);
    }

    function hasConsent(address _subject) external view returns (bool) {
        return consentHashOf[_subject] != bytes32(0);
    }
}
