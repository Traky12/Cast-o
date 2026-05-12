// SPDX-License-Identifier: MIT
// CASTUO-SYSTEM™ — Certificación de materiales compuestos (BioCoin Castúo)
pragma solidity ^0.8.0;

contract MaterialCertification {
    struct Certification {
        uint256 id;
        string materialType;
        uint256 kgProduced;
        string rawMaterial;
        uint256 energyKwh;
        string certificationBody;
        string date;
        string validity;
        string ipfsHash;
    }

    struct Sale {
        uint256 id;
        address buyer;
        uint256[] materialIds;
        uint256[] kgSold;
        string date;
    }

    uint256 public nextCertificationId = 1;
    uint256 public nextSaleId = 1;

    mapping(uint256 => Certification) public certifications;
    mapping(uint256 => Sale) public sales;

    event CertificationRegistered(
        uint256 indexed id,
        string materialType,
        uint256 kgProduced,
        string certificationBody
    );

    event SaleRegistered(
        uint256 indexed id,
        address buyer,
        string date
    );

    function registerCertification(
        string memory materialType,
        uint256 kgProduced,
        string memory rawMaterial,
        uint256 energyKwh,
        string memory certificationBody,
        string memory date,
        string memory validity,
        string memory ipfsHash
    ) public {
        uint256 id = nextCertificationId;
        certifications[id] = Certification({
            id: id,
            materialType: materialType,
            kgProduced: kgProduced,
            rawMaterial: rawMaterial,
            energyKwh: energyKwh,
            certificationBody: certificationBody,
            date: date,
            validity: validity,
            ipfsHash: ipfsHash
        });
        nextCertificationId++;
        emit CertificationRegistered(id, materialType, kgProduced, certificationBody);
    }

    function registerSale(
        address buyer,
        uint256[] memory materialIds,
        uint256[] memory kgSold,
        string memory date
    ) public {
        require(materialIds.length == kgSold.length, "Length mismatch");
        uint256 id = nextSaleId;
        sales[id] = Sale({
            id: id,
            buyer: buyer,
            materialIds: materialIds,
            kgSold: kgSold,
            date: date
        });
        nextSaleId++;
        emit SaleRegistered(id, buyer, date);
    }

    function getCertification(uint256 id) public view returns (
        uint256,
        string memory,
        uint256,
        string memory,
        uint256,
        string memory,
        string memory,
        string memory,
        string memory
    ) {
        Certification memory c = certifications[id];
        return (
            c.id,
            c.materialType,
            c.kgProduced,
            c.rawMaterial,
            c.energyKwh,
            c.certificationBody,
            c.date,
            c.validity,
            c.ipfsHash
        );
    }

    function getSale(uint256 id) public view returns (
        uint256,
        address,
        uint256[] memory,
        uint256[] memory,
        string memory
    ) {
        Sale memory s = sales[id];
        return (s.id, s.buyer, s.materialIds, s.kgSold, s.date);
    }
}
