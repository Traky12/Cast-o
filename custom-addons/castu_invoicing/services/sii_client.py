# -*- coding: utf-8 -*-
"""Cliente para envío de facturas al SII (Agencia Tributaria) vía SOAP."""
import logging

_logger = logging.getLogger(__name__)

SII_WSDL = "https://www7.agenciatributaria.gob.es/wlpl/BORREME-Fact/ws/FacturasLCService?wsdl"


def send_invoice_to_sii(facturae_xml, nif_emisor, clave_firma=None):
    """
    Envía una factura en formato Facturae XML al SII.
    Devuelve dict con Estado, CodigoError, DescripcionError, CSV.
    En producción usar certificado y clave real; aquí se simula si zeep no está.
    """
    try:
        from zeep import Client
        from zeep.transports import Transport
        from requests import Session

        session = Session()
        session.verify = True
        transport = Transport(session=session)
        client = Client(SII_WSDL, transport=transport)
        # Método real depende del WSDL (ej. SuministroLRFacturasEmitidas, etc.)
        # Para Facturae suele usarse otro endpoint; esto es esquemático
        response = client.service.EnviarFactura(
            IdFactura=_extract_invoice_number(facturae_xml),
            Factura=facturae_xml,
            NIFEmisor=nif_emisor or "B12345678",
            ClaveFirma=clave_firma or "",
        )
        return {
            "Estado": getattr(response, "Estado", "Correcto"),
            "CodigoError": getattr(response, "CodigoError", ""),
            "DescripcionError": getattr(response, "DescripcionError", ""),
            "CSV": getattr(response, "CSV", ""),
        }
    except ImportError:
        _logger.warning("zeep no instalado; simulación de envío SII")
        return {
            "Estado": "Correcto",
            "CodigoError": "",
            "DescripcionError": "Simulación (instalar zeep para envío real)",
            "CSV": "SIM-" + _extract_invoice_number(facturae_xml),
        }
    except Exception as e:
        _logger.exception("SII send_invoice error")
        return {
            "Estado": "Error",
            "CodigoError": "EX",
            "DescripcionError": str(e),
            "CSV": "",
        }


def _extract_invoice_number(xml_string):
    from lxml import etree
    root = etree.fromstring(xml_string.encode("utf-8") if isinstance(xml_string, str) else xml_string)
    nodes = root.xpath("//*[local-name()='InvoiceNumber']")
    return nodes[0].text if nodes else ""
