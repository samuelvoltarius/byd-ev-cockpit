"""Network guards shared by the optional local-device adapters.

Only literal RFC 1918 IPv4 addresses are accepted. Redirects are deliberately
disabled so an approved LAN host cannot bounce a request to localhost, a cloud
service, or a link-local metadata endpoint.
"""
from __future__ import annotations

import contextlib
import ipaddress
import socket
import urllib.error
import urllib.request
from urllib.parse import urlsplit


RFC1918_NETWORKS = tuple(
    ipaddress.ip_network(value)
    for value in ("10.0.0.0/8", "172.16.0.0/12", "192.168.0.0/16")
)
# WALLBOX_VERTRAG §2: dazu 100.64.0.0/10 (Tailscale/CGNAT = eigener VPN des Nutzers)
PRIVATE_NETWORKS = RFC1918_NETWORKS + (ipaddress.ip_network("100.64.0.0/10"),)
# Unsere eigenen Server bekommen nie Wallbox-Anfragen (Regel 2), egal wohin der Name aufloest
GESPERRTE_NAMEN = ("serveone.at",)

# Nur fuer den Praxistest (Koordination 22.10.): ein oeffentliches https-Ziel freischalten, solange der
# Testlauf laeuft. Kein Schalter in Config, Umgebung oder Oberflaeche; nur ueber testziel() im Testskript.
_TESTZIELE = set()


@contextlib.contextmanager
def testziel(host: str):
    host = host.strip().lower()
    _TESTZIELE.add(host)
    try:
        yield
    finally:
        _TESTZIELE.discard(host)


def _gesperrt(name: str) -> bool:
    name = name.strip().lower().rstrip(".")
    return any(name == g or name.endswith("." + g) for g in GESPERRTE_NAMEN)


def private_ziel(host: str, label: str = "device", aufloesen=socket.getaddrinfo):
    """WALLBOX_VERTRAG §2: (schema, adresse) fuer eine private IPv4 (RFC 1918, 100.64/10) oder einen Namen,
    der NUR auf solche Adressen aufloest. Die Anfrage geht dann an die aufgeloeste Adresse (kein zweites
    Aufloesen, kein Umbiegen). Testziel im Praxistest: ('https', name)."""
    if not isinstance(host, str) or not host.strip():
        raise ValueError(f"{label}: Adresse fehlt")
    host = host.strip()
    if host.lower() in _TESTZIELE:
        return "https", host.lower()
    try:
        ipaddress.ip_address(host)
    except ValueError:
        pass                                   # ein Name: unten aufloesen
    else:
        return "http", private_ipv4(host, label)   # eine Adresse: nur privat, nie aufloesen
    if _gesperrt(host) or not all(c.isalnum() or c in ".-" for c in host):
        raise ValueError(f"{label}: Adresse nicht erlaubt")
    try:
        infos = aufloesen(host, None, socket.AF_INET, socket.SOCK_STREAM)
    except (OSError, UnicodeError) as exc:
        raise ValueError(f"{label}: Name nicht gefunden") from exc
    ips = sorted({i[4][0] for i in infos})
    if not ips:
        raise ValueError(f"{label}: Name nicht gefunden")
    for ip in ips:
        private_ipv4(ip, label)            # jede Adresse muss privat sein, sonst abgelehnt
    return "http", ips[0]


def private_ipv4(value: str, label: str = "device") -> str:
    """Return a canonical literal RFC 1918 address or raise ``ValueError``."""
    try:
        ip = ipaddress.ip_address(value.strip())
    except (AttributeError, ValueError) as exc:
        raise ValueError(f"{label} must be a private IPv4 address") from exc
    if ip.version != 4 or not any(ip in network for network in PRIVATE_NETWORKS):
        raise ValueError(f"{label} must be a private IPv4 address (RFC 1918 or 100.64.0.0/10)")
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


def open_lan_url(url: str, timeout: float, method: str = "GET", headers=None, data=None):
    """Open an RFC 1918 HTTP URL without following redirects (GET, or POST for evcc control)."""
    if method not in ("GET", "POST"):
        raise ValueError("Only GET and POST are allowed for LAN requests")
    parsed = urlsplit(url)
    if parsed.username or parsed.password or not parsed.hostname:
        raise ValueError("Only plain HTTP URLs to private LAN devices are allowed")
    if parsed.scheme == "https" and parsed.hostname.lower() in _TESTZIELE:
        pass                                   # nur waehrend testziel() im Praxistest
    elif parsed.scheme != "http":
        raise ValueError("Only plain HTTP URLs to private LAN devices are allowed")
    else:
        private_ipv4(parsed.hostname, "URL host")
    try:
        port = parsed.port
    except ValueError as exc:
        raise ValueError("Invalid LAN URL port") from exc
    if port is not None and not 1 <= port <= 65535:
        raise ValueError("Invalid LAN URL port")
    kopf = {"Accept": "application/json"}
    kopf.update(headers or {})
    request = urllib.request.Request(url, headers=kopf, method=method,
                                     data=(data if data is not None else b"") if method == "POST" else None)
    return _LAN_OPENER.open(request, timeout=timeout)
