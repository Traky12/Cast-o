// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/**
 * CompostToken: trazabilidad on-chain de batches de compost (calidad + kg).
 * Registro inmutable por batch para certificación en Biofertilizantes.org y GaiaChain.
 */
contract CompostToken {
    struct Batch {
        address owner;
        uint256 kg;
        uint256 temperature;
        uint256 humidity;
        uint256 ph;
        string batchId;
        bool registered;
    }

    mapping(uint256 => Batch) public batches;
    uint256 public batchCount;

    event CompostRegistered(
        uint256 indexed batchIndex,
        address indexed owner,
        uint256 kg,
        uint256 temperature,
        uint256 humidity,
        uint256 ph,
        string batchId
    );

    function registerCompostQuality(
        uint256 kg,
        uint256 temperature,
        uint256 humidity,
        uint256 ph,
        string calldata batchId
    ) external {
        require(kg > 0, "kg must be > 0");
        require(bytes(batchId).length > 0, "batchId required");
        uint256 idx = batchCount;
        batches[idx] = Batch({
            owner: msg.sender,
            kg: kg,
            temperature: temperature,
            humidity: humidity,
            ph: ph,
            batchId: batchId,
            registered: true
        });
        batchCount++;
        emit CompostRegistered(idx, msg.sender, kg, temperature, humidity, ph, batchId);
    }

    function getBatch(uint256 index) external view returns (
        address owner,
        uint256 kg,
        uint256 temperature,
        uint256 humidity,
        uint256 ph,
        string memory batchId,
        bool registered
    ) {
        Batch storage b = batches[index];
        return (b.owner, b.kg, b.temperature, b.humidity, b.ph, b.batchId, b.registered);
    }
}
