"""Baut die Projektseite byd.serveone.at/panoptes/ (DE + EN) nach website/panoptes/.

Aufruf: python website/bau_panoptes.py <ordner-mit-screenshots>
Inhalt: von Alfred abgenommene Panoptes-README + DISCLAIMER.md Fassung 1. Bilder: 24 Screenshots (hell/dunkel,
PC/Handy), Musterdaten. Die Seite folgt hell/dunkel dem Geraet; die Screenshots wechseln passend mit.
"""
import html
import os
import shutil
import sys

HIER = os.path.dirname(os.path.abspath(__file__))
ZIEL = os.path.join(HIER, "panoptes")
VORSCHAU = ""                   # mit --vorschau: noindex (Vorschau unter nicht verlinktem Pfad)
NAME = "Alfred Aigner"
QUELLE = ""                      # Ordner mit den Screenshots (aus main())          # laut Impressum (Medieninhaber), fuer den Haftungstext

T = {
    "de": {
        "lang": "de", "andere": "en/", "andere_name": "English", "pfad": "",
        "title": "Panoptes – die Community-App für deinen BYD",
        "desc": "Panoptes ist eine kostenlose Community-App für BYD-Autos mit DiLink 3, 4 und 5: Wächter mit Kamera, Fernzugang, Telegram-Meldungen, Karte mit Ladesäulen und Verbindung zum Routenplaner.",
        "zurueck": "← BYD EU Community",
        "eyebrow": "Kostenlos · für BYD mit DiLink 3, 4 und 5 · Community-Projekt",
        "h1a": "Panoptes", "h1b": "dein BYD, wach und vernetzt",
        "sub": "Eine App, die direkt am Bildschirm in deinem Auto läuft. Dazu eine Oberfläche, die du am Handy oder PC öffnest: Wächter mit Kamera, Fernzugang, Meldungen über Telegram, eine eigene Karte mit Ladesäulen und die Verbindung zum Routenplaner.",
        "wichtig": "<b>Wichtig:</b> Panoptes ist ein privates Freizeitprojekt und nicht von BYD. Bitte lies die <a href=\"hinweise.html\">Hinweise</a>, bevor du es installierst.",
        "hero_alt_pc": "Panoptes-Startseite am PC: Ladestand, Reichweite, Karte und Ladekosten",
        "hero_alt_handy": "Panoptes-Startseite am Handy: Ladestand und Reichweite",
        "h_kann": "Was Panoptes kann",
        "kann": [
            ("🚗", "Am Bildschirm im Auto", "Panoptes läuft als eigene App im Vollbild, mit großen Tasten. Während der Fahrt sind Einstellungen gesperrt; Start, Karte und Wächter bleiben erreichbar."),
            ("🛡️", "Wächter mit KI-Erkennung", "Steht dein Auto, achten die Kameras auf das Umfeld. Du entscheidest selbst, wann aufgenommen wird: nur bei Erschütterung, mit KI-Erkennung überall oder nur an deinen privaten Orten wie Garage oder Einfahrt. Damit die Batterien geschont werden, legt sich der Wächter auf Wunsch schlafen."),
            ("🌍", "Fernzugang", "Über Tailscale erreichst du dein Auto von überall. Eingerichtet wird das mit einem QR-Code am Bildschirm im Auto und deinem eigenen Tailscale-Konto."),
            ("💬", "Meldungen über Telegram", "Dein eigener Bot meldet Wächter-Ereignisse, Laden, schwache Starterbatterie, Reifendruck und Updates. Jede Meldung einzeln schaltbar, mit Ruhezeit für die Nacht. Bilder und Videos nur, wenn du das einschaltest."),
            ("🗺️", "Karte mit Ladesäulen", "Du wählst selbst, woher die Karte kommt: vom Community-Server (mit Gelände und freien Ladeplätzen, wo Betreiber Daten liefern), von OpenStreetMap oder gar nicht. Solange du nichts wählst, bleibt die Karte leer."),
            ("🔋", "„Reicht es noch?“", "Mit einer Route aus dem Routenplaner sagt dir Panoptes unterwegs, ob der Akku bis zum nächsten Stopp reicht, und schlägt bei Bedarf einen Ladestopp vor."),
            ("📊", "Monatsbericht", "Gefahrene Kilometer, Verbrauch, Laden und Kosten, Standverlust und Wächter-Ereignisse eines Monats auf einen Blick, auch zum Drucken. Gerechnet wird im Auto."),
            ("📒", "Fahrten und Laden", "Fahrten, Verbrauch und Ladekosten werden im Auto mitgeschrieben und übersichtlich angezeigt."),
            ("🧭", "Verbindung zum Routenplaner", "Panoptes lässt sich mit deinem Konto auf <a href=\"/ev/\">byd.serveone.at/ev/</a> verbinden: Code am Auto anzeigen, am Handy bestätigen, fertig. Jederzeit trennbar."),
            ("🖥️", "EV-Cockpit am PC", "Das <a href=\"/ev-cockpit/\">EV-Cockpit</a> zeigt die Daten von Panoptes am PC und kann die Einstellungen ändern. Koppeln bestätigst du mit einem Tipp und einer vierstelligen Prüfzahl."),
            ("⬆️", "Updates in der App", "Panoptes sucht auf Wunsch selbst nach neuen Versionen. Installiert wird nur, wenn das Auto steht und die Zündung aus ist."),
            ("🌐", "Fünf Sprachen", "Deutsch, Englisch, Französisch, Italienisch und Niederländisch. Home Assistant kommt bald."),
        ],
        "h_bilder": "So sieht Panoptes aus",
        "bilder_lead": "Panoptes 0.1.8 am Bildschirm im Auto, am PC und am Handy. Wo es beide Fassungen gibt, folgen die Bilder hell oder dunkel deinem Gerät. Klick auf ein Bild zum Vergrößern. Alle Bilder zeigen Musterdaten (Musterstandort Wien).",
        "bilder": [
            ("Am Bildschirm im Auto: Start mit Ladestand, Reichweite und Schnellzugriffen.", [("start", "display", "Panoptes am Bildschirm im Auto: Start mit Ladestand und Reichweite")]),
            ("Wächter: Du wählst selbst, wann aufgenommen wird.", [("waechter", "display", "Wächter am Bildschirm im Auto mit der Wahl, wann aufgenommen wird"), ("waechter", "handy", "Wächter am Handy")]),
            ("Karte mit Ladesäulen und freien Plätzen, aus der Quelle, die du gewählt hast.", [("karte", "pc", "Karte mit Ladesäulen am PC"), ("karte", "display", "Karte am Bildschirm im Auto")]),
            ("Kartenquelle: Community-Server, OpenStreetMap oder keine. Ohne Wahl bleibt die Karte leer.", [("kartenquelle", "display", "Auswahl der Kartenquelle: Community-Server, OpenStreetMap oder keine")]),
            ("Monatsbericht: Kilometer, Verbrauch, Laden, Standverlust und Wächter eines Monats.", [("monatsbericht", "pc", "Monatsbericht am PC"), ("monatsbericht", "display", "Monatsbericht am Bildschirm im Auto")]),
            ("Gerät koppeln: das EV-Cockpit mit Prüfzahl erlauben.", [("geraete", "pc", "Gerät koppeln: das EV-Cockpit möchte sich verbinden, Prüfzahl 4711")]),
            ("Telegram: jede Meldungsart einzeln.", [("telegram", "handy", "Telegram-Meldungen am Handy, jede Art einzeln schaltbar")]),
        ],
        "handy": "am Handy", "pc": "am PC",
        "h_zus": "Wie alles zusammenhängt",
        "zus_lead": "Panoptes läuft im Auto. Alles andere ist freiwillig und lässt sich einzeln verbinden und wieder trennen.",
        "svg": {"auto": "Panoptes", "auto2": "im Auto", "cockpit": "EV-Cockpit", "cockpit2": "am PC", "planer": "Routenplaner", "planer2": "byd.serveone.at/ev/",
                "karte": "Community-Karte", "karte2": "Kacheln, Ladesäulen", "tg": "Telegram-Bot", "tg2": "dein eigener", "ha": "Home Assistant", "ha2": "bald",
                "t1": "Kopplung", "t2": "Konto, Ziel, Fahrtenbuch E2E", "t3": "Karte (wenn gewählt)", "t4": "Meldungen", "t5": "bald", "t6": "Route, Ladekarten",
                "aria": "Grafik: Panoptes im Auto in der Mitte, verbunden mit EV-Cockpit am PC, Routenplaner, Community-Karte, Telegram-Bot und bald Home Assistant"},
        "verb": [
            ("1", "Panoptes ↔ EV-Cockpit (Kopplung)", "Du erlaubst das Cockpit einmal mit einer Prüfzahl, in Telegram oder auf der Panoptes-Seite. Dann holt das Cockpit Fahrzeugwerte, Einstellungen und das Fahrtenbuch direkt aus dem Auto, über dein Heimnetz oder Tailscale.",
             "Nicht dabei: Fernzugang, Passwort und Anschlüsse. Nichts davon läuft über unsere Server, das Fahrtenbuch bleibt auf deinem PC. Den Zugang hebt das Cockpit im Schlüsselbund deines Rechners auf. Was es sonst an Server schickt (Karte, 3D-Modell, Routenplaner, Zählung), entscheidest du mit eigenen Häkchen; ohne Häkchen nichts."),
            ("2", "Panoptes ↔ Routenplaner", "Nach dem Verbinden kommt dein Ziel mit Ladestopps ins Auto. Panoptes meldet Ladestand, Verbrauchsfaktor und Fahrstatus, damit der Plan stimmt. Schaltest du es ein (standardmäßig aus) und rufst auf /ev/ dein Fahrtenbuch ab, kommt es Ende-zu-Ende verschlüsselt direkt vom Auto in deinen Browser.",
             "Nicht dabei: Der Server kann das Fahrtenbuch nicht lesen; er bekommt nur verschlüsselte Daten und hält sie laut Routenplaner höchstens 2 Minuten im Arbeitsspeicher. Die ungefähre Position geht nur mit, wenn Panoptes unterwegs einen neuen Ladestopp vorschlägt."),
            ("3", "Panoptes ↔ Community-Karte", "Wenn du sie als Kartenquelle wählst, kommen Kartenkacheln und Ladesäulen-Daten von byd.serveone.at, mit Live-Belegung, wo es offene Daten gibt. Ohne Wahl lädt Panoptes keine Karte.",
             "Nicht dabei: Fahrten und Aufnahmen. Der Server sieht nur deine IP-Adresse und den Kartenausschnitt. Geteilte Regeln gehen nur an den Community-Server, wenn du sie selbst teilst (standardmäßig aus)."),
            ("4", "Panoptes → Telegram", "Dein eigener Bot schickt dir Meldungstexte. Bilder und Videos nur, wenn du das ausdrücklich einschaltest; dann liegen sie auf den Servern von Telegram.",
             "Nicht dabei: Keine Videos auf unseren Servern, kein Umweg über das Projekt."),
            ("5", "Panoptes ↔ Home Assistant (bald)", "Geplant ist eine direkte Verbindung zwischen deinem Auto und deinem eigenen Home Assistant.",
             "Nicht dabei: Die Daten sollen nicht bei uns liegen."),
            ("6", "EV-Cockpit ↔ Routenplaner", "Das Cockpit zeigt die bereitliegende Route und deine Ladekarten. Ist es mit Panoptes gekoppelt, meldet nur Panoptes den Ladestand, damit nichts doppelt ankommt.",
             "Nicht dabei: Deine Fahrten bleiben auf dem PC."),
        ],
        "nicht": "Was nicht fließt",
        "h_ds": "Datenschutz: was wohin geht",
        "ds_lead": "Grundsatz: Deine Aufnahmen, Fahrten und Positionen bleiben im Auto. Panoptes schickt keine Kamera-Aufnahmen an die Server des Projekts. Was Daten nach außen schickt, ist standardmäßig aus; du schaltest es einzeln ein, und Panoptes sagt dir vorher, wohin die Daten gehen. Es gibt keine Werbung und kein Tracking.",
        "ds_kopf": ("Wohin", "Was", "Wann"),
        "ds": [
            ("Im Auto (USB-Stick, App)", "Wächter-Aufnahmen, Fahrtenbuch, Ladeverlauf, Monatsbericht, Einstellungen", "immer. Bei neuer Einrichtung löscht Panoptes Aufnahmen nach 72 Stunden, einzelne kannst du behalten."),
            ("Kartenquelle (Community-Server byd.serveone.at oder OpenStreetMap Deutschland)", "Deine IP-Adresse und der Kartenausschnitt, also ungefähr, wo dein Auto steht. Beim Community-Server zusätzlich die Abfrage freier Ladeplätze für den Ausschnitt.", "erst, wenn du unter System → Kartenquelle eine Quelle wählst. Am Bildschirm im Auto gilt die Wahl fürs ganze Auto; Handy und PC fragen getrennt."),
            ("Telegram", "Meldungstexte; Bilder und Videos nur, wenn du das einschaltest (dann liegen sie bei Telegram)", "nur mit eigenem Bot"),
            ("Tailscale", "Verbindung für den Fernzugang", "nur mit eingerichtetem Fernzugang"),
            ("Routenplaner (byd.serveone.at/ev)", "Ladestand, Verbrauchsfaktor, Fahrstatus; die ungefähre Position nur für einen neu vorgeschlagenen Ladestopp. Das Fahrtenbuch nur, wenn du es einschaltest (standardmäßig aus) und auf /ev/ selbst abrufst: Ende-zu-Ende verschlüsselt, der Server bekommt nur verschlüsselte Daten und hält sie laut Routenplaner höchstens 2 Minuten im Arbeitsspeicher.", "nur nach dem Verbinden, jederzeit trennbar"),
            ("Community-Server (byd.serveone.at/community)", "geteilte Regeln, nur wenn du sie teilst", "standardmäßig aus"),
            ("Open-Meteo", "ungefähre Position für das Wetter", "nur mit deiner Einwilligung, standardmäßig aus"),
            ("Weitere Dienste (BYD-Konto, MQTT/Smart Home, ABRP, Stadia Maps, KI-Assistent)", "je nach Dienst; an der Eingabe steht, wohin deine Anfragen gehen", "nur, wenn du sie selbst einrichtest"),
        ],
        "h_brauch": "Was du brauchst",
        "brauch": [
            "Einen BYD mit DiLink 3, 4 oder 5 und Android 9 oder neuer am Bildschirm im Auto.",
            "Getestet ist Panoptes bisher vor allem mit dem <b>BYD Dolphin Surf (DiLink 3)</b>. Auf anderen Modellen kann manches fehlen oder anders sein; was dein Auto nicht kann, blendet Panoptes aus.",
            "Speicherplatz für die Kamera-Aufnahmen, am besten einen USB-Stick im Auto.",
            "Für den Fernzugang ein kostenloses Tailscale-Konto, für Meldungen einen eigenen Telegram-Bot. Panoptes zeigt dir, wie das geht.",
        ],
        "h_dl": "Herunterladen und installieren",
        "dl_bald": "Bald",
        "dl_text": "Die fertige App und eine Schritt-für-Schritt-Anleitung, wie sie auf die verschiedenen BYD-Modelle kommt, folgen hier. Je nach Modell und Software-Stand ist der Weg unterschiedlich.",
        "dl_code": "Der Quellcode kommt nach der Open-Source-Freigabe auf GitHub, unter der MIT-Lizenz.",
        "h_hinweise": "Hinweise",
        "hinweise_kurz": "Privates Freizeitprojekt, kostenlos und ohne Gewähr. Nutzung auf eigenes Risiko und nur privat mit dem eigenen Fahrzeug. Für eine rechtmäßige Nutzung (Datenschutz, Kamera-Aufnahmen, Fernbefehle, Straßenverkehr) sind allein die Nutzer verantwortlich. Wächter-Aufnahmen sind nur für den eigenen Privatgrund gedacht, ohne öffentlichen Raum oder Nachbargrund. Soweit gesetzlich zulässig, übernimmt der Entwickler keine Haftung; Haftung für Vorsatz, grobe Fahrlässigkeit, Personenschäden und zwingende Verbraucherrechte bleiben unberührt. Nicht mit BYD verbunden; alle Marken gehören ihren Inhabern.",
        "alle_hinweise": "Alle Hinweise lesen",
        "h_links": "Mehr aus der Community",
        "links": [("/ev/", "🧭 Routenplaner"), ("/ev-cockpit/", "🖥️ EV-Cockpit"), ("/", "🗺️ Community-Karte")],
        "footer": "Privates Freizeitprojekt, ohne Gewähr, nicht mit BYD verbunden. Nutzung auf eigenes Risiko.",
        "f_hinweise": "Hinweise", "f_impressum": "Impressum", "f_datenschutz": "Datenschutz",
        "lizenz": "Kartendaten © OpenStreetMap-Mitwirkende (ODbL). 3D-Automodelle teils von Nazh (CC BY 4.0), teils selbst erstellt (CC0).",
        # Hinweis-Seite (DISCLAIMER.md Fassung 1, Grundtext)
        "hw_title": "Wichtige Hinweise – Panoptes, EV-Cockpit, Routenplaner",
        "hw_h1": "Wichtige Hinweise",
        "hw_stand": "Gilt für Panoptes, das EV-Cockpit und den Routenplaner. Stand 21.10.2026.",
        "hw": [
            ("Freizeitprojekt.", "Panoptes, das EV-Cockpit und der Routenplaner sind ein privates Freizeitprojekt von {name}. Sie werden kostenlos und ohne Gewähr angeboten."),
            ("Ohne Gewähr.", "Es gibt keine Garantie, dass alles fehlerfrei, vollständig oder jederzeit verfügbar ist. Das gilt auch für Ladestände, Reichweiten, Preise, Belegung von Ladesäulen, Routen, Blitzer- und Gefahrenhinweise. Prüfe Wichtiges selbst; im Straßenverkehr gilt immer, was du siehst und was die Schilder sagen."),
            ("Eigenes Risiko.", "Du nutzt alles auf eigenes Risiko. Soweit gesetzlich zulässig, übernimmt {name} keine Haftung für Schäden, die aus der Nutzung entstehen, auch nicht für Schäden am Fahrzeug, an Daten oder durch Fernbefehle."),
            ("Du bist verantwortlich.", "Du allein entscheidest, wie du die Funktionen einsetzt, und bist dafür verantwortlich, dass das erlaubt ist. Das betrifft vor allem Datenschutz, Kamera-Aufnahmen, Fernbefehle über das BYD-Konto und die Regeln im Straßenverkehr."),
            ("Nur privat.", "Gedacht ist alles nur für die private Nutzung mit deinem eigenen Fahrzeug. Ein gewerblicher Einsatz (z. B. Flotten, Vermietung, Taxi, Firmenwagen-Überwachung) ist nicht vorgesehen."),
            ("Wächter nur auf eigenem Grund.", "Kamera-Aufnahmen des Wächters sind für deinen eigenen Privatgrund gedacht (z. B. Garage, Einfahrt). Richte die Kameras so aus, dass weder öffentlicher Raum (Straße, Gehweg, öffentlicher Parkplatz) noch das Grundstück der Nachbarn erfasst wird. Aufnahmen nicht veröffentlichen."),
            ("Nicht von BYD.", "Dieses Projekt ist nicht mit BYD verbunden und wird von BYD weder unterstützt noch geprüft. „BYD“, „DiLink“ und alle anderen genannten Namen und Marken gehören ihren jeweiligen Inhabern."),
            ("Gesetzliche Rechte bleiben.", "Die Haftung für Vorsatz und grobe Fahrlässigkeit, für Personenschäden sowie zwingende Rechte von Verbraucherinnen und Verbrauchern werden durch diese Hinweise nicht eingeschränkt."),
        ],
        "hw_zurueck": "← Zurück zu Panoptes",
    },
    "en": {
        "lang": "en", "andere": "../", "andere_name": "Deutsch", "pfad": "../",
        "title": "Panoptes – the community app for your BYD",
        "desc": "Panoptes is a free community app for BYD cars with DiLink 3, 4 and 5: camera guard, remote access, Telegram notifications, a map with chargers and a link to the route planner.",
        "zurueck": "← BYD EU Community",
        "eyebrow": "Free · for BYD with DiLink 3, 4 and 5 · community project",
        "h1a": "Panoptes", "h1b": "your BYD, awake and connected",
        "sub": "An app that runs right on your car's screen, plus an interface you open on your phone or PC: a camera guard, remote access, Telegram notifications, its own map with chargers and a link to the route planner.",
        "wichtig": "<b>Important:</b> Panoptes is a private hobby project and not made by BYD. Please read the <a href=\"hinweise.html\">notes</a> before installing it.",
        "hero_alt_pc": "Panoptes home on a PC: charge level, range, map and charging costs",
        "hero_alt_handy": "Panoptes home on a phone: charge level and range",
        "h_kann": "What Panoptes does",
        "kann": [
            ("🚗", "On the car screen", "Panoptes runs as its own full-screen app with large buttons. While driving, settings are locked; home, map and guard stay available."),
            ("🛡️", "Guard with AI detection", "While your car is parked, the cameras watch its surroundings. You decide when it records: only on impact, with AI detection everywhere, or only at your own private places such as your garage or driveway. To protect the batteries, the guard can go to sleep."),
            ("🌍", "Remote access", "Reach your car from anywhere via Tailscale. Setup uses a QR code on the car screen and your own Tailscale account."),
            ("💬", "Telegram notifications", "Your own bot reports guard events, charging, a weak starter battery, tyre pressure and updates. Each kind can be switched on its own, with quiet hours for the night. Pictures and videos only if you turn that on."),
            ("🗺️", "Map with chargers", "You choose where the map comes from: the community server (with terrain and free charging spots where operators provide data), OpenStreetMap, or none. Until you choose, the map stays empty."),
            ("🔋", "\u201cWill it make it?\u201d", "With a route from the route planner, Panoptes tells you on the road whether the battery will last to the next stop and suggests a charging stop if needed."),
            ("📊", "Monthly report", "Distance, consumption, charging and costs, standby loss and guard events of a month at a glance, also for printing. Calculated in the car."),
            ("📒", "Trips and charging", "Trips, consumption and charging costs are recorded in the car and shown clearly."),
            ("🧭", "Route planner link", "Connect Panoptes to your account on <a href=\"/ev/\">byd.serveone.at/ev/</a>: show a code in the car, confirm on your phone, done. Disconnect at any time."),
            ("🖥️", "EV Cockpit on your PC", "The <a href=\"/ev-cockpit/\">EV Cockpit</a> shows Panoptes data on your PC and can change its settings. You confirm the pairing with one tap and a four-digit check number."),
            ("⬆️", "Updates in the app", "If you like, Panoptes looks for new versions itself. Installing only happens while the car is parked with the ignition off."),
            ("🌐", "Five languages", "German, English, French, Italian and Dutch. Home Assistant is coming soon."),
        ],
        "h_bilder": "What Panoptes looks like",
        "bilder_lead": "Panoptes 0.1.8 on the car screen, on a PC and on a phone. Where both versions exist, the pictures follow your device's light or dark setting. Click a picture to enlarge it. All pictures show sample data (sample location Vienna) and the German interface.",
        "bilder": [
            ("On the car screen: home with charge level, range and quick actions.", [("start", "display", "Panoptes on the car screen: home with charge level and range")]),
            ("Guard: you choose when it records.", [("waechter", "display", "Guard on the car screen with the choice of when it records"), ("waechter", "handy", "Guard on a phone")]),
            ("Map with chargers and free spots, from the source you chose.", [("karte", "pc", "Map with chargers on a PC"), ("karte", "display", "Map on the car screen")]),
            ("Map source: community server, OpenStreetMap or none. Without a choice the map stays empty.", [("kartenquelle", "display", "Choosing the map source: community server, OpenStreetMap or none")]),
            ("Monthly report: distance, consumption, charging, standby loss and guard events of a month.", [("monatsbericht", "pc", "Monthly report on a PC"), ("monatsbericht", "display", "Monthly report on the car screen")]),
            ("Pair a device: allow the EV Cockpit with a check number.", [("geraete", "pc", "Pairing: the EV Cockpit wants to connect, check number 4711")]),
            ("Telegram: every kind of message on its own.", [("telegram", "handy", "Telegram notifications on a phone, each kind switchable")]),
        ],
        "handy": "on a phone", "pc": "on a PC",
        "h_zus": "How it all fits together",
        "zus_lead": "Panoptes runs in the car. Everything else is optional and can be connected and disconnected one by one.",
        "svg": {"auto": "Panoptes", "auto2": "in the car", "cockpit": "EV Cockpit", "cockpit2": "on your PC", "planer": "Route planner", "planer2": "byd.serveone.at/ev/",
                "karte": "Community map", "karte2": "tiles, chargers", "tg": "Telegram bot", "tg2": "your own", "ha": "Home Assistant", "ha2": "soon",
                "t1": "pairing", "t2": "account, destination, trip log E2E", "t3": "map (if chosen)", "t4": "notifications", "t5": "soon", "t6": "route, charge cards",
                "aria": "Diagram: Panoptes in the car in the middle, connected to the EV Cockpit on a PC, the route planner, the community map, a Telegram bot and, soon, Home Assistant"},
        "verb": [
            ("1", "Panoptes ↔ EV Cockpit (pairing)", "You allow the cockpit once with a check number, in Telegram or on the Panoptes page. The cockpit then fetches vehicle data, settings and the trip log straight from the car, over your home network or Tailscale.",
             "Not included: remote access, password and ports. None of this goes through our servers; the trip log stays on your PC. The cockpit keeps the access key in your computer's keyring. Anything else it sends to servers (map, 3D model, route planner, usage count) needs its own tick; without a tick, nothing."),
            ("2", "Panoptes ↔ route planner", "Once linked, your destination with charging stops goes into the car. Panoptes reports charge level, consumption factor and driving status so the plan is right. If you turn it on (off by default) and fetch your trip log on /ev/, it comes end-to-end encrypted straight from the car to your browser.",
             "Not included: the server cannot read the trip log; it only receives encrypted data and, according to the route planner, keeps it in memory for 2 minutes at most. Your approximate position is only sent when Panoptes suggests a new charging stop on the road."),
            ("3", "Panoptes ↔ community map", "If you choose it as map source, map tiles and charger data come from byd.serveone.at, with live availability where open data exists. Without a choice Panoptes loads no map.",
             "Not included: trips and recordings. The server only sees your IP address and the map area. Shared rules only go to the community server if you share them yourself (off by default)."),
            ("4", "Panoptes → Telegram", "Your own bot sends you message texts. Pictures and videos only if you explicitly turn that on; they are then stored on Telegram's servers.",
             "Not included: no videos on our servers, no detour through the project."),
            ("5", "Panoptes ↔ Home Assistant (soon)", "A direct connection between your car and your own Home Assistant is planned.",
             "Not included: the data is not meant to be stored with us."),
            ("6", "EV Cockpit ↔ route planner", "The cockpit shows the route waiting for you and your charge cards. When it is paired with Panoptes, only Panoptes reports the charge level, so nothing arrives twice.",
             "Not included: your trips stay on your PC."),
        ],
        "nicht": "What does not flow",
        "h_ds": "Privacy: what goes where",
        "ds_lead": "Principle: your recordings, trips and positions stay in the car. Panoptes does not send camera recordings to the project's servers. Anything that sends data out is off by default; you turn each item on separately, and Panoptes tells you beforehand where the data goes. No ads, no tracking.",
        "ds_kopf": ("Where", "What", "When"),
        "ds": [
            ("In the car (USB stick, app)", "guard recordings, trip log, charging history, monthly report, settings", "always. On a new setup Panoptes deletes recordings after 72 hours; you can keep individual ones."),
            ("Map source (community server byd.serveone.at or OpenStreetMap Germany)", "your IP address and the map area, so roughly where your car is. With the community server also the query for free charging spots in that area.", "only once you choose a source under System → Map source. On the car screen the choice applies to the whole car; phone and PC ask separately."),
            ("Telegram", "message texts; pictures and videos only if you turn that on (they are then stored at Telegram)", "only with your own bot"),
            ("Tailscale", "connection for remote access", "only with remote access set up"),
            ("Route planner (byd.serveone.at/ev)", "charge level, consumption factor, driving status; your approximate position only for a newly suggested charging stop. The trip log only if you turn it on (off by default) and fetch it yourself on /ev/: end-to-end encrypted; the server only receives encrypted data and, according to the route planner, keeps it in memory for 2 minutes at most.", "only after linking, can be disconnected at any time"),
            ("Community server (byd.serveone.at/community)", "shared rules, only if you share them", "off by default"),
            ("Open-Meteo", "approximate position for the weather", "only with your consent, off by default"),
            ("Other services (BYD account, MQTT/smart home, ABRP, Stadia Maps, AI assistant)", "depends on the service; the input field tells you where your requests go", "only if you set them up yourself"),
        ],
        "h_brauch": "What you need",
        "brauch": [
            "A BYD with DiLink 3, 4 or 5 and Android 9 or newer on the car screen.",
            "So far Panoptes has mainly been tested on the <b>BYD Dolphin Surf (DiLink 3)</b>. On other models some things may be missing or work differently; Panoptes hides what your car cannot do.",
            "Storage for camera recordings, ideally a USB stick in the car.",
            "A free Tailscale account for remote access and your own Telegram bot for notifications. Panoptes shows you how.",
        ],
        "h_dl": "Download and install",
        "dl_bald": "Soon",
        "dl_text": "The ready-made app and step-by-step instructions for getting it onto the various BYD models will follow here. The way differs by model and software version.",
        "dl_code": "The source code will be published on GitHub under the MIT licence after the open-source release.",
        "h_hinweise": "Notes",
        "hinweise_kurz": "Private hobby project, free and without warranty. Use at your own risk, for private use with your own vehicle only. Users alone are responsible for lawful use (data protection, camera recordings, remote commands, traffic rules). Guardian recordings are intended for your own private property only, without capturing public space or neighbouring property. To the extent permitted by law, the developer accepts no liability; liability for intent, gross negligence, personal injury and mandatory consumer rights remains unaffected. Not affiliated with BYD; all trademarks belong to their owners.",
        "alle_hinweise": "Read all notes",
        "h_links": "More from the community",
        "links": [("/ev/", "🧭 Route planner"), ("/ev-cockpit/", "🖥️ EV Cockpit"), ("/", "🗺️ Community map")],
        "footer": "Private hobby project, no warranty, not affiliated with BYD. Use at your own risk.",
        "f_hinweise": "Notes", "f_impressum": "Imprint (German)", "f_datenschutz": "Privacy (German)",
        "lizenz": "Map data © OpenStreetMap contributors (ODbL). 3D car models partly by Nazh (CC BY 4.0), partly own work (CC0).",
        "hw_title": "Important notes – Panoptes, EV Cockpit, route planner",
        "hw_h1": "Important notes",
        "hw_stand": "Applies to Panoptes, the EV Cockpit and the route planner. As of 21 Oct 2026.",
        "hw": [
            ("Hobby project.", "Panoptes, EV Cockpit and the route planner are a private hobby project by {name}. They are provided free of charge and without warranty."),
            ("No warranty.", "There is no guarantee that everything is correct, complete or always available. This includes charge levels, range, prices, charger availability, routes, speed camera and hazard warnings. Check anything important yourself; on the road, what you see and the road signs always come first."),
            ("Your own risk.", "You use everything at your own risk. To the extent permitted by law, {name} accepts no liability for any damage resulting from its use, including damage to your vehicle, to data, or caused by remote commands."),
            ("You are responsible.", "You alone decide how you use the features, and you are responsible for making sure that use is legal. This applies especially to data protection, camera recordings, remote commands via your BYD account, and traffic rules."),
            ("Private use only.", "Everything is intended for private use with your own vehicle only. Commercial use (e.g. fleets, rental, taxi, monitoring company cars) is not intended."),
            ("Guardian on your own property only.", "Guardian recordings are intended for your own private property (e.g. garage, driveway). Point the cameras so that neither public space (street, pavement, public car park) nor your neighbours' property is captured. Do not publish recordings."),
            ("Not BYD.", "This project is not affiliated with BYD and is not supported or reviewed by BYD. “BYD”, “DiLink” and all other names and trademarks mentioned belong to their respective owners."),
            ("Your legal rights remain.", "Liability for intent and gross negligence, for personal injury, and mandatory consumer rights are not limited by these notes."),
        ],
        "hw_zurueck": "← Back to Panoptes",
    },
}

