// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

/**
 * @title EUCore
 * @notice Núcleo europeo inquebrantable — CASTÚO-SYSTEM™ Global v10.0.
 * @dev Registro de estándares UE (GDPR, AI Act 2024/1689, PAC 2027) + nodos autorizados para escalabilidad.
 */
contract EUCore {
    address public owner;
    mapping(string => bool) public compliantStandards;
    mapping(address => bool) public authorizedNodes;

    event StandardAdded(string standard);
    event NodeAuthorized(address node);

    constructor() {
        owner = msg.sender;
        compliantStandards["GDPR"] = true;
        compliantStandards["AI_Act_2024/1689"] = true;
        compliantStandards["PAC_2027"] = true;
    }

    function addCompliantStandard(string memory standard) public {
        require(msg.sender == owner, "Only owner");
        compliantStandards[standard] = true;
        emit StandardAdded(standard);
    }

    function authorizeNode(address node) public {
        require(msg.sender == owner, "Only owner");
        authorizedNodes[node] = true;
        emit NodeAuthorized(node);
    }

    function isCompliant(string memory standard) public view returns (bool) {
        return compliantStandards[standard];
    }

    function isAuthorized(address node) public view returns (bool) {
        return authorizedNodes[node];
    }
}
