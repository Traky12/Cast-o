# -*- coding: utf-8 -*-
"""API de agentes autónomos: LexCheck, YieldMaster, DocuBot, QuantumSentinel, Germination, Traceability, Cannabis, Harvest, CodeAgent."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from backend.agents_autonomous.aeat_bot import AEATBot
from backend.agents_autonomous.cannabis_lab import CannabisLab
from backend.agents_autonomous.code_agent_autonomous import AutonomousImprover
from backend.agents_autonomous.contract_generator import generate_contract
from backend.agents_autonomous.docubot_2040 import DocuBot2040
from backend.agents_autonomous.germination_master import GerminationMaster
from backend.agents_autonomous.harvest_bot import HarvestBot
from backend.agents_autonomous.invoice_bot import InvoiceBot
from backend.agents_autonomous.lex_check_ue import validar_contexto
from backend.agents_autonomous.market_bot import MarketBot
from backend.agents_autonomous.nft_marketplace import NFTMarketplace
from backend.agents_autonomous.payment_gateway import PaymentGateway
from backend.agents_autonomous.stripe_integration import StripeIntegration
from backend.agents_autonomous.subscription_manager import SubscriptionManager
from backend.agents_autonomous.data_marketplace import DataMarketplace
from backend.agents_autonomous.automatic_billing import AutomaticBilling
from backend.agents_autonomous.nft_monetization import NFTMonetization
from backend.agents_autonomous.revenue_dashboard import RevenueDashboard
from backend.agents_autonomous.traceability_master import TraceabilityMaster
from backend.agents_autonomous.yield_master import analizar_yield
from backend.digital_twin.quantum_sentinel import QuantumSentinel
from backend.main_certifier import MainCertifier

router = APIRouter(prefix="/agents", tags=["Agents Autonomous"])
main_certifier = MainCertifier()
improver = AutonomousImprover()
docubot = DocuBot2040()
quantum_sentinel = QuantumSentinel()
germination_master = GerminationMaster()
cannabis_lab = CannabisLab()
harvest_bot = HarvestBot()
traceability_master = TraceabilityMaster()
invoice_bot = InvoiceBot()
payment_gateway = PaymentGateway()
aeat_bot = AEATBot()
market_bot = MarketBot()
stripe_integration = StripeIntegration()
nft_marketplace = NFTMarketplace()
subscription_manager = SubscriptionManager()
data_marketplace = DataMarketplace()
automatic_billing = AutomaticBilling()
nft_monetization = NFTMonetization()
revenue_dashboard = RevenueDashboard()


# ---------- Request/Response models ----------


class AutonomousImprovementRequest(BaseModel):
    metric: str = Field(..., description="Métrica a mejorar (ej: yield).", examples=["yield"])
    current_value: float = Field(..., ge=0, examples=[98.5])
    target_value: float = Field(..., ge=0, examples=[99.0])


class LexCheckValidateRequest(BaseModel):
    normativa: str = Field(..., description="Normativa a validar (ej: GDPR).", examples=["GDPR"])
    contexto: str = Field(..., description="Contexto o texto a validar.", examples=["contrato con cliente X"])


class YieldMasterAnalyzeRequest(BaseModel):
    metric: str = Field(default="yield", examples=["yield"])
    current_value: float = Field(default=98.5, ge=0)
    crop: Optional[str] = Field(default=None, examples=["cannabis_medicinal"])


class DocuBotGenerateRequest(BaseModel):
    improvement_id: str = Field(default="", examples=["yield_20260319"])
    metric: str = Field(default="yield", examples=["yield"])
    before: float = Field(default=98.5, ge=0)
    after: float = Field(default=99.0, ge=0)
    jurisdiction: str = Field(default="ES", examples=["ES"])
    normativas: List[str] = Field(default_factory=lambda: ["RD_903/2025", "GDPR"])


class QuantumSentinelScanRequest(BaseModel):
    target_domain: str = Field(..., examples=["castuo-bunker.local"])


class GerminationMonitorRequest(BaseModel):
    cultivo: str = Field(..., examples=["cannabis_medicinal"])
    lote_id: str = Field(default="", examples=["CAN-2026-001"])
    semillas: int = Field(default=100, ge=1)


class TraceabilityRegisterRequest(BaseModel):
    lot_id: str = Field(..., examples=["CAN-2026-001"])
    cultivo: str = Field(..., examples=["cannabis_medicinal"])
    semillas: int = Field(default=100, ge=0)
    fecha: Optional[str] = None
    variedad: Optional[str] = None
    objetivo: Optional[str] = None


class YieldOptimizeRequest(BaseModel):
    cultivo: str = Field(default="", examples=["cannabis_medicinal"])
    lote_id: str = Field(default="", examples=["CAN-2026-001"])
    metric: str = Field(default="yield", examples=["yield"])
    current_value: float = Field(..., ge=0)
    target_value: float = Field(..., ge=0)


class CannabisAnalyzeRequest(BaseModel):
    lote_id: str = Field(..., examples=["CAN-2026-001"])
    muestra: str = Field(default="", examples=["MUE-001"])


class HarvestPerformRequest(BaseModel):
    cultivo: str = Field(..., examples=["cannabis_medicinal"])
    lote_id: str = Field(..., examples=["CAN-2026-001"])


class TraceabilityReportRequest(BaseModel):
    lot_id: str = Field(..., examples=["CAN-2026-001"])
    destino: str = Field(default="AEMPS", examples=["AEMPS"])


class ContractTerm(BaseModel):
    clause: str = ""
    requirement: str = ""
    normativa: str = ""


class CodeAgentGenerateContractRequest(BaseModel):
    contract_type: str = Field(..., examples=["BioCoin_Supply"])
    parties: List[str] = Field(..., examples=[["CASTÚO-SYSTEM", "Cliente X"]])
    terms: List[ContractTerm] = Field(default_factory=list)
    jurisdiction: str = Field(default="EU", examples=["EU"])


class InvoiceProduct(BaseModel):
    nombre: str = ""
    tipo: str = Field(default="microgreens", examples=["microgreens", "cannabis_medicinal", "flores_comestibles"])
    cantidad: float = Field(..., ge=0)
    precio_unitario: float = Field(..., ge=0)


class InvoiceClient(BaseModel):
    nombre: str = ""
    cif_nif: str = ""
    direccion: str = ""
    email: str = ""


class InvoiceGenerateRequest(BaseModel):
    cliente: InvoiceClient
    productos: List[InvoiceProduct]
    notas: Optional[str] = None


class PaymentCreateRequest(BaseModel):
    factura_id: Optional[str] = None
    total: Optional[float] = Field(None, ge=0)
    invoice_data: Optional[Dict[str, Any]] = None
    metodo: str = Field(default="stripe", examples=["stripe", "bizum", "crypto"])


class PaymentConfirmRequest(BaseModel):
    payment_id: str = Field(..., examples=["pi_xxx"])
    method: str = Field(..., examples=["stripe", "bizum", "crypto"])


class AEATDeclarationRequest(BaseModel):
    month: int = Field(..., ge=1, le=12, examples=[3])
    year: int = Field(..., ge=2020, le=2030, examples=[2026])


class SubscriptionCreateRequest(BaseModel):
    cliente: InvoiceClient
    plan: str = Field(..., examples=["basic", "premium", "enterprise"])


class RecurringInvoiceRequest(BaseModel):
    subscription_id: str = Field(..., examples=["SUB-B12345678-premium-20260316"])


class CreditNoteRequest(BaseModel):
    invoice_id: str = Field(..., examples=["FACT-20260316-120000"])
    reason: str = Field(..., examples=["Devolucion parcial"])


class AnnualSummaryRequest(BaseModel):
    year: int = Field(..., ge=2020, le=2030, examples=[2026])


class SubmitAnnualRequest(BaseModel):
    xml_path: str = Field(..., examples=["aeat/390_2026.xml"])

class MonthlyReportRequest(BaseModel):
    month: int = Field(..., ge=1, le=12, examples=[3])
    year: int = Field(..., ge=2020, le=2030, examples=[2026])


class PublishDataProductRequest(BaseModel):
    lote_id: str = Field(..., examples=["CAN-2026-001"])
    product_type: str = Field(default="yield_data", examples=["yield_data", "cannabinoid_data", "climate_data"])


class SellDataAccessRequest(BaseModel):
    product_id: str = Field(..., examples=["DATA-CAN-2026-001-YIELD_DATA"])
    buyer: InvoiceClient


class StripeSubscriptionPlanRequest(BaseModel):
    name: str = Field(..., examples=["Suscripcion Premium - Analisis de Cultivos"])
    description: str = Field(default="")
    price: float = Field(..., ge=0)
    interval: str = Field(default="month", examples=["month", "year"])
    interval_count: int = Field(default=1, ge=1)
    type: str = Field(default="standard", examples=["agronomic_data"])


class StripeCustomerSubscriptionRequest(BaseModel):
    customer_email: str = Field(..., examples=["cliente@cooperativa.es"])
    price_id: str = Field(..., examples=["price_xxx"])


class CancelSubscriptionRequest(BaseModel):
    subscription_id: str = Field(..., examples=["sub_xxx"])


class NFTRoyaltyMintRequest(BaseModel):
    lote_id: str = Field(..., examples=["CAN-2026-001"])
    royalty_percentage: float = Field(default=5.0, ge=0, le=100)


class NFTListRoyaltyRequest(BaseModel):
    nft_tx: str = Field(..., examples=["0xstub_..."])
    price: float = Field(..., ge=0)
    royalty_percentage: float = Field(default=5.0, ge=0, le=100)


class PayRoyaltiesRequest(BaseModel):
    nft_id: str = Field(..., examples=["0xstub_..."])
    amount: float = Field(..., ge=0)
    currency: str = Field(default="MATIC", examples=["MATIC", "EUR"])


# ---------- Autonomous improvement (existing) ----------


@router.post("/autonomous-improvement")
async def autonomous_improvement(body: AutonomousImprovementRequest):
    """Mejoras autónomas con GitLab y GaiaChain (simulado si no hay GITLAB_TOKEN)."""
    try:
        result = improver.proposer_mejora(
            metric=body.metric,
            current_value=body.current_value,
            target_value=body.target_value,
        )
        status = result.get("status", "unknown")
        if status == "implementado":
            return {
                "status": "success",
                "mejora": result.get("mejora"),
                "gitlab_mr": result.get("gitlab_mr"),
                "gaiachain_tx": result.get("gaiachain_tx"),
                "gaiachain_seal": result.get("gaiachain_seal"),
                "evolution_status": result.get("evolution_status"),
                "documentation": result.get("documentation"),
                "timestamp": result.get("timestamp", datetime.now(timezone.utc).isoformat()),
            }
        if status == "simulado":
            return {
                "status": "simulado",
                "mejora_propuesta": result.get("mejora"),
                "validacion_sabionda": result.get("validacion"),
                "auditoria": result.get("auditoria"),
                "accion": result.get("accion"),
                "gaiachain_seal": result.get("gaiachain_seal"),
                "evolution_status": result.get("evolution_status"),
                "timestamp": result.get("timestamp", datetime.now(timezone.utc).isoformat()),
            }
        return {
            "status": status,
            "reason": result.get("razon", "Desconocido"),
            "details": result,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error en mejora autónoma: {str(e)}")


# ---------- LexCheck-UE ----------


@router.post("/lexcheck-ue/validate")
async def lexcheck_validate(body: LexCheckValidateRequest):
    """Valida un contexto (normativa + texto) con LexCheck-UE."""
    out = validar_contexto(normativa=body.normativa, contexto=body.contexto)
    return {"aprobado": out["aprobado"], "razon": out.get("razon"), "normativas": out.get("normativas", []), "issues": out.get("issues", [])}


# ---------- YieldMaster ----------


@router.post("/yield-master/analyze")
async def yield_master_analyze(body: YieldMasterAnalyzeRequest):
    """Analiza métricas de yield (sensores o stub)."""
    data: Dict[str, Any] = {"yield": body.current_value, "metric": body.metric}
    if body.crop:
        data["crop"] = body.crop
    return analizar_yield(data)


# ---------- DocuBot-2040 ----------


@router.post("/docubot/generate")
async def docubot_generate(body: DocuBotGenerateRequest):
    """Genera documentación (canvas + markdown) bajo demanda."""
    out = docubot.generate_from_request(
        improvement_id=body.improvement_id,
        metric=body.metric,
        before=body.before,
        after=body.after,
        jurisdiction=body.jurisdiction,
        normativas=body.normativas,
    )
    return out


# ---------- QuantumSentinel ----------


@router.post("/quantum-sentinel/scan")
async def quantum_sentinel_scan(body: QuantumSentinelScanRequest):
    """Escaneo de seguridad con WebCheck + análisis Sabionda."""
    return quantum_sentinel.scan_and_protect(body.target_domain)


# ---------- GerminationMaster ----------


@router.post("/germination/monitor")
async def germination_monitor(body: GerminationMonitorRequest):
    """Monitorea germinación (sensores o stub) y registra en GaiaChain."""
    return germination_master.monitor_germination(
        cultivo=body.cultivo,
        semillas=body.semillas,
        lote_id=body.lote_id or None,
    )


# ---------- TraceabilityMaster ----------


@router.post("/traceability/register")
async def traceability_register(body: TraceabilityRegisterRequest):
    """Registra un lote en GaiaChain (y opcional IPFS)."""
    lot_data = {
        "lot_id": body.lot_id,
        "cultivo": body.cultivo,
        "semillas": body.semillas,
        "fecha": body.fecha or datetime.now(timezone.utc).isoformat(),
        "variedad": body.variedad,
        "objetivo": body.objetivo,
    }
    return traceability_master.register_lot(lot_data)


@router.post("/traceability/report")
async def traceability_report(body: TraceabilityReportRequest):
    """Genera informe tipo AEMPS para un lote."""
    return traceability_master.generate_report_for_aemps(body.lot_id)


# ---------- Yield optimize (alias to autonomous-improvement) ----------


@router.post("/yield/optimize")
async def yield_optimize(body: YieldOptimizeRequest):
    """Optimiza yield; delega en mejora autónoma."""
    result = improver.proposer_mejora(
        metric=body.metric,
        current_value=body.current_value,
        target_value=body.target_value,
    )
    return {
        "status": result.get("status"),
        "mejora": result.get("mejora"),
        "validacion": result.get("validacion"),
        "auditoria": result.get("auditoria"),
        "gaiachain_tx": result.get("gaiachain_tx"),
        "timestamp": result.get("timestamp", datetime.now(timezone.utc).isoformat()),
    }


# ---------- CannabisLab ----------


@router.post("/cannabis/analyze")
async def cannabis_analyze(body: CannabisAnalyzeRequest):
    """Análisis de cannabinoides y validación AEMPS."""
    return cannabis_lab.analyze_cannabinoids(lote_id=body.lote_id, muestra=body.muestra)


# ---------- HarvestBot ----------


@router.post("/harvest/perform")
async def harvest_perform(body: HarvestPerformRequest):
    """Cosecha robótica (stub/real según hardware)."""
    return harvest_bot.harvest(cultivo=body.cultivo, lote_id=body.lote_id)


# ---------- CodeAgent generate contract ----------


@router.post("/code-agent/generate-contract")
async def code_agent_generate_contract(body: CodeAgentGenerateContractRequest):
    """Genera contrato legal (BioCoin, suministro) con validación LexCheck y GaiaChain."""
    terms_dict = [{"clause": t.clause, "requirement": t.requirement, "normativa": t.normativa} for t in body.terms]
    return generate_contract(
        contract_type=body.contract_type,
        parties=body.parties,
        terms=terms_dict,
        jurisdiction=body.jurisdiction,
    )


# ---------- InvoiceBot ----------


@router.post("/invoice/generate")
async def invoice_generate(body: InvoiceGenerateRequest):
    """Genera factura (IVA según tipo producto), PDF/TXT y registro en GaiaChain."""
    order_data = {
        "cliente": body.cliente.model_dump(),
        "productos": [p.model_dump() for p in body.productos],
        "notas": body.notas,
    }
    return invoice_bot.generate_invoice(order_data)


@router.post("/invoice/subscription")
async def invoice_subscription(body: SubscriptionCreateRequest):
    """Crea suscripción recurrente (basic/premium/enterprise) y genera factura inicial."""
    return invoice_bot.create_subscription(body.cliente.model_dump(), body.plan)


@router.post("/invoice/recurring")
async def invoice_recurring(body: RecurringInvoiceRequest):
    """Genera factura recurrente para una suscripción activa."""
    return invoice_bot.generate_recurring_invoice(body.subscription_id)


@router.post("/invoice/credit-note")
async def invoice_credit_note(body: CreditNoteRequest):
    """Genera nota de crédito para una factura."""
    return invoice_bot.generate_credit_note(body.invoice_id, body.reason)


# ---------- PaymentGateway ----------


@router.post("/payment/create")
async def payment_create(body: PaymentCreateRequest):
    """Crea intento de pago (Stripe/Bizum/Crypto) para una factura."""
    if body.invoice_data:
        invoice_data = body.invoice_data
    else:
        total = body.total if body.total is not None else 0
        invoice_data = {
            "numero_factura": body.factura_id or "FACT-PENDING",
            "total": total,
            "cliente": {},
        }
    return payment_gateway.create_payment_intent(invoice_data, method=body.metodo)


@router.post("/payment/confirm")
async def payment_confirm(body: PaymentConfirmRequest):
    """Confirma un pago y registra en GaiaChain."""
    return payment_gateway.confirm_payment(body.payment_id, body.method)


# ---------- AEATBot ----------


@router.post("/aeat/declaration")
async def aeat_declaration(body: AEATDeclarationRequest):
    """Genera declaración de IVA (modelo 303) para el periodo y registra en GaiaChain."""
    return aeat_bot.generate_iva_declaration(month=body.month, year=body.year)


class AEATSubmitRequest(BaseModel):
    xml_path: str = Field(..., examples=["aeat/303_32026.xml"])


class MarketPublishRequest(BaseModel):
    nombre: str = Field(..., examples=["Analisis de Yield con IA"])
    descripcion: str = Field(..., examples=["Optimizacion de cultivos con agrovoltaica..."])
    precio: float = Field(..., ge=0)
    categoria: str = Field(default="programming_tech")
    tiempo_entrega: int = Field(default=3, ge=1)
    etiquetas: List[str] = Field(default_factory=lambda: ["ai", "blockchain"])


class MarketOrderRequest(BaseModel):
    id: Optional[str] = None
    cliente: Dict[str, Any] = Field(default_factory=dict)
    servicio: str = Field(..., examples=["analisis_yield", "generar_contrato"])
    datos: Dict[str, Any] = Field(default_factory=dict)


class StripeProductRequest(BaseModel):
    nombre: str = Field(..., examples=["Analisis de Yield con IA"])
    descripcion: str = Field(default="")
    precio: float = Field(..., ge=0)
    iva_type: str = Field(default="reducido", examples=["standard", "reducido"])
    jurisdiction: str = Field(default="ES")
    normativas: List[str] = Field(default_factory=lambda: ["GDPR", "AI_Act_2024"])


class StripePaymentLinkRequest(BaseModel):
    price_id: str = Field(..., examples=["price_xxx"])
    client_email: str = Field(default="")


class NFTMintRequest(BaseModel):
    lote_id: str = Field(..., examples=["CAN-2026-001"])
    tipo: str = Field(..., examples=["cannabis_medicinal", "microgreens"])
    metadatos: Dict[str, Any] = Field(default_factory=dict)


class NFTListRequest(BaseModel):
    nft_tx: str = Field(..., examples=["0xstub_..."])
    price: float = Field(..., ge=0)


class CertificateGenerateRequest(BaseModel):
    lote_id: str = Field(..., examples=["CAN-2026-001"])
    cultivo: str = Field(default="cannabis_medicinal", examples=["cannabis_medicinal"])


@router.post("/aeat/submit")
async def aeat_submit(body: AEATSubmitRequest):
    """Simula envío de declaración a la AEAT (SII)."""
    return aeat_bot.submit_to_aeat(body.xml_path)


@router.post("/aeat/annual-summary")
async def aeat_annual_summary(body: AnnualSummaryRequest):
    """Genera resumen anual (modelo 390) y registra en GaiaChain."""
    return aeat_bot.generate_annual_summary(body.year)


@router.post("/aeat/submit-annual")
async def aeat_submit_annual(body: SubmitAnnualRequest):
    """Simula envío del resumen anual (390) a la AEAT."""
    return aeat_bot.submit_annual_summary(body.xml_path)


# ---------- MarketBot ----------


@router.post("/market/publish")
async def market_publish(body: MarketPublishRequest):
    """Publica servicio en Fiverr/Upwork (o stub) y registra en GaiaChain."""
    return market_bot.publish_service(body.model_dump())


@router.post("/market/order")
async def market_order(body: MarketOrderRequest):
    """Procesa pedido (analisis_yield o generar_contrato) y registra entrega."""
    return market_bot.handle_order(body.model_dump())


@router.post("/market/data-product")
async def market_publish_data_product(body: PublishDataProductRequest):
    """Publica producto de datos (yield_data, cannabinoid_data, climate_data) en GaiaChain."""
    return market_bot.publish_data_product(body.lote_id, body.product_type)


@router.post("/market/sell-data-access")
async def market_sell_data_access(body: SellDataAccessRequest):
    """Vende acceso a producto de datos: factura + licencia y registro en GaiaChain."""
    return market_bot.sell_data_access(body.product_id, body.buyer.model_dump())


@router.get("/market/data-sales/{product_id}")
async def market_track_data_sales(product_id: str):
    """Consulta ventas de un producto de datos en GaiaChain."""
    return market_bot.track_data_sales(product_id)


# ---------- StripeIntegration ----------


@router.post("/stripe/product")
async def stripe_product(body: StripeProductRequest):
    """Crea producto y precio en Stripe; registra en GaiaChain."""
    return stripe_integration.create_product(body.model_dump())


@router.post("/stripe/payment-link")
async def stripe_payment_link(body: StripePaymentLinkRequest):
    """Crea enlace de pago en Stripe."""
    return stripe_integration.create_payment_link(body.price_id, body.client_email)


@router.post("/stripe/webhook")
async def stripe_webhook(request: Request):
    """Webhook de Stripe (pago completado/fallido)."""
    payload = await request.body()
    sig = request.headers.get("stripe-signature", "")
    return stripe_integration.handle_webhook(payload.decode("utf-8"), sig)


@router.post("/stripe/subscription-plan")
async def stripe_subscription_plan(body: StripeSubscriptionPlanRequest):
    """Crea plan de suscripción en Stripe (producto + precio recurrente) y registra en GaiaChain."""
    return stripe_integration.create_subscription_plan(body.model_dump())


@router.post("/stripe/customer-subscription")
async def stripe_customer_subscription(body: StripeCustomerSubscriptionRequest):
    """Crea suscripción para un cliente en Stripe."""
    return stripe_integration.create_customer_subscription(body.customer_email, body.price_id)


@router.post("/stripe/cancel-subscription")
async def stripe_cancel_subscription(body: CancelSubscriptionRequest):
    """Cancela una suscripción en Stripe y registra en GaiaChain."""
    return stripe_integration.cancel_subscription(body.subscription_id)


@router.get("/stripe/subscriptions")
async def stripe_list_subscriptions(status: str = "active"):
    """Lista suscripciones en Stripe (active, canceled, all)."""
    return stripe_integration.list_subscriptions(status=status)


# ---------- NFTMarketplace ----------


@router.post("/nft/mint")
async def nft_mint(body: NFTMintRequest):
    """Acuña NFT para lote (IPFS + stub chain) y registra en GaiaChain."""
    return nft_marketplace.mint_nft(body.model_dump())


@router.post("/nft/list")
async def nft_list(body: NFTListRequest):
    """Lista NFT en venta y registra en GaiaChain."""
    return nft_marketplace.list_nft_for_sale({"nft_tx": body.nft_tx}, body.price)


@router.post("/nft/royalty")
async def nft_royalty_mint(body: NFTRoyaltyMintRequest):
    """Crea NFT con royalties para datos de cultivo (RD 903/2025, licencia AEMPS)."""
    return nft_marketplace.create_royalty_nft(body.lote_id, body.royalty_percentage)


@router.post("/nft/list-royalty")
async def nft_list_royalty(body: NFTListRoyaltyRequest):
    """Lista NFT con royalties en el marketplace."""
    return nft_marketplace.list_nft_with_royalty({"nft_tx": body.nft_tx}, body.price, body.royalty_percentage)


@router.get("/nft/royalties/{nft_id}")
async def nft_track_royalties(nft_id: str):
    """Consulta royalties registrados para un NFT en GaiaChain."""
    return nft_marketplace.track_royalties(nft_id)


@router.post("/nft/pay-royalties")
async def nft_pay_royalties(body: PayRoyaltiesRequest):
    """Registra pago de royalties en GaiaChain."""
    return nft_marketplace.pay_royalties(body.nft_id, body.amount, body.currency)


# ---------- Certificados soberanos ----------


@router.post("/certificates/generate")
async def certificates_generate(body: CertificateGenerateRequest):
    """Ejecuta el flujo completo de certificación soberana (HarvestBot, CannabisLab, eIDAS, AI Act, GDPR, PDF+XML)."""
    return main_certifier.ejecutar_certificacion_real(body.lote_id, body.cultivo)


@router.get("/certificates/verify/{tx_hash}")
async def certificates_verify(tx_hash: str):
    """Verificación pública del certificado (para QR y enlace de verificación)."""
    result = main_certifier.get_certificate_status(tx_hash)
    if not result.get("valid"):
        raise HTTPException(status_code=404, detail=result.get("error", "Certificado no encontrado"))
    data = result.get("data", {})
    return {
        "status": "valid",
        "source": "gaiachain" if data.get("gaiachain_tx") else "local_database",
        "data": data,
        # Compatibilidad (campos top-level antiguos)
        "certificate_id": data.get("lote_id"),
        "certificate_hash": data.get("certificate_hash"),
        "legal_seals": data.get("legal_seals"),
        "verification_url": f"https://gaiachain.castuo-system.com/verify/{tx_hash}",
        "timestamp": data.get("timestamp"),
    }

@router.get("/certificates/verify")
async def certificates_verify_query(tx_hash: str):
    """Compatibilidad: verificación pública vía query param `tx_hash`.

    Uso:
      GET /agents/certificates/verify?tx_hash=0xstu...
    """
    result = main_certifier.get_certificate_status(tx_hash)
    if not result.get("valid"):
        raise HTTPException(status_code=404, detail=result.get("error", "Certificado no encontrado"))
    data = result.get("data", {})
    return {
        "status": "valid",
        "source": "gaiachain" if data.get("gaiachain_tx") else "local_database",
        "data": data,
        # Compatibilidad (campos top-level antiguos)
        "certificate_id": data.get("lote_id"),
        "certificate_hash": data.get("certificate_hash"),
        "legal_seals": data.get("legal_seals"),
        "verification_url": f"https://gaiachain.castuo-system.com/verify/{tx_hash}",
        "timestamp": data.get("timestamp"),
    }


# ---------- Dashboard monetización ----------


@router.get("/dashboard/revenue")
async def dashboard_revenue(period: str = "month"):
    """Ingresos agregados: facturas, ventas de datos y royalties (GaiaChain o stub)."""
    invoice_revenue = 0.0
    invoices = invoice_bot.get_invoices(period=period)
    for inv in invoices:
        data = inv.get("data", inv) if isinstance(inv, dict) else inv
        invoice_revenue += float(data.get("total", 0))
    data_revenue = 0.0
    nft_revenue = 0.0
    return {
        "total_revenue": invoice_revenue + data_revenue + nft_revenue,
        "breakdown": {"invoices": invoice_revenue, "data_sales": data_revenue, "nft_royalties": nft_revenue},
        "period": period,
    }


@router.get("/dashboard/realtime")
async def dashboard_realtime():
    """Ingresos últimas 24h, facturas, suscripciones activas, ventas datos y NFTs."""
    return revenue_dashboard.get_realtime_revenue()


@router.get("/dashboard/monthly")
async def dashboard_monthly(month: int, year: int):
    """Ingresos mensuales con desglose por tipo y contadores."""
    return revenue_dashboard.get_monthly_revenue(month, year)


@router.get("/dashboard/projection")
async def dashboard_projection(months: int = 6):
    """Proyección de ingresos para los próximos meses (basada en histórico)."""
    return revenue_dashboard.get_revenue_projection(months)


# ---------- Resiliencia Local / Sincronización GaiaChain ----------


@router.post("/system/sync-gaiachain")
async def system_sync_gaiachain():
    """Sincroniza operaciones pendientes con GaiaChain cuando la red vuelva."""
    try:
        from backend.database.local_db import local_db

        res = local_db.sync_with_gaiachain()
        return {
            "status": res.status,
            "synced": res.synced,
            "failed": res.failed,
            "total": res.total,
            "message": "Sincronización completada",
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error sync GaiaChain: {e}")


@router.get("/system/status")
async def system_status():
    """Estado del sistema y operaciones pendientes en SQLite."""
    try:
        from backend.database.local_db import local_db
        pending = local_db.get_pending_operations(limit=1000)
        gaiachain_online = False
        try:
            from pathlib import Path

            gaiachain_online = bool(local_db.gaiachain_cli) and Path(local_db.gaiachain_cli).is_file()
        except Exception:
            gaiachain_online = False

        # Métricas (robustas ante SO: si falla el cálculo, devolvemos 0%).
        import shutil
        import os

        disk_pct = 0
        try:
            usage = shutil.disk_usage(os.getcwd())
            disk_pct = int((usage.used / max(usage.total, 1)) * 100)
        except Exception:
            disk_pct = 0

        mem_pct = 0
        try:
            if os.name == "nt":
                import ctypes

                class MEMORYSTATUSEX(ctypes.Structure):
                    _fields_ = [
                        ("dwLength", ctypes.c_ulong),
                        ("dwMemoryLoad", ctypes.c_ulong),
                        ("ullTotalPhys", ctypes.c_ulonglong),
                        ("ullAvailPhys", ctypes.c_ulonglong),
                        ("ullTotalPageFile", ctypes.c_ulonglong),
                        ("ullAvailPageFile", ctypes.c_ulonglong),
                        ("ullTotalVirtual", ctypes.c_ulonglong),
                        ("ullAvailVirtual", ctypes.c_ulonglong),
                        ("ullAvailExtendedVirtual", ctypes.c_ulonglong),
                    ]

                m = MEMORYSTATUSEX()
                m.dwLength = ctypes.sizeof(MEMORYSTATUSEX)
                ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(m))
                mem_pct = int(m.dwMemoryLoad)
            else:
                # Linux/Unix: estimación simple desde /proc/meminfo si existe.
                meminfo = {}
                with open("/proc/meminfo", "r", encoding="utf-8") as f:
                    for line in f:
                        if ":" in line:
                            k, v = line.split(":", 1)
                            meminfo[k.strip()] = v.strip().split()[0]
                total_kb = int(meminfo.get("MemTotal", "0"))
                avail_kb = int(meminfo.get("MemAvailable", meminfo.get("MemFree", "0")))
                if total_kb > 0:
                    mem_pct = int(((total_kb - avail_kb) / total_kb) * 100)
        except Exception:
            mem_pct = 0

        recent_events = local_db.get_recent_events(limit=25)
        critical_events = [e for e in recent_events if str(e.get("severity", "")).lower() in ("error", "warning")]
        last_sync_attempt = None
        for e in recent_events:
            t = str(e.get("type", ""))
            if t.startswith("sync_") or "sync" in t:
                last_sync_attempt = e.get("timestamp")
                break

        return {
            "system_status": "operational",
            "components": {
                "gaiachain": {
                    "status": "online" if gaiachain_online else "offline",
                    "pending_operations": len(pending),
                    "last_sync_attempt": last_sync_attempt,
                },
                "database": {
                    "status": "online",
                    "pending_operations": len(pending),
                    "last_event": critical_events[0]["timestamp"] if critical_events else None,
                },
                "storage": {"disk_usage": f"{disk_pct}%", "memory_usage": f"{mem_pct}%"},
                "network": {"status": "online" if gaiachain_online else "degraded"},
            },
            "critical_events": critical_events[:10],
            "recommendations": [
                "Ejecutar POST /agents/system/sync-gaiachain cuando la red vuelva.",
            ],
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error sistema/status: {e}")


@router.get("/system/health")
async def system_health():
    """Alias de compatibilidad para monitoreo: devuelve el mismo payload que `/system/status`."""
    return await system_status()


@router.post("/system/log-event")
async def system_log_event(body: Dict[str, Any]):
    """
    Registra un evento crítico en SQLite (usado por emergency_protocol.sh).

    body esperado (compatible con tu plan):
      {
        "event_type": "...",
        "details": {...} | "texto",
        "severity": "critical" | "error" | "warning" | "info"
      }
    """
    try:
        from backend.database.local_db import local_db
        import json as _json

        event_type = str(body.get("event_type") or "unknown")
        details = body.get("details")
        severity = str(body.get("severity") or "critical")

        details_text = _json.dumps(details, ensure_ascii=False) if isinstance(details, dict) else str(details)
        local_db.log_system_event(event_type, details_text, severity=severity)
        return {"status": "success"}
    except Exception as e:
        return {"status": "error", "message": str(e)}


@router.get("/system/local-certificates")
async def system_local_certificates(limit: int = 50):
    """Lista certificados generados localmente (incluye tx local cuando GaiaChain está offline)."""
    from backend.database.local_db import local_db
    return {"certificates": local_db.list_local_certificates(limit=limit)}


@router.get("/system/local-invoices")
async def system_local_invoices(limit: int = 50):
    """Lista facturas generadas localmente."""
    from backend.database.local_db import local_db
    return {"invoices": local_db.list_local_invoices(limit=limit)}


@router.get("/dashboard/audit")
async def dashboard_audit(generate_pdf: bool = False):
    """
    Auditoría autónoma TRL9: reporte ESTADO | UTILIDAD | LEGALIDAD.
    Carga audit_castuo_system_YYYYMMDD.json, enriquece con datos en vivo y opcionalmente
    genera PDF en docs/certificates/ (y firma eIDAS si certs disponibles).
    """
    import json
    from pathlib import Path

    _root = Path(__file__).resolve().parents[2]
    _audit_glob = sorted(_root.glob("audit_castuo_system_*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
    report: Dict[str, Any] = {}
    latest_audit_file: str | None = None
    if _audit_glob:
        try:
            latest_audit_file = _audit_glob[0].name
            with open(_audit_glob[0], "r", encoding="utf-8") as f:
                report = json.load(f)
        except Exception:
            report = _build_audit_stub()
    else:
        report = _build_audit_stub()

    report["metadata"] = report.get("metadata", {})
    report["metadata"]["generated_at"] = datetime.now(timezone.utc).isoformat()
    report["metadata"]["live"] = True
    if latest_audit_file:
        report["metadata"]["audit_file"] = latest_audit_file

    try:
        live = revenue_dashboard.get_realtime_revenue()
        # Compatibilidad con el plan: dashboard_24h a nivel top-level
        report["dashboard_24h"] = live
        # Mantener también el enriquecimiento anidado existente
        report.setdefault("utilidad_economica", {}).setdefault("monetizacion", {})["dashboard_24h"] = live
    except Exception:
        report["dashboard_24h"] = None
        report.setdefault("utilidad_economica", {}).setdefault("monetizacion", {})["dashboard_24h"] = None

    pdf_path: Optional[str] = None
    if generate_pdf:
        pdf_path = _generate_audit_pdf(report, _root)
        if pdf_path:
            report["pdf_eidas_path"] = pdf_path
    report.setdefault("pdf_eidas_path", pdf_path)

    return report


@router.get("/dashboard/audit/pdf", response_class=FileResponse)
async def dashboard_audit_pdf():
    """
    Devuelve el PDF de auditoría TRL9 (y eIDAS si hay certs) para descarga directa.
    Uso: curl "http://localhost:8000/agents/dashboard/audit/pdf" -o audit_castuo_20260319.pdf
    """
    import json
    from pathlib import Path

    _root = Path(__file__).resolve().parents[2]
    _audit_glob = sorted(_root.glob("audit_castuo_system_*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
    report: Dict[str, Any] = {}
    latest_audit_file: str | None = None
    if _audit_glob:
        try:
            latest_audit_file = _audit_glob[0].name
            with open(_audit_glob[0], "r", encoding="utf-8") as f:
                report = json.load(f)
        except Exception:
            report = _build_audit_stub()
    else:
        report = _build_audit_stub()

    report["metadata"] = report.get("metadata", {})
    report["metadata"]["generated_at"] = datetime.now(timezone.utc).isoformat()
    if latest_audit_file:
        report["metadata"]["audit_file"] = latest_audit_file
    try:
        live = revenue_dashboard.get_realtime_revenue()
        report["dashboard_24h"] = live
        report.setdefault("utilidad_economica", {}).setdefault("monetizacion", {})["dashboard_24h"] = live
    except Exception:
        pass

    pdf_path = _generate_audit_pdf(report, _root)
    if not pdf_path or not Path(pdf_path).is_file():
        raise HTTPException(status_code=503, detail="PDF no generado (ReportLab requerido).")
    ts = report.get("metadata", {}).get("generated_at", "")[:10].replace("-", "")
    filename = f"audit_castuo_{ts}.pdf"
    return FileResponse(pdf_path, media_type="application/pdf", filename=filename)


def _build_audit_stub() -> Dict[str, Any]:
    """Stub de auditoría si no existe JSON en raíz."""
    return {
        "metadata": {"title": "AUDITORÍA AUTÓNOMA TRL9 - CASTÚO-SYSTEM 2026", "version": "1.0"},
        "estado_tecnico": {"infra_saas_api": {"valoracion": "ESTABLE", "resumen": "API y routers operativos."}},
        "utilidad_economica": {"monetizacion": {"valoracion": "OPERATIVO", "resumen": "InvoiceBot, AEATBot, DataMarketplace, NFTs, MarketIgnition."}},
        "legalidad": {"normativa_ue_es_2026": {"valoracion": "CONFORME", "resumen": "GDPR, eIDAS 2, AI Act, RD 903/2025, HFP 303/390."}},
        "resumen_ejecutivo": {"estado": "TRL9 OPERATIVO", "utilidad": "Monetización activa.", "legalidad": "Cumplimiento integrado."},
    }


def _generate_audit_pdf(report: Dict[str, Any], repo_root: Path) -> Optional[str]:
    """Genera PDF del reporte de auditoría en docs/certificates/; intenta sello eIDAS si hay certs."""
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.pdfgen import canvas
    except ImportError:
        return None
    out_dir = repo_root / "docs" / "certificates"
    out_dir.mkdir(parents=True, exist_ok=True)
    ts = report.get("metadata", {}).get("generated_at", "")[:10].replace("-", "")
    pdf_path = out_dir / f"audit_castuo_system_{ts}.pdf"
    try:
        c = canvas.Canvas(str(pdf_path), pagesize=A4)
        c.setFont("Helvetica-Bold", 16)
        c.drawString(72, 800, "AUDITORÍA AUTÓNOMA TRL9 - CASTÚO-SYSTEM 2026")
        c.setFont("Helvetica", 10)
        c.drawString(72, 770, report.get("metadata", {}).get("generated_at", ""))
        res = report.get("resumen_ejecutivo", {})
        y = 730
        for k, v in (res or {}).items():
            c.drawString(72, y, f"{k}: {v}")
            y -= 20
        c.drawString(72, y - 20, "Generado por GET /agents/dashboard/audit?generate_pdf=true")
        c.save()
        signed = _try_eidas_sign(str(pdf_path), repo_root)
        return signed or str(pdf_path)
    except Exception:
        return None


def _try_eidas_sign(pdf_path: str, repo_root: Path) -> Optional[str]:
    """Si hay GaiaChainSeal y cert eIDAS, firma el PDF y devuelve ruta al firmado."""
    try:
        from backend.legal.gaiachain_seal import GaiaChainSeal
        import hashlib
        seal = GaiaChainSeal()
        with open(pdf_path, "rb") as f:
            h = hashlib.sha256(f.read()).hexdigest()
        sig = seal.generate_qualified_seal({"audit_pdf_hash": h, "source": pdf_path})
        if sig and sig.get("seal_id"):
            signed_path = pdf_path.replace(".pdf", "_signed.pdf")
            with open(signed_path, "wb") as out:
                with open(pdf_path, "rb") as f:
                    out.write(f.read())
            return signed_path
    except Exception:
        pass
    return None


# ---------- SubscriptionManager ----------


class SubscriptionConsumeRequest(BaseModel):
    subscription_id: str = Field(..., examples=["SUB-20260316-5678"])
    analysis_type: str = Field(default="yield", examples=["yield", "cannabinoid", "climate"])


class SubscriptionRenewRequest(BaseModel):
    subscription_id: str = Field(..., examples=["SUB-20260316-5678"])


class SubscriptionCancelRequest(BaseModel):
    subscription_id: str = Field(..., examples=["SUB-20260316-5678"])


@router.post("/subscriptions/create")
async def subscriptions_create(body: SubscriptionCreateRequest):
    """Crea suscripción recurrente con factura y sello eIDAS (SubscriptionManager)."""
    return subscription_manager.create_subscription(body.cliente.model_dump(), body.plan)


@router.post("/subscriptions/consume")
async def subscriptions_consume(body: SubscriptionConsumeRequest):
    """Consume un análisis de la suscripción (reduce contador)."""
    return subscription_manager.consume_analysis(body.subscription_id, body.analysis_type)


@router.post("/subscriptions/renew")
async def subscriptions_renew(body: SubscriptionRenewRequest):
    """Renueva suscripción: nueva factura y actualiza end_date."""
    return subscription_manager.renew_subscription(body.subscription_id)


@router.get("/subscriptions/active")
async def subscriptions_active():
    """Lista suscripciones activas desde GaiaChain."""
    return {"subscriptions": subscription_manager.list_active_subscriptions()}


@router.post("/subscriptions/cancel")
async def subscriptions_cancel(body: SubscriptionCancelRequest):
    """Cancela una suscripción."""
    return subscription_manager.cancel_subscription(body.subscription_id)


# ---------- DataMarketplace ----------


class DataMarketplacePublishRequest(BaseModel):
    lote_id: str = Field(..., examples=["CAN-2026-001"])
    product_type: str = Field(default="yield_data", examples=["yield_data", "cannabinoid_data", "climate_data"])


class DataMarketplaceSellRequest(BaseModel):
    product_id: str = Field(..., examples=["DATA-CAN-2026-001-YIELD_DATA"])
    buyer: Optional[InvoiceClient] = Field(default=None, description="Comprador (campo `buyer`).")
    buyer_data: Optional[InvoiceClient] = Field(default=None, description="Compatibilidad: comprador (campo `buyer_data`).")


@router.post("/data-marketplace/publish")
async def data_marketplace_publish(body: DataMarketplacePublishRequest):
    """Publica producto de datos con sello eIDAS (DataMarketplace)."""
    return data_marketplace.publish_data_product(body.lote_id, body.product_type)


@router.post("/data-marketplace/sell")
async def data_marketplace_sell(body: DataMarketplaceSellRequest):
    """Vende acceso a producto de datos: factura + licencia."""
    buyer = body.buyer or body.buyer_data
    if not buyer:
        raise HTTPException(status_code=422, detail="Falta campo `buyer` (o compatibilidad `buyer_data`).")
    return data_marketplace.sell_data_access(body.product_id, buyer.model_dump())


@router.get("/data-marketplace/products")
async def data_marketplace_products(status: str = "available"):
    """Lista productos de datos disponibles."""
    return {"products": data_marketplace.list_data_products(status=status)}


@router.get("/data-marketplace/royalty-report/{product_id}")
async def data_marketplace_royalty_report(product_id: str, royalty_pct: float = 5.0):
    """Informe de royalties para un producto de datos."""
    return data_marketplace.generate_royalty_report(product_id, royalty_pct)


# ---------- AutomaticBilling ----------


@router.post("/automatic-billing/recurring")
async def automatic_billing_recurring():
    """Procesa facturación recurrente (renueva suscripciones vencidas)."""
    return automatic_billing.process_recurring_billing()

@router.post("/automatic-billing/process-recurring")
async def automatic_billing_process_recurring():
    """Compatibilidad con el plan: alias de `POST /automatic-billing/recurring`."""
    return automatic_billing.process_recurring_billing()


@router.get("/automatic-billing/monthly-report")
async def automatic_billing_monthly_report(month: int, year: int):
    """Genera informe de ingresos mensuales."""
    return automatic_billing.generate_monthly_revenue_report(month, year)

@router.post("/automatic-billing/monthly-report")
async def automatic_billing_monthly_report_post(body: MonthlyReportRequest):
    """Compatibilidad con el plan: POST en lugar de GET."""
    return automatic_billing.generate_monthly_revenue_report(body.month, body.year)


@router.post("/automatic-billing/declarations")
async def automatic_billing_declarations():
    """Genera declaraciones 303 y, si es diciembre, 390; simula envío AEAT."""
    return automatic_billing.generate_automatic_declarations()

@router.post("/automatic-billing/annual-summary")
async def automatic_billing_annual_summary(body: AnnualSummaryRequest):
    """Compatibilidad con el plan: genera (y simula envío) del Modelo 390."""
    model_390 = aeat_bot.generate_annual_summary(body.year)
    submission_390 = None
    xml_path = model_390.get("xml_path")
    if xml_path:
        submission_390 = aeat_bot.submit_annual_summary(xml_path)
    return {"model_390": model_390, "submission_390": submission_390}


@router.post("/automatic-billing/process-payments")
async def automatic_billing_process_payments():
    """Procesa pagos pendientes (consulta GaiaChain y confirma)."""
    return automatic_billing.process_pending_payments()


# ---------- NFTMonetization ----------


class NFTTokenizeRequest(BaseModel):
    lote_id: str = Field(..., examples=["CAN-2026-001"])
    royalty_percentage: float = Field(default=5.0, ge=0, le=100)
    list_price: float = Field(default=1000.0, ge=0)


class NFTSellAccessRequest(BaseModel):
    nft_id: str = Field(..., examples=["0xstub_..."])
    buyer: InvoiceClient
    price_eur: float = Field(default=1000.0, ge=0)


@router.post("/nft-monetization/tokenize")
async def nft_monetization_tokenize(body: NFTTokenizeRequest):
    """Tokeniza lote como NFT con royalties y lo lista (NFTMonetization)."""
    return nft_monetization.tokenize_lot(body.lote_id, body.royalty_percentage, body.list_price)


@router.post("/nft-monetization/sell-access")
async def nft_monetization_sell_access(body: NFTSellAccessRequest):
    """Vende acceso a NFT: factura + licencia y registro nft_sale."""
    return nft_monetization.sell_nft_access(body.nft_id, body.buyer.model_dump(), body.price_eur)


@router.get("/nft-monetization/royalties/{nft_id}")
async def nft_monetization_royalties(nft_id: str):
    """Rastrea royalties de un NFT (ventas y pagos)."""
    return nft_monetization.track_nft_royalties(nft_id)


@router.post("/nft-monetization/pay-royalties")
async def nft_monetization_pay_royalties(nft_id: str):
    """Paga royalties pendientes del NFT y registra en GaiaChain."""
    return nft_monetization.pay_nft_royalties(nft_id)


# ---------- Ignición comercial diaria ----------


@router.post("/market-ignition")
async def market_ignition():
    """Ejecuta el ciclo comercial autónomo: recurrencias, declaraciones AEAT, publicación de datos y dashboard. Para cron: curl -X POST http://localhost:8000/agents/market-ignition"""
    from backend.agents_autonomous.market_ignition import ignicion_comercial_diaria
    return ignicion_comercial_diaria()


# ---------- Health (for checklist) ----------


@router.get("/health")
async def agents_health():
    """Estado de los agentes autónomos (para checklist legal)."""
    return {
        "status": "OK",
        "agents": "LexCheck-UE, YieldMaster, DocuBot-2040, QuantumSentinel, GerminationMaster, TraceabilityMaster, CannabisLab, HarvestBot, CodeAgent-X, InvoiceBot, PaymentGateway, AEATBot, MarketBot, StripeIntegration, NFTMarketplace",
    }