CSS = """
:root{--bg:#0b0f14;--card:#131a22;--card2:#182029;--line:#243040;--txt:#e7edf3;--mut:#93a2b3;
 --grn:#28d17c;--grn2:#1aa862;--blue:#38bdf8;--amber:#ffb020;--lime:#c8f560;--link:#3aa0ff;--node:#16212c;--note-bg:#10241a;--note-bd:#1c4a33;--note-tx:#bfe6d2}
@media (prefers-color-scheme: light){:root{--bg:#f4f7f9;--card:#ffffff;--card2:#eef3f6;--line:#d5dee6;--txt:#14202b;--mut:#55667a;
 --grn:#13995a;--grn2:#0e7d49;--blue:#0a7fb8;--amber:#a86a00;--lime:#4f7d00;--link:#0a66c2;--node:#ffffff;--note-bg:#e9f7ef;--note-bd:#b7e2c8;--note-tx:#1d4d33}}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--txt);font:17px/1.65 system-ui,-apple-system,Segoe UI,Roboto,sans-serif;-webkit-font-smoothing:antialiased}
a{color:var(--link);text-decoration:none}a:hover{text-decoration:underline}
.wrap{max-width:980px;margin:0 auto;padding:22px 16px 70px}
.top{display:flex;justify-content:space-between;align-items:center;font-size:14px;margin-bottom:6px;gap:12px}
.top a{color:var(--mut);font-weight:600}
header{text-align:center;padding:24px 0 6px}
.eyebrow{color:var(--grn);font-weight:700;letter-spacing:.12em;text-transform:uppercase;font-size:12px}
h1{font-size:clamp(30px,6vw,48px);line-height:1.12;margin:.3em 0 .25em}
.grad{background:linear-gradient(90deg,var(--grn),var(--blue));-webkit-background-clip:text;background-clip:text;color:transparent}
.sub{color:var(--mut);font-size:19px;max-width:680px;margin:0 auto}
h2{font-size:26px;margin:46px 0 6px}
.lead{color:var(--mut);margin:.3em 0 1.1em}
.card{background:var(--card);border:1px solid var(--line);border-radius:16px;padding:18px 20px;margin:14px 0}
.note{background:var(--note-bg);border:1px solid var(--note-bd);border-radius:12px;padding:13px 16px;color:var(--note-tx);font-size:15.5px;margin:18px 0}
.note a{color:inherit;text-decoration:underline}
.hero{display:grid;grid-template-columns:3fr 1fr;gap:16px;align-items:end;margin-top:22px}
.hero img,.galerie img{width:100%;height:auto;display:block;border-radius:12px;border:1px solid var(--line);background:var(--card)}
.raster{display:grid;grid-template-columns:repeat(auto-fill,minmax(270px,1fr));gap:14px}
.feat{background:var(--card);border:1px solid var(--line);border-radius:14px;padding:16px 18px}
.feat .ic{font-size:24px}.feat h3{margin:4px 0 4px;font-size:17.5px}.feat p{margin:0;color:var(--mut);font-size:15.5px}
.galerie{display:grid;grid-template-columns:1fr;gap:30px}
.galerie figure{margin:0}
.paar{display:grid;grid-template-columns:3fr 1fr;gap:10px;align-items:end}
.zwei{display:grid;grid-template-columns:1fr 1fr;gap:10px;align-items:start}
.galerie figcaption{color:var(--mut);font-size:14.5px;margin-top:8px}
.galerie figcaption b{color:var(--txt)}
.diagramm{background:var(--card);border:1px solid var(--line);border-radius:16px;padding:10px;margin:8px 0 14px}
.diagramm svg{width:100%;height:auto;display:block}
.diagramm .schmal{display:none}@media(max-width:640px){.diagramm .breit{display:none}.diagramm .schmal{display:block}}
.verb{display:grid;grid-template-columns:repeat(auto-fill,minmax(290px,1fr));gap:12px}
.verb .card{margin:0}
.verb h3{margin:0 0 6px;font-size:16.5px;display:flex;gap:8px;align-items:center}
.nr{flex:0 0 auto;width:24px;height:24px;border-radius:50%;background:var(--grn);color:#04110a;font-size:13px;font-weight:800;display:grid;place-items:center}
.verb p{margin:0 0 8px;font-size:15px}.verb p.nicht{color:var(--mut);margin:0;font-size:14.5px}
.verb p.nicht b{color:var(--amber)}
.tab{overflow-x:auto}
table{width:100%;border-collapse:collapse;font-size:15px;min-width:560px}
th,td{border:1px solid var(--line);padding:9px 12px;text-align:left;vertical-align:top}
th{background:var(--card2)}
ul.liste{margin:.2em 0;padding-left:1.2em}ul.liste li{margin:.35em 0}
.bald{display:inline-block;background:var(--card2);border:1px solid var(--line);border-radius:999px;padding:2px 12px;font-size:13px;font-weight:700;color:var(--amber);margin-left:8px;vertical-align:middle}
.btns{display:flex;flex-wrap:wrap;gap:10px;margin:8px 0}
.btn{display:inline-flex;align-items:center;gap:8px;border:1px solid var(--line);background:var(--card2);color:var(--txt);font-weight:700;padding:10px 16px;border-radius:12px;font-size:15.5px}
.btn:hover{text-decoration:none;border-color:var(--grn)}
.foot{color:var(--mut);font-size:13.5px;text-align:center;margin-top:46px;border-top:1px solid var(--line);padding-top:18px}
.foot a{color:var(--mut);text-decoration:underline}
ol.hw{padding-left:1.3em}ol.hw li{margin:.7em 0}
@media(max-width:720px){.hero,.galerie,.paar,.zwei{grid-template-columns:1fr}.hero .handy,.paar .handy{max-width:260px;margin:0 auto}h2{font-size:23px}}
"""


