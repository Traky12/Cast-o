# Diseno: entropia multimodal y claves (solo diseno)

## Alcance

Este documento **no** implementa recoleccion de biometricos ni keylogging en produccion. Describe riesgos y requisitos legales para cualquier futura linea de trabajo.

## RGPD / datos especiales

- Datos biometricos con fines de identificacion unica suelen ser **categoria especial** (Art. 9 RGPD).
- Necesidad de **base juridica** explicita, **DPIA** (Art. 35 si aplica), minimizacion y alternativas menos intrusivas.

## Seguridad criptografica

- La entropia de sensores de uso (raton, teclado, microfono) **no** debe usarse sola como unica fuente para claves de alto valor sin estimacion de entropia (p. ej. NIST SP 800-90B) y modelo de amenazas.
- Claves de usuario deben preferir **TRNG del SO**, **WebCrypto**, o **HSM**; la fusion multimodal, si se valida, es capa adicional, no sustituto auditado por defecto.

## Estado en repo

Implementaciones de laboratorio o stubs deben ir etiquetadas como **experimental** y desactivadas por defecto. No enlazar como "implementado en produccion" sin evidencia de auditoria.

## GaiaChain / witness

Si se registra metadata de generacion de claves, registrar **hashes** o **compromisos** criptograficos, no material de clave ni vectores biometricos en claro.
