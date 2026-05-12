#!/usr/bin/env python3
"""TRACES/Hyperledger Client with Tenacity Retries"""

import os
import json
import asyncio
from typing import Dict, Any
from datetime import datetime
import httpx
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    before_sleep_log
)
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TRACESClient:
    def __init__(self, api_url: str, api_key: str):
        self.api_url = api_url
        self.api_key = api_key
        self.client = httpx.AsyncClient(timeout=30.0)
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        before_sleep=before_sleep_log(logger, logging.INFO)
    )
    async def send_to_traces(self, certificate_data: Dict[str, Any]) -> Dict[str, Any]:
        """Send certificate to TRACES with automatic retries"""
        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }
        
        payload = {
            'certificate_number': certificate_data.get('certificate_number'),
            'product_code': certificate_data.get('product_code'),
            'destination_country': certificate_data.get('destination_country'),
            'timestamp': datetime.utcnow().isoformat(),
            'hyperledger_hash': self._generate_hash(certificate_data)
        }
        
        response = await self.client.post(
            f'{self.api_url}/api/v1/documents/send',
            json=payload,
            headers=headers
        )
        
        if response.status_code not in [200, 201]:
            raise Exception(f"TRACES error: {response.status_code} {response.text}")
        
        return response.json()
    
    def _generate_hash(self, data: Dict[str, Any]) -> str:
        """Generate Hyperledger-compatible hash"""
        import hashlib
        data_str = json.dumps(data, sort_keys=True)
        return hashlib.sha256(data_str.encode()).hexdigest()
    
    async def send_batch(self, certificates: list) -> list:
        """Send multiple certificates"""
        tasks = [self.send_to_traces(cert) for cert in certificates]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        return results

async def main():
    client = TRACESClient(
        api_url=os.getenv('TRACES_API_URL'),
        api_key=os.getenv('TRACES_API_KEY')
    )
    
    cert = {
        'certificate_number': 'ES2026001',
        'product_code': 'BEEF_PRODUCT',
        'destination_country': 'FR'
    }
    
    result = await client.send_to_traces(cert)
    print(json.dumps(result, indent=2))

if __name__ == '__main__':
    asyncio.run(main())