def bild(name, art, alt, pfad, klasse="", sofort=False):
    """<picture>: hell im hellen Modus (wenn es die Fassung gibt), sonst dunkel."""
    b = pfad + "bilder/" + name + "-" + art
    w, h = {"pc": (1440, 900), "handy": (780, 1688), "display": (1280, 720)}[art]
    hell = os.path.exists(os.path.join(QUELLE, name + "-" + art + "-hell.webp"))
    quelle = ('<source media="(prefers-color-scheme: light)" srcset="%s-hell.webp">' % b) if hell else ""
    return ('<a href="%s-dunkel.webp" target="_blank" rel="noopener"%s><picture>%s'
            '<img src="%s-dunkel.webp" alt="%s" width="%d" height="%d"%s></picture></a>'
            % (b, (' class="%s"' % klasse) if klasse else "", quelle, b, html.escape(alt), w, h,
               ' loading="eager" fetchpriority="high"' if sofort else ' loading="lazy" decoding="async"'))


def diagramm(s):
    e = html.escape
    # Knoten: (x, y, w, h, titel, zeile2, gestrichelt)
    k = {"auto": (355, 220, 200, 110, s["auto"], s["auto2"], False),
         "cockpit": (40, 40, 200, 90, s["cockpit"], s["cockpit2"], False),
         "planer": (670, 40, 210, 90, s["planer"], s["planer2"], False),
         "karte": (40, 410, 210, 90, s["karte"], s["karte2"], False),
         "tg": (690, 230, 190, 90, s["tg"], s["tg2"], False),
         "ha": (670, 410, 210, 90, s["ha"], s["ha2"], True)}
    mitte = lambda n: (k[n][0] + k[n][2] / 2, k[n][1] + k[n][3] / 2)
    kanten = [("auto", "cockpit", "1", s["t1"], False), ("auto", "planer", "2", s["t2"], False),
              ("auto", "karte", "3", s["t3"], False), ("auto", "tg", "4", s["t4"], False),
              ("auto", "ha", "5", s["t5"], True), ("cockpit", "planer", "6", s["t6"], True)]
    o = ['<svg viewBox="0 0 910 520" role="img" aria-label="%s" xmlns="http://www.w3.org/2000/svg">' % e(s["aria"]),
         '<style>.kn{fill:var(--node);stroke:var(--line);stroke-width:1.5}.kn.haupt{stroke:var(--grn);stroke-width:2.5}'
         '.kn.bald{stroke-dasharray:6 5}.t1{fill:var(--txt);font:700 17px system-ui,sans-serif}.t2{fill:var(--mut);font:13px system-ui,sans-serif}'
         '.li{stroke:var(--grn);stroke-width:2.2;fill:none}.li.bald{stroke:var(--mut);stroke-dasharray:6 5}'
         '.lb{fill:var(--mut);font:600 12.5px system-ui,sans-serif}.lbbg{fill:var(--bg)}.nk{fill:var(--grn)}.nt{fill:#04110a;font:800 12px system-ui,sans-serif}</style>']
    for a, b, nr, txt, bald in kanten:
        (x1, y1), (x2, y2) = mitte(a), mitte(b)
        o.append('<line class="li%s" x1="%d" y1="%d" x2="%d" y2="%d"/>' % (" bald" if bald else "", x1, y1, x2, y2))
    for n, (x, y, w, h, t1, t2, bald) in k.items():
        o.append('<rect class="kn%s%s" x="%d" y="%d" width="%d" height="%d" rx="16"/>'
                 % (" haupt" if n == "auto" else "", " bald" if bald else "", x, y, w, h))
        o.append('<text class="t1" x="%d" y="%d" text-anchor="middle">%s</text>' % (x + w / 2, y + h / 2 - 3, e(t1)))
        o.append('<text class="t2" x="%d" y="%d" text-anchor="middle">%s</text>' % (x + w / 2, y + h / 2 + 18, e(t2)))
    for a, b, nr, txt, bald in kanten:
        (x1, y1), (x2, y2) = mitte(a), mitte(b)
        mx, my = (x1 + x2) / 2, (y1 + y2) / 2
        breite = 9 + len(txt) * 6.6
        o.append('<rect class="lbbg" x="%d" y="%d" width="%d" height="22" rx="11"/>' % (mx - breite / 2 - 12, my - 11, breite + 24))
        o.append('<circle class="nk" cx="%d" cy="%d" r="10"/><text class="nt" x="%d" y="%d" text-anchor="middle">%s</text>'
                 % (mx - breite / 2 - 2, my, mx - breite / 2 - 2, my + 4, nr))
        o.append('<text class="lb" x="%d" y="%d" text-anchor="middle">%s</text>' % (mx + 8, my + 4, e(txt)))
    o.append("</svg>")
    return "\n".join(o)


