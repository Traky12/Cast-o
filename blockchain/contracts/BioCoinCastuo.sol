// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

/**
 * @title BioCoin Castúo (CASTUO-SYSTEM™)
 * @notice Token con trazabilidad Git: cada mint vincula gitCommitHash y gitTxHash (GS1 EPCIS / BioCoin).
 */
contract BioCoinCastuo {
    string public name = "BioCoin Castúo";
    string public symbol = "BIOCAST";
    uint8 public decimals = 18;
    uint256 public totalSupply;

    mapping(address => uint256) public balanceOf;

    event Minted(
        address indexed minter,
        address indexed to,
        uint256 amount,
        string gitCommitHash,
        string gitTxHash,
        uint256 timestamp
    );

    constructor(uint256 initialSupply) {
        require(initialSupply > 0, "Initial supply must be > 0");
        totalSupply = initialSupply * (10 ** uint256(decimals));
        balanceOf[msg.sender] = totalSupply;
        emit Minted(msg.sender, msg.sender, totalSupply, "", "", block.timestamp);
    }

    /**
     * @param to Destinatario de los tokens.
     * @param amount Cantidad a minar (en unidades con 18 decimales).
     * @param gitCommitHash Hash del commit de Git (ej. SHA).
     * @param gitTxHash TX hash de BioCoin Castúo / GS1 EPCIS (32 hex).
     */
    function mint(
        address to,
        uint256 amount,
        string calldata gitCommitHash,
        string calldata gitTxHash
    ) external {
        require(to != address(0), "Mint to zero address");
        require(amount > 0, "Amount must be > 0");
        totalSupply += amount;
        balanceOf[to] += amount;
        emit Minted(msg.sender, to, amount, gitCommitHash, gitTxHash, block.timestamp);
    }
}
