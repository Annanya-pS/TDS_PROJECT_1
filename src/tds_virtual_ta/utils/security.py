
import hmac
import hashlib
import secrets
from typing import Optional
from ..config import settings


def validate_secret(provided_secret: str) -> bool:
    """
    Validate secret key using constant-time comparison.
    
    Args:
        provided_secret: Secret from request
    
    Returns:
        True if valid
    """
    expected_secret = settings.service_secret
    return hmac.compare_digest(provided_secret, expected_secret)


def generate_task_id() -> str:
    """
    Generate cryptographically secure task ID.
    
    Returns:
        Random URL-safe task ID
    """
    return secrets.token_urlsafe(16)


def generate_hmac_signature(data: str, key: Optional[str] = None) -> str:
    """Generate HMAC-SHA256 signature."""
    if key is None:
        key = settings.service_secret
    
    signature = hmac.new(
        key.encode('utf-8'),
        data.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()
    
    return signature


def sanitize_log_data(data: dict) -> dict:
    """Remove sensitive info from logs."""
    sensitive_keys = ['secret', 'token', 'password', 'api_key', 'authorization']
    
    sanitized = data.copy()
    for key in list(sanitized.keys()):
        if any(sensitive in key.lower() for sensitive in sensitive_keys):
            sanitized[key] = '***REDACTED***'
    
    return sanitized
