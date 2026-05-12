// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/**
 * @title CastuoToken (BIOC) — placeholder gobernanza MiCA
 * @notice Token utilidad / ART según whitepaper; minting restringido vía oráculo/HSM off-chain.
 * @dev Sustituir por ERC-3643 o estándar acordado con asesor legal antes de mainnet.
 */
contract CastuoToken {
    string public constant name = "Castuo BioCoin";
    string public constant symbol = "BIOC";
    uint8 public constant decimals = 18;
    uint256 public totalSupply;

    mapping(address => uint256) public balanceOf;
    address public governance;

    event Transfer(address indexed from, address indexed to, uint256 value);

    constructor(address _governance) {
        governance = _governance;
    }

    function mint(address to, uint256 amount) external {
        require(msg.sender == governance, "gov");
        totalSupply += amount;
        balanceOf[to] += amount;
        emit Transfer(address(0), to, amount);
    }
}
