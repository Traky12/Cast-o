# Email: Propuesta de Colaboración — ForestOwnershipToken

*Versión detallada. Para envío final con lista de adjuntos y comandos de exportación, ver [Documentación final de envío a la Junta](DOCUMENTACION_FINAL_ENVIO_JUNTA.md).*

**Asunto:** Propuesta de Colaboración para Implementación del Sistema ForestOwnershipToken en la Junta de Extremadura

**De:** Gregorio Jiménez Bodes \<gregorio.jimenez@castuo-system.com\>

**Para:** Dirección General de Medio Ambiente \<medioambiente@juntaex.es\>

**CC:** Dirección General de Economía Rural \<economiarural@juntaex.es\>, Dirección General de Política Forestal \<politicaforestal@juntaex.es\>

**Fecha:** [Fecha actual]

---

Estimados/as miembros de la Junta de Extremadura,

Me complace presentarles, en nombre de CASTÚO-SYSTEM™, una propuesta de colaboración para la implementación del sistema **ForestOwnershipToken**, una solución innovadora que permite la tokenización de propiedades forestales con certificaciones PEFC/FSC y Red Natura 2000, el cálculo automático de subvenciones (hasta €800/ha/año, con posibilidad de ampliación según normativa), y la vinculación a mercados de carbono.

Este sistema ha sido diseñado específicamente para cumplir con las normativas de Extremadura (Ley 3/2023 de Montes, Decreto 45/2020, Orden 15/03/2021), y está listo para ser implementado en colaboración con su equipo.

---

## Plan de implementación propuesto

### 1. Acuerdo con SIGPAC

Hemos preparado un borrador de acuerdo para el acceso a la API de SIGPAC, que permitirá la validación automática de parcelas antes de su tokenización. Este acuerdo no tiene coste para la Junta y garantiza el cumplimiento de las normativas de Extremadura.

**Acciones requeridas:**

- Revisión y firma del acuerdo adjunto ([borrador en docs/acuerdos](../acuerdos/borrador_acuerdo_sigpac.md)).
- Proporcionar credenciales de acceso a la API de SIGPAC para nuestro equipo técnico.

### 2. Despliegue del dashboard de verificación

Hemos desarrollado un dashboard de verificación que permite a los técnicos de la Junta:

- Verificar propiedades forestales en tiempo real.
- Calcular subvenciones automáticas (PAC 2040, Decreto 45/2020).
- Consultar certificaciones (PEFC, FSC, Red Natura 2000).

**Requisitos técnicos:** Servidor con Ubuntu 22.04 LTS, Docker 20.10+, Nginx 1.18+. Certificado SSL (Let's Encrypt).

**Instrucciones de despliegue:**

```bash
# Clonar repositorio (o copiar build)
cd frontend/extremadura-dashboard
cp .env.example .env
# Editar .env con REACT_APP_FOREST_OWNERSHIP_TOKEN_ADDRESS y credenciales
docker build -t extremadura-dashboard:latest .
docker-compose up -d
```

**Documentación adjunta:** [Guía de despliegue del dashboard](../guias/guia_despliegue_dashboard.md).

### 3. Plan de formación para técnicos

Hemos diseñado un plan de formación detallado para capacitar a 50 técnicos de la Junta en el uso del sistema. Incluye:

- **Talleres presenciales (5 sesiones de 2 h):** Introducción al sistema; mintado de propiedades; cálculo y reclamación de subvenciones; actualización de CO₂ tras talas; resolución de problemas.
- **Materiales:** [Guías técnicas](../guias/README.md), entorno de prueba (dashboard-test), [cronograma y prácticas](PLAN_FORMACION_TECNICOS.md).

| Fase              | Duración  | Acciones                          |
|-------------------|-----------|-----------------------------------|
| Preparación       | 2 semanas | Configuración del entorno de prueba. |
| Talleres presenciales | 4 semanas | 5 sesiones (2 por semana).        |
| Prácticas         | 4 semanas | Mintado de 100 tokens piloto.    |
| Evaluación        | 2 semanas | Examen práctico y encuesta.      |

### 4. Plan piloto con 10 propietarios

Proponemos un piloto inicial con 10 propietarios forestales (parcelas con PEFC/FSC, Cáceres y Badajoz 50 % cada una, 1–10 ha).

| Semana | Actividad                              |
|--------|----------------------------------------|
| 1      | Reunión inicial con propietarios.     |
| 2      | Mintado de parcelas (1 por propietario). |
| 3      | Reclamación de subvenciones.          |
| 4      | Simulación de tala (1 parcela).       |
| 5      | Encuesta de satisfacción.             |

**Métricas de éxito:** 100 % parcelas tokenizadas; 100 % subvenciones reclamadas; tiempo medio por transacción &lt; 10 minutos.

---

## Presupuesto y ROI

| Concepto              | Coste (€) | Financiación        |
|-----------------------|-----------|----------------------|
| Formación (5 talleres)| 15.000    | Junta de Extremadura |
| Despliegue dashboard  | 5.000     | CASTÚO-SYSTEM™      |
| Soporte técnico (3 meses) | 10.000 | Junta de Extremadura |
| **Total**             | **30.000**|                      |

**ROI estimado (100 ha):** Subvenciones 100.000 €/año, créditos de carbono 50.000 €/año, reducción de fraudes 50.000 €/año → **150.000 € ingresos + 50.000 € ahorros; ROI 600 % (inversión 30.000 €).**

---

## Próximos pasos propuestos

1. Revisar y firmar el acuerdo con SIGPAC (adjunto).
2. Coordinar el despliegue del dashboard en servidores de la Junta (guía adjunta).
3. Confirmar fechas para los talleres de formación (propuesta: inicio en 2 semanas).
4. Seleccionar los 10 propietarios piloto ([lista en propietarios_piloto.csv](propietarios_piloto.csv)).

---

## Documentación adjunta

- Borrador acuerdo SIGPAC: [docs/acuerdos/borrador_acuerdo_sigpac.md](../acuerdos/borrador_acuerdo_sigpac.md)
- Guía de despliegue: [docs/guias/guia_despliegue_dashboard.md](../guias/guia_despliegue_dashboard.md)
- Plan de formación: [PLAN_FORMACION_TECNICOS.md](PLAN_FORMACION_TECNICOS.md)
- Lista propietarios piloto: [propietarios_piloto.csv](propietarios_piloto.csv)
- Script de despliegue: [frontend/extremadura-dashboard/docker-compose.yml](../../frontend/extremadura-dashboard/docker-compose.yml)

---

## Cierre

Este proyecto representa una oportunidad única para modernizar la gestión forestal en Extremadura, garantizando trazabilidad, cumplimiento normativo y nuevos ingresos para los propietarios. Estamos seguros de que, con la colaboración de la Junta, podremos implementar este sistema de manera eficiente y escalable.

Quedamos a su disposición para reunirnos y discutir los detalles del plan en la fecha que mejor se ajuste a su agenda. Pueden contactarme directamente en este correo o en el teléfono 600 000 000.

Atentamente,

**Gregorio Jiménez Bodes**  
CEO, CASTÚO-SYSTEM™  
gregorio.jimenez@castuo-system.com  
[Firma digital]
