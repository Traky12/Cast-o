# Configuracion de YubiKey (HSM-like, firmas y autenticacion) - Scaffold

## Objetivo
Reducir riesgo de exfiltracion de secretos mediante:
- claves residentes en hardware (YubiKey)
- firma de desafios/artefactos sin exponer material criptografico al host

## Requisitos (placeholders)
- YubiKey compatible (modelo a definir).
- Herramientas:
  - `yubikey-personalization`
  - `yubikey-manager`
  - herramientas de challenge-response (por ejemplo `ykchalresp`, segun paquete del SO)

## Principio de soberania
- Nunca hardcodear PINs o secretos en el repo.
- Registrar evidencias mediante `POST /api/v1/witness` (GaiaChain) solo con hashes del evento, usando el contrato minimal del repo: `{"hash","coop_id","ipfs_cid"}`

## Ejemplo de configuracion de slot (plantilla)
Nota: ajusta a tu modelo/firmware. Ejecuta bajo control y documentacion.

```bash
sudo apt-get install -y yubikey-personalization yubikey-manager

ykpersonalize -1 -o hmac-sha1 -o challenge-response -o fixed=0xAAAAAAAAAAAA -a "YubiKey for Castuo-System"
```

## Firmar un desafio (plantilla)
Plantilla de script:
- `scripts/ops/security/yubikey-sign.sh`

## Verificacion y trazabilidad
1. Generar `challenge` con formato estable:
   - `commit:<sha>|action:<name>|timestamp:<utc>`
2. Firmar en YubiKey.
3. Calcular SHA256 del string de firma y registrar witness en GaiaChain.

