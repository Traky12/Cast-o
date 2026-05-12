// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

/**
 * @title JapanCompliance
 * @notice Cumplimiento Japón — MHLW + JAS (Japanese Agricultural Standard). CASTÚO Global v9.0.
 * @dev THC en basis points: 30 = 0.30% (límite japonés).
 */
contract JapanCompliance {
    address public mhlw; // Ministerio de Salud japonés (MHLW)

    struct Batch {
        uint256 id;
        string variety;
        uint256 thc; // basis points: 30 = 0.30%
        bool mhlwApproved;
        bool jasCertified; // JAS (Japanese Agricultural Standard)
    }

    mapping(uint256 => Batch) public batches;

    constructor(address _mhlw) {
        mhlw = _mhlw;
    }

    function requestApproval(
        uint256 batchId,
        string memory variety,
        uint256 thc
    ) public {
        require(thc <= 30, "THC exceeds Japanese limit (0.3%)");
        batches[batchId] = Batch(batchId, variety, thc, false, false);
    }

    function approveBatch(uint256 batchId) public {
        require(msg.sender == mhlw, "Only MHLW can approve");
        batches[batchId].mhlwApproved = true;
    }

    function certifyJAS(uint256 batchId) public {
        require(batches[batchId].mhlwApproved, "MHLW approval required first");
        batches[batchId].jasCertified = true;
    }
}
