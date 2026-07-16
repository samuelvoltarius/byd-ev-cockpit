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
- nur mit **zwei** Gegenstellen redet: der **BYD-Cloud** (dein Auto) und — nur wenn du es
  einschaltest — **deinem eigenen Home Assistant**.

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

- **Getestet an einem einzigen Auto.** Andere BYD-Modelle: ungetestet. Rückmeldungen
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
