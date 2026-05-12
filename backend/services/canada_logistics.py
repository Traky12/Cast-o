# -*- coding: utf-8 -*-
"""Integración con APIs de logística en Canadá (Canada Post, Purolator, FedEx)."""
from __future__ import annotations

import uuid
from datetime import datetime, timedelta
from typing import Any, Dict


class CanadaLogisticsService:
    """Servicio para integrar con APIs de logística en Canadá."""

    def __init__(self) -> None:
        self.carriers: Dict[str, Dict[str, str]] = {
            "canada_post": {
                "api_url": "https://api.canadapost-postescanada.ca/rs/ship/price",
                "tracking_url": "https://www.canadapost-postescanada.ca/track-web/en#/details/",
            },
            "purolator": {
                "api_url": "https://api.purolator.com/v1/shipments",
                "tracking_url": "https://www.purolator.com/en/ship-track/tracking-details.page?pin=",
            },
            "fedex_ca": {
                "api_url": "https://apis.fedex.com/ship/v1/shipments",
                "tracking_url": "https://www.fedex.com/en-ca/tracking.html?tracknumbers=",
            },
        }

    def create_shipment(self, carrier: str, shipment_data: Dict[str, Any]) -> Dict[str, Any]:
        """Crea un envío con un transportista canadiense."""
        if carrier not in self.carriers:
            raise ValueError(f"Transportista no soportado: {carrier}")
        tracking_number = f"{carrier.upper()}-{datetime.utcnow().strftime('%Y%m%d')}-{uuid.uuid4().hex[:8]}"
        contents = (shipment_data.get("contents") or "").lower()
        is_cannabis = "cannabis" in contents
        return {
            "carrier": carrier,
            "tracking_number": tracking_number,
            "shipping_label": f"https://labels.{carrier}.com/{tracking_number}",
            "tracking_url": self.carriers[carrier]["tracking_url"] + tracking_number,
            "estimated_delivery": (datetime.utcnow() + timedelta(days=5)).strftime("%Y-%m-%d"),
            "status": "in_transit",
            "cost": {
                "currency": "CAD",
                "amount": 25.00 if carrier == "canada_post" else 35.00 if carrier == "purolator" else 40.00,
                "taxes": 1.13,
            },
            "customs_info": {
                "required_documents": ["commercial_invoice", "phytosanitary_certificate", "packing_list"],
                "brokerage_fees": "Included" if carrier == "purolator" else "Not included",
            },
            "cannabis_specific": {
                "excise_stamp": "Required for all cannabis shipments" if is_cannabis else "Not applicable",
                "age_verification": "Required for delivery (19+ years)" if is_cannabis else "Not applicable",
            },
        }

    def track_shipment(self, carrier: str, tracking_number: str) -> Dict[str, Any]:
        """Rastrea un envío con un transportista canadiense."""
        if carrier not in self.carriers:
            raise ValueError(f"Transportista no soportado: {carrier}")
        statuses = ["received", "in_transit", "at_sorting_facility", "out_for_delivery", "delivered"]
        current_status = statuses[datetime.utcnow().day % 5]
        return {
            "carrier": carrier,
            "tracking_number": tracking_number,
            "status": current_status,
            "last_update": datetime.utcnow().isoformat(),
            "location": "Toronto, ON" if carrier == "canada_post" else "Vancouver, BC" if carrier == "purolator" else "Montreal, QC",
            "next_step": {
                "received": "In transit to sorting facility",
                "in_transit": "Expected arrival at destination city in 2 days",
                "at_sorting_facility": "Being processed for final delivery",
                "out_for_delivery": "Delivery expected today",
                "delivered": "Package delivered and signed for by recipient",
            }[current_status],
            "estimated_delivery": (datetime.utcnow() + timedelta(days=2)).strftime("%Y-%m-%d"),
            "tracking_url": self.carriers[carrier]["tracking_url"] + tracking_number,
            "customs_status": "cleared" if current_status != "received" else "not_yet_processed",
        }

    def get_shipping_rates(
        self,
        carrier: str,
        origin: str,
        destination: str,
        weight: float,
        is_cannabis: bool = False,
    ) -> Dict[str, Any]:
        """Obtiene tarifas de envío para transportistas canadienses."""
        if carrier not in self.carriers:
            raise ValueError(f"Transportista no soportado: {carrier}")
        cannabis_surcharge = 10.00 if is_cannabis else 0.00
        if carrier == "canada_post":
            return {
                "carrier": "canada_post",
                "origin": origin,
                "destination": destination,
                "weight_kg": weight,
                "is_cannabis": is_cannabis,
                "service_levels": [
                    {
                        "name": "Priority",
                        "delivery_time": "1-3 business days",
                        "price": 20.00 + (weight * 5.00) + cannabis_surcharge,
                        "currency": "CAD",
                        "includes": ["tracking", "delivery confirmation"],
                    },
                    {
                        "name": "Xpresspost",
                        "delivery_time": "2-4 business days",
                        "price": 15.00 + (weight * 3.00) + cannabis_surcharge,
                        "currency": "CAD",
                        "includes": ["tracking"],
                    },
                ],
                "notes": [
                    f"Additional {cannabis_surcharge} CAD surcharge for cannabis products",
                    "Excise stamps required for all cannabis shipments",
                    "Age verification (19+) required for cannabis deliveries",
                ],
            }
        if carrier == "purolator":
            return {
                "carrier": "purolator",
                "origin": origin,
                "destination": destination,
                "weight_kg": weight,
                "is_cannabis": is_cannabis,
                "service_levels": [
                    {
                        "name": "Purolator Express",
                        "delivery_time": "Next business day by 9:00 AM",
                        "price": 40.00 + (weight * 8.00) + cannabis_surcharge,
                        "currency": "CAD",
                        "includes": ["guaranteed delivery", "real-time tracking"],
                    },
                    {
                        "name": "Purolator Ground",
                        "delivery_time": "1-5 business days",
                        "price": 25.00 + (weight * 4.00) + cannabis_surcharge,
                        "currency": "CAD",
                        "includes": ["tracking"],
                    },
                ],
                "notes": [
                    f"Additional {cannabis_surcharge} CAD handling fee for cannabis products",
                    "Brokerage fees included for international shipments",
                ],
            }
        return {
            "carrier": "fedex_ca",
            "origin": origin,
            "destination": destination,
            "weight_kg": weight,
            "is_cannabis": is_cannabis,
            "service_levels": [
                {
                    "name": "FedEx Priority Overnight",
                    "delivery_time": "Next business day by 10:30 AM",
                    "price": 50.00 + (weight * 10.00) + cannabis_surcharge,
                    "currency": "CAD",
                    "includes": ["money-back guarantee", "real-time tracking"],
                },
                {
                    "name": "FedEx Ground",
                    "delivery_time": "2-5 business days",
                    "price": 20.00 + (weight * 3.00) + cannabis_surcharge,
                    "currency": "CAD",
                    "includes": ["tracking"],
                },
            ],
            "notes": [
                f"Additional {cannabis_surcharge} CAD surcharge for cannabis shipments",
                "Adult signature (19+) required for cannabis deliveries",
            ],
        }
