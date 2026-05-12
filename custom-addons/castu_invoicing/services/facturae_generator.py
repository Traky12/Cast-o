# -*- coding: utf-8 -*-
"""Generador de XML Facturae 3.2.1 para envío al SII."""
from lxml import etree

NS = "http://www.facturae.es/Facturae/2014/v3.2.1/Facturae"


def _tag(name):
    return "{%s}%s" % (NS, name)


def generate_facturae(invoice):
    """Genera el XML Facturae 3.2.1 a partir del registro castu.material.invoice."""
    facturae = etree.Element(_tag("Facturae"), nsmap={None: NS})

    file_header = etree.SubElement(facturae, _tag("FileHeader"))
    etree.SubElement(file_header, _tag("SchemaVersion")).text = "3.2.1"
    etree.SubElement(file_header, _tag("Modality")).text = "I"
    etree.SubElement(file_header, _tag("InvoiceIssuerType")).text = "EM"

    parties = etree.SubElement(facturae, _tag("Parties"))
    company = invoice.company_id or invoice.env.company
    seller = etree.SubElement(parties, _tag("SellerParty"))
    tax_id = etree.SubElement(seller, _tag("TaxIdentification"))
    etree.SubElement(tax_id, _tag("PersonTypeCode")).text = "J"
    etree.SubElement(tax_id, _tag("ResidenceTypeCode")).text = "01"
    etree.SubElement(tax_id, _tag("TaxIdentificationNumber")).text = (
        (company.vat or "B12345678").replace(" ", "")
    )
    legal_entity = etree.SubElement(seller, _tag("LegalEntity"))
    etree.SubElement(legal_entity, _tag("CorporateName")).text = company.name or "CASTUO-SYSTEM"

    partner = invoice.partner_id
    buyer = etree.SubElement(parties, _tag("BuyerParty"))
    buyer_tax_id = etree.SubElement(buyer, _tag("TaxIdentification"))
    etree.SubElement(buyer_tax_id, _tag("PersonTypeCode")).text = (
        "J" if partner.company_type == "company" else "F"
    )
    etree.SubElement(buyer_tax_id, _tag("ResidenceTypeCode")).text = "01"
    etree.SubElement(buyer_tax_id, _tag("TaxIdentificationNumber")).text = (
        (partner.vat or "").replace(" ", "") or "00000000A"
    )
    buyer_legal = etree.SubElement(buyer, _tag("LegalEntity"))
    etree.SubElement(buyer_legal, _tag("CorporateName")).text = partner.name

    invoices_el = etree.SubElement(facturae, _tag("Invoices"))
    inv = etree.SubElement(invoices_el, _tag("Invoice"))
    inv_header = etree.SubElement(inv, _tag("InvoiceHeader"))
    etree.SubElement(inv_header, _tag("InvoiceNumber")).text = invoice.name
    etree.SubElement(inv_header, _tag("InvoiceIssueDate")).text = invoice.date.isoformat()
    items_el = etree.SubElement(inv, _tag("Items"))
    for line in invoice.invoice_line_ids:
        line_el = etree.SubElement(items_el, _tag("InvoiceLine"))
        etree.SubElement(line_el, _tag("ItemDescription")).text = (line.material_id.name if line.material_id else "Material")[:250]
        etree.SubElement(line_el, _tag("Quantity")).text = str(round(line.kg, 2))
        etree.SubElement(line_el, _tag("UnitPriceWithoutTax")).text = str(round(line.price_unit / 1.21, 4))
        etree.SubElement(line_el, _tag("TotalCost")).text = str(round(line.subtotal, 2))

    taxes_el = etree.SubElement(inv, _tag("TaxesOutputs"))
    tax_el = etree.SubElement(taxes_el, _tag("Tax"))
    etree.SubElement(tax_el, _tag("TaxTypeCode")).text = "01"
    etree.SubElement(tax_el, _tag("TaxRate")).text = "21.00"
    base = sum(l.subtotal / 1.21 for l in invoice.invoice_line_ids)
    etree.SubElement(tax_el, _tag("TaxableBase")).text = str(round(base, 2))
    etree.SubElement(tax_el, _tag("TaxAmount")).text = str(round(invoice.amount_total - base, 2))
    etree.SubElement(inv, _tag("InvoiceTotal")).text = str(round(invoice.amount_total, 2))

    return etree.tostring(
        facturae, pretty_print=True, encoding="unicode", xml_declaration=True, standalone=True
    )
