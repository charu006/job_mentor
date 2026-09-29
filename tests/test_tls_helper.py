from __future__ import annotations

import os
import ssl
import types

import certifi

import job_mentor.network as network_module


def test_build_ssl_context_uses_system_bundle_when_valid(monkeypatch):
    seen = {}

    def fake_create_default_context(*, cafile=None, **kwargs):
        seen["cafile"] = cafile
        ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        return ctx

    monkeypatch.setattr(ssl, "get_default_verify_paths", lambda: types.SimpleNamespace(cafile="/etc/ssl/cert.pem"))
    monkeypatch.setattr(os.path, "exists", lambda path: path == "/etc/ssl/cert.pem")
    monkeypatch.setattr(ssl, "create_default_context", fake_create_default_context)

    ctx = network_module.build_ssl_context()

    assert seen["cafile"] is None
    assert ctx.verify_mode == ssl.CERT_REQUIRED


def test_build_ssl_context_falls_back_to_certifi(monkeypatch):
    seen = {}

    def fake_create_default_context(*, cafile=None, **kwargs):
        seen["cafile"] = cafile
        ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        return ctx

    monkeypatch.setattr(
        ssl,
        "get_default_verify_paths",
        lambda: types.SimpleNamespace(cafile=r"C:\Program Files\Common Files\SSL\cert.pem"),
    )
    monkeypatch.setattr(os.path, "exists", lambda path: path != r"C:\Program Files\Common Files\SSL\cert.pem")
    monkeypatch.setattr(certifi, "where", lambda: r"C:\fake\certifi\cacert.pem")
    monkeypatch.setattr(ssl, "create_default_context", fake_create_default_context)

    ctx = network_module.build_ssl_context()

    assert seen["cafile"] == r"C:\fake\certifi\cacert.pem"
    assert ctx.verify_mode == ssl.CERT_REQUIRED


def test_urlopen_with_reliable_ssl_calls_urlopen_with_verified_context(monkeypatch):
    captured = {}

    class DummyRequest:
        pass

    class DummyResponse:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def read(self):
            return b"{}"

    def fake_urlopen(request, timeout=20, context=None, **kwargs):
        captured["request"] = request
        captured["timeout"] = timeout
        captured["context"] = context
        return DummyResponse()

    monkeypatch.setattr(network_module, "urllib_urlopen", fake_urlopen)

    with network_module.urlopen_with_reliable_ssl(DummyRequest(), timeout=15) as response:
        assert response.read() == b"{}"

    assert captured["timeout"] == 15
    assert captured["context"] is not None
    assert captured["context"].verify_mode == ssl.CERT_REQUIRED
