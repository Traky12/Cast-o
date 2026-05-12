// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/token/ERC721/ERC721.sol";
import "@openzeppelin/contracts/utils/Counters.sol";

/**
 * ForestOwnershipToken: propiedad forestal tokenizada (Ley 3/2023, Decreto 45/2020, Orden 15/03/2021).
 * Parcela, propietario, coordenadas, especies, CO₂ secuestrado. Integrable con SIGPAC, BRIF y CarbonCredit.
 */
contract ForestOwnershipToken is ERC721 {
    using Counters for Counters.Counter;
    Counters.Counter private _tokenIds;

    struct ForestProperty {
        string parcelaId;
        address owner;
        string coordinates;
        uint256 area;
        string treeSpecies;
        uint256 carbonSequestered;
        string ipfsHash;
        bool isProtected;
    }

    mapping(uint256 => ForestProperty) private _tokenIdToProperty;
    mapping(uint256 => string[]) private _tokenIdToCertifications;
    mapping(address => uint256[]) private _ownerToTokens;

    event PropertyMinted(uint256 indexed tokenId, address indexed owner, string parcelaId);
    event PropertyTransferred(uint256 indexed tokenId, address indexed newOwner);
    event CarbonUpdated(uint256 indexed tokenId, uint256 newCarbonValue);
    event MetadataUpdated(uint256 indexed tokenId, string newIpfsHash);
    event DataRedacted(uint256 indexed tokenId, string reason, uint256 timestamp);

    constructor() ERC721("ForestOwnershipToken", "FOT") {}

    function mintProperty(
        address to,
        string memory parcelaId,
        string memory coordinates,
        uint256 area,
        string memory treeSpecies,
        uint256 carbonSequestered,
        bool isProtected,
        string memory ipfsHash,
        string[] memory certifications
    ) external returns (uint256) {
        require(to != address(0), "Invalid address");
        require(area > 0, "Area must be > 0");
        require(bytes(parcelaId).length > 0, "parcelaId required");

        _tokenIds.increment();
        uint256 newTokenId = _tokenIds.current();

        _mint(to, newTokenId);
        _tokenIdToProperty[newTokenId] = ForestProperty({
            parcelaId: parcelaId,
            owner: to,
            coordinates: coordinates,
            area: area,
            treeSpecies: treeSpecies,
            carbonSequestered: carbonSequestered,
            ipfsHash: ipfsHash,
            isProtected: isProtected
        });
        for (uint256 i = 0; i < certifications.length; i++) {
            _tokenIdToCertifications[newTokenId].push(certifications[i]);
        }

        _ownerToTokens[to].push(newTokenId);
        emit PropertyMinted(newTokenId, to, parcelaId);
        return newTokenId;
    }

    function transferProperty(uint256 tokenId, address newOwner) external {
        require(ownerOf(tokenId) == msg.sender, "Not the owner");
        require(newOwner != address(0), "Invalid new owner");
        address previousOwner = msg.sender;
        _transfer(previousOwner, newOwner, tokenId);
        _tokenIdToProperty[tokenId].owner = newOwner;
        _removeFromOwnerTokens(previousOwner, tokenId);
        _ownerToTokens[newOwner].push(tokenId);
        emit PropertyTransferred(tokenId, newOwner);
    }

    function _removeFromOwnerTokens(address owner, uint256 tokenId) private {
        uint256[] storage tokens = _ownerToTokens[owner];
        for (uint256 i = 0; i < tokens.length; i++) {
            if (tokens[i] == tokenId) {
                tokens[i] = tokens[tokens.length - 1];
                tokens.pop();
                break;
            }
        }
    }

    function getProperty(uint256 tokenId) external view returns (ForestProperty memory) {
        require(ownerOf(tokenId) != address(0), "Token does not exist");
        return _tokenIdToProperty[tokenId];
    }

    function getOwnerProperties(address owner) external view returns (uint256[] memory) {
        return _ownerToTokens[owner];
    }

    function updateCarbonSequestered(uint256 tokenId, uint256 newCarbonValue) external {
        require(ownerOf(tokenId) == msg.sender, "Not the owner");
        _tokenIdToProperty[tokenId].carbonSequestered = newCarbonValue;
        emit CarbonUpdated(tokenId, newCarbonValue);
    }

    function updateMetadata(uint256 tokenId, string memory newIpfsHash) external {
        require(ownerOf(tokenId) == msg.sender, "Not the owner");
        require(bytes(newIpfsHash).length > 0, "ipfsHash required");
        _tokenIdToProperty[tokenId].ipfsHash = newIpfsHash;
        emit MetadataUpdated(tokenId, newIpfsHash);
    }

    function logRedaction(uint256 tokenId, string memory reason) external {
        require(ownerOf(tokenId) == msg.sender, "Not the owner");
        emit DataRedacted(tokenId, reason, block.timestamp);
    }

    function getCertifications(uint256 tokenId) external view returns (string[] memory) {
        require(ownerOf(tokenId) != address(0), "Token does not exist");
        return _tokenIdToCertifications[tokenId];
    }

    function getEligibleSubsidies(uint256 tokenId) external view returns (string[] memory) {
        require(ownerOf(tokenId) != address(0), "Token does not exist");
        ForestProperty memory property = _tokenIdToProperty[tokenId];
        string[] memory certs = _tokenIdToCertifications[tokenId];
        uint256 areaHa = property.area / 10000;
        uint256 count = 0;
        bool hasPefcFsc = false;
        bool hasRedNatura = false;
        for (uint256 i = 0; i < certs.length; i++) {
            if (_eq(certs[i], "PEFC") || _eq(certs[i], "FSC")) hasPefcFsc = true;
            if (_eq(certs[i], "Red Natura 2000")) hasRedNatura = true;
        }
        if (areaHa > 0) count++;
        if (hasPefcFsc) count++;
        if (hasRedNatura) count++;
        if (property.isProtected && !hasRedNatura) count++;
        string[] memory subsidies = new string[](count);
        uint256 j = 0;
        if (areaHa > 0) {
            subsidies[j++] = string(abi.encodePacked("PAC_2040:", _uint2str(200 * areaHa)));
        }
        if (hasPefcFsc) {
            subsidies[j++] = string(abi.encodePacked("Decreto_45_2020:", _uint2str(150 * areaHa)));
        }
        if (hasRedNatura) {
            subsidies[j++] = string(abi.encodePacked("Red_Natura_2000:", _uint2str(300 * areaHa)));
        }
        if (property.isProtected && !hasRedNatura) {
            subsidies[j++] = string(abi.encodePacked("Area_Protegida:", _uint2str(100 * areaHa)));
        }
        return subsidies;
    }

    function calculateSubsidies(uint256 tokenId) external view returns (uint256) {
        require(ownerOf(tokenId) != address(0), "Token does not exist");
        ForestProperty memory property = _tokenIdToProperty[tokenId];
        string[] memory certs = _tokenIdToCertifications[tokenId];
        uint256 areaHa = property.area / 10000;
        uint256 total = 200 * areaHa;
        for (uint256 i = 0; i < certs.length; i++) {
            if (_eq(certs[i], "PEFC") || _eq(certs[i], "FSC")) {
                total += 150 * areaHa;
                break;
            }
        }
        for (uint256 i = 0; i < certs.length; i++) {
            if (_eq(certs[i], "Red Natura 2000")) {
                total += 300 * areaHa;
                break;
            }
        }
        if (property.isProtected) {
            bool hasRedNatura = false;
            for (uint256 i = 0; i < certs.length; i++) {
                if (_eq(certs[i], "Red Natura 2000")) {
                    hasRedNatura = true;
                    break;
                }
            }
            if (!hasRedNatura) total += 100 * areaHa;
        }
        return total;
    }

    function _eq(string memory a, string memory b) private pure returns (bool) {
        return keccak256(bytes(a)) == keccak256(bytes(b));
    }

    function _uint2str(uint256 v) private pure returns (string memory) {
        if (v == 0) return "0";
        uint256 j = v;
        uint256 len;
        while (j != 0) {
            len++;
            j /= 10;
        }
        bytes memory bstr = new bytes(len);
        uint256 k = len;
        j = v;
        while (j != 0) {
            k = k > 0 ? k - 1 : 0;
            bstr[k] = bytes1(uint8(48 + (j % 10)));
            j /= 10;
        }
        return string(bstr);
    }
}
