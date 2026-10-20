# EV-Cockpit

*[🇬🇧 English](README.md) · 🇩🇪 Deutsch*

**Ein kleines Cockpit für dein BYD — läuft auf deinem eigenen Rechner. Deine Auto-Daten
bleiben bei dir und werden an niemanden gesendet.**

> Die Oberfläche ist **zweisprachig — Deutsch und Englisch**. Sie richtet sich automatisch nach deiner Browsersprache; unten in der Ecke gibt es einen 🌐-Umschalter.

Ladestand mit ehrlicher Reichweite (aus deinem echten Verbrauch gerechnet, nicht die
geschönte Werksangabe), Vorklimatisieren, Batterie-Vorheizen, Sitzheizung, Auto finden,
Reifendruck-Warnung, Ladesäulen auf der Karte, Strompreis — und optional an dein Home
Assistant angebunden. Ein Assistent führt dich in fünf Schritten durch die Einrichtung.

Gebaut und getestet an genau **einem** Auto (BYD Dolphin Surf). Für andere Modelle fragt
das Tool dein Auto selbst, was es kann, und zeigt nur das an. Läuft es bei dir nicht wie
erwartet: [bitte ein Issue aufmachen](../../issues) — das hilft allen anderen mit.

---

## „Bleibt wirklich alles bei mir?" — deshalb ist der Code offen

Dieses Tool fragt dich nach deinem BYD-Cloud-Login. Das ist Vertrauenssache, und
„vertrau mir" ist zu wenig. Darum liegt hier der **komplette Quelltext offen**: Du (oder
jemand, dem du vertraust) kann nachlesen, dass das Programm

- deine Zugangsdaten **nur lokal** speichert (`~/.evcockpit/` auf deinem Rechner),
- **nichts** an den Autor oder irgendeine Webseite sendet,
- nur mit ausdrücklich eingerichteten Gegenstellen redet: der **BYD-Cloud** für die
  native BYD-Ansicht sowie optional deinem **Home Assistant**, **evcc** und lokalen
  Geräten im privaten Netz.

Es gibt genau **eine** freiwillige, standardmäßig **abgeschaltete** Ausnahme: einen
anonymen Zähl-Ping (nur „jemand hat es installiert" + Modell, **keine** IP, **kein**
Fahrzeug, **keine** Kennung), den du im Assistenten per Häkchen erlauben kannst. Such im
Code nach `PING_URL` — mehr verlässt deinen Rechner nicht.

**Bitte lege dir für dieses Tool einen zweiten BYD-Account an** und lade ihn in der
BYD-App als Zusatznutzer zum Auto ein. So gibst du deine Haupt-Zugangsdaten nicht aus der
Hand, und du kannst den Zugang jederzeit wieder entziehen.

---

## Loslegen

### Windows
1. Fertiges Paket herunterladen: **[Releases](../../releases)** → `ev-cockpit-windows.zip`
2. Entpacken, `Start.bat` doppelklicken.
3. Der Browser öffnet sich von selbst. Falls nicht: <http://127.0.0.1:8099>

Python ist im Windows-Paket enthalten — du musst nichts installieren.

### Linux / macOS / Raspberry Pi
```bash
git clone https://github.com/samuelvoltarius/byd-ev-cockpit.git
cd byd-ev-cockpit
./start.sh
```
`start.sh` legt beim ersten Start eine eigene Umgebung im Ordner an (`.venv/`) und lädt
die BYD-Bibliothek hinein — dein System bleibt unangetastet. Fehlt auf Debian/Ubuntu/
Raspberry Pi das venv-Paket, sagt dir das Skript den passenden `apt`-Befehl.

Danach im Browser: <http://127.0.0.1:8099>

---

## Home Assistant (optional)

Im Assistenten unter „Extras" aktivierbar. Das Auto taucht dann in Home Assistant von
selbst auf (MQTT-Discovery) — mit allen Werten und Schaltern. Braucht einen MQTT-Broker
(bei HA meist das Mosquitto-Add-on). Wer eine PV-Anlage in HA hat, kann seine
Solar-Leistung neben Ladestand und Strompreis anzeigen lassen — **nur lesend**.

## Wallboxen, PV-Anlagen und weitere Fahrzeuge (optional)

