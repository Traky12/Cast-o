#!/usr/bin/env python3
from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone

try:
    import boto3
except ImportError:  # pragma: no cover
    boto3 = None


def cleanup_old_backups() -> None:
    if boto3 is None:
        print("boto3 no instalado, omitiendo limpieza GDPR")
        return

    region = os.getenv("AWS_REGION", "eu-west-1")
    bucket = os.getenv("GDPR_BACKUP_BUCKET", "castuo-gdpr-backups")
    client = boto3.client("s3", region_name=region)

    cutoff = datetime.now(timezone.utc) - timedelta(days=30)
    paginator = client.get_paginator("list_objects_v2")
    for page in paginator.paginate(Bucket=bucket, Prefix="gdpr/"):
        for obj in page.get("Contents", []):
            if obj["LastModified"] < cutoff:
                client.delete_object(Bucket=bucket, Key=obj["Key"])
                print(f"Deleted old backup: {obj['Key']}")


if __name__ == "__main__":
    cleanup_old_backups()