def diagramm_schmal(s):
    """Hochkant fuer Handys: Panoptes oben, darunter die Verbindungen 1-5 als Zweige eines Stamms."""
    e = html.escape
    knoten = [("1", s["cockpit"], s["cockpit2"], s["t1"], False), ("2", s["planer"], s["planer2"], s["t2"], False),
              ("3", s["karte"], s["karte2"], s["t3"], False), ("4", s["tg"], s["tg2"], s["t4"], False),
              ("5", s["ha"], s["ha2"], s["t5"], True)]
    h = 130 + len(knoten) * 96
    o = ['<svg viewBox="0 0 400 %d" role="img" aria-label="%s" xmlns="http://www.w3.org/2000/svg">' % (h, e(s["aria"])),
         '<style>.kn{fill:var(--node);stroke:var(--line);stroke-width:1.5}.kn.haupt{stroke:var(--grn);stroke-width:2.5}'
         '.kn.bald{stroke-dasharray:6 5}.t1{fill:var(--txt);font:700 18px system-ui,sans-serif}.t2{fill:var(--mut);font:14px system-ui,sans-serif}'
         '.t3{fill:var(--grn);font:600 14px system-ui,sans-serif}.li{stroke:var(--grn);stroke-width:2.4;fill:none}'
         '.li.bald{stroke:var(--mut);stroke-dasharray:6 5}.nk{fill:var(--grn)}.nt{fill:#04110a;font:800 13px system-ui,sans-serif}</style>']
    letzte = 130 + (len(knoten) - 1) * 96 + 38
    o.append('<line class="li" x1="34" y1="60" x2="34" y2="%d"/><line class="li" x1="34" y1="60" x2="80" y2="60"/>' % (letzte - 96))
    o.append('<line class="li bald" x1="34" y1="%d" x2="34" y2="%d"/>' % (letzte - 96, letzte))
    o.append('<rect class="kn haupt" x="80" y="16" width="290" height="88" rx="16"/>')
    o.append('<text class="t1" x="225" y="55" text-anchor="middle">%s</text><text class="t2" x="225" y="80" text-anchor="middle">%s</text>'
             % (e(s["auto"]), e(s["auto2"])))
    for i, (nr, t1, t2, lab, bald) in enumerate(knoten):
        y = 130 + i * 96
        cy = y + 38
        o.append('<line class="li%s" x1="34" y1="%d" x2="80" y2="%d"/>' % (" bald" if bald else "", cy, cy))
        o.append('<rect class="kn%s" x="80" y="%d" width="290" height="76" rx="14"/>' % (" bald" if bald else "", y))
        o.append('<text class="t1" x="98" y="%d">%s</text><text class="t2" x="98" y="%d">%s</text><text class="t3" x="352" y="%d" text-anchor="end">%s</text>'
                 % (y + 30, e(t1), y + 55, e(t2), y + 30, e(lab if len(lab) < 18 else lab.split(",")[0])))
        o.append('<circle class="nk" cx="34" cy="%d" r="12"/><text class="nt" x="34" y="%d" text-anchor="middle">%s</text>' % (cy, cy + 4.5, nr))
    o.append("</svg>")
    return "\n".join(o)


