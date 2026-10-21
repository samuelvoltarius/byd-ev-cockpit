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

## Dein Auto in 3D

Statt einer Silhouette zeigt das Cockpit dein Modell in 3D: dieselben Modelle wie in Panoptes, in deiner Lackfarbe
(Farbknöpfe unter dem Auto). Das Modell (~1 MB) lädt das Cockpit einmal vom Community-Server, prüft es per Prüfsumme
und legt es auf deinem Rechner ab. Ein eigenes Foto hat Vorrang. Die Modelle stammen teils von Nazh Design (CC BY 4.0), teils sind es Eigenbauten des Panoptes-Projekts (CC0),
Details unter „Über“.

## Woher kommen die Daten? Du wählst

Gleich im zweiten Schritt des Assistenten fragt das Cockpit, woher es die Werte deines Autos holen soll:

- **BYD-Konto:** über die BYD-Cloud, mit einem eigenen zweiten Konto (siehe oben). Für die meisten am einfachsten.
- **Home Assistant:** Dein Auto ist dort schon drin, z. B. über eine BYD-Integration oder Panoptes. Adresse und
  Zugriffs-Token eintragen, „Mein Auto suchen“ drücken. Das Cockpit schlägt Ladestand, Reichweite, Kilometerstand,
  Laden und Standort selbst vor, du bestätigst nur. Es liest nur und fragt dann **nie** zusätzlich die BYD-Cloud ab
  (zwei Abfrager auf einem Konto stören sich, Fehler 6024).
- **Panoptes im Auto:** direkt von der Panoptes-App auf dem Infotainment (siehe unten).

Ein BYD-Konto ist bei Home Assistant und Panoptes nur noch **optional**, für Fernbefehle wie Vorklimatisieren.

## Home Assistant (optional)

