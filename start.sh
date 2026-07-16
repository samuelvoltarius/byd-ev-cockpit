#!/usr/bin/env bash
# EV-Cockpit starten (Linux / macOS / Raspberry Pi)
cd "$(dirname "$0")"

command -v python3 >/dev/null || { echo "Bitte zuerst Python 3 installieren."; exit 1; }

# Eigene Umgebung IM Programmordner (.venv). Moderne Systeme — Debian 12, Ubuntu 24.04,
# Raspberry Pi OS Bookworm, Fedora, Homebrew — verbieten "pip install" ins System (PEP 668).
# Das alte "pip install --user" ist dort auf einen Fehler gelaufen. Ein venv ist der Weg,
# den PEP 668 ausdruecklich offenlaesst, und er fasst das System des Nutzers nicht an.
if [ ! -x .venv/bin/python ]; then
  echo "  Richte die Umgebung ein (einmalig, dauert etwa eine Minute) ..."
  python3 -m venv .venv 2>/dev/null || {
    echo
    echo "  Python kann hier keine eigene Umgebung anlegen."
    echo "  Unter Debian, Ubuntu und Raspberry Pi OS fehlt dafuer ein Paket:"
    echo
    echo "      sudo apt install python3-venv"
    echo
    echo "  Danach start.sh einfach nochmal aufrufen."
    exit 1; }
fi

# Feste Versionen — dieselben wie im Windows-Paket. So laeuft bei allen derselbe Code.
.venv/bin/python -c "import pybyd, paho.mqtt.client" 2>/dev/null || {
  echo "  Lade die BYD-Bibliothek (einmalig) ..."
  .venv/bin/pip install -q --disable-pip-version-check pybyd==0.0.72 paho-mqtt==2.1.0 || {
    echo
    echo "  Download fehlgeschlagen. Bist du online?"
    echo "  Klappt es weiterhin nicht: bitte melden, office@photo-aigner.at"
    exit 1; }
}

echo "  Starte EV-Cockpit ..."
exec .venv/bin/python evcockpit.py