def kopf(t, titel, desc, alt_de, alt_en, kanon):
    return """<!doctype html>
<html lang="%s">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="color-scheme" content="dark light">%s
<title>%s</title>
<meta name="description" content="%s">
<link rel="canonical" href="%s">
<link rel="alternate" hreflang="de" href="%s">
<link rel="alternate" hreflang="en" href="%s">
<meta property="og:title" content="%s">
<meta property="og:description" content="%s">
<style>%s</style>
</head>
<body>
<div class="wrap">
""" % (t["lang"], VORSCHAU, html.escape(titel), html.escape(desc), kanon, alt_de, alt_en, html.escape(titel), html.escape(desc), CSS)


def fuss(t, pfad):
    return """  <script>document.addEventListener('click',function(e){var a=e.target.closest('a');var i=a&&a.querySelector('picture img');
    if(i&&i.currentSrc){e.preventDefault();window.open(i.currentSrc,'_blank','noopener');}});</script>
  <div class="foot">%s<br>
    <a href="%shinweise.html">%s</a> · <a href="/impressum">%s</a> · <a href="/datenschutz">%s</a><br>
    <span style="font-size:12.5px">%s</span></div>
</div>
</body>
</html>
""" % (html.escape(t["footer"]), pfad, t["f_hinweise"], t["f_impressum"], t["f_datenschutz"], html.escape(t["lizenz"]))