Zusätzlich (unter „Extras"): Werte und Schalter an Home Assistant senden. Das Auto taucht dann in Home Assistant von
selbst auf (MQTT-Discovery) — mit allen Werten und Schaltern. Braucht einen MQTT-Broker
(bei HA meist das Mosquitto-Add-on). Wer eine PV-Anlage in HA hat, kann seine
Solar-Leistung neben Ladestand und Strompreis anzeigen lassen — **nur lesend**.

## Wallboxen, PV-Anlagen und weitere Fahrzeuge (optional)

Das Cockpit liest die herstellerneutrale lokale API von [evcc](https://evcc.io/). Damit
funktionieren alle in evcc eingerichteten Wallboxen, Netz-/PV-/Batteriezähler und
Fahrzeuge unabhängig vom Hersteller — zum Beispiel go-e, BYD, VW oder Audi.

**Steuern (nur wenn du es willst):** Standardmäßig liest das Cockpit nur. Je Ladepunkt kannst du
„Steuern erlauben“ antippen. Dann darf das Cockpit über evcc genau zwei Dinge ändern: den
**Lademodus** (Aus / Sofort / Min+PV / PV) und den **Ziel-Ladestand**. Nach jeder Änderung liest es bei
evcc nach und zeigt, ob sie übernommen wurde. Alles andere (Phasen, Stromstärke, Schutz) regelt evcc
selbst. go-e und Shelly werden direkt nur gelesen, nie geschaltet.

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

## Daten direkt von Panoptes im Auto (optional)

Läuft die Panoptes-App (vormals SurfMate) im Auto, holt das Cockpit Ladestand, Kilometer, Standort,
Gang, Schloss und Außentemperatur direkt von dort (Heimnetz oder Tailscale, Port 8180) — jede Minute,
ohne die BYD-Cloud zu belasten. Im Assistenten die Adresse des Autos eintragen und **„Mit Panoptes verbinden“**
drücken: Das Cockpit zeigt eine vierstellige Prüfzahl, du erlaubst in **Telegram** oder in der Panoptes-Seite
„Gekoppelte Geräte“ mit einem Tipp (ab Panoptes 0.1.7). Kein Code abtippen. Ältere Panoptes (ab 0.1.5) koppelst
du unter „Erweitert“ mit dem Kopplungs-Code oder dem Link aus „Neues Gerät koppeln“. Die Kopplung erneuert sich
täglich von selbst und lässt sich in Panoptes jederzeit entfernen. Ist das Auto aus oder nicht erreichbar, fragt das Cockpit
wie bisher die BYD-Cloud. **Steuern (Klima, Schloss, Laden) läuft weiterhin über die BYD-Cloud.**

**Fernbefehle nur bei ausgeschaltetem Auto:** Vor jedem Befehl fragt das Cockpit frisch nach, ob das Auto aus ist
(über Panoptes bzw. die BYD-Cloud). Ist es an, steht nicht in P oder ist der Zustand unklar, wird der Befehl
nicht gesendet. Grund: Ein Cloud-Befehl kann ein eingeschaltetes Auto komplett abschalten.

## Routenplaner der BYD-Community (optional)

Mitglieder der [BYD-Community-Karte](https://byd.serveone.at) verbinden das Cockpit im Assistenten mit
**„Mit Routenplaner verbinden“**: Das Cockpit zeigt einen Code und einen Link, du meldest dich auf `/ev/` an und
tippst auf „Erlauben“. Das Cockpit bekommt einen eigenen Geräte-Schlüssel mit begrenzten Rechten (widerrufbar
unter „Meine Geräte“). Der alte persönliche Link (`byd.serveone.at/ev/#z=…`) geht weiter unter „Erweitert“. Danach:

- **Ladestand an den Planer:** Der Planer kennt dann den Start-Ladestand deines Autos. Gesendet wird nur der
  letzte Wert, kein Ort, nur wenn das Auto wach ist.
- **Echten Verbrauch lernen** (eigenes Häkchen): Deine Fahrten bleiben auf deinem Rechner. Nach jeder Fahrt
  ohne Laden fragt das Cockpit beim Planer nur den Modellwert ab (Kilometer, Dauer, Außentemperatur; dort wird
  nichts gespeichert), rechnet daraus deinen Korrekturfaktor und schickt **nur diese eine Zahl**.
- Ist **Panoptes im Auto gekoppelt**, meldet Panoptes Ladestand und Faktor selbst; das Cockpit schickt dann
  nichts (je Auto nur eine Quelle). Jede Meldung trägt eine zufällige Fahrzeug-Kennung, nie die VIN.
- Im Cockpit erscheint der Knopf **„Route planen"**: Er öffnet direkt im Cockpit denselben Planer wie
  `byd.serveone.at/ev/` mit deinem Login. Routen, Fahrzeuge und „An Auto senden“ sind dieselben wie dort.
  Auf der Startseite steht die bereitliegende Route (Strecke, Ladestopps, Ankunft) und die **Rückmeldung aus
  dem Auto** („im Auto angekommen“, „Navigation läuft“). Ins Auto kommt die Route über Panoptes; ohne
  Panoptes über den Handy-Link des Planers. Der Link-Schlüssel bleibt auf deinem Rechner und steht nie in der Seite.
- **💳 Meine Ladekarten:** Unter „Routenplaner“ hakst du an, welche Ladekarten du hast. Die Liste liegt beim
  Planer (nur welche Karten, keine Ladevorgänge) und gilt genauso auf `/ev/`. Die Säulen auf der Karte zeigen dann
  den Preis deiner Karte, der Planer bevorzugt passende Ladestopps.

**Karte:** Das Cockpit zeigt standardmäßig dieselbe Karte wie Planer und Panoptes-App (vom Server der Community,
byd.serveone.at); solange der Server sie nicht vollständig liefert, OpenStreetMap. Ohne Häkchen „Karte im
Community-Look": immer OpenStreetMap. Die Kartenbibliotheken (MapLibre, PMTiles) liegen im Paket, kein CDN.
Mit Häkchen „Ladesäulen" zeigt die Community-Karte die **Live-Belegung** (derzeit Österreich, Schweiz und Deutschland, über den Planer; Quelle und Lizenz stehen unten in der Karte):
frei normal, belegt **rot**, außer Betrieb grau, Status unbekannt grau mit „?“ (Quelle steht unten in der Karte). Dafür geht nur der auf ~5 km gerundete Kartenmittelpunkt per POST
an den Planer (kein Zugriffslog), höchstens alle 2 Minuten je Gebiet.

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
- Das Steuern von Ladepunkten über evcc (Modus, Ziel-Ladestand) ist bisher nur gegen ein nachgebautes evcc
  getestet, noch nicht an einer echten Wallbox.
- Der Dolphin Surf hat **keinen Innenraum-Temperaturfühler** — deshalb keine Innentemp
  und kein Thermostat. Klima wird über eine Zieltemperatur geschaltet, nicht geregelt.
- **Aufsperren gibt es bewusst nicht.** Ein Knopf im Browser, der dein Auto öffnet, wäre
  ein Einbruchswerkzeug für jeden, der an deinen Rechner kommt. Zusperren ist harmlos und
  ist drin.
- Klappt ein Befehl mal nicht: kurz warten und **einmal** nochmal — nicht hektisch
  mehrfach, das mag die BYD-Cloud nicht.

## Hinweise / Haftung

**DE:** Privates Freizeitprojekt, kostenlos und ohne Gewähr. Nutzung auf eigenes Risiko und nur privat mit dem eigenen Fahrzeug. Für eine rechtmäßige Nutzung (Datenschutz, Kamera-Aufnahmen, Fernbefehle, Straßenverkehr) sind allein die Nutzer verantwortlich. Wächter-Aufnahmen sind nur für den eigenen Privatgrund gedacht, ohne öffentlichen Raum oder Nachbargrund. Soweit gesetzlich zulässig, übernimmt der Entwickler keine Haftung; Haftung für Vorsatz, grobe Fahrlässigkeit, Personenschäden und zwingende Verbraucherrechte bleiben unberührt. Nicht mit BYD verbunden; alle Marken gehören ihren Inhabern. Siehe auch LICENSE.

**EN:** Private hobby project, free and without warranty. Use at your own risk, for private use with your own vehicle only. Users alone are responsible for lawful use (data protection, camera recordings, remote commands, traffic rules). Guardian recordings are intended for your own private property only, without capturing public space or neighbouring property. To the extent permitted by law, the developer accepts no liability; liability for intent, gross negligence, personal injury and mandatory consumer rights remains unaffected. Not affiliated with BYD; all trademarks belong to their owners. See also LICENSE.

Der Einrichtungs-Assistent zeigt diese Hinweise im ersten Schritt; weiter geht es erst mit Häkchen.

## Fragen & Fehler

Bitte [ein Issue aufmachen](../../issues) — das ist der beste Weg zum Betreuer, und es hilft
auch allen anderen.
