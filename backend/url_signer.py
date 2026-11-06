"""
url_signer.py
Cryptographic HMAC-SHA256 URL signing and token protection engine for PyCDN edge media.
Provides CDN-grade signed URLs with time-to-live expiration and client IP binding.
"""

import hmac
import hashlib
import time
import base64
import json
from urllib.parse import urlparse, parse_qs, urlencode
from typing import Tuple, Optional, Dict, Any


class UrlSigner:
    """
    Cryptographic HMAC-SHA256 URL Signer & Verifier for Edge CDN Media Delivery.
    Defends against hotlinking, unauthorized stream rips, and parameter tampering.
    """

    def __init__(self, secret_key: str, default_ttl: int = 3600):
        if not secret_key or len(secret_key) < 16:
            raise ValueError("Secret key must be at least 16 characters for cryptographic safety")
        self.secret_key = secret_key.encode('utf-8')
        self.default_ttl = default_ttl

    def _compute_signature(self, path: str, expires: int, client_ip: Optional[str] = None) -> str:
        """
        Creates HMAC-SHA256 signature over normalized message:
        f"{normalized_path}|{expires}|{client_ip or '*'}"
        """
        normalized_path = "/" + path.strip("/")
        ip_token = client_ip.strip() if client_ip else "*"
        payload = f"{normalized_path}|{expires}|{ip_token}".encode('utf-8')
        
        mac = hmac.new(self.secret_key, payload, hashlib.sha256).digest()
        # Return URL-safe base64 without padding for clean URLs
        return base64.urlsafe_b64encode(mac).decode('utf-8').rstrip('=')

    def sign_url(self, url_or_path: str, ttl: Optional[int] = None, client_ip: Optional[str] = None) -> str:
        """
        Signs a URL or relative path with HMAC-SHA256 token and expiration.
        """
        parsed = urlparse(url_or_path)
        path = parsed.path or "/"
        expires = int(time.time() + (ttl if ttl is not None else self.default_ttl))

        sig = self._compute_signature(path, expires, client_ip)

        # Merge existing query params if any
        params = parse_qs(parsed.query)
        params["exp"] = [str(expires)]
        params["sig"] = [sig]
        if client_ip:
            params["ip"] = [client_ip]

        # Flatten query dictionary
        flat_query = {k: v[0] for k, v in params.items()}
        new_query = urlencode(flat_query)

        if parsed.netloc:
            scheme = parsed.scheme or "https"
            return f"{scheme}://{parsed.netloc}{path}?{new_query}"
        return f"{path}?{new_query}"

    def verify_url(self, url_or_path: str, client_ip: Optional[str] = None) -> Tuple[bool, str]:
        """
        Validates signature, expiration, and optional IP binding using constant-time comparison.
        Returns (is_valid, reason).
        """
        parsed = urlparse(url_or_path)
        params = parse_qs(parsed.query)
        path = parsed.path or "/"

        sig_list = params.get("sig")
        exp_list = params.get("exp")

        if not sig_list or not exp_list:
            return False, "MISSING_SIGNATURE_OR_EXPIRY"

        signature = sig_list[0]
        try:
            expires = int(exp_list[0])
        except ValueError:
            return False, "INVALID_EXPIRY_FORMAT"

        # Check expiration
        now = int(time.time())
        if now > expires:
            return False, "EXPIRED_URL"

        # Check IP binding if present in URL
        url_ip_list = params.get("ip")
        if url_ip_list:
            bound_ip = url_ip_list[0]
            if not client_ip or client_ip.strip() != bound_ip.strip():
                return False, "IP_MISMATCH"
            expected_sig = self._compute_signature(path, expires, bound_ip)
        else:
            expected_sig = self._compute_signature(path, expires, None)

        # Constant-time comparison
        if not hmac.compare_digest(signature, expected_sig):
            return False, "SIGNATURE_TAMPERED"

        return True, "VALID"

    def generate_token_bearer(self, resource_id: str, ttl: int = 300, metadata: Optional[Dict[str, Any]] = None) -> str:
        """
        Creates an encrypted/signed Bearer token string containing JSON claims.
        """
        expires = int(time.time() + ttl)
        claims = {
            "res": resource_id,
            "exp": expires,
            "meta": metadata or {}
        }
        raw_json = json.dumps(claims, separators=(',', ':')).encode('utf-8')
        encoded_payload = base64.urlsafe_b64encode(raw_json).decode('utf-8').rstrip('=')
        
        sig = hmac.new(self.secret_key, encoded_payload.encode('utf-8'), hashlib.sha256).digest()
        encoded_sig = base64.urlsafe_b64encode(sig).decode('utf-8').rstrip('=')
        
        return f"{encoded_payload}.{encoded_sig}"

    def verify_token_bearer(self, token: str) -> Tuple[bool, Optional[Dict[str, Any]], str]:
        """
        Verifies Bearer token integrity and returns (valid, claims, reason).
        """
        parts = token.split('.')
        if len(parts) != 2:
            return False, None, "MALFORMED_TOKEN"

        payload_b64, sig_b64 = parts[0], parts[1]

        # Recompute signature
        expected_sig = hmac.new(self.secret_key, payload_b64.encode('utf-8'), hashlib.sha256).digest()
        expected_sig_b64 = base64.urlsafe_b64encode(expected_sig).decode('utf-8').rstrip('=')

        if not hmac.compare_digest(sig_b64, expected_sig_b64):
            return False, None, "INVALID_SIGNATURE"

        # Decode payload
        try:
            # Re-add padding if needed
            padded = payload_b64 + '=' * (-len(payload_b64) % 4)
            claims = json.loads(base64.urlsafe_b64decode(padded.encode('utf-8')).decode('utf-8'))
        except Exception:
            return False, None, "INVALID_PAYLOAD"

        if time.time() > claims.get("exp", 0):
            return False, None, "EXPIRED_TOKEN"

        return True, claims, "VALID"
