// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

/**
 * @title FranchiseContract
 * @notice Franquicias SABIONDA — cooperativas locales bajo licencia (origen Extremeño).
 * @dev Cuota inicial; regalías por ingresos; 50% cooperativa extremeña, 50% fondo equidad.
 */
contract FranchiseContract {
    struct Franchise {
        address franchisee;
        string region;
        uint256 startDate;
        uint256 endDate;
        uint256 royaltyPercentage;
        bool active;
    }

    mapping(address => Franchise) public franchises;
    address public owner;
    address public extremeñaCooperative;
    uint256 public franchiseFee = 0.1 ether;

    event FranchiseGranted(address franchisee, string region);
    event RoyaltyPaid(address franchisee, uint256 amount);

    modifier onlyCooperative() {
        require(msg.sender == extremeñaCooperative, "Only cooperative");
        _;
    }

    constructor(address _cooperative) {
        owner = msg.sender;
        extremeñaCooperative = _cooperative;
    }

    function grantFranchise(
        address franchisee,
        string memory region,
        uint256 durationDays,
        uint256 royaltyPercentage
    ) public payable {
        require(msg.value >= franchiseFee, "Incorrect franchise fee");
        require(!franchises[franchisee].active, "Franchisee already exists");

        franchises[franchisee] = Franchise({
            franchisee: franchisee,
            region: region,
            startDate: block.timestamp,
            endDate: block.timestamp + durationDays * 1 days,
            royaltyPercentage: royaltyPercentage,
            active: true
        });

        if (msg.value > franchiseFee) {
            (bool ok, ) = payable(extremeñaCooperative).call{ value: msg.value - franchiseFee }("");
            require(ok, "Transfer failed");
        }
        emit FranchiseGranted(franchisee, region);
    }

    function payRoyalty(uint256 revenue) public payable {
        address franchisee = msg.sender;
        require(franchises[franchisee].active, "Franchise not active");
        require(block.timestamp <= franchises[franchisee].endDate, "Franchise expired");
        uint256 royalty = (revenue * franchises[franchisee].royaltyPercentage) / 100;
        require(msg.value == royalty, "Incorrect royalty amount");

        uint256 half = msg.value / 2;
        (bool ok1, ) = payable(extremeñaCooperative).call{ value: half }("");
        require(ok1, "Transfer coop failed");
        (bool ok2, ) = payable(address(this)).call{ value: msg.value - half }("");
        require(ok2, "Transfer fund failed");

        emit RoyaltyPaid(franchisee, msg.value);
    }

    function renewFranchise(address franchisee, uint256 newDurationDays) public payable onlyCooperative {
        require(franchises[franchisee].active, "Franchise not active");
        require(msg.value >= franchiseFee / 2, "Incorrect renewal fee");
        franchises[franchisee].endDate += newDurationDays * 1 days;
    }

    function revokeFranchise(address franchisee) public onlyCooperative {
        franchises[franchisee].active = false;
    }
}
