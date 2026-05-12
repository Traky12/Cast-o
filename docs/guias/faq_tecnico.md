# FAQ Técnico — ForestOwnershipToken y Junta de Extremadura

Solución a problemas comunes en mintado, subvenciones, SIGPAC y GaiaChain.

---

## Mintado

1. **Error: "FOREST_OWNERSHIP_TOKEN_ADDRESS y PRIVATE_KEY son obligatorios"**  
   Configure las variables de entorno en el shell o en un `.env` antes de ejecutar los scripts.

2. **Error: "parcelaId required"**  
   Asegúrese de pasar un ID catastral no vacío (ej. `XT-12345-001`).

3. **Error: "Invalid address"**  
   La dirección del propietario debe ser una dirección Ethereum válida (0x + 40 hex).

4. **Transacción revertida por gas**  
   Aumente el gas en el script (p. ej. 600000 para mint con muchas certificaciones) o compruebe que la red no está congestionada.

## Subvenciones

5. **calculateSubsidies devuelve 0**  
   Compruebe que el token existe y que el área es > 0 (área en m²; se convierte a ha dividiendo por 10000).

6. **No aparecen códigos en getEligibleSubsidies**  
   Las certificaciones deben coincidir exactamente con "PEFC", "FSC" o "Red Natura 2000" (sensibles a mayúsculas y espacios).

## SIGPAC

7. **SIGPAC no devuelve datos**  
   Sin `SIGPAC_API_KEY`, el script de mint certificado usa datos por defecto. Configure la clave o use `--no-sigpac` y pase datos manualmente.

8. **Validación SIGPAC falla para parcela válida**  
   Compruebe el formato del ID de parcela según la API de SIGPAC y los límites de uso.

## IPFS

9. **Timeout al subir a IPFS**  
   Compruebe conectividad con el nodo IPFS (Infura o local). Use `--upload-ipfs` solo si el nodo está disponible o suba metadatos por separado y pase el hash al mint.

10. **Metadatos no se ven en el dashboard**  
    El dashboard obtiene el `ipfsHash` del contrato y lo resuelve vía `ipfs.io`. Si el contenido no está pinnado, puede no estar disponible.

## GaiaChain / Red

11. **Error de conexión al RPC**  
    Verifique `GAIA_CHAIN_RPC` y que el nodo testnet/producción esté accesible desde su red.

12. **Nonce too low**  
    Otra transacción del mismo cuenta se ha enviado antes; espere confirmación o reinicie con el nonce actual.

## Dashboard

13. **El dashboard no muestra datos**  
    Configure `REACT_APP_FOREST_OWNERSHIP_TOKEN_ADDRESS` en el build del frontend y recargue. Compruebe que el Token ID existe en el contrato.

14. **Wallet no conecta**  
    Use un navegador con MetaMask (o compatible) y la red configurada para GaiaChain.

## Talas y CO₂

15. **updateCarbonSequestered falla**  
    Solo el propietario actual del token puede llamar. Use la clave privada de la cuenta que posee el NFT.

16. **El valor de CO₂ queda en 0**  
    La reducción (volume_m3 × 1000) no puede superar el valor actual; el contrato pone mínimo 0.

## Certificaciones

17. **Certificaciones no aparecen en getCertifications**  
    Deben haberse pasado en el mint como array de strings (ej. `-c PEFC FSC`).

18. **Subvención menor de lo esperado**  
    Revise las reglas: PAC 200€/ha, PEFC/FSC 150€/ha, Red Natura 300€/ha, área protegida 100€/ha. El área se toma en hectáreas (area_m² / 10000).

## Producción

19. **Diferencias entre testnet y producción**  
    Direcciones de contratos y RPC son distintos. Use las variables de entorno adecuadas por entorno.

20. **Auditoría y cumplimiento**  
    Para auditoría de cumplimiento (Ley 3/2023, Decreto 45/2020), utilice los metadatos en IPFS y los eventos on-chain (PropertyMinted, CarbonUpdated) como prueba de trazabilidad.

---

*Versión PDF: exportar desde este Markdown.*
