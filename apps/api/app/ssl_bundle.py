"""
Optionally merge a local TLS-intercept CA into certifi (dev / Docker only).

Looks for /etc/ssl/certs/corp-proxy.pem (mount via private compose overlay if needed).
No-op when the file is absent — public registries and default CAs are unchanged.
"""
from __future__ import annotations

import os
from pathlib import Path

_BUNDLE_PATH = Path("/tmp/local-ca-bundle.pem")
_CORP_PROXY_PEM = Path("/etc/ssl/certs/corp-proxy.pem")
_applied = False


def apply_corporate_ssl_bundle() -> str | None:
    global _applied
    if _applied:
        return str(_BUNDLE_PATH) if _BUNDLE_PATH.exists() else None
    if not _CORP_PROXY_PEM.is_file():
        return None
    import certifi

    _BUNDLE_PATH.write_text(
        Path(certifi.where()).read_text().rstrip() + "\n" + _CORP_PROXY_PEM.read_text().lstrip()
    )
    bundle = str(_BUNDLE_PATH)

    def _where() -> str:
        return bundle

    certifi.where = _where  # type: ignore[method-assign]
    os.environ["SSL_CERT_FILE"] = bundle
    os.environ["REQUESTS_CA_BUNDLE"] = bundle
    os.environ["GRPC_DEFAULT_SSL_ROOTS_FILE_PATH"] = bundle
    _applied = True
    return bundle


def aiohttp_ssl_context() -> "ssl.SSLContext | bool":
    """Return SSL context for aiohttp, or True for default verification."""
    import ssl

    bundle = apply_corporate_ssl_bundle()
    if bundle:
        return ssl.create_default_context(cafile=bundle)
    return True
