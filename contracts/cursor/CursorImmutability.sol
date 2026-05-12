// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

/**
 * @title CursorImmutability
 * @notice Registro de ejecuciones de Cursor firmadas por HSM — anti-hacking v1.0.
 * @dev registerExecution(scriptHash, v, r, s, environment) verifica firma HSM.
 */
contract CursorImmutability {
    address public owner;
    address public hsm;
    mapping(bytes32 => bool) private executedScripts;
    mapping(bytes32 => bytes) private scriptSignatures;
    mapping(bytes32 => string) private scriptEnvironments;

    event ScriptExecuted(bytes32 indexed scriptHash, address indexed caller);
    event ScriptReverted(bytes32 indexed scriptHash, string reason);

    constructor(address _hsm) {
        owner = msg.sender;
        hsm = _hsm;
    }

    function registerExecution(
        bytes32 scriptHash,
        uint8 v,
        bytes32 r,
        bytes32 s,
        string calldata environment
    ) public returns (bool) {
        bytes32 messageHash = keccak256(abi.encodePacked(scriptHash, environment));
        address signer = ecrecover(messageHash, v, r, s);
        require(signer != address(0), "Invalid signature");
        require(signer == hsm, "Only HSM can register");
        require(!executedScripts[scriptHash], "Script already executed");

        executedScripts[scriptHash] = true;
        scriptSignatures[scriptHash] = abi.encodePacked(r, s, v);
        scriptEnvironments[scriptHash] = environment;

        emit ScriptExecuted(scriptHash, msg.sender);
        return true;
    }

    function isExecuted(bytes32 scriptHash) public view returns (bool) {
        return executedScripts[scriptHash];
    }

    function getSignature(bytes32 scriptHash) public view returns (bytes memory) {
        return scriptSignatures[scriptHash];
    }

    function getEnvironment(bytes32 scriptHash) public view returns (string memory) {
        return scriptEnvironments[scriptHash];
    }

    function revertExecution(bytes32 scriptHash, string calldata reason) public {
        require(msg.sender == owner, "Only owner");
        require(executedScripts[scriptHash], "Script not executed");
        delete executedScripts[scriptHash];
        delete scriptSignatures[scriptHash];
        delete scriptEnvironments[scriptHash];
        emit ScriptReverted(scriptHash, reason);
    }
}
