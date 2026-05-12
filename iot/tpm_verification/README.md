# Verificación de firmware TPM 2.0 — CASTÚO-SYSTEM™ (Libelium IoT)

Verificación criptográfica de firmware en dispositivos Libelium con soporte TPM 2.0 (boot seguro + firma RSA-SHA256).

## Compilación

```bash
# Con OpenSSL (mínimo requerido)
gcc -o tpm_firmware_verifier tpm_firmware_verifier.c -lcrypto -lssl

# Con TSS2 (opcional, para attestation en dispositivo)
# gcc -o tpm_firmware_verifier tpm_firmware_verifier.c -ltss2-esys -ltss2-mu -lcrypto -lssl
```

## Ejecución en dispositivo IoT

```bash
./tpm_firmware_verifier /firmware/bin/firmware.bin \
    /firmware/keys/firmware.pub.pem \
    /firmware/bin/firmware.sig
```

Salida esperada: `✅ Firma válida: Firmware verificado con TPM 2.0 / OpenSSL`

## Firma del firmware (en servidor de build)

```bash
# Generar clave (o usar HSM)
openssl genrsa -out firmware.priv.pem 2048
openssl rsa -in firmware.priv.pem -pubout -out firmware.pub.pem

# Firmar firmware
openssl dgst -sha256 -sign firmware.priv.pem -out firmware.sig firmware.bin

# Copiar a dispositivo: firmware.bin, firmware.pub.pem, firmware.sig
```

## Servicio systemd

Instalar unidad en el dispositivo:

```bash
sudo cp tpm-firmware-verifier.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable tpm-firmware-verifier
sudo systemctl start tpm-firmware-verifier
```

Ver `tpm-firmware-verifier.service` para rutas y reinicio en fallo.
