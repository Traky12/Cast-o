// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

import "./DynamicCompliance.sol";

/**
 * @title GlobalGovernance
 * @notice Gobernanza global DAO — CASTÚO-SYSTEM™ v10.0.
 * @dev Votación para añadir estándares locales; ejecución automática vía DynamicCompliance.
 */
contract GlobalGovernance {
    DynamicCompliance public dynamicCompliance;

    struct Proposal {
        uint256 id;
        string description;
        string countryCode;
        string standard;
        uint256 votesFor;
        uint256 votesAgainst;
        bool executed;
    }

    mapping(uint256 => Proposal) public proposals;
    uint256 public proposalCount;
    address public owner;

    event ProposalCreated(uint256 id, string description);
    event Voted(uint256 id, address voter, bool support);
    event ProposalExecuted(uint256 id);

    constructor(address _dynamicCompliance) {
        owner = msg.sender;
        dynamicCompliance = DynamicCompliance(_dynamicCompliance);
    }

    function createProposal(
        string memory description,
        string memory countryCode,
        string memory standard
    ) public {
        proposalCount++;
        proposals[proposalCount] = Proposal(
            proposalCount,
            description,
            countryCode,
            standard,
            0,
            0,
            false
        );
        emit ProposalCreated(proposalCount, description);
    }

    function vote(uint256 proposalId, bool support) public {
        require(!proposals[proposalId].executed, "Proposal already executed");
        if (support) {
            proposals[proposalId].votesFor++;
        } else {
            proposals[proposalId].votesAgainst++;
        }
        emit Voted(proposalId, msg.sender, support);
    }

    function executeProposal(uint256 proposalId) public {
        require(
            proposals[proposalId].votesFor > proposals[proposalId].votesAgainst,
            "Proposal did not pass"
        );
        require(!proposals[proposalId].executed, "Proposal already executed");
        proposals[proposalId].executed = true;

        string[] memory standards = new string[](1);
        standards[0] = proposals[proposalId].standard;
        address[] memory authorities;
        dynamicCompliance.addCountryRules(
            proposals[proposalId].countryCode,
            standards,
            authorities
        );

        emit ProposalExecuted(proposalId);
    }
}
