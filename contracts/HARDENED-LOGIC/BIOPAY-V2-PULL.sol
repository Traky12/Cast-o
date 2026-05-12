// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/**
 * @title BioPayV2 — Pago por biomasa (Patrón Pull — CIPHER-LEVEL-5)
 * @notice Consenso triple-check off-chain (NIR tolva + VULCAN firma + TERRA hash).
 *         Solo el orquestador autoriza; el productor retira (pull) para evitar reentrancy.
 * @dev No usar send() ni transfer() directos. Flujo: Authorize -> Pull.
 */
contract BioPayV2 {
    address public orchestrator;
    address public admin;

    mapping(address => uint256) public payments;

    bool private _locked;

    event QualityValidated(uint256 indexed shipmentId, bool success);
    event FundsWithdrawn(address indexed producer, uint256 amount);
    event PaymentAuthorized(address indexed producer, uint256 amount, uint256 shipmentId);

    error NotOrchestrator();
    error NotAdmin();
    error ReentrancyGuard();
    error NoFunds();

    modifier onlyOrchestrator() {
        if (msg.sender != orchestrator) revert NotOrchestrator();
        _;
    }

    modifier onlyAdmin() {
        if (msg.sender != admin) revert NotAdmin();
        _;
    }

    modifier nonReentrant() {
        if (_locked) revert ReentrancyGuard();
        _locked = true;
        _;
        _locked = false;
    }

    constructor(address _orchestrator) {
        admin = msg.sender;
        orchestrator = _orchestrator;
    }

    function setOrchestrator(address o) external onlyAdmin {
        orchestrator = o;
    }

    /**
     * Llamar solo tras triple-check: NIR (tolva), VULCAN (predicción aérea), TERRA (trazabilidad campo).
     */
    function authorizePayment(address _producer, uint256 _amount, uint256 _shipmentId) external onlyOrchestrator {
        require(_producer != address(0) && _amount > 0, "Bad params");
        payments[_producer] += _amount;
        emit QualityValidated(_shipmentId, true);
        emit PaymentAuthorized(_producer, _amount, _shipmentId);
    }

    function withdrawFunds() external nonReentrant {
        uint256 amount = payments[msg.sender];
        if (amount == 0) revert NoFunds();

        payments[msg.sender] = 0;
        (bool success, ) = payable(msg.sender).call{value: amount}("");
        require(success, "Transfer failed");

        emit FundsWithdrawn(msg.sender, amount);
    }

    receive() external payable {}
}
