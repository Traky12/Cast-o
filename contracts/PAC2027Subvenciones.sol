// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

/**
 * @title PAC2027Subvenciones
 * @notice Trazabilidad legal de subvenciones PAC 2027 en GaiaChain (CASTÚO-SYSTEM™ v7.1).
 * @dev Auditor único; elegibilidad por finca; solicitud con mínimo 365 días desde última auditoría.
 */
contract PAC2027Subvenciones {
    struct Farm {
        uint256 id;
        string owner;
        bool isEligible;
        uint256 lastAudit;
    }

    mapping(uint256 => Farm) public farms;
    address public auditor;

    event SubvencionApproved(uint256 indexed farmId, uint256 amount);

    constructor() {
        auditor = msg.sender;
    }

    modifier onlyAuditor() {
        require(msg.sender == auditor, "Only auditor");
        _;
    }

    /**
     * @notice Solicita subvención PAC 2027 (ej. 500 €/ha). Requiere finca elegible y auditoría al menos hace 365 días.
     */
    function requestSubvencion(uint256 farmId) external {
        require(farms[farmId].isEligible, "Farm not eligible");
        require(
            block.timestamp - farms[farmId].lastAudit >= 365 days,
            "Audit too recent"
        );
        emit SubvencionApproved(farmId, 500); // 500 €/ha
        farms[farmId].lastAudit = block.timestamp;
    }

    /**
     * @notice Establece elegibilidad de una finca (solo auditor).
     */
    function setEligibility(uint256 farmId, bool eligible) external onlyAuditor {
        farms[farmId].isEligible = eligible;
    }

    /**
     * @notice Registra o actualiza datos de finca (solo auditor).
     */
    function setFarm(
        uint256 farmId,
        string calldata owner,
        bool eligible,
        uint256 lastAuditTimestamp
    ) external onlyAuditor {
        farms[farmId] = Farm({
            id: farmId,
            owner: owner,
            isEligible: eligible,
            lastAudit: lastAuditTimestamp
        });
    }
}