BASIS = "https://byd.serveone.at/panoptes/"


def seite(t):
    p = t["pfad"]
    kanon = BASIS + ("en/" if t["lang"] == "en" else "")
    o = [kopf(t, t["title"], t["desc"], BASIS, BASIS + "en/", kanon)]
    o.append('  <div class="top"><a href="/">%s</a><a href="%s" hreflang="%s">🌐 %s</a></div>'
             % (t["zurueck"], t["andere"], "en" if t["lang"] == "de" else "de", t["andere_name"]))
    o.append('  <header><div class="eyebrow">%s</div><h1>%s — <span class="grad">%s</span></h1><p class="sub">%s</p></header>'
             % (t["eyebrow"], t["h1a"], t["h1b"], t["sub"]))
    o.append('  <div class="hero">%s<div class="handy">%s</div></div>'
             % (bild("start", "pc", t["hero_alt_pc"], p, sofort=True), bild("start", "handy", t["hero_alt_handy"], p, sofort=True)))
    o.append('  <div class="note">%s</div>' % t["wichtig"])
    # Funktionen
    o.append('  <h2 id="funktionen">%s</h2>\n  <div class="raster">' % t["h_kann"])
    for ic, h, txt in t["kann"]:
        o.append('    <div class="feat"><div class="ic">%s</div><h3>%s</h3><p>%s</p></div>' % (ic, h, txt))
    o.append("  </div>")
    # Galerie
    o.append('  <h2 id="bilder">%s</h2><p class="lead">%s</p>\n  <div class="galerie">' % (t["h_bilder"], t["bilder_lead"]))
    for cap, bilder in t["bilder"]:
        breit = [x for x in bilder if x[1] != "handy"]
        hoch = [x for x in bilder if x[1] == "handy"]
        teile = "".join(bild(n, a, alt, p) for n, a, alt in breit)
        if hoch:
            teile = '<div class="paar">%s<div class="handy">%s</div></div>' % (
                "".join(bild(n, a, alt, p) for n, a, alt in breit) or "<div></div>", "".join(bild(n, a, alt, p) for n, a, alt in hoch))
        elif len(breit) == 2:
            teile = '<div class="zwei">%s</div>' % teile
        o.append('    <figure>%s<figcaption><b>%s</b></figcaption></figure>' % (teile, html.escape(cap)))
    o.append("  </div>")
    # Zusammenhang
    o.append('  <h2 id="zusammenhang">%s</h2><p class="lead">%s</p>' % (t["h_zus"], t["zus_lead"]))
    o.append('  <div class="diagramm"><div class="breit">%s</div><div class="schmal">%s</div></div>\n  <div class="verb">'
             % (diagramm(t["svg"]), diagramm_schmal(t["svg"])))
    for nr, h, was, nicht in t["verb"]:
        o.append('    <div class="card"><h3><span class="nr">%s</span>%s</h3><p>%s</p><p class="nicht"><b>%s:</b> %s</p></div>'
                 % (nr, html.escape(h), html.escape(was), t["nicht"], html.escape(nicht.split(": ", 1)[1] if ": " in nicht[:20] else nicht)))
    o.append("  </div>")
    # Datenschutz
    o.append('  <h2 id="datenschutz">%s</h2><p class="lead">%s</p>' % (t["h_ds"], t["ds_lead"]))
    o.append('  <div class="tab"><table><tr><th>%s</th><th>%s</th><th>%s</th></tr>' % t["ds_kopf"])
    for wo, was, wann in t["ds"]:
        o.append("    <tr><td><b>%s</b></td><td>%s</td><td>%s</td></tr>" % (html.escape(wo), html.escape(was), html.escape(wann)))
    o.append("  </table></div>")
    # Was du brauchst + Download
    o.append('  <h2 id="brauchst">%s</h2>\n  <div class="card"><ul class="liste">%s</ul></div>'
             % (t["h_brauch"], "".join("<li>%s</li>" % x for x in t["brauch"])))
    o.append('  <h2 id="download">%s<span class="bald">%s</span></h2>\n  <div class="card"><p style="margin-top:0">%s</p><p style="margin-bottom:0;color:var(--mut)">%s</p></div>'
             % (t["h_dl"], t["dl_bald"], t["dl_text"], t["dl_code"]))
    # Hinweise
    o.append('  <h2 id="hinweise">%s</h2>\n  <div class="card"><p style="margin-top:0">%s</p><p style="margin-bottom:0"><a href="%shinweise.html">%s →</a></p></div>'
             % (t["h_hinweise"], html.escape(t["hinweise_kurz"]), "", t["alle_hinweise"]))
    o.append('  <h2>%s</h2>\n  <div class="btns">%s</div>' % (t["h_links"], "".join('<a class="btn" href="%s">%s</a>' % l for l in t["links"])))
    o.append(fuss(t, ""))
    return "\n".join(o)


