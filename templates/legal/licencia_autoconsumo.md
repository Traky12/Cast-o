# LICENCIA DE AUTOCONSUMO (RD 244/2019)

- **Titular**: {{ empresa.nombre }}
- **NIF**: {{ empresa.nif }}
- **Dirección**: {{ empresa.direccion }}
- **Potencia Instalada**: {{ potencia }} kW
- **Número de Registro REA**: {{ rea.numero }}
- **Fecha de Autorización**: {{ fecha }}
- **Firma Digital**: [{{ documento.hash }}](https://ipfs.io/ipfs/{{ documento.ipfs }})

**TX BioCoin Castúo**: [{{ tx_hash }}](https://explorer.biocoin.castu-system.com/tx/{{ tx_hash }})
**Git Commit**: [{{ git_commit }}](https://github.com/castu-system/{{ repo }}/commit/{{ git_commit }})
