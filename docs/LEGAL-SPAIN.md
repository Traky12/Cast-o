# CASTUO-SYSTEM™ | Gestión documental España (BOE + SII Facturae)

Automatización de generación, firma, envío y almacenamiento de documentos legales en España, vinculados a BioCoin Castúo y Git.

---

## 1. Documentos obligatorios (BOE)

- **Licencia de autoconsumo** (RD 244/2019): titular, NIF, dirección, potencia instalada, número REA, fecha.
- **Registro REA**: número de registro y datos del titular.
- **Certificado de instalación eléctrica** (REBT): firma del instalador autorizado.
- **Facturas electrónicas**: formato **Facturae 3.2.1** (obligatorio B2G), envío al Punto General de Entrada (FACe).

---

## 2. Paso 1: Generación de documentos legales

### Plantilla (Markdown)

Ver **templates/legal/licencia_autoconsumo.md**: titular, NIF, dirección, potencia, número REA, fecha, hash del documento, IPFS, TX BioCoin Castúo y Git commit.

### Script de generación

```bash
pip install jinja2 pyDigitalSignatureServices boto3 requests ipfshttpclient
python scripts/legal/generar_documento.py
```

El script (en **scripts/legal/generar_documento.py**):

- Carga datos y plantilla Jinja2.
- Genera el documento, calcula hash SHA-256 y sube a IPFS.
- Opcional: firma con DSS y guardado en S3.
- Sugiere commit con TX hash para vincular a Git.

### Ejemplo de salida

```
✅ Documento generado y firmado: QmXoypiz...
   - Hash: abc123...
   - TX BioCoin: a1b2c3...
   git commit --allow-empty -m "docs(legal): Licencia REA-2026-0001 TX:[a1b2c3...]"
```

---

## 3. Paso 2: Envío de facturas a SII (Facturae 3.2.1)

### Requisitos

- XML Facturae 3.2.1 (esquema oficial).
- Firma electrónica avanzada (XAdES).
- Envío a FACe (Agencia Tributaria).

### Plantilla XML

Ver **templates/legal/facturae.xml**: FileHeader, Parties (Seller/Buyer), Invoices con Taxes y Extensions (BioCoinTX, GitCommit).

### Script de envío

```bash
pip install jinja2 lxml zeep
python scripts/legal/enviar_facturae.py
```

En **scripts/legal/enviar_facturae.py** se genera el XML desde plantilla, se firma (implementar con tu librería XAdES) y se envía al WSDL del SII (configurar credenciales y clave en entorno).

### Recomendaciones

- Priorizar **SII Facturae** para facturar a administraciones públicas.
- Formato Facturae 3.2.1 y firma XAdES.
- Registro en **REA** si se genera energía (autoconsumo).

---

## 4. Paso 3: Almacenamiento y backup

- **Cifrado**: Age (clave en gestor de secretos).
- **Backup**: S3 (o compatible) en bucket dedicado, acceso restringido.

```bash
# Cifrar documento
age -e -r age1ql3c5... licencia_REA-2026-0001.pdf > licencia_REA-2026-0001.pdf.age
aws s3 cp licencia_REA-2026-0001.pdf.age s3://castu-system-legal-backup/
```

- **Registro**: opcional en Notion/Confluence (nombre, hash, IPFS, S3, TX BioCoin) para auditoría.

---

## 5. Flujo completo (ejemplo licencia de cultivo)

1. **Generar**: `python scripts/legal/generar_documento.py --finca "La Esperanza" --potencia 500`
2. **Firmar**: herramienta DSS sobre el PDF generado.
3. **Subir IPFS y registrar EPCIS**: `python scripts/legal/registrar_epcis.py --tx a1b2c3... --ipfs QmXoypiz...`
4. **Vincular a Git**: `git add ... && git commit -m "legal(rea): Licencia REA-2026-0001 TX:[a1b2c3...]"`
5. **Notificar autoridades** (ej. REA): según procedimiento oficial.
6. **Backup cifrado**: Age + S3 como arriba.

---

Para el marco general de cumplimiento y Europa, ver **[COMPLIANCE-LEGAL.md](COMPLIANCE-LEGAL.md)** y **[LEGAL-EUROPE.md](LEGAL-EUROPE.md)**.
