// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract CarbonCredit {
    address public owner;
    uint256 public totalCredits;
    mapping(address => uint256) public credits;

    event CreditIssued(address indexed to, uint256 amount);

    constructor() {
        owner = msg.sender;
    }

    function issueCredits(address to, uint256 amount) public {
        require(msg.sender == owner, "Not authorized");
        credits[to] += amount;
        totalCredits += amount;
        emit CreditIssued(to, amount);
    }

    function getCredits(address account) public view returns (uint256) {
        return credits[account];
    }
}
