// blockchain/chaincode/hemp_traceability.go
// Trazabilidad de cáñamo en GaiaChain — RD 903/2025, ZKP simplificado.
package main

import (
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"fmt"
	"log"

	"github.com/hyperledger/fabric-contract-api-go/contractapi"
)

// HempBatch representa un lote de producción de cáñamo
type HempBatch struct {
	BatchID      string  `json:"batch_id"`
	GreenhouseID string  `json:"greenhouse_id"`
	Strain       string  `json:"strain"`
	PlantingDate string  `json:"planting_date"`
	HarvestDate  string  `json:"harvest_date"`
	THCLevel     float64 `json:"thc_level"`
	CBDLevel     float64 `json:"cbd_level"`
	WeightKg     float64 `json:"weight_kg"`
	Owner        string  `json:"owner"`
	Status       string  `json:"status"` // planted, growing, harvested, processed
	ZKProof      string  `json:"zk_proof"`
}

// SmartContract funciones para trazabilidad de cáñamo
type SmartContract struct {
	contractapi.Contract
}

// InitLedger inicializa el chaincode
func (s *SmartContract) InitLedger(ctx contractapi.TransactionContextInterface) error {
	return nil
}

func sha256Hash(input string) string {
	h := sha256.Sum256([]byte(input))
	return hex.EncodeToString(h[:])[:16]
}

func generateZKProof(batchID string, greenhouseID string) string {
	proofData := fmt.Sprintf("%s-%s-%d", batchID, greenhouseID, 2026)
	return "ZKP-" + sha256Hash(proofData)
}

func verifyZKProof(proof string, batchID string, greenhouseID string) bool {
	return proof == generateZKProof(batchID, greenhouseID)
}

// CreateHempBatch crea un nuevo lote de cáñamo
func (s *SmartContract) CreateHempBatch(ctx contractapi.TransactionContextInterface,
	batchID string, greenhouseID string, strain string, plantingDate string,
	harvestDate string, thcLevel float64, cbdLevel float64, weightKg float64) error {

	if thcLevel >= 0.2 {
		return fmt.Errorf("THC level %.2f exceeds legal limit of 0.2%%", thcLevel)
	}

	zkProof := generateZKProof(batchID, greenhouseID)
	hempBatch := HempBatch{
		BatchID:      batchID,
		GreenhouseID: greenhouseID,
		Strain:       strain,
		PlantingDate: plantingDate,
		HarvestDate:  harvestDate,
		THCLevel:     thcLevel,
		CBDLevel:     cbdLevel,
		WeightKg:     weightKg,
		Owner:        "CASTUA-Cooperative",
		Status:       "planted",
		ZKProof:      zkProof,
	}

	batchJSON, err := json.Marshal(hempBatch)
	if err != nil {
		return err
	}
	return ctx.GetStub().PutState(batchID, batchJSON)
}

// UpdateHempStatus actualiza el estado del lote
func (s *SmartContract) UpdateHempStatus(ctx contractapi.TransactionContextInterface,
	batchID string, newStatus string, verifier string) error {

	batchJSON, err := ctx.GetStub().GetState(batchID)
	if err != nil {
		return err
	}
	if batchJSON == nil {
		return fmt.Errorf("hemp batch %s does not exist", batchID)
	}

	var hempBatch HempBatch
	if err = json.Unmarshal(batchJSON, &hempBatch); err != nil {
		return err
	}

	validTransitions := map[string][]string{
		"planted":   {"growing"},
		"growing":   {"harvested"},
		"harvested": {"processed", "wasted"},
		"processed": {"sold"},
		"wasted":    {"composted"},
	}
	allowed := validTransitions[hempBatch.Status]
	valid := false
	for _, st := range allowed {
		if st == newStatus {
			valid = true
			break
		}
	}
	if !valid {
		return fmt.Errorf("invalid status transition from %s to %s", hempBatch.Status, newStatus)
	}

	hempBatch.Status = newStatus
	if newStatus == "sold" {
		hempBatch.Owner = verifier
	}
	hempBatch.ZKProof = generateZKProof(batchID, hempBatch.GreenhouseID)

	updatedBatchJSON, err := json.Marshal(hempBatch)
	if err != nil {
		return err
	}
	return ctx.GetStub().PutState(batchID, updatedBatchJSON)
}

// GetHempBatch devuelve el lote verificando ZKP
func (s *SmartContract) GetHempBatch(ctx contractapi.TransactionContextInterface, batchID string) (*HempBatch, error) {
	batchJSON, err := ctx.GetStub().GetState(batchID)
	if err != nil {
		return nil, err
	}
	if batchJSON == nil {
		return nil, fmt.Errorf("hemp batch %s does not exist", batchID)
	}

	var hempBatch HempBatch
	if err = json.Unmarshal(batchJSON, &hempBatch); err != nil {
		return nil, err
	}
	if !verifyZKProof(hempBatch.ZKProof, batchID, hempBatch.GreenhouseID) {
		return nil, fmt.Errorf("invalid ZKP for batch %s", batchID)
	}
	return &hempBatch, nil
}

func main() {
	chaincode, err := contractapi.NewChaincode(&SmartContract{})
	if err != nil {
		log.Panicf("Error creating hemp traceability chaincode: %s", err)
	}
	if err := chaincode.Start(); err != nil {
		log.Panicf("Error starting hemp traceability chaincode: %s", err)
	}
}
