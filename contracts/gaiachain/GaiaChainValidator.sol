// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

/**
 * @title GaiaChainValidator
 * @notice Validación de transacciones con firma HSM — CASTÚO-SYSTEM™ anti-hacking v1.0.
 * @dev Solo el HSM puede validar; ecrecover(hash, v, r, s) para verificar firma.
 */
contract GaiaChainValidator {
    address public owner;
    address public hsm;
    mapping(bytes32 => bool) private validTransactions;
    mapping(bytes32 => address) private transactionSigners;

    event TransactionValidated(bytes32 indexed txHash, address indexed signer);
    event TransactionReverted(bytes32 indexed txHash, string reason);

    constructor(address _hsm) {
        owner = msg.sender;
        hsm = _hsm;
    }

    function validateTransaction(
        bytes32 txHash,
        uint8 v,
        bytes32 r,
        bytes32 s
    ) public returns (bool) {
        address signer = ecrecover(txHash, v, r, s);
        require(signer != address(0), "Invalid signature");
        require(signer == hsm, "Only HSM can validate");
        validTransactions[txHash] = true;
        transactionSigners[txHash] = signer;
        emit TransactionValidated(txHash, signer);
        return true;
    }

    function isValidTransaction(bytes32 txHash) public view returns (bool) {
        return validTransactions[txHash];
    }

    function getSigner(bytes32 txHash) public view returns (address) {
        return transactionSigners[txHash];
    }

    function revertTransaction(bytes32 txHash, string memory reason) public {
        require(msg.sender == owner, "Only owner");
        require(validTransactions[txHash], "Transaction not found");
        delete validTransactions[txHash];
        delete transactionSigners[txHash];
        emit TransactionReverted(txHash, reason);
    }
}
