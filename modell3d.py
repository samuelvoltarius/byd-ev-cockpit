"""3D-Automodelle wie in Panoptes (gemeinsames Manifest auf byd.serveone.at/tiles/models/).

- Welches Modell: aus dem Modellnamen im Cockpit (Dolphin Surf = "seagull" usw.).
- Das Modell wird EINMAL vom Community-Server geladen, gegen die sha256 aus dem Manifest geprueft und lokal
  abgelegt (~1 MB). Danach kommt es vom eigenen Rechner - auch offline, ohne Spur beim Server.
- Lizenz: CC BY 4.0 (Nazh Design) -> Namensnennung ist Pflicht und wird im Cockpit angezeigt.
- verfuegbar:false oder file:null -> kein Modell, das Cockpit bleibt bei Foto/Silhouette.
"""
import hashlib
import json
import os
import re
import time
import urllib.request

MANIFEST_URL = "https://byd.serveone.at/tiles/models/manifest.json"
BASIS_URL = "https://byd.serveone.at/tiles/models/"
MAX_BYTES = 8 * 1024 * 1024
LIZENZEN_URL = "https://byd.serveone.at/tiles/models/MODELLE_LIZENZEN.md"

# Cockpit-Modellname (Teilstring, klein) -> Manifest-id. Reihenfolge zaehlt: "Dolphin Surf" vor "Dolphin".
ZUORDNUNG = (
    ("dolphin surf", "seagull"), ("seagull", "seagull"), ("dolphin", "dolphin"),
    ("atto 3", "atto3"), ("atto3", "atto3"), ("seal u", "seal-u"), ("sealion", "sealion7"),
    ("seal", "seal"), ("shark", "shark"), ("han", "han"), ("tang", "tang"),
)


def modell_id(modellname):
    n = (modellname or "").lower()
    for teil, mid in ZUORDNUNG:
        if teil in n:
            return mid
    return ""


def eintrag(manifest, mid):
    """Manifest-Eintrag, wenn das Modell wirklich ladbar ist, sonst None."""
    for m in (manifest or {}).get("models") or []:
        if m.get("id") == mid:
            f = m.get("file")
            if m.get("verfuegbar") and isinstance(f, str) and re.fullmatch(r"[a-z0-9_-]+\.glb", f) \
                    and re.fullmatch(r"[0-9a-f]{64}", str(m.get("sha256") or "")):
                return m
            return None
    return None


def info(m, farben=()):
    """Was die Oberflaeche braucht (inkl. Pflicht-Namensnennung)."""
    return {"verfuegbar": True, "id": m["id"], "name": m.get("name") or m["id"],
            "attribution": m.get("attribution") or ("„%s“ von %s, %s" % (m.get("title") or m.get("name"),
                                                                       m.get("author") or "?", m.get("license") or "")),
            "license": m.get("license"), "licenseUrl": m.get("licenseUrl"), "author": m.get("author"),
            "authorUrl": m.get("authorUrl"), "source": m.get("source"), "lizenzen": LIZENZEN_URL,
            "paint": m.get("paintMeshHint") or "bodypaint", "farben": list(farben)}


def _hole(url, timeout=30):
    req = urllib.request.Request(url, headers={"User-Agent": "ev-cockpit"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        daten = r.read(MAX_BYTES + 1)
    if len(daten) > MAX_BYTES:
        raise ValueError("Modell zu gross")
    return daten


def datei(m, ordner, hole=_hole):
    """Pfad zur lokal abgelegten, gepruften .glb. Laedt nur, wenn sie fehlt oder nicht passt."""
    ziel = os.path.join(ordner, m["file"])
    if os.path.exists(ziel):
        with open(ziel, "rb") as f:
            if hashlib.sha256(f.read()).hexdigest() == m["sha256"]:
                return ziel
    daten = hole(BASIS_URL + m["file"])
    if hashlib.sha256(daten).hexdigest() != m["sha256"]:
        raise ValueError("Modell stimmt nicht mit dem Manifest überein (sha256)")
    os.makedirs(ordner, exist_ok=True)
    tmp = ziel + ".tmp"
    with open(tmp, "wb") as f:
        f.write(daten)
    os.replace(tmp, ziel)
    return ziel


class Manifest:
    """Manifest hoechstens alle 6 h neu holen."""

    def __init__(self, hole=_hole, uhr=time.time):
        self.hole, self.uhr, self.t, self.d = hole, uhr, 0.0, None

    def get(self):
        if self.d is None or self.uhr() - self.t > 6 * 3600:
            self.d = json.loads(self.hole(MANIFEST_URL).decode("utf-8"))
            self.t = self.uhr()
        return self.d