def hinweise(t):
    kanon = BASIS + ("en/" if t["lang"] == "en" else "") + "hinweise.html"
    o = [kopf(t, t["hw_title"], t["hw_stand"], BASIS + "hinweise.html", BASIS + "en/hinweise.html", kanon)]
    o.append('  <div class="top"><a href="./">%s</a><a href="%shinweise.html" hreflang="%s">🌐 %s</a></div>'
             % (t["hw_zurueck"], t["andere"], "en" if t["lang"] == "de" else "de", t["andere_name"]))
    o.append('  <h1 style="font-size:clamp(28px,5vw,40px)">%s</h1><p class="lead">%s</p>\n  <div class="card"><ol class="hw">'
             % (t["hw_h1"], t["hw_stand"]))
    for h, txt in t["hw"]:
        o.append("    <li><b>%s</b> %s</li>" % (html.escape(h), html.escape(txt.replace("{name}", NAME))))
    o.append("  </ol></div>")
    o.append(fuss(t, ""))
    return "\n".join(o)


def main(bilder_quelle):
    global QUELLE
    QUELLE = bilder_quelle
    alt = os.path.join(ZIEL, "bilder")
    if os.path.isdir(alt):
        shutil.rmtree(alt)                 # alte Bilder (0.1.7) nicht mitschleppen
    os.makedirs(os.path.join(ZIEL, "en"), exist_ok=True)
    os.makedirs(os.path.join(ZIEL, "bilder"), exist_ok=True)
    n = 0
    for f in sorted(os.listdir(bilder_quelle)):
        if f.endswith(".webp"):
            shutil.copyfile(os.path.join(bilder_quelle, f), os.path.join(ZIEL, "bilder", f))
            n += 1
    for lang, unter in (("de", ""), ("en", "en")):
        t = T[lang]
        for name, inhalt in (("index.html", seite(t)), ("hinweise.html", hinweise(t))):
            with open(os.path.join(ZIEL, unter, name), "w", encoding="utf-8", newline="\n") as f:
                f.write(inhalt)
    print("ok:", n, "Bilder, 4 Seiten in", ZIEL)


if __name__ == "__main__":
    if "--vorschau" in sys.argv:
        VORSCHAU = '\n<meta name="robots" content="noindex, nofollow">'
    main(sys.argv[1])
