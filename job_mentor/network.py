from __future__ import annotations

import os
import ssl
from typing import Any
from urllib.request import Request, urlopen as urllib_urlopen

import certifi


def build_ssl_context() -> ssl.SSLContext:
    """Return a default-verify SSL context using the platform CA bundle when present.

    Python 3.11 on some Windows installs exposes a default CA path that does not exist
    (for example C:\\Program Files\\Common Files\\SSL\\cert.pem). In that case, fall back
    to certifi's bundled CA bundle so HTTPS requests remain verified without a manual
    SSL_CERT_FILE workaround.
    """
    default_paths = ssl.get_default_verify_paths()
    default_cafile = getattr(default_paths, "cafile", None)
    if default_cafile and os.path.exists(default_cafile):
        return ssl.create_default_context()

    cafile = certifi.where()
    if cafile and os.path.exists(cafile):
        return ssl.create_default_context(cafile=cafile)

    return ssl.create_default_context()


def urlopen_with_reliable_ssl(request: Request, timeout: float | int = 20, **kwargs: Any):
    """Open an HTTPS request using a valid CA bundle while preserving certificate verification."""
    context = build_ssl_context()
    return urllib_urlopen(request, timeout=timeout, context=context, **kwargs)


urlopen = urlopen_with_reliable_ssl
