// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

/**
 * @title FairPriceContract
 * @notice Precios justos para agricultores — CASTÚO-SYSTEM™ (origen Extremeño).
 * @dev Solo cooperativa extremeña puede certificar fincas; precio justo = base + 15% (coop + fondo equidad).
 */
contract FairPriceContract {
    struct Product {
        string name;
        uint256 basePrice;
        uint256 minPrice;
        uint256 maxPrice;
        address[] certifiedFarms;
    }

    mapping(string => Product) public products;
    address public owner;
    address public extremeñaCooperative;

    event PriceUpdated(string product, uint256 newPrice);
    event FarmCertified(address farm, string product);

    modifier onlyOwner() {
        require(msg.sender == owner, "Only owner");
        _;
    }

    constructor(address _cooperative) {
        owner = msg.sender;
        extremeñaCooperative = _cooperative;
    }

    function addProduct(
        string memory name,
        uint256 basePrice,
        uint256 minPrice,
        uint256 maxPrice
    ) public onlyOwner {
        products[name] = Product({
            name: name,
            basePrice: basePrice,
            minPrice: minPrice,
            maxPrice: maxPrice,
            certifiedFarms: new address[](0)
        });
        emit PriceUpdated(name, basePrice);
    }

    function certifyFarm(address farm, string memory product) public {
        require(msg.sender == extremeñaCooperative, "Only Extremadura cooperative can certify farms");
        products[product].certifiedFarms.push(farm);
        emit FarmCertified(farm, product);
    }

    /// @notice Precio justo = basePrice + 10% cooperativa + 5% fondo equidad
    function getFairPrice(string memory product) public view returns (uint256) {
        return (products[product].basePrice * 115) / 100;
    }

    function isCertifiedFarm(address farm, string memory product) public view returns (bool) {
        address[] storage farms = products[product].certifiedFarms;
        for (uint256 i = 0; i < farms.length; i++) {
            if (farms[i] == farm) return true;
        }
        return false;
    }
}
