// SPDX-License-Identifier: MIT
// CASTUO-SYSTEM™ — Créditos de carbono (BioCoin Castúo)
pragma solidity ^0.8.0;

contract CarbonCredits {
    struct Credit {
        uint256 id;
        uint256 materialId;
        uint256 kgProduced;
        uint256 savingsKgCO2;
        string date;
        string verificationDoc;
        address owner;
        bool sold;
    }

    uint256 public nextCreditId = 1;
    mapping(uint256 => Credit) public credits;
    mapping(address => uint256[]) public creditsByOwner;

    event CreditRegistered(
        uint256 indexed id,
        uint256 materialId,
        uint256 savingsKgCO2,
        string date
    );

    event CreditSold(
        uint256 indexed id,
        address buyer,
        uint256 pricePerTon
    );

    function registerCredit(
        uint256 materialId,
        uint256 kgProduced,
        uint256 savingsKgCO2,
        string memory date,
        string memory verificationDoc
    ) public {
        uint256 id = nextCreditId;
        credits[id] = Credit({
            id: id,
            materialId: materialId,
            kgProduced: kgProduced,
            savingsKgCO2: savingsKgCO2,
            date: date,
            verificationDoc: verificationDoc,
            owner: msg.sender,
            sold: false
        });
        creditsByOwner[msg.sender].push(id);
        nextCreditId++;
        emit CreditRegistered(id, materialId, savingsKgCO2, date);
    }

    function sellCredit(
        uint256 creditId,
        address buyer,
        uint256 pricePerTon
    ) public {
        Credit storage credit = credits[creditId];
        require(credit.owner == msg.sender, "Solo el dueño puede vender");
        require(!credit.sold, "Este crédito ya ha sido vendido");
        credit.sold = true;
        credit.owner = buyer;
        emit CreditSold(creditId, buyer, pricePerTon);
    }

    function getCredit(uint256 id) public view returns (Credit memory) {
        return credits[id];
    }

    function getCreditsByOwner(address owner) public view returns (uint256[] memory) {
        return creditsByOwner[owner];
    }
}
