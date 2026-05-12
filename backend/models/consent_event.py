from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel


class ConsentEvent(BaseModel):
    token_id: str
    status: str
    timestamp: datetime
    gaiachain_tx: Optional[str] = None
    ipfs_cid: Optional[str] = None
    block_number: Optional[int] = None
    audit_trail: Optional[List[Dict[str, Any]]] = None
    error: Optional[str] = None

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}


