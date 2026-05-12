// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

/**
 * @title DynamicCompliance
 * @notice Módulo de adaptación legal dinámica — CASTÚO-SYSTEM™ v10.0.
 * @dev Reglas por país (estándares + autoridades) para cumplimiento automático en 50+ jurisdicciones.
 */
contract DynamicCompliance {
    struct CountryRules {
        string countryCode;
        string[] standards;
        address[] authorities;
    }

    mapping(string => CountryRules) public countryRules;
    address public owner;
    address public governance;

    event RulesAdded(string countryCode, string standard);
    event AuthorityAdded(string countryCode, address authority);
    event GovernanceSet(address governance);

    modifier onlyOwnerOrGovernance() {
        require(msg.sender == owner || msg.sender == governance, "Only owner or governance");
        _;
    }

    constructor() {
        owner = msg.sender;
    }

    function setGovernance(address _governance) public {
        require(msg.sender == owner, "Only owner");
        governance = _governance;
        emit GovernanceSet(_governance);
    }

    function addCountryRules(
        string memory countryCode,
        string[] memory standards,
        address[] memory authorities
    ) public onlyOwnerOrGovernance {
        countryRules[countryCode] = CountryRules(countryCode, standards, authorities);
        for (uint256 i = 0; i < standards.length; i++) {
            emit RulesAdded(countryCode, standards[i]);
        }
        for (uint256 i = 0; i < authorities.length; i++) {
            emit AuthorityAdded(countryCode, authorities[i]);
        }
    }

    function isCompliant(string memory countryCode, string memory standard) public view returns (bool) {
        CountryRules storage rules = countryRules[countryCode];
        for (uint256 i = 0; i < rules.standards.length; i++) {
            if (keccak256(abi.encodePacked(rules.standards[i])) == keccak256(abi.encodePacked(standard))) {
                return true;
            }
        }
        return false;
    }

    function isAuthority(string memory countryCode, address authority) public view returns (bool) {
        CountryRules storage rules = countryRules[countryCode];
        for (uint256 i = 0; i < rules.authorities.length; i++) {
            if (rules.authorities[i] == authority) {
                return true;
            }
        }
        return false;
    }
}
