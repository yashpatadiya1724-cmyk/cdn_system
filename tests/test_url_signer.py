"""
Unit Tests for PyCDN Cryptographic HMAC-SHA256 URL Signing Engine
"""

import time
import pytest
from backend.url_signer import UrlSigner


@pytest.fixture
def signer():
    return UrlSigner(secret_key="production_super_secret_signing_key_2026", default_ttl=60)


def test_sign_and_verify_valid_url(signer):
    """Verify that a freshly signed URL validates cleanly."""
    path = "/media/protected/sample-video.mp4"
    signed_url = signer.sign_url(path, ttl=120)

    is_valid, reason = signer.verify_url(signed_url)
    assert is_valid is True
    assert reason == "VALID"


def test_url_expiration_rejection(signer):
    """Verify that expired signed URLs are rejected."""
    path = "/media/protected/stream.m3u8"
    # Sign with -10 second TTL (already expired)
    signed_url = signer.sign_url(path, ttl=-10)

    is_valid, reason = signer.verify_url(signed_url)
    assert is_valid is False
    assert reason == "EXPIRED_URL"


def test_signature_tamper_rejection(signer):
    """Verify that altering path or signature payload is detected."""
    path = "/media/confidential/report.pdf"
    signed_url = signer.sign_url(path, ttl=300)

    # Tamper with path
    tampered_url = signed_url.replace("report.pdf", "secret_database.csv")
    is_valid, reason = signer.verify_url(tampered_url)
    assert is_valid is False
    assert reason == "SIGNATURE_TAMPERED"

    # Tamper with signature parameter
    tampered_sig = signed_url.replace("sig=", "sig=invalid_sig_")
    is_valid_sig, reason_sig = signer.verify_url(tampered_sig)
    assert is_valid_sig is False
    assert reason_sig == "SIGNATURE_TAMPERED"


def test_client_ip_binding_restriction(signer):
    """Verify that IP-bound URLs only validate for the matching client IP."""
    path = "/enterprise/secure-data.tar.gz"
    client_ip = "192.168.1.100"
    signed_url = signer.sign_url(path, ttl=60, client_ip=client_ip)

    # Valid matching IP
    is_valid, reason = signer.verify_url(signed_url, client_ip="192.168.1.100")
    assert is_valid is True
    assert reason == "VALID"

    # Mismatched attacker IP
    is_invalid, reason_bad = signer.verify_url(signed_url, client_ip="10.0.0.99")
    assert is_invalid is False
    assert reason_bad == "IP_MISMATCH"


def test_token_bearer_claims_roundtrip(signer):
    """Verify Bearer token encoding and claims verification."""
    token = signer.generate_token_bearer(
        resource_id="tenant-video-883",
        ttl=180,
        metadata={"role": "premium_user", "max_bitrate": "4k"}
    )

    valid, claims, reason = signer.verify_token_bearer(token)
    assert valid is True
    assert claims["res"] == "tenant-video-883"
    assert claims["meta"]["role"] == "premium_user"
    assert reason == "VALID"
