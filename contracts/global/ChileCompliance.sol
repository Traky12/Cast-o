// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

/**
 * @title ChileCompliance
 * @notice Cumplimiento Chile — SAG (Servicio Agrícola y Ganadero). Ley 20.000 cannabis medicinal. CASTÚO Global v9.0.
 * @dev THC en basis points: 100 = 1.0% (límite Chile para uso medicinal).
 */
contract ChileCompliance {
    address public sag; // Servicio Agrícola y Ganadero de Chile

    struct Batch {
        uint256 id;
        string variety;
        uint256 thc; // basis points: 100 = 1.0%
        bool sagApproved;
        string exportLicense; // Licencia de exportación SAG
    }

    mapping(uint256 => Batch) public batches;

    constructor(address _sag) {
        sag = _sag;
    }

    function requestApproval(
        uint256 batchId,
        string memory variety,
        uint256 thc
    ) public {
        require(thc <= 100, "THC exceeds Chilean limit (1.0%)");
        batches[batchId] = Batch(batchId, variety, thc, false, "");
    }

    function approveBatch(uint256 batchId, string memory license) public {
        require(msg.sender == sag, "Only SAG can approve");
        require(
            keccak256(abi.encodePacked(license)) !=
                keccak256(abi.encodePacked("")),
            "Invalid license"
        );
        batches[batchId].sagApproved = true;
        batches[batchId].exportLicense = license;
    }
}
