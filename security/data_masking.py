# -*- coding: utf-8 -*-
"""
Enmascaramiento de datos — GDPR (Art. 5, 32), anonimización para auditorías.
Normativas: ISO 27018, GDPR.
"""
import json
import re
from typing import Any, Dict, List, Union

try:
    from faker import Faker
    FAKER = Faker(["es_ES"])
except ImportError:
    FAKER = None


class DataMasking:
    """
    Enmascaramiento y anonimización de datos sensibles (NIF, email, teléfono, dirección, GPS, IP).
    """

    def __init__(self) -> None:
        self.faker = FAKER
        self.masking_rules = {
            "nif": re.compile(r"\b\d{8}[A-Z]\b"),
            "email": re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"),
            "phone": re.compile(r"\b\d{9}\b"),
            "address": re.compile(r"\bC\/|Calle|Avda?\.?\s[\w\s]+,\s*\d{1,3}\b"),
            "gps": re.compile(r"\b\d+\.\d+,\s*\d+\.\d+\b"),
            "ip": re.compile(r"\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b"),
        }

    def mask_sensitive_data(self, data: Union[str, Dict, List]) -> Union[str, Dict, List]:
        """Aplica enmascaramiento compatible GDPR a datos sensibles."""
        if isinstance(data, dict):
            return {k: self.mask_sensitive_data(v) for k, v in data.items()}
        if isinstance(data, list):
            return [self.mask_sensitive_data(i) for i in data]
        if not isinstance(data, str):
            return data

        s = data
        s = self.masking_rules["nif"].sub(lambda m: f"[NIF_MASKED_{m.group(0)[:2]}...]", s)
        s = self.masking_rules["email"].sub(
            lambda m: f"[EMAIL_MASKED_{m.group(0).split('@')[0][:2]}@...]", s
        )
        s = self.masking_rules["phone"].sub("[PHONE_MASKED]", s)
        s = self.masking_rules["address"].sub("[ADDRESS_MASKED]", s)
        s = self.masking_rules["gps"].sub(
            lambda m: f"[GPS_MASKED_{m.group(0).split(',')[0][:4]}...]", s
        )
        s = self.masking_rules["ip"].sub("[IP_MASKED]", s)
        return s

    def generate_fake_data(self, data_type: str) -> str:
        """Genera dato falso para anonimización (es_ES si Faker disponible)."""
        if self.faker:
            if data_type == "nif":
                return self.faker.nif()
            if data_type == "email":
                return self.faker.email()
            if data_type == "phone":
                return self.faker.phone_number()
            if data_type == "address":
                return self.faker.address().replace("\n", ", ")
            if data_type == "name":
                return self.faker.name()
            if data_type == "date":
                return self.faker.date_between(start_date="-1y", end_date="today").isoformat()
        return f"[FAKE_{data_type.upper()}]"

    def anonymize_dataset(self, dataset: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Anonimiza un conjunto de registros (nombres, email, teléfono, dirección, NIF, fecha)."""
        anonymized = []
        sensitive_keys = {
            "name": "name", "nombre": "name",
            "email": "email", "correo": "email",
            "phone": "phone", "telefono": "phone", "movil": "phone",
            "address": "address", "direccion": "address",
            "nif": "nif", "dni": "nif", "cif": "nif",
            "date": "date", "fecha": "date",
        }
        for record in dataset:
            if not isinstance(record, dict):
                anonymized.append(self.mask_sensitive_data(record))
                continue
            new_record = {}
            for k, v in record.items():
                kind = sensitive_keys.get(k.lower())
                if kind:
                    new_record[k] = self.generate_fake_data(kind)
                else:
                    new_record[k] = self.mask_sensitive_data(v)
            anonymized.append(new_record)
        return anonymized
