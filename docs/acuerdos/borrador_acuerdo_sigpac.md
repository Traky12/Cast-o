# Borrador de Acuerdo de Colaboración — Validación de Parcelas Forestales (SIGPAC)

**Asunto:** Acuerdo de colaboración para el acceso a la API de SIGPAC en el marco del sistema ForestOwnershipToken (Junta de Extremadura).

**Partes:**

- **Junta de Extremadura**, a través de la Dirección General de Medio Ambiente (y, en su caso, Dirección General de Agricultura y Ganadería), con domicilio en [dirección], en adelante «la Junta».
- **CASTÚO-SYSTEM™ S.L.**, representada por Gregorio Jiménez Bodes, con domicilio en [dirección], CIF B12345678, en adelante «CASTÚO».

**Fecha:** [Fecha]

---

## 1. Objeto

El presente acuerdo tiene por objeto establecer las condiciones de colaboración para el acceso de CASTÚO a los servicios de validación de parcelas (API SIGPAC o equivalente) que la Junta o el Ministerio de Agricultura, Pesca y Alimentación (MAPA) pongan a su disposición, con la finalidad exclusiva de validar parcelas antes de su tokenización en el sistema ForestOwnershipToken, en el marco del proyecto de digitalización forestal de la Junta de Extremadura.

---

## 2. Alcance del acceso

2.1. **Endpoint y uso:** El acceso se limitará al uso de la API de validación de parcelas (por ejemplo, `https://sigpac.mapa.gob.es/...` o la URL que la Junta/MAPA indique) para comprobar, antes del mintado de un token ForestOwnershipToken, la validez del identificador de parcela, el área, el estado de protección y, en su caso, las certificaciones asociadas.

2.2. **Límite de uso:** Se establece un límite de **10.000 solicitudes/mes** salvo que las partes acuerden otra cifra por escrito.

2.3. **Formato de respuesta esperado:** La Junta/MAPA se comprometen a facilitar (o autorizar) una respuesta en formato estructurado (p. ej. JSON) que permita a CASTÚO conocer, como mínimo: validez de la parcela, área (m²), condición de zona protegida (Red Natura 2000 u otra) y, si aplica, certificaciones (PEFC, FSC, etc.).

Ejemplo de estructura de respuesta (orientativo):

```json
{
  "valid": true,
  "certifications": ["PEFC", "FSC"],
  "area": 10000,
  "protected": false
}
```

---

## 3. Credenciales y seguridad

3.1. La Junta (o el MAPA, según corresponda) proporcionará a CASTÚO las credenciales de acceso a la API (clave, token o certificado) necesarias para el uso descrito.

3.2. CASTÚO se compromete a:

- Utilizar las credenciales únicamente para la validación de parcelas en el marco del sistema ForestOwnershipToken.
- No cederlas a terceros ni usarlas para fines distintos a los previstos en este acuerdo.
- Cumplir la normativa de protección de datos (RGPD) y la Ley 3/2023 de Montes de Extremadura en el tratamiento de cualquier dato obtenido.

---

## 4. Confidencialidad y protección de datos

4.1. Los datos obtenidos mediante la API se utilizarán exclusivamente para la validación previa al mintado de tokens y para la mejora del servicio dentro del proyecto con la Junta.

4.2. CASTÚO actuará como encargado del tratamiento respecto de los datos personales que, en su caso, reciba, en los términos que establezca el contrato o anexo de encargo de tratamiento entre la Junta y CASTÚO.

---

## 5. Duración y prórroga

5.1. El acuerdo tendrá una vigencia de **un (1) año** desde su firma, prorrogable por periodos sucesivos de un año salvo denuncia por cualquiera de las partes con al menos tres (3) meses de antelación al fin del periodo en curso.

5.2. **Coste:** Se acuerda que el acceso se enmarca en un **acuerdo de colaboración sin contraprestación económica** para la Junta, sin perjuicio de los costes de despliegue y soporte que CASTÚO asuma en el marco del proyecto global.

---

## 6. Modificación y resolución

6.1. Cualquier modificación del presente acuerdo requerirá el consentimiento por escrito de ambas partes.

6.2. Cualquiera de las partes podrá resolver el acuerdo con un preaviso de tres (3) meses, por escrito. En caso de resolución, CASTÚO cesará de inmediato en el uso de la API y devolverá o destruirá las credenciales según indique la Junta.

---

## 7. Firma

Por la **Junta de Extremadura**:

Nombre: _________________________  
Cargo: _________________________  
Fecha: _________________________  
Firma: _________________________

Por **CASTÚO-SYSTEM™ S.L.**:

Nombre: Gregorio Jiménez Bodes  
Cargo: CEO  
Fecha: _________________________  
Firma: _________________________

---

*Este borrador debe ser revisado por la Asesoría Jurídica de la Junta y, en su caso, por el MAPA, antes de su firma. Las referencias a URLs y estructuras JSON son orientativas y podrán adaptarse a la API real ofrecida por la Administración.*
