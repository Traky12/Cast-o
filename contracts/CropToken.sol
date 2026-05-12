// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract CropToken {
    enum CropType { Lettuce, Cannabis, Tomato, Strawberry }

    struct Crop {
        CropType cropType;
        uint256 quantity;
        string farmId;
        uint256 co2Saved;
        string verraProjectId;
    }

    mapping(uint256 => Crop) public crops;
    uint256 public cropCount;

    event CropTokenized(
        uint256 indexed tokenId,
        string farmId,
        CropType cropType,
        uint256 quantity
    );

    function tokenizeCrop(
        string memory farmId,
        CropType cropType,
        uint256 quantity,
        uint256 co2Saved,
        string memory verraProjectId
    ) public {
        cropCount++;
        crops[cropCount] = Crop({
            cropType: cropType,
            quantity: quantity,
            farmId: farmId,
            co2Saved: co2Saved,
            verraProjectId: verraProjectId
        });
        emit CropTokenized(cropCount, farmId, cropType, quantity);
    }

    function getCrop(uint256 tokenId) public view returns (Crop memory) {
        return crops[tokenId];
    }
}
