// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

/**
 * @title JuntaExtremaduraAlliance
 * @notice Alianza con la Junta de Extremadura — programas de subvenciones (PAC 2027, etc.).
 * @dev Solo juntaAddress puede crear programas y distribuir; registro de inversiones.
 */
contract JuntaExtremaduraAlliance {
    struct SubsidyProgram {
        string name;
        uint256 budget;
        uint256 distributed;
        uint256 maxPerFarm;
        bool active;
    }

    address public owner;
    address public juntaAddress;
    uint256 public totalSubsidies;
    uint256 public totalInvestment;
    uint256 public programCount;

    mapping(uint256 => SubsidyProgram) public programs;
    mapping(address => uint256) public farmSubsidies;
    mapping(address => mapping(uint256 => uint256)) public subsidyByFarmAndProgram;

    event SubsidyProgramCreated(uint256 id, string name, uint256 budget);
    event SubsidyDistributed(address farm, uint256 programId, uint256 amount);
    event InvestmentMade(uint256 amount, string purpose);

    modifier onlyJunta() {
        require(msg.sender == juntaAddress, "Only Junta");
        _;
    }

    constructor(address _junta) {
        owner = msg.sender;
        juntaAddress = _junta;
    }

    function createSubsidyProgram(
        string memory name,
        uint256 budget,
        uint256 maxPerFarm
    ) public onlyJunta {
        uint256 id = programCount;
        programs[id] = SubsidyProgram({
            name: name,
            budget: budget,
            distributed: 0,
            maxPerFarm: maxPerFarm,
            active: true
        });
        programCount++;
        emit SubsidyProgramCreated(id, name, budget);
    }

    function distributeSubsidy(
        address farm,
        uint256 programId,
        uint256 amount
    ) public onlyJunta {
        require(programId < programCount, "Invalid program");
        SubsidyProgram storage prog = programs[programId];
        require(prog.active, "Program not active");
        require(prog.distributed + amount <= prog.budget, "Budget exceeded");
        require(
            subsidyByFarmAndProgram[farm][programId] + amount <= prog.maxPerFarm,
            "Max per farm exceeded"
        );

        prog.distributed += amount;
        subsidyByFarmAndProgram[farm][programId] += amount;
        farmSubsidies[farm] += amount;
        totalSubsidies += amount;

        emit SubsidyDistributed(farm, programId, amount);
    }

    function registerInvestment(uint256 amount, string memory purpose) public onlyJunta {
        totalInvestment += amount;
        emit InvestmentMade(amount, purpose);
    }

    function getFarmSubsidies(address farm) public view returns (uint256) {
        return farmSubsidies[farm];
    }

    function getProgramStatus(uint256 programId) public view returns (
        string memory name,
        uint256 budget,
        uint256 distributed,
        uint256 maxPerFarm,
        bool active
    ) {
        require(programId < programCount, "Invalid program");
        SubsidyProgram storage p = programs[programId];
        return (p.name, p.budget, p.distributed, p.maxPerFarm, p.active);
    }
}
