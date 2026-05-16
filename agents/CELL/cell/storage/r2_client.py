"""
Cloudflare R2 client (S3-compatible).
Used to fetch insights.yaml produced by IRIS.
"""
from __future__ import annotations

import logging
from typing import Optional

import boto3
import yaml
from botocore.exceptions import ClientError

from cell.config import settings

logger = logging.getLogger(__name__)

_s3_client = None


def _get_client():
    global _s3_client
    if _s3_client is None:
        _s3_client = boto3.client(
            "s3",
            endpoint_url=settings.r2_endpoint_url,
            aws_access_key_id=settings.r2_access_key_id,
            aws_secret_access_key=settings.r2_secret_access_key,
            region_name="auto",
        )
    return _s3_client


def fetch_insights_yaml(path: str) -> Optional[dict]:
    """
    Fetch and parse insights.yaml from R2.
    `path` is the key inside the bucket, e.g.
    "/projects/PROJ-CRM-0014/2025-05-06_meet-standup-001/insights.yaml"
    Leading slash is stripped if present.
    Returns parsed dict or None on failure.
    """
    key = path.lstrip("/")
    try:
        client = _get_client()
        response = client.get_object(Bucket=settings.r2_bucket_name, Key=key)
        raw = response["Body"].read()
        data = yaml.safe_load(raw)
        logger.info("Fetched insights.yaml from R2: %s", key)
        return data
    except ClientError as exc:
        error_code = exc.response["Error"]["Code"]
        logger.error("R2 ClientError fetching %s: %s", key, error_code)
        return None
    except yaml.YAMLError as exc:
        logger.error("YAML parse error for %s: %s", key, exc)
        return None
    except Exception as exc:
        logger.exception("Unexpected error fetching %s: %s", key, exc)
        return None
