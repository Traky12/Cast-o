# -*- coding: utf-8 -*-
"""Modelos para productos y pedidos e-commerce (Shopify, WooCommerce, Amazon)."""
from datetime import datetime
from typing import Dict, List, Optional

from pydantic import BaseModel


class ProductImage(BaseModel):
    """Imagen de un producto."""
    url: str
    alt_text: str
    is_primary: bool = False


class ProductVariant(BaseModel):
    """Variante de un producto (tamaño, variedad)."""
    id: str
    sku: str
    name: str
    price: float
    compare_at_price: Optional[float] = None
    weight: float = 0.0
    inventory_quantity: int = 0
    inventory_policy: str = "deny"
    barcode: Optional[str] = None
    image: Optional[ProductImage] = None


class EcommerceProduct(BaseModel):
    """Producto listo para sincronizar con plataformas de e-commerce."""
    id: Optional[str] = None
    title: str
    description: str
    handle: str = ""
    product_type: str = "microgreens"
    vendor: str = "CASTUO-SYSTEM"
    status: str = "active"
    tags: List[str] = []
    images: List[ProductImage] = []
    variants: List[ProductVariant] = []
    options: List[Dict] = []
    published_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    metafields: List[Dict] = []
    seo: Dict = {"title": "", "description": "", "keywords": []}


class EcommerceOrder(BaseModel):
    """Pedido de e-commerce."""
    id: str
    order_number: str
    customer: Dict = {}
    line_items: List[Dict] = []
    shipping_address: Dict = {}
    billing_address: Dict = {}
    payment_method: str = ""
    total_price: float = 0.0
    financial_status: str = "pending"
    fulfillment_status: str = "unfulfilled"
    created_at: datetime = datetime.now()
    updated_at: datetime = datetime.now()
    metafields: List[Dict] = []


class EcommercePlatformConfig(BaseModel):
    """Configuración para una plataforma de e-commerce."""
    platform: str
    api_key: str
    api_secret: str
    store_url: str
    webhook_secret: Optional[str] = None
    active: bool = True
    last_sync: Optional[datetime] = None
