// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

/**
 * @title MAPAAlliance
 * @notice Alianza con MAPA (Ministerio) — distribución de subvenciones PAC 2027.
 * @dev Solo dirección MAPA puede firmar alianza y distribuir subsidios; tope por finca.
 */
contract MAPAAlliance {
    address public owner;
    address public mapaAddress;
    uint256 public totalSubsidiesDistributed;
    mapping(address => uint256) public farmSubsidies;
    uint256 public constant MAX_SUBSIDY_PER_FARM = 500 ether;

    event SubsidyDistributed(address farm, uint256 amount);
    event AllianceSigned(uint256 amount);

    constructor(address _mapa) {
        owner = msg.sender;
        mapaAddress = _mapa;
    }

    receive() external payable {}

    function signAlliance() public payable {
        require(msg.sender == mapaAddress, "Only MAPA can sign alliance");
        require(msg.value > 0, "Funding required");
        emit AllianceSigned(msg.value);
    }

    function distributeSubsidy(address farm, uint256 amount) public {
        require(msg.sender == mapaAddress, "Only MAPA can distribute subsidies");
        require(farmSubsidies[farm] + amount <= MAX_SUBSIDY_PER_FARM, "Max subsidy per farm exceeded");
        require(address(this).balance >= amount, "Insufficient balance");

        farmSubsidies[farm] += amount;
        totalSubsidiesDistributed += amount;
        (bool ok, ) = payable(farm).call{ value: amount }("");
        require(ok, "Transfer failed");
        emit SubsidyDistributed(farm, amount);
    }

    function getFarmSubsidy(address farm) public view returns (uint256) {
        return farmSubsidies[farm];
    }

    function getTotalSubsidies() public view returns (uint256) {
        return totalSubsidiesDistributed;
    }
}
