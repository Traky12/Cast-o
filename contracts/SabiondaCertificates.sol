// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

/**
 * @title SabiondaCertificates
 * @notice Emisión de certificados de formación verificables en GaiaChain (Sistema Sabionda).
 * @dev Desplegar en GaiaChain testnet/mainnet. Integrar con Moodle vía backend (FastAPI).
 */
contract SabiondaCertificates {
    struct Certificate {
        string courseName;
        string studentId;
        string studentName;
        uint256 completionDate;
        bool isValid;
    }

    mapping(string => Certificate) public certificates;
    address public owner;

    event CertificateIssued(
        string indexed courseName,
        string indexed studentId,
        uint256 completionDate
    );

    event CertificateRevoked(string indexed studentId);

    constructor() {
        owner = msg.sender;
    }

    modifier onlyOwner() {
        require(msg.sender == owner, "Only owner can perform this action");
        _;
    }

    /**
     * @notice Emite un certificado para un alumno que ha completado un curso.
     * @param courseName Nombre del curso (ej: "Experto en Trazabilidad Blockchain").
     * @param studentId Identificador único del alumno.
     * @param studentName Nombre del alumno (puede ser hash o pseudónimo por RGPD).
     * @param completionDate Fecha de finalización (timestamp Unix).
     */
    function issueCertificate(
        string memory courseName,
        string memory studentId,
        string memory studentName,
        uint256 completionDate
    ) external onlyOwner {
        require(bytes(studentId).length > 0, "Student ID required");
        require(!certificates[studentId].isValid, "Certificate already exists for this student");

        certificates[studentId] = Certificate({
            courseName: courseName,
            studentId: studentId,
            studentName: studentName,
            completionDate: completionDate,
            isValid: true
        });

        emit CertificateIssued(courseName, studentId, completionDate);
    }

    /**
     * @notice Verifica un certificado por studentId.
     * @param studentId Identificador del alumno.
     * @return Certificate struct (courseName, studentId, studentName, completionDate, isValid).
     */
    function verifyCertificate(string memory studentId) external view returns (Certificate memory) {
        require(certificates[studentId].isValid, "Certificate not valid or revoked");
        return certificates[studentId];
    }

    /**
     * @notice Revoca un certificado (solo owner).
     * @param studentId Identificador del alumno.
     */
    function revokeCertificate(string memory studentId) external onlyOwner {
        require(certificates[studentId].isValid, "Certificate already invalid");
        certificates[studentId].isValid = false;
        emit CertificateRevoked(studentId);
    }

    /**
     * @notice Comprueba si un certificado existe y es válido.
     * @param studentId Identificador del alumno.
     */
    function isCertificateValid(string memory studentId) external view returns (bool) {
        return certificates[studentId].isValid;
    }
}
