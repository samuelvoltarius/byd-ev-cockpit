"""Network guards shared by the optional local-device adapters.

Only literal RFC 1918 IPv4 addresses are accepted. Redirects are deliberately
disabled so an approved LAN host cannot bounce a request to localhost, a cloud
service, or a link-local metadata endpoint.
"""
from __future__ import annotations

import ipaddress
import urllib.error
import urllib.request
from urllib.parse import urlsplit


RFC1918_NETWORKS = tuple(
    ipaddress.ip_network(value)
    for value in ("10.0.0.0/8", "172.16.0.0/12", "192.168.0.0/16")
)


def private_ipv4(value: str, label: str = "device") -> str:
    """Return a canonical literal RFC 1918 address or raise ``ValueError``."""
    try:
        ip = ipaddress.ip_address(value.strip())
    except (AttributeError, ValueError) as exc:
        raise ValueError(f"{label} must be a private IPv4 address") from exc
    if ip.version != 4 or not any(ip in network for network in RFC1918_NETWORKS):
        raise ValueError(f"{label} must be an RFC 1918 private IPv4 address")
    return str(ip)


def private_ipv4_network(value: str, max_addresses: int = 256) -> ipaddress.IPv4Network:
    """Validate a small network contained entirely in one RFC 1918 range."""
    try:
        network = ipaddress.ip_network(value.strip(), strict=False)
    except (AttributeError, ValueError) as exc:
        raise ValueError("Specify a private IPv4 subnet") from exc
    if (
        network.version != 4
        or network.num_addresses > max_addresses
        or not any(network.subnet_of(allowed) for allowed in RFC1918_NETWORKS)
    ):
        raise ValueError("Specify an RFC 1918 IPv4 /24 subnet or smaller")
    return network


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise urllib.error.HTTPError(
            req.full_url, code, "HTTP redirects are disabled for LAN requests", headers, fp
        )


_LAN_OPENER = urllib.request.build_opener(_NoRedirect())


def open_lan_url(url: str, timeout: float, method: str = "GET"):
    """Open an RFC 1918 HTTP URL without following redirects (GET, or POST for evcc control)."""
    if method not in ("GET", "POST"):
        raise ValueError("Only GET and POST are allowed for LAN requests")
    parsed = urlsplit(url)
    if parsed.scheme != "http" or parsed.username or parsed.password or not parsed.hostname:
        raise ValueError("Only plain HTTP URLs to private LAN devices are allowed")
    private_ipv4(parsed.hostname, "URL host")
    try:
        port = parsed.port
    except ValueError as exc:
        raise ValueError("Invalid LAN URL port") from exc
    if port is not None and not 1 <= port <= 65535:
        raise ValueError("Invalid LAN URL port")
    request = urllib.request.Request(url, headers={"Accept": "application/json"}, method=method,
                                     data=b"" if method == "POST" else None)
    return _LAN_OPENER.open(request, timeout=timeout)
