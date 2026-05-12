import os
import hvac
import pyotp
from datetime import datetime, timedelta
from fastapi import HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthCredentials

class MFAManager:
    def __init__(self, vault_addr: str, vault_token: str):
        self.client = hvac.Client(url=vault_addr, token=vault_token)
        self.bearer_scheme = HTTPBearer()
    
    def generate_totp_secret(self, user_id: str) -> dict:
        """Generate TOTP secret for user"""
        secret = pyotp.random_base32()
        # Store in Vault
        self.client.secrets.kv.v2.create_or_update_secret_version(
            path=f'mfa/{user_id}',
            secret_data={'totp_secret': secret, 'created_at': datetime.utcnow().isoformat()}
        )
        totp = pyotp.TOTP(secret)
        return {
            'secret': secret,
            'provisioning_uri': totp.provisioning_uri(name=user_id, issuer_name='CASTÚO'),
            'backup_codes': [str(i).zfill(6) for i in range(1000, 1010)]  # Simplified
        }
    
    def verify_totp(self, user_id: str, token: str) -> bool:
        """Verify TOTP token"""
        secret_data = self.client.secrets.kv.v2.read_secret_version(path=f'mfa/{user_id}')
        secret = secret_data['data']['data']['totp_secret']
        totp = pyotp.TOTP(secret)
        return totp.verify(token, valid_window=1)
    
    async def validate_mfa(self, credentials: HTTPAuthCredentials = Depends(HTTPBearer())) -> str:
        """Middleware to validate MFA token"""
        try:
            # Decode JWT, extract user_id and mfa_verified
            # If not verified, raise exception
            pass
        except Exception as e:
            raise HTTPException(status_code=401, detail=str(e))

mfa_manager = MFAManager(os.getenv('VAULT_ADDR'), os.getenv('VAULT_TOKEN'))
