// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

/**
 * @title MasterAdmin
 * @notice Administración maestra GaiaChain — solo hash de clave maestra registrado; transacciones críticas con firma HSM.
 * @dev registerMasterKey una vez; verifyMasterAccess(inputHash) para comprobar acceso; executeCriticalTransaction con firma HSM.
 */
contract MasterAdmin {
    address public owner;
    address public hsmAddress;
    bytes32 public masterKeyHash;
    mapping(address => bool) public admins;
    mapping(bytes32 => bool) public executedTransactions;

    event MasterKeyRegistered(bytes32 indexed keyHash);
    event AdminAdded(address indexed admin);
    event TransactionExecuted(bytes32 indexed txHash);

    modifier onlyOwner() {
        require(msg.sender == owner, "Only owner");
        _;
    }

    constructor(address _hsm) {
        owner = msg.sender;
        hsmAddress = _hsm;
    }

    function registerMasterKey(bytes32 _masterKeyHash) public onlyOwner {
        require(masterKeyHash == bytes32(0), "Master key already registered");
        masterKeyHash = _masterKeyHash;
        emit MasterKeyRegistered(_masterKeyHash);
    }

    function verifyMasterAccess(bytes32 _inputHash) public view returns (bool) {
        return _inputHash == masterKeyHash;
    }

    function addAdmin(address _admin) public onlyOwner {
        admins[_admin] = true;
        emit AdminAdded(_admin);
    }

    function removeAdmin(address _admin) public onlyOwner {
        admins[_admin] = false;
    }

    function executeCriticalTransaction(
        bytes32 txHash,
        uint8 v,
        bytes32 r,
        bytes32 s
    ) public {
        require(admins[msg.sender], "Not authorized admin");
        address signer = ecrecover(txHash, v, r, s);
        require(signer != address(0) && signer == hsmAddress, "Invalid HSM signature");
        require(!executedTransactions[txHash], "Already executed");
        executedTransactions[txHash] = true;
        emit TransactionExecuted(txHash);
    }

    function isExecuted(bytes32 txHash) public view returns (bool) {
        return executedTransactions[txHash];
    }
}
