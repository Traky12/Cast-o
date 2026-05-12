// SPDX-License-Identifier: MIT
// CASTUO-SYSTEM™ — Mercado de créditos (VCS, GS, EUA)
pragma solidity ^0.8.0;

contract CarbonMarket {
    struct Credit {
        uint256 id;
        string standard;
        uint256 vintageYear;
        uint256 quantity;
        string projectId;
        string verificationDoc;
        address owner;
        bool retired;
    }

    struct Transfer {
        uint256 id;
        uint256 creditId;
        address from;
        address to;
        uint256 quantity;
        uint256 pricePerTon;
        uint256 timestamp;
    }

    uint256 public nextCreditId = 1;
    uint256 public nextTransferId = 1;
    mapping(uint256 => Credit) public credits;
    mapping(uint256 => Transfer) public transfers;
    mapping(address => uint256[]) public creditsByOwner;

    event CreditIssued(uint256 indexed id, string standard, uint256 quantity, address owner);
    event CreditTransferred(uint256 indexed id, uint256 creditId, address from, address to, uint256 quantity, uint256 pricePerTon);
    event CreditRetired(uint256 indexed id, uint256 quantity);

    function issueCredit(
        string memory standard,
        uint256 vintageYear,
        uint256 quantity,
        string memory projectId,
        string memory verificationDoc
    ) public {
        uint256 id = nextCreditId++;
        credits[id] = Credit({
            id: id,
            standard: standard,
            vintageYear: vintageYear,
            quantity: quantity,
            projectId: projectId,
            verificationDoc: verificationDoc,
            owner: msg.sender,
            retired: false
        });
        creditsByOwner[msg.sender].push(id);
        emit CreditIssued(id, standard, quantity, msg.sender);
    }

    function transferCredit(uint256 creditId, address to, uint256 quantity, uint256 pricePerTon) public {
        Credit storage c = credits[creditId];
        require(c.owner == msg.sender && c.quantity >= quantity && !c.retired);
        c.quantity -= quantity;
        if (c.quantity == 0) c.retired = true;
        creditsByOwner[to].push(creditId);
        transfers[nextTransferId] = Transfer({
            id: nextTransferId,
            creditId: creditId,
            from: msg.sender,
            to: to,
            quantity: quantity,
            pricePerTon: pricePerTon,
            timestamp: block.timestamp
        });
        emit CreditTransferred(nextTransferId++, creditId, msg.sender, to, quantity, pricePerTon);
    }

    function retireCredit(uint256 creditId, uint256 quantity) public {
        Credit storage c = credits[creditId];
        require(c.owner == msg.sender && c.quantity >= quantity && !c.retired);
        c.quantity -= quantity;
        c.retired = c.quantity == 0;
        emit CreditRetired(creditId, quantity);
    }

    function getCredit(uint256 id) public view returns (Credit memory) { return credits[id]; }
    function getCreditsByOwner(address owner) public view returns (uint256[] memory) { return creditsByOwner[owner]; }
}
