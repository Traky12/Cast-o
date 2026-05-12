#!/usr/bin/env python3
"""GDPR Deletion Workflow - Article 17 Right to be Forgotten"""

import os
import psycopg
from datetime import datetime
from typing import List
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class GDPRDeletionManager:
    def __init__(self, db_url: str):
        self.db_url = db_url
        self.conn = psycopg.connect(db_url)
    
    def delete_user_data(self, user_id: str, imsi: str) -> dict:
        """Delete all user data from system (GDPR Article 17)"""
        cursor = self.conn.cursor()
        try:
            # Start transaction
            cursor.execute("BEGIN;")
            
            # Delete from cascade tables
            tables_to_delete = [
                'sensor_telemetry',
                'iot_events',
                'alerts',
                'commands',
                'documentos',
                'ganado',
                'salud_animal'
            ]
            
            for table in tables_to_delete:
                cursor.execute(f"DELETE FROM {table} WHERE user_id = %s OR imsi = %s", (user_id, imsi))
                logger.info(f"Deleted from {table}: {cursor.rowcount} rows")
            
            # Log deletion in audit trail (write-once)
            cursor.execute("""
                INSERT INTO audit_log_deletion (user_id, imsi, deleted_at, reason)
                VALUES (%s, %s, %s, %s)
            """, (user_id, imsi, datetime.utcnow(), 'GDPR Article 17 Request'))
            
            # Commit
            cursor.execute("COMMIT;")
            logger.info(f"GDPR deletion completed for user_id={user_id}, imsi={imsi}")
            
            return {'status': 'success', 'deleted_user': user_id, 'timestamp': datetime.utcnow().isoformat()}
        
        except Exception as e:
            cursor.execute("ROLLBACK;")
            logger.error(f"Error in GDPR deletion: {e}")
            raise
        finally:
            cursor.close()

if __name__ == '__main__':
    manager = GDPRDeletionManager(os.getenv('DATABASE_URL'))
    result = manager.delete_user_data('user123', 'imsi123')
    print(result)
