// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/**
 * @title BioPay-Quality-v1 — pago cooperativa por potencial etanólico (Pe)
 * @notice Pe ∝ M × %Azúcares × (1 − %Humedad) × FactorBonus. Oráculo IoT (NIR) en recepción.
 * @dev Tesorería deposita ETH; oráculo fija calidad; pago automático al productor.
 */
contract BioPayQualityV1 {
    address public oracle;
    address public admin;

    uint256 public basePricePerKgWei;
    uint256 public constant BPS = 10_000;
    uint256 public constant MAX_MOISTURE_BPS = 2500;

    struct Shipment {
        address producer;
        uint256 weightKg;
        uint256 sugarBps;
        uint256 moistureBps;
        uint256 carbonBonusBps;
        bool registered;
        bool qualitySet;
        bool paid;
        uint256 priceWei;
    }

    mapping(uint256 => Shipment) public shipments;
    uint256 public treasuryBalance;

    event ShipmentRegistered(uint256 indexed id, address indexed producer, uint256 weightKg);
    event QualitySubmitted(
        uint256 indexed id,
        uint256 sugarBps,
        uint256 moistureBps,
        uint256 carbonBonusBps,
        uint256 computedPriceWei,
        string qualityGrade
    );
    event PaymentExecuted(uint256 indexed id, address indexed producer, uint256 amountWei);
    event TreasuryDeposit(address indexed from, uint256 amount);

    error NotOracle();
    error NotAdmin();
    error BadShipment();
    error AlreadyPaid();
    error MoistureTooHigh();
    error InsufficientTreasury();

    modifier onlyOracle() {
        if (msg.sender != oracle) revert NotOracle();
        _;
    }

    modifier onlyAdmin() {
        if (msg.sender != admin) revert NotAdmin();
        _;
    }

    constructor(address _oracle, uint256 _basePricePerKgWei) {
        admin = msg.sender;
        oracle = _oracle;
        basePricePerKgWei = _basePricePerKgWei;
    }

    function setOracle(address o) external onlyAdmin {
        oracle = o;
    }

    function setBasePrice(uint256 w) external onlyAdmin {
        basePricePerKgWei = w;
    }

    receive() external payable {
        treasuryBalance += msg.value;
        emit TreasuryDeposit(msg.sender, msg.value);
    }

    function depositTreasury() external payable {
        treasuryBalance += msg.value;
        emit TreasuryDeposit(msg.sender, msg.value);
    }

    function registerShipment(uint256 id, address producer, uint256 weightKg) external onlyOracle {
        if (producer == address(0) || weightKg == 0) revert BadShipment();
        Shipment storage s = shipments[id];
        if (s.registered) revert BadShipment();
        s.producer = producer;
        s.weightKg = weightKg;
        s.registered = true;
        emit ShipmentRegistered(id, producer, weightKg);
    }

    /**
     * @param sugarBps 0-10000 = 0-100% azúcares fermentables
     * @param moistureBps humedad; si > 15% penalización fuerte (revert si > 25%)
     * @param carbonBonusBps bonus huella negativa (drones/monitoreo); 0 si no aplica
     */
    function submitQualityAndPay(
        uint256 id,
        uint256 sugarBps,
        uint256 moistureBps,
        uint256 carbonBonusBps
    ) external onlyOracle {
        Shipment storage s = shipments[id];
        if (!s.registered || s.paid) revert BadShipment();
        if (moistureBps > MAX_MOISTURE_BPS) revert MoistureTooHigh();
        if (sugarBps > BPS) sugarBps = BPS;

        s.sugarBps = sugarBps;
        s.moistureBps = moistureBps;
        s.carbonBonusBps = carbonBonusBps;
        s.qualitySet = true;

        uint256 price = _computePrice(s);
        s.priceWei = price;
        if (treasuryBalance < price) revert InsufficientTreasury();

        treasuryBalance -= price;
        s.paid = true;

        (bool ok,) = s.producer.call{value: price}("");
        require(ok, "transfer");

        string memory grade = _grade(sugarBps, moistureBps);
        emit QualitySubmitted(id, sugarBps, moistureBps, carbonBonusBps, price, grade);
        emit PaymentExecuted(id, s.producer, price);
    }

    function _computePrice(Shipment memory s) internal view returns (uint256) {
        uint256 dry = BPS - s.moistureBps;
        uint256 bonusMul = BPS + s.carbonBonusBps;
        if (bonusMul > BPS * 2) bonusMul = BPS * 2;

        uint256 p = basePricePerKgWei * s.weightKg;
        p = (p * s.sugarBps) / BPS;
        p = (p * dry) / BPS;
        p = (p * bonusMul) / BPS;
        return p;
    }

    function _grade(uint256 sugarBps, uint256 moistureBps) internal pure returns (string memory) {
        if (sugarBps >= 7500 && moistureBps <= 1200) return "A+ Premium";
        if (sugarBps >= 6000 && moistureBps <= 1500) return "A";
        return "B";
    }
}