Das Cockpit liest die herstellerneutrale lokale API von [evcc](https://evcc.io/). Damit
funktionieren alle in evcc eingerichteten Wallboxen, Netz-/PV-/Batteriezähler und
Fahrzeuge unabhängig vom Hersteller — zum Beispiel go-e, BYD, VW oder Audi. Das Cockpit
sendet über diese Verbindung keine Lade- oder Fahrzeugbefehle.

Geräte ohne fertigen evcc-Adapter können in evcc als **benutzerdefiniertes Gerät** über
lokales HTTP, MQTT oder Modbus beschrieben werden. Das ist auch der saubere Weg für
Tuya-basierte Hardware: Sie benötigt eine dokumentierte lokale Schnittstelle oder eine
lokale Bridge wie Home Assistant/MQTT. Eine reine proprietäre Hersteller-Cloud kann nicht
sicher und wahrheitsgemäß als „universell unterstützt“ bezeichnet werden.

Im Cockpit die private IPv4-Adresse des evcc-Servers und dessen Port (normalerweise 7070)
eintragen. Aus Sicherheitsgründen werden nur RFC-1918-Adressen (`10/8`, `172.16/12`,
`192.168/16`) akzeptiert und HTTP-Weiterleitungen nicht verfolgt.

Fahrzeugprofile werden unter `~/.evcockpit/vehicles.json` gespeichert. Die lokale API
`POST /vehicles/profiles` erwartet `{"profiles": [...]}`; Zugangsdaten werden aus den
Profilen entfernt und niemals dort gespeichert.

## Routenplaner der BYD-Community (optional)

Mitglieder der [BYD-Community-Karte](https://byd.serveone.at) bekommen einen persönlichen Link zum
Routenplaner (`byd.serveone.at/ev/#z=…`). Im Assistenten eingefügt, passiert Folgendes:

- **Ladestand an den Planer:** Der Planer kennt dann den Start-Ladestand deines Autos. Gesendet wird nur der
  letzte Wert, kein Ort, nur wenn das Auto wach ist.
- **Fahrten melden** (eigenes Häkchen): Nach jeder Fahrt ohne Laden gehen Kilometer, Dauer, Ladestand
  vorher/nachher und Außentemperatur an den Planer — **keine Orte, keine Uhrzeit**. Daraus lernt er den echten
  Verbrauch deines Autos.
- Im Cockpit erscheint der Knopf **„Route planen"**. Der Link-Schlüssel bleibt auf deinem Rechner und steht nie in der Seite.

**Karte:** Das Cockpit zeigt standardmäßig dieselbe Karte wie Planer und Panoptes-App (vom Server der Community,
byd.serveone.at); solange der Server sie nicht vollständig liefert, OpenStreetMap. Ohne Häkchen „Karte im
Community-Look": immer OpenStreetMap. Die Kartenbibliotheken (MapLibre, PMTiles) liegen im Paket, kein CDN.

## Zwei Autos

Zweite Instanz mit eigenem Konfig-Ordner und Port starten:
```bash
EVCOCKPIT_CFGDIR=~/.evcockpit-zweitwagen EVCOCKPIT_PORT=8100 ./start.sh
```

## Einstellungen (Umgebungsvariablen)

| Variable | Standard | Bedeutung |
|---|---|---|
| `EVCOCKPIT_PORT` | `8099` | Port des Cockpits |
| `EVCOCKPIT_BIND` | `127.0.0.1` | Nur der eigene Rechner. Für LAN-Zugriff auf `0.0.0.0` setzen. |
| `EVCOCKPIT_CFGDIR` | `~/.evcockpit` | Wo Konfiguration und Zugangsdaten liegen |

---

## Was es braucht

- Ein BYD mit Cloud-Anbindung (BYD-App-Konto).
- Python 3.10+ (bei Linux/Mac), Windows-Paket bringt es mit.
- Steht auf den Schultern von [**pyBYD**](https://pypi.org/project/pybyd/) — ohne diese
  Bibliothek gäbe es das hier nicht.

## Grenzen — ehrlich

- Die native Fahrzeugsteuerung ist **an einem einzigen BYD getestet**. Andere Fahrzeuge
  werden über evcc nur lesend angezeigt; verfügbare Daten hängen vom jeweiligen Adapter ab. Rückmeldungen
  ([Issues](../../issues)) sehr willkommen.
- Der Dolphin Surf hat **keinen Innenraum-Temperaturfühler** — deshalb keine Innentemp
  und kein Thermostat. Klima wird über eine Zieltemperatur geschaltet, nicht geregelt.
- **Aufsperren gibt es bewusst nicht.** Ein Knopf im Browser, der dein Auto öffnet, wäre
  ein Einbruchswerkzeug für jeden, der an deinen Rechner kommt. Zusperren ist harmlos und
  ist drin.
- Klappt ein Befehl mal nicht: kurz warten und **einmal** nochmal — nicht hektisch
  mehrfach, das mag die BYD-Cloud nicht.

## Haftung

Freies, nicht-kommerzielles Community-Projekt, gebaut in der Freizeit, **ohne jede Gewähr** —
siehe [LICENSE](LICENSE). Nutzung auf eigene Verantwortung. Kein offizielles BYD-Produkt und
in keiner Weise mit BYD verbunden. „BYD" ist eine Marke der jeweiligen Rechteinhaber.

## Fragen & Fehler

Bitte [ein Issue aufmachen](../../issues) — das ist der beste Weg zum Betreuer, und es hilft
auch allen anderen.
