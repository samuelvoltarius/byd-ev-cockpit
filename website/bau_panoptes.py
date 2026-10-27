"""Baut die Projektseite byd.serveone.at/panoptes/ (DE + EN) nach website/panoptes/.

Aufruf: python website/bau_panoptes.py <ordner-mit-screenshots>
Inhalt: von Alfred abgenommene Panoptes-README + DISCLAIMER.md Fassung 1. Bilder: 24 Screenshots (hell/dunkel,
PC/Handy), Musterdaten. Die Seite folgt hell/dunkel dem Geraet; die Screenshots wechseln passend mit.
"""
import html
import os
import shutil
import sys

# Version, Download-Link, Prüfsumme: NICHT hier, sondern in byd-community/public/versionen.json (siehe versionen_laden)
HIER = os.path.dirname(os.path.abspath(__file__))
ZIEL = os.path.join(HIER, "panoptes")
VORSCHAU = ""                   # mit --vorschau: noindex (Vorschau unter nicht verlinktem Pfad)
NAME = "Alfred Aigner"
QUELLE = ""                      # Ordner mit den Screenshots (aus main())          # laut Impressum (Medieninhaber), fuer den Haftungstext

T = {
    "de": {
        "lang": "de", "andere": "en/", "andere_name": "English", "pfad": "",
        "title": "Panoptes – die Community-App für deinen BYD",
        "desc": "Panoptes ist eine kostenlose Community-App für BYD-Autos mit DiLink 3, 4 und 5, derzeit in Erprobung: Wächter mit Kamera, Fahrten und Laden mit Kosten, Wallbox, Fernzugang, Telegram-Meldungen, Karte mit Ladesäulen und Verbindung zum Routenplaner.",
        "zurueck": "← BYD EU Community",
        "eyebrow": "Kostenlos · für BYD mit DiLink 3, 4 und 5 · in Erprobung",
        "h1a": "Panoptes", "h1b": "dein BYD, wach und vernetzt",
        "sub": "Eine App, die direkt am Bildschirm in deinem Auto läuft. Dazu eine Oberfläche, die du am Handy oder PC öffnest: Wächter mit Kamera, Fahrten und Laden mit Kosten, deine Wallbox, Fernzugang, Meldungen über Telegram, eine eigene Karte mit Ladesäulen und die Verbindung zum Routenplaner.",
        "wichtig": "<b>Neu, Oktober 2026:</b> Panoptes gibt es jetzt öffentlich als <b>Erprobungsversion {V}</b>, mit Quellcode und <a href=\"#installieren\">Schritt-für-Schritt-Anleitung</a>. Getestet ist es bisher vor allem auf einem BYD Dolphin Surf (DiLink 3). Panoptes ist ein privates Freizeitprojekt und nicht von BYD. Bitte lies vor der Installation die <a href=\"hinweise.html\">Hinweise</a>.",
        "hero_alt_pc": "Panoptes-Startseite am PC: Ladestand, Reichweite, Karte und Ladekosten",
        "hero_alt_handy": "Panoptes-Startseite am Handy: Ladestand und Reichweite",
        "h_camp": "Camping-Modus <span class=\"bald\">in Erprobung</span>",
        "camp_lead": "Seit 0.1.16.1: Du schläfst im Auto, und Panoptes passt auf Strom, Wächter und Bildschirm auf. Heizen ist noch in Erprobung und bleibt aus, bis du es in den Einstellungen freigibst.",
        "camp": [
            ("Was er tut", "<ul class=\"liste\"><li><b>Wächter „bewohnt“:</b> Solange Camping läuft, schreckt der Wächter nicht ab (kein Bildschirm, Licht oder Hupe) und meldet keinen Erschütterungsalarm, wenn du dich bewegst.</li><li><b>Nachtbildschirm:</b> Nach einer einstellbaren Zeit ohne Berührung wird der Bildschirm fast schwarz, mit großer Uhr und ein paar Zahlen. Ohne Töne.</li><li><b>Akku-Schutz und Restdauer:</b> Du legst eine Untergrenze fest (ab Werk 20 %). Panoptes zeigt, wie lange der Akku für die Heizung reicht, und hört vor der Grenze auf. Das Auto schaltet Panoptes nie ab.</li></ul>"),
            ("Einschalten", "<ul class=\"liste\"><li>Per Tipp am Bildschirm im Auto, nur im Stand (Gang P).</li><li>Am Handy über die Oberfläche von Panoptes.</li><li>Über Telegram mit <code>/camping</code>.</li><li>Planen zu einer festen Zeit (Start und Weckzeit) geht ab 0.1.17 über die Schnittstelle von Panoptes; die Bedienung im EV-Cockpit folgt.</li><li>Beim Losfahren endet Camping von selbst.</li></ul>"),
            ("Heizen: in Erprobung", "<p><b>Panoptes heizt erst, wenn du es in den Einstellungen freigibst.</b> Bis dahin läuft ein Probelauf: Panoptes zeigt nur, was es tun würde, und schaltet nichts.</p><ul class=\"liste\"><li><b>Auto an:</b> Panoptes schaltet die Klimaanlage direkt.</li><li><b>Auto aus:</b> über die BYD-Cloud, dafür brauchst du ein BYD-Konto. Das weckt das Auto bei jedem Heizgang.</li></ul>"),
            ("Grenzen", "<ul class=\"liste\"><li><b>Kein Innenraumfühler:</b> Der Dolphin Surf hat keinen. Panoptes zeigt deshalb nie eine Innentemperatur und heizt in Intervallen nach der Außentemperatur („alle x Minuten für y Minuten“). Optional kannst du einen externen Fühler dazunehmen.</li><li><b>Verbrauch:</b> Grob 1,5 bis 3 % Akku pro Stunde bei 0 °C, wenn geheizt wird. Das ist eine Schätzung, kein Messwert; Panoptes lernt aus deinem echten Verbrauch.</li><li><b>Nach DC-Ladeende:</b> BYD schaltet das Auto dann selbst ab.</li><li>Camping ersetzt keine Aufsicht. Lass nie Kinder oder Tiere allein im Auto.</li></ul>"),
        ],
        "camp_bilder_lead": "Die Bilder stammen aus einem Emulator, nicht aus einem Auto. Darum steht bei den Werten „nicht verfügbar“, und die Modellangabe oben ist die des Emulators. Im Auto siehst du hier deine echten Werte. Klick auf ein Bild zum Vergrößern.",
        "camp_bilder": [
            ("Camping-Seite am Bildschirm im Auto: Einschalten, Akku, Heizdauer; oben der Hinweis „Probelauf“.", [("camping", "display", "Camping-Seite von Panoptes: Camping ist aus, Knopf Einschalten, Hinweis Probelauf, Werte noch nicht verfügbar")]),
            ("Einstellungen: Wärme, Heizweg, Akku-Untergrenze, 12-V-Warnung.", [("camping-einstellungen", "display", "Camping-Einstellungen: Wärme, Heizweg Probelauf, Vorheizen, Akku-Untergrenze 20 Prozent, 12-Volt-Warnung")]),
            ("Nachtbildschirm: fast schwarz, große Uhr, Rückmeldung „Zu kalt / Passt / Zu warm“. Daneben die Camping-Seite am Handy.", [("nacht", "display", "Nachtbildschirm: schwarzer Hintergrund, große Uhr und Datum, Tasten Zu kalt, Passt, Zu warm"), ("camping", "handy", "Camping-Seite am Handy bei 390 Pixel Breite")]),
        ],
        "h_kann": "Was Panoptes kann",
        "kann": [
            ("🚗", "Am Bildschirm im Auto", "Panoptes läuft als eigene App im Vollbild, mit großen Tasten. Während der Fahrt sind Einstellungen gesperrt; Start, Karte und Wächter bleiben erreichbar."),
            ("🧩", "Einrichtungshilfe", "Ein Assistent führt dich beim ersten Start Schritt für Schritt durch Rechte, Wächter, Karte, Datenfreigaben und Updates. Nichts ist vorausgewählt; alles, was Daten nach außen schickt, bleibt aus, bis du es einschaltest. Was dein Auto nicht kann, überspringt er mit einer Erklärung."),
            ("🛡️", "Wächter mit KI-Erkennung", "Steht dein Auto, achten die Kameras auf das Umfeld. Du entscheidest selbst, wann aufgenommen wird: nur bei Erschütterung, mit KI-Erkennung überall oder nur an deinen privaten Orten wie Garage oder Einfahrt. Ohne Wahl nimmt er nur bei Erschütterung auf. Damit die 12-V-Batterie geschont wird, legt er sich schlafen; die Grenze richtet sich nach dem Batterietyp (Blei, AGM oder LFP)."),
            ("📒", "Fahrten und Laden", "Fahrten, Verbrauch und Ladungen werden im Auto mitgeschrieben. Panoptes zeigt die Kosten je Ladung, je Monat und als Ø Kosten je 100 km. Fehlt ein Preis, steht dort „Preis fehlt“ statt einer erfundenen Zahl; Gratis-Laden lässt sich ausdrücklich eintragen."),
            ("🔌", "„Wo hast du geladen?“", "Nach dem Laden fragt Panoptes im Stand, nie während der Fahrt, nach Station und Preis. Mit „Ort merken“ kennt es den Preis beim nächsten Mal. Die Frage lässt sich abschalten."),
            ("💳", "Deine Ladekarten im Auto", "Ladekarten und Netze, Mindestleistung, Stecker und Ankunfts-Ladestand stellst du im Auto ein. Der Routenplaner rechnet damit; gespeichert wird das nur im Auto."),
            ("🏠", "Wallbox <span class=\"bald\">in Erprobung</span>", "Deine Wallbox über evcc, Home Assistant oder Tuya einrichten, ab Version 0.1.12 auch direkt (z. B. go-e, KEBA, openWB, Easee, Zaptec): Ladestand sehen, Modus, Ladegrenze und Strom einstellen. Steuern nur, wenn das Auto steht, mit Rückfrage und je Ladepunkt eigens freigegeben. Bisher nur mit Demo- und Testgeräten geprüft."),
            ("📍", "Deine Orte", "Eine Liste für alles: Zuhause, Garage, Arbeit oder der Ladeplatz mit eigenem Preis. Je Ort legst du fest, ob er privat ist (Wächter), ein Ladepreis gilt oder er als Ziel im Navi steht. Die Orte verlassen das Auto nicht."),
            ("🌍", "Fernzugang", "Über Tailscale erreichst du dein Auto von überall. Eingerichtet wird das mit einem QR-Code am Bildschirm im Auto und deinem eigenen Tailscale-Konto. Für Fortgeschrittene gibt es ab 0.1.14 zusätzlich einen unabhängigen Notzugang, ab Werk aus."),
            ("💬", "Meldungen über Telegram", "Dein eigener Bot meldet Wächter-Ereignisse, Laden, schwache Starterbatterie, Reifendruck und Updates. Jede Kategorie einzeln schaltbar, mit Ruhezeit für die Nacht. Bilder und Videos nur, wenn du das einschaltest."),
            ("🗺️", "Karte mit Ladesäulen", "Du wählst selbst, woher die Karte kommt: vom Community-Server (mit Gelände und freien Ladeplätzen, wo Betreiber Daten liefern), von OpenStreetMap oder gar nicht. Solange du nichts wählst, bleibt die Karte leer. Blitzer zeigt sie nur in Österreich, ab Werk aus und mit Rechtshinweis."),
            ("🔋", "„Reicht es noch?“", "Mit einer Route aus dem Routenplaner, auch mit Zwischenzielen, sagt dir Panoptes unterwegs, ob der Akku bis zum nächsten Stopp reicht, und schlägt bei Bedarf einen Ladestopp vor."),
            ("📊", "Monatsbericht", "Gefahrene Kilometer, Verbrauch, Laden und Kosten, Standverlust und Wächter-Ereignisse eines Monats auf einen Blick, auch zum Drucken. Gerechnet wird im Auto."),
            ("🔁", "Umstieg von OverDrive", "Wer bisher die App OverDrive genutzt hat, übernimmt Fahrten, Ladungen und Einstellungen, mit Vorschau und ohne Doppelte. Einwilligungen und riskante Schalter übernimmt Panoptes nie, die stellst du selbst ein."),
            ("🧭", "Verbindung zum Routenplaner", "Panoptes lässt sich mit deinem Konto auf <a href=\"/ev/\">byd.serveone.at/ev/</a> verbinden: Code am Auto anzeigen, am Handy bestätigen, fertig. Jederzeit trennbar."),
            ("🖥️", "EV-Cockpit am PC", "Das <a href=\"/ev-cockpit/\">EV-Cockpit</a> zeigt die Daten von Panoptes am PC, auch Ladungen und Kosten, und kann die Einstellungen ändern. Koppeln bestätigst du mit einem Tipp und einer vierstelligen Prüfzahl."),
            ("⬆️", "Updates in der App", "Panoptes sucht auf Wunsch selbst nach neuen Versionen. Installiert wird nur, wenn das Auto steht und die Zündung aus ist. Ab 0.1.13 verändert Panoptes keine dauerhaften Android-Einstellungen mehr (etwa „Bildschirm immer an“); früher gesetzte Werte lassen sich zurücksetzen."),
            ("🏕️", "Camping-Modus <span class=\"bald\">in Erprobung</span>", "Wächter „bewohnt“, Nachtbildschirm, Akku-Schutz mit Restdauer. Einschalten per Tipp, am Handy oder mit /camping in Telegram. Geheizt wird erst nach deiner Freigabe in den Einstellungen. <a href=\"#camping\">Mehr dazu</a>"),
            ("🌐", "Fünf Sprachen", "Deutsch, Englisch, Französisch, Italienisch und Niederländisch."),
        ],
        "h_bilder": "So sieht Panoptes aus",
        "bilder_lead": "Panoptes 0.1.8 bis 0.1.10 am Bildschirm im Auto, am PC und am Handy. Wo es beide Fassungen gibt, folgen die Bilder hell oder dunkel deinem Gerät. Klick auf ein Bild zum Vergrößern. Alle Bilder zeigen Musterdaten (Musterstandort Wien); die Einrichtungshilfe ist im Emulator aufgenommen.",
        "bilder": [
            ("Am Bildschirm im Auto: Start mit Ladestand, Reichweite und Schnellzugriffen.", [("start", "display", "Panoptes am Bildschirm im Auto: Start mit Ladestand und Reichweite")]),
            ("Einrichtungshilfe: Du wählst selbst, nichts ist vorausgewählt, Datenfreigaben sind aus.", [("einrichtung", "display", "Einrichtungshilfe: Wann soll der Wächter aufnehmen?"), ("freigaben", "display", "Einrichtungshilfe: Daten teilen, alles ist aus")]),
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
                "karte": "Community-Karte", "karte2": "Kacheln, Ladesäulen", "tg": "Telegram-Bot", "tg2": "dein eigener", "ha": "Home Assistant", "ha2": "geplant",
                "wb": "Wallbox", "wb2": "in Erprobung",
                "t1": "Kopplung", "t2": "Konto, Ziel, Fahrtenbuch E2E", "t3": "Karte (wenn gewählt)", "t4": "Meldungen", "t5": "Heimnetz", "t6": "geplant", "t7": "Route, Ladekarten",
                "aria": "Grafik: Panoptes im Auto in der Mitte, verbunden mit EV-Cockpit am PC, Routenplaner, Community-Karte, Telegram-Bot, Wallbox und geplant Home Assistant"},
        "verb": [
            ("1", "Panoptes ↔ EV-Cockpit (Kopplung)", "Du erlaubst das Cockpit einmal mit einer Prüfzahl, in Telegram oder auf der Panoptes-Seite. Dann holt das Cockpit Fahrzeugwerte, Einstellungen und das Fahrtenbuch direkt aus dem Auto, über dein Heimnetz oder Tailscale.",
             "Nicht dabei: Fernzugang, Passwort und Anschlüsse. Nichts davon läuft über unsere Server, das Fahrtenbuch bleibt auf deinem PC. Den Zugang hebt das Cockpit im Schlüsselbund deines Rechners auf. Was es sonst an Server schickt (Karte, 3D-Modell, Routenplaner, Zählung), entscheidest du mit eigenen Häkchen; ohne Häkchen nichts."),
            ("2", "Panoptes ↔ Routenplaner", "Nach dem Verbinden kommt dein Ziel mit Ladestopps ins Auto. Panoptes meldet Ladestand, Verbrauchsfaktor und Fahrstatus, damit der Plan stimmt. Schaltest du es ein (standardmäßig aus) und rufst auf /ev/ dein Fahrtenbuch ab, kommt es Ende-zu-Ende verschlüsselt direkt vom Auto in deinen Browser.",
             "Nicht dabei: Der Server kann das Fahrtenbuch nicht lesen; er bekommt nur verschlüsselte Daten und hält sie laut Routenplaner höchstens 2 Minuten im Arbeitsspeicher. Die ungefähre Position geht nur mit, wenn Panoptes unterwegs einen neuen Ladestopp vorschlägt."),
            ("3", "Panoptes ↔ Community-Karte", "Wenn du sie als Kartenquelle wählst, kommen Kartenkacheln und Ladesäulen-Daten von byd.serveone.at, mit Live-Belegung, wo es offene Daten gibt. Ohne Wahl lädt Panoptes keine Karte.",
             "Nicht dabei: Fahrten und Aufnahmen. Der Server sieht nur deine IP-Adresse und den Kartenausschnitt. Geteilte Regeln gehen nur an den Community-Server, wenn du sie selbst teilst (standardmäßig aus)."),
            ("4", "Panoptes → Telegram", "Dein eigener Bot schickt dir Meldungstexte. Bilder und Videos nur, wenn du das ausdrücklich einschaltest; dann liegen sie auf den Servern von Telegram.",
             "Nicht dabei: Keine Videos auf unseren Servern, kein Umweg über das Projekt."),
            ("5", "Panoptes ↔ Wallbox (in Erprobung)", "Panoptes spricht deine Wallbox im Heimnetz an, über evcc, Home Assistant, Tuya oder direkt. Steuern geht nur, wenn das Auto steht und du den Ladepunkt freigegeben hast, jede Änderung mit Rückfrage. Die Freigabe nimmst du jederzeit zurück.",
             "Nicht dabei: Nichts davon läuft über unsere Server. Zugangsdaten liegen verschlüsselt im Auto. Hersteller-Clouds (Easee, Zaptec, Tuya) nur mit deiner Einwilligung je Gerät."),
            ("6", "Panoptes ↔ Home Assistant (geplant)", "Geplant ist eine direkte Verbindung zwischen deinem Auto und deinem eigenen Home Assistant. Für die Wallbox kann Panoptes Home Assistant schon heute nutzen.",
             "Nicht dabei: Die Daten sollen nicht bei uns liegen."),
            ("7", "EV-Cockpit ↔ Routenplaner", "Das Cockpit zeigt die bereitliegende Route und deine Ladekarten. Ist es mit Panoptes gekoppelt, meldet nur Panoptes den Ladestand, damit nichts doppelt ankommt.",
             "Nicht dabei: Deine Fahrten bleiben auf dem PC."),
        ],
        "nicht": "Was nicht fließt",
        "h_ds": "Datenschutz: was wohin geht",
        "ds_lead": "Grundsatz: Deine Aufnahmen, Fahrten und Positionen bleiben im Auto. Panoptes schickt keine Kamera-Aufnahmen an die Server des Projekts. Was Daten nach außen schickt, ist standardmäßig aus; du schaltest es einzeln ein, und Panoptes sagt dir vorher, wohin die Daten gehen. Es gibt keine Werbung und kein Tracking.",
        "ds_kopf": ("Wohin", "Was", "Wann"),
        "ds": [
            ("Im Auto (USB-Stick, App)", "Wächter-Aufnahmen, Fahrtenbuch, Ladungen und Preise, Monatsbericht, deine Orte, Ladekarten, Einstellungen; Zugangsdaten (z. B. für die Wallbox) verschlüsselt", "immer. Bei neuer Einrichtung löscht Panoptes Aufnahmen nach 72 Stunden, einzelne kannst du behalten. Fehlt eine Datei (z. B. USB-Stick nicht eingesteckt), wird die Fahrt markiert, nicht gelöscht."),
            ("EV-Cockpit auf deinem PC", "Fahrzeugwerte, Fahrten, Ladungen und Kosten; deine Orte nur mit Namen, nie mit Koordinaten", "nur nach dem Koppeln, direkt vom Auto über dein Heimnetz oder Tailscale"),
            ("Kartenquelle (Community-Server byd.serveone.at oder OpenStreetMap Deutschland)", "Deine IP-Adresse und der Kartenausschnitt, also ungefähr, wo dein Auto steht. Beim Community-Server zusätzlich die Abfrage freier Ladeplätze für den Ausschnitt.", "erst, wenn du unter System → Kartenquelle eine Quelle wählst. Am Bildschirm im Auto gilt die Wahl fürs ganze Auto; Handy und PC fragen getrennt."),
            ("Telegram", "Meldungstexte; Bilder und Videos nur, wenn du das einschaltest (dann liegen sie bei Telegram)", "nur mit eigenem Bot"),
            ("Tailscale", "Verbindung für den Fernzugang und den Notzugang, in deinem eigenen Tailscale-Netz", "nur mit eingerichtetem Fernzugang; der Notzugang ist ab Werk aus"),
            ("Deine Wallbox", "Ladebefehle im Heimnetz; Easee, Zaptec und die Tuya-Cloud über die Hersteller-Cloud", "nur, wenn du eine Wallbox einrichtest; Hersteller-Cloud nur mit eigener Einwilligung je Gerät"),
            ("Routenplaner (byd.serveone.at/ev)", "Ladestand, Verbrauchsfaktor, Fahrstatus und deine Ladekarten für die Preisabfrage (der Server speichert sie nicht); die ungefähre Position nur für einen neu vorgeschlagenen Ladestopp oder, wenn du es erlaubst, für Preisvorschläge nach dem Laden. Das Fahrtenbuch nur, wenn du es einschaltest (standardmäßig aus) und auf /ev/ selbst abrufst: Ende-zu-Ende verschlüsselt, der Server bekommt nur verschlüsselte Daten und hält sie laut Routenplaner höchstens 2 Minuten im Arbeitsspeicher.", "nur nach dem Verbinden, jederzeit trennbar"),
            ("Community-Server (byd.serveone.at/community)", "geteilte Regeln, nur wenn du sie teilst", "standardmäßig aus"),
            ("Open-Meteo", "ungefähre Position für das Wetter", "nur mit deiner Einwilligung, standardmäßig aus"),
            ("Panoptes-Zählung (freiwillig, Standard aus)", "Zufalls-ID und Version, einmal am Tag. Keine IP-Speicherung, keine Fahrzeugdaten, kein Ort. Ausschalten löscht die Einträge am Server; Einträge ohne Meldung seit 90 Tagen werden anonym zu einer Monatszahl zusammengefasst.", "nur, wenn du unter Einstellungen → Datenschutz „Anonym mitzählen“ einschaltest (byd.serveone.at/panoptes/ping, ab 0.1.17)"),
            ("Besucherzählung dieser Webseite (eigenes Umami, analytics.serveone.at)", "aufgerufene Seite, Herkunftsseite, Browser, Gerätetyp, Land; Klicks auf den Download-Knopf als Zahl. Keine Cookies, keine IP-Adresse; bei „Do Not Track“ wird nicht gezählt. Das betrifft nur diese Webseite, nicht die App.", "beim Besuch der Webseite; Details in der <a href=\"/datenschutz#zaehlung\">Datenschutzerklärung</a>"),
            ("Weitere Dienste (BYD-Konto, MQTT/Smart Home, ABRP, Stadia Maps, KI-Assistent)", "je nach Dienst; an der Eingabe steht, wohin deine Anfragen gehen", "nur, wenn du sie selbst einrichtest"),
        ],
        "h_stand": "Stand der Entwicklung",
        "stand_lead": "Ehrlich, was wo läuft. „Im Testbetrieb“ heißt: läuft seit Version 0.1.11 in einem Testauto (BYD Dolphin Surf). „Gebaut“ heißt: fertig in 0.1.12 bis 0.1.14, der Test im Auto steht noch aus.",
        "stand_kopf": ("Funktion", "Stand"),
        "stand": [
            ("Wächter, Karte, Telegram, Monatsbericht, Routenplaner, EV-Cockpit", "im Testbetrieb"),
            ("Einrichtungshilfe, Ladekarten im Auto, „Wo hast du geladen?“, Kosten je 100 km", "im Testbetrieb"),
            ("Orte, Umstieg von OverDrive, 12-V-Batterietyp, Schutz vor dem Löschen von Fahrten", "im Testbetrieb"),
            ("Wallbox über evcc, Home Assistant, Tuya", "im Testbetrieb, aber nur mit Demo- und Testgeräten geprüft, noch nicht mit einer echten Wallbox"),
            ("Wallbox direkt (go-e, Shelly, KEBA, Heidelberg, openWB, Easee, Zaptec), Orte als Navi-Favoriten", "gebaut (0.1.12), nur mit Testgeräten geprüft"),
            ("Keine dauerhaften Eingriffe in Android-Einstellungen mehr", "gebaut (0.1.13)"),
            ("Notzugang", "gebaut (0.1.14), ab Werk aus"),
            ("Camping-Modus: Wächter „bewohnt“, Nachtbildschirm, Akku-Schutz", "im Testbetrieb (seit 0.1.16.1), Planen ab 0.1.17"),
            ("Camping: Heizen (Intervall nach Außentemperatur)", "in Erprobung, ab Werk als Probelauf; heizt erst nach Freigabe"),
            ("Home Assistant als eigene Verbindung", "geplant"),
        ],
        "h_brauch": "Was du brauchst",
        "brauch": [
            "Einen BYD mit DiLink 3, 4 oder 5 und Android 9 oder neuer am Bildschirm im Auto.",
            "Getestet ist Panoptes bisher vor allem mit dem <b>BYD Dolphin Surf (DiLink 3)</b>. Auf anderen Modellen kann manches fehlen oder anders sein; was dein Auto nicht kann, blendet Panoptes aus.",
            "Speicherplatz für die Kamera-Aufnahmen, am besten einen USB-Stick im Auto.",
            "Für den Fernzugang ein kostenloses Tailscale-Konto, für Meldungen einen eigenen Telegram-Bot. Panoptes zeigt dir, wie das geht.",
        ],
        "h_dl": "Herunterladen und installieren",
        "dl_anker": "installieren",
        "dl_bald": "Erprobungsversion {V}",
        "dl_text": "Panoptes {V} ist eine <b>Erprobungsversion</b>: Sie läuft im Alltag in einem Testauto (BYD Dolphin Surf, DiLink 3). Auf anderen Modellen kann manches fehlen oder anders sein. Die Installation ist nichts für jeden: Du brauchst etwas Geduld, einen PC und musst am Auto eine Entwickler-Freigabe einschalten. Nutzung auf eigenes Risiko, siehe <a href=\"hinweise.html\">Hinweise</a>.",
        "dl_knopf": "⬇️ Panoptes {V} herunterladen (APK, 71 MB)",
        "hero_dl": "⬇️ Panoptes {V} herunterladen", "hero_anl": "Anleitung", "kopf_dl": "⬇️ Download",
        "dl_release": "Release auf GitHub", "dl_quelle": "Quellcode",
        "dl_pruef": "Prüfsumme (SHA-256)", "dl_zert": "Signaturzertifikat (SHA-256)",
        "dl_update": "<b>Wichtig zu Updates:</b> Ab 0.1.15 kommen Updates automatisch aus dem öffentlichen GitHub-Repository (System → App-Updates, nur wenn das Auto steht). Ab 0.1.15 sucht Panoptes selbst nach Updates. Mit 0.1.17 und 0.1.18 bitte einmal von Hand installieren (siehe Hinweis oben). <b>Wer noch 0.1.14.1 hat, installiert {V} einmal von Hand</b>, genau wie beim ersten Mal (Schritt 4); deine Einstellungen und Daten bleiben dabei erhalten. Der Grund: Ab 0.1.15 ist Panoptes mit einem neuen, dauerhaften Schlüssel signiert (mit Herkunftsnachweis vom bisherigen), den 0.1.14.1 von selbst noch nicht annimmt.",
        "h_anl": "Schritt für Schritt",
        "anl": [
            ("Vorher lesen.", "Panoptes ist für dein eigenes Auto gedacht, privat und auf eigenes Risiko. Lies die <a href=\"hinweise.html\">Hinweise</a>. Für die Installation schaltest du am Auto Entwickler-Funktionen ein. Ob das für deine Garantie eine Rolle spielt, klärst du im Zweifel mit deinem Händler."),
            ("Herunterladen und prüfen.", "Lade die Datei <code>{APK}</code> mit dem Knopf oben auf deinen PC. Vergleiche dann die Prüfsumme. Unter Windows tippst du in der Eingabeaufforderung <code>certutil -hashfile {APK} SHA256</code>, am Mac oder unter Linux <code>shasum -a 256 {APK}</code>. Die Ausgabe muss genau die Prüfsumme oben ergeben. Weicht sie ab, installiere die Datei <b>nicht</b>."),
            ("Entwickler-Freigabe (ADB) am Auto einschalten.", "Panoptes startet seine Hintergrunddienste, zum Beispiel für die Kameras, über die ADB-Schnittstelle des Autos. Diese Verbindung bleibt im Auto (127.0.0.1). Ab Werk ist die Schnittstelle aus. Eingeschaltet wird sie im BYD-Entwicklermenü, mit den Schaltern für USB-Debugging bzw. kabelloses ADB. Wie du in dieses Menü kommst, hängt stark von Modell und Software-Stand ab; bei neuerer BYD-Software ist es mit einem Code gesperrt. Geprüft haben wir diesen Schritt bisher nur am Dolphin Surf (DiLink 3). Ohne diese Freigabe läuft Panoptes nicht vollständig."),
            ("App aufs Auto bringen.", "<b>Geprüfter Weg, mit PC:</b> Installiere am PC die Android-Plattform-Tools von Google (darin ist <code>adb</code>). PC und Auto müssen im selben Netz sein, zum Beispiel im WLAN-Hotspot deines Handys. Tippe dann <code>adb connect &lt;Adresse-des-Autos&gt;:5555</code> und <code>adb install -r {APK}</code>. Die Adresse des Autos siehst du in den WLAN-Einstellungen am Auto oder in der Geräteliste deines Hotspots. Am Ende muss <code>Success</code> erscheinen. <b>Ohne PC (Community-Berichte, von uns nicht geprüft):</b> Manche BYD-Software-Stände installieren APK-Dateien direkt vom USB-Stick über den eingebauten Installationsdialog. Ordnername und Ablauf unterscheiden sich je nach Region und Software. Fragt Android nach „Installation aus unbekannten Quellen“, erlaubst du das nur für diese Installation."),
            ("Erster Start mit der Einrichtungshilfe.", "Öffne Panoptes am Bildschirm im Auto. Der Assistent führt dich Schritt für Schritt durch alles Nötige: Sprache, Hinweise bestätigen, <b>Autostart</b>, Anzeige über anderen Apps, Berechtigungen, <b>USB-Freigabe</b>, dein Auto und die Kameras, Wächter, Betriebsart, Kartenquelle, Daten teilen, Blitzer und Updates. Danach kommen freiwillige Extras: Telegram, Routenplaner, EV-Cockpit und Fernzugang. Nichts ist vorausgewählt. Was Daten nach außen schickt, bleibt aus, bis du es selbst einschaltest."),
            ("Autostart freigeben.", "Damit Panoptes nach dem Einsteigen von selbst läuft, muss es in der BYD-App-Verwaltung erlaubt sein. Die Einrichtungshilfe öffnet die richtige Seite; dort nimmst du bei Panoptes den Haken bei der Autostart-Sperre weg. <b>BYD setzt diesen Schalter nach jeder Installation und jedem Update zurück.</b> Panoptes erinnert dich dann. Auf DiLink 5 gibt es diese Verwaltung nicht, der Schritt entfällt."),
            ("USB-Freigabe bestätigen.", "Android fragt einmal „USB-Debugging zulassen?“. Setze den Haken bei <b>„Immer von diesem Computer zulassen“</b> und tippe auf <b>Zulassen</b>. Der „Computer“ ist dabei Panoptes selbst im Auto. Ohne Haken fragt Android nach jedem Neustart wieder."),
            ("Am Handy oder PC öffnen (freiwillig).", "Mit eingerichtetem Fernzugang (Tailscale) öffnest du die Adresse deines Autos im Browser. Zum Anmelden brauchst du den <b>Zugangscode</b>, den du in der App am Auto unter <b>Start → Zugangscode</b> findest. Weitere Geräte, etwa das EV-Cockpit, erlaubst du unter <b>System → Gerät koppeln</b>."),
        ],
        "h_stolper": "Wenn etwas hakt",
        "stolper": [
            "<b>Panoptes startet nach einem Update nicht von selbst:</b> Autostart wieder freigeben (Schritt 6). BYD setzt ihn nach jeder Installation zurück.",
            "<b>Panoptes hat kein Internet:</b> Der eingebaute BYD-Verkehrsmonitor kann das Internet anderer Apps blockieren. Panoptes bietet dir an, ihn auszuschalten. Danach ist ein Neustart des Bildschirms nötig.",
            "<b>Kameras oder Wächter laufen nicht:</b> Prüfe, ob die USB-Freigabe mit „Immer zulassen“ bestätigt ist (Schritt 7) und die ADB-Freigabe noch an ist; ein BYD-Software-Update kann sie zurücksetzen.",
            "<b>Wohin mit den Aufnahmen?</b> Am besten auf einen USB-Stick im Auto.",
            "<b>Wieder entfernen:</b> In den Android-Einstellungen am Auto unter Apps deinstallieren. Daten in der App gehen dabei verloren; Aufnahmen auf dem USB-Stick bleiben.",
        ],
        "dl_code": "<b>Quellcode und Lizenz:</b> Der vollständige Quellcode genau dieser Version steht öffentlich auf <a href=\"https://github.com/samuelvoltarius/panoptes\">GitHub (samuelvoltarius/panoptes)</a>. Der eigene Code steht unter der MIT-Lizenz. Die APK enthält Teile unter anderen Lizenzen, darunter das Programm fast_cam_capture (GPL-3.0) und die Erkennungsmodelle YOLO (AGPL-3.0). Die vollständige Liste steht in den <a href=\"https://github.com/samuelvoltarius/panoptes/blob/main/THIRD_PARTY_NOTICES.md\">Lizenzhinweisen</a>. Fehler und Vorschläge meldest du dort unter Issues.",
        "dl_ds": "<b>Datenschutz:</b> Panoptes schickt nur dann Daten nach außen, wenn du es selbst einschaltest (siehe <a href=\"#datenschutz\">Datenschutz</a>). Die App enthält keine Werbung und kein Tracking. Der Download selbst kommt von GitHub; dafür gelten die Datenschutzregeln von GitHub.",
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
        "desc": "Panoptes is a free community app for BYD cars with DiLink 3, 4 and 5, currently in testing: camera guard, trips and charging with costs, wallbox, remote access, Telegram notifications, a map with chargers and a link to the route planner.",
        "zurueck": "← BYD EU Community",
        "eyebrow": "Free · for BYD with DiLink 3, 4 and 5 · in testing",
        "h1a": "Panoptes", "h1b": "your BYD, awake and connected",
        "sub": "An app that runs right on your car's screen, plus an interface you open on your phone or PC: a camera guard, trips and charging with costs, your wallbox, remote access, Telegram notifications, its own map with chargers and a link to the route planner.",
        "wichtig": "<b>New, October 2026:</b> Panoptes is now publicly available as <b>test version {V}</b>, with source code and a <a href=\"#install\">step-by-step guide</a>. So far it has mainly been tested on a BYD Dolphin Surf (DiLink 3). Panoptes is a private hobby project and not made by BYD. Please read the <a href=\"hinweise.html\">notes</a> before installing.",
        "hero_alt_pc": "Panoptes home on a PC: charge level, range, map and charging costs",
        "hero_alt_handy": "Panoptes home on a phone: charge level and range",
        "h_camp": "Camping mode <span class=\"bald\">in testing</span>",
        "camp_lead": "Since 0.1.16.1: you sleep in the car, and Panoptes looks after power, the guard and the screen. Heating is still in testing and stays off until you allow it in the settings.",
        "camp": [
            ("What it does", "<ul class=\"liste\"><li><b>Guard \u201coccupied\u201d:</b> While camping runs, the guard does not scare anyone off (no screen, lights or horn) and raises no shake alarm when you move.</li><li><b>Night screen:</b> After a time without touch that you can set, the screen turns almost black, with a big clock and a few numbers. No sounds.</li><li><b>Battery protection and time left:</b> You set a lower limit (20 % by default). Panoptes shows how long the battery lasts for heating and stops before the limit. Panoptes never switches the car off.</li></ul>"),
            ("Switching on", "<ul class=\"liste\"><li>With a tap on the car screen, only while parked (gear P).</li><li>On your phone, in Panoptes\u2019 web interface.</li><li>In Telegram with <code>/camping</code>.</li><li>Scheduling for a set time (start and wake-up time) works from 0.1.17 through Panoptes\u2019 interface; operating it from the EV Cockpit follows.</li><li>Camping ends by itself when you drive off.</li></ul>"),
            ("Heating: in testing", "<p><b>Panoptes only heats once you allow it in the settings.</b> Until then it runs a dry run: it only shows what it would do and switches nothing.</p><ul class=\"liste\"><li><b>Car on:</b> Panoptes switches the climate control directly.</li><li><b>Car off:</b> through the BYD cloud, which needs a BYD account. This wakes the car for every heating run.</li></ul>"),
            ("Limits", "<ul class=\"liste\"><li><b>No cabin sensor:</b> the Dolphin Surf has none. Panoptes therefore never shows an interior temperature and heats in intervals based on the outside temperature (\u201cevery x minutes for y minutes\u201d). You can add an external sensor if you like.</li><li><b>Consumption:</b> roughly 1.5 to 3 % battery per hour at 0 \u00b0C while heating. That is an estimate, not a measurement; Panoptes learns from your real consumption.</li><li><b>After DC charging ends:</b> BYD then switches the car off by itself.</li><li>Camping is no substitute for supervision. Never leave children or animals alone in the car.</li></ul>"),
        ],
        "camp_bilder_lead": "The pictures come from an emulator, not from a car. That is why the values read \u201cnot available\u201d and the model name at the top is the emulator\u2019s. In the car you see your real values here. Click a picture to enlarge it. The interface is shown in German.",
        "camp_bilder": [
            ("Camping page on the car screen: switch on, battery, heating time; the \u201cdry run\u201d notice at the top.", [("camping", "display", "Panoptes camping page: camping is off, Switch on button, dry run notice, values not yet available")]),
            ("Settings: warmth, heating route, battery limit, 12 V warning.", [("camping-einstellungen", "display", "Camping settings: warmth, heating route dry run, pre-heating, battery limit 20 percent, 12-volt warning")]),
            ("Night screen: almost black, big clock, feedback \u201ctoo cold / fine / too warm\u201d. Next to it the camping page on a phone.", [("nacht", "display", "Night screen: black background, big clock and date, buttons too cold, fine, too warm"), ("camping", "handy", "Camping page on a phone at 390 pixels wide")]),
        ],
        "h_kann": "What Panoptes does",
        "kann": [
            ("🚗", "On the car screen", "Panoptes runs as its own full-screen app with large buttons. While driving, settings are locked; home, map and guard stay available."),
            ("🧩", "Setup assistant", "On first start an assistant guides you step by step through permissions, guard, map, data sharing and updates. Nothing is preselected; anything that sends data out stays off until you turn it on. Whatever your car cannot do is skipped with an explanation."),
            ("🛡️", "Guard with AI detection", "While your car is parked, the cameras watch its surroundings. You decide when it records: only on impact, with AI detection everywhere, or only at your own private places such as your garage or driveway. Without a choice it only records on impact. To protect the 12 V battery it goes to sleep; the threshold follows the battery type (lead-acid, AGM or LFP)."),
            ("📒", "Trips and charging", "Trips, consumption and charging sessions are recorded in the car. Panoptes shows the cost per session, per month and as average cost per 100 km. If a price is missing it says \u201cprice missing\u201d instead of inventing a number; free charging can be entered explicitly."),
            ("🔌", "\u201cWhere did you charge?\u201d", "After charging, Panoptes asks for the station and price while parked, never while driving. With \u201cremember place\u201d it knows the price next time. The question can be switched off."),
            ("💳", "Your charge cards in the car", "Charge cards and networks, minimum power, plug and arrival charge level are set in the car. The route planner uses them; they are only stored in the car."),
            ("🏠", "Wallbox <span class=\"bald\">in testing</span>", "Set up your wallbox via evcc, Home Assistant or Tuya, and from version 0.1.12 also directly (e.g. go-e, KEBA, openWB, Easee, Zaptec): see the status, set mode, charge limit and current. Control only while the car is parked, with confirmation and enabled per charge point. So far only checked with demo and test devices."),
            ("📍", "Your places", "One list for everything: home, garage, work or the charging spot with its own price. For each place you decide whether it is private (guard), a charging price applies or it is a destination in the navigation. Places never leave the car."),
            ("🌍", "Remote access", "Reach your car from anywhere via Tailscale. Setup uses a QR code on the car screen and your own Tailscale account. For advanced users, 0.1.14 adds an independent emergency access, off by default."),
            ("💬", "Telegram notifications", "Your own bot reports guard events, charging, a weak starter battery, tyre pressure and updates. Each category can be switched on its own, with quiet hours for the night. Pictures and videos only if you turn that on."),
            ("🗺️", "Map with chargers", "You choose where the map comes from: the community server (with terrain and free charging spots where operators provide data), OpenStreetMap, or none. Until you choose, the map stays empty. Speed cameras are shown in Austria only, off by default and with a legal notice."),
            ("🔋", "\u201cWill it make it?\u201d", "With a route from the route planner, including waypoints, Panoptes tells you on the road whether the battery will last to the next stop and suggests a charging stop if needed."),
            ("📊", "Monthly report", "Distance, consumption, charging and costs, standby loss and guard events of a month at a glance, also for printing. Calculated in the car."),
            ("🔁", "Switching from OverDrive", "If you used the OverDrive app before, you can take over trips, charging sessions and settings, with a preview and without duplicates. Panoptes never takes over consents or risky switches; you set those yourself."),
            ("🧭", "Route planner link", "Connect Panoptes to your account on <a href=\"/ev/\">byd.serveone.at/ev/</a>: show a code in the car, confirm on your phone, done. Disconnect at any time."),
            ("🖥️", "EV Cockpit on your PC", "The <a href=\"/ev-cockpit/\">EV Cockpit</a> shows Panoptes data on your PC, including charging sessions and costs, and can change its settings. You confirm the pairing with one tap and a four-digit check number."),
            ("⬆️", "Updates in the app", "If you like, Panoptes looks for new versions itself. Installing only happens while the car is parked with the ignition off. From 0.1.13 Panoptes no longer changes permanent Android settings (such as \u201cscreen always on\u201d); values set earlier can be reset."),
            ("🏕️", "Camping mode <span class=\"bald\">in testing</span>", "Guard \u201coccupied\u201d, night screen, battery protection with time left. Switch on with a tap, on your phone or with /camping in Telegram. Heating only starts after you allow it in the settings. <a href=\"#camping\">More</a>"),
            ("🌐", "Five languages", "German, English, French, Italian and Dutch."),
        ],
        "h_bilder": "What Panoptes looks like",
        "bilder_lead": "Panoptes 0.1.8 to 0.1.10 on the car screen, on a PC and on a phone. Where both versions exist, the pictures follow your device's light or dark setting. Click a picture to enlarge it. All pictures show sample data (sample location Vienna) and the German interface; the setup assistant was captured in an emulator.",
        "bilder": [
            ("On the car screen: home with charge level, range and quick actions.", [("start", "display", "Panoptes on the car screen: home with charge level and range")]),
            ("Setup assistant: you choose, nothing is preselected, data sharing is off.", [("einrichtung", "display", "Setup assistant: when should the guard record?"), ("freigaben", "display", "Setup assistant: data sharing, everything is off")]),
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
                "karte": "Community map", "karte2": "tiles, chargers", "tg": "Telegram bot", "tg2": "your own", "ha": "Home Assistant", "ha2": "planned",
                "wb": "Wallbox", "wb2": "in testing",
                "t1": "pairing", "t2": "account, destination, trip log E2E", "t3": "map (if chosen)", "t4": "notifications", "t5": "home network", "t6": "planned", "t7": "route, charge cards",
                "aria": "Diagram: Panoptes in the car in the middle, connected to the EV Cockpit on a PC, the route planner, the community map, a Telegram bot, a wallbox and, planned, Home Assistant"},
        "verb": [
            ("1", "Panoptes ↔ EV Cockpit (pairing)", "You allow the cockpit once with a check number, in Telegram or on the Panoptes page. The cockpit then fetches vehicle data, settings and the trip log straight from the car, over your home network or Tailscale.",
             "Not included: remote access, password and ports. None of this goes through our servers; the trip log stays on your PC. The cockpit keeps the access key in your computer's keyring. Anything else it sends to servers (map, 3D model, route planner, usage count) needs its own tick; without a tick, nothing."),
            ("2", "Panoptes ↔ route planner", "Once linked, your destination with charging stops goes into the car. Panoptes reports charge level, consumption factor and driving status so the plan is right. If you turn it on (off by default) and fetch your trip log on /ev/, it comes end-to-end encrypted straight from the car to your browser.",
             "Not included: the server cannot read the trip log; it only receives encrypted data and, according to the route planner, keeps it in memory for 2 minutes at most. Your approximate position is only sent when Panoptes suggests a new charging stop on the road."),
            ("3", "Panoptes ↔ community map", "If you choose it as map source, map tiles and charger data come from byd.serveone.at, with live availability where open data exists. Without a choice Panoptes loads no map.",
             "Not included: trips and recordings. The server only sees your IP address and the map area. Shared rules only go to the community server if you share them yourself (off by default)."),
            ("4", "Panoptes → Telegram", "Your own bot sends you message texts. Pictures and videos only if you explicitly turn that on; they are then stored on Telegram's servers.",
             "Not included: no videos on our servers, no detour through the project."),
            ("5", "Panoptes ↔ wallbox (in testing)", "Panoptes talks to your wallbox in your home network, via evcc, Home Assistant, Tuya or directly. Control only works while the car is parked and you have enabled the charge point, each change with confirmation. You can withdraw the permission at any time.",
             "Not included: none of this goes through our servers. Credentials are stored encrypted in the car. Manufacturer clouds (Easee, Zaptec, Tuya) only with your consent per device."),
            ("6", "Panoptes ↔ Home Assistant (planned)", "A direct connection between your car and your own Home Assistant is planned. For the wallbox, Panoptes can already use Home Assistant today.",
             "Not included: the data is not meant to be stored with us."),
            ("7", "EV Cockpit ↔ route planner", "The cockpit shows the route waiting for you and your charge cards. When it is paired with Panoptes, only Panoptes reports the charge level, so nothing arrives twice.",
             "Not included: your trips stay on your PC."),
        ],
        "nicht": "What does not flow",
        "h_ds": "Privacy: what goes where",
        "ds_lead": "Principle: your recordings, trips and positions stay in the car. Panoptes does not send camera recordings to the project's servers. Anything that sends data out is off by default; you turn each item on separately, and Panoptes tells you beforehand where the data goes. No ads, no tracking.",
        "ds_kopf": ("Where", "What", "When"),
        "ds": [
            ("In the car (USB stick, app)", "guard recordings, trip log, charging sessions and prices, monthly report, your places, charge cards, settings; credentials (e.g. for the wallbox) encrypted", "always. On a new setup Panoptes deletes recordings after 72 hours; you can keep individual ones. If a file is missing (e.g. USB stick not plugged in), the trip is marked, not deleted."),
            ("EV Cockpit on your PC", "vehicle data, trips, charging sessions and costs; your places by name only, never with coordinates", "only after pairing, straight from the car over your home network or Tailscale"),
            ("Map source (community server byd.serveone.at or OpenStreetMap Germany)", "your IP address and the map area, so roughly where your car is. With the community server also the query for free charging spots in that area.", "only once you choose a source under System → Map source. On the car screen the choice applies to the whole car; phone and PC ask separately."),
            ("Telegram", "message texts; pictures and videos only if you turn that on (they are then stored at Telegram)", "only with your own bot"),
            ("Tailscale", "connection for remote access and emergency access, in your own Tailscale network", "only with remote access set up; emergency access is off by default"),
            ("Your wallbox", "charging commands in your home network; Easee, Zaptec and the Tuya cloud via the manufacturer cloud", "only if you set up a wallbox; manufacturer cloud only with your own consent per device"),
            ("Route planner (byd.serveone.at/ev)", "charge level, consumption factor, driving status and your charge cards for the price query (the server does not store them); your approximate position only for a newly suggested charging stop or, if you allow it, for price suggestions after charging. The trip log only if you turn it on (off by default) and fetch it yourself on /ev/: end-to-end encrypted; the server only receives encrypted data and, according to the route planner, keeps it in memory for 2 minutes at most.", "only after linking, can be disconnected at any time"),
            ("Community server (byd.serveone.at/community)", "shared rules, only if you share them", "off by default"),
            ("Open-Meteo", "approximate position for the weather", "only with your consent, off by default"),
            ("Panoptes counting (optional, off by default)", "random ID and version, once a day. No IP address stored, no vehicle data, no location. Switching it off deletes the entries on the server; entries without a report for 90 days are merged into an anonymous monthly number.", "only if you switch on \u201cCount anonymously\u201d under Settings \u2192 Privacy (byd.serveone.at/panoptes/ping, from 0.1.17)"),
            ("Visitor counting on this website (own Umami, analytics.serveone.at)", "page viewed, referring page, browser, device type, country; clicks on the download button as a number. No cookies, no IP address; nothing is counted with “Do Not Track”. This only concerns this website, not the app.", "when you visit the website; details in the <a href=\"/datenschutz#zaehlung\">privacy policy</a> (German)"),
            ("Other services (BYD account, MQTT/smart home, ABRP, Stadia Maps, AI assistant)", "depends on the service; the input field tells you where your requests go", "only if you set them up yourself"),
        ],
        "h_stand": "Development status",
        "stand_lead": "Honestly, what runs where. \u201cIn test use\u201d means: running since version 0.1.11 in a test car (BYD Dolphin Surf). \u201cBuilt\u201d means: finished in 0.1.12 to 0.1.14, the test in the car is still pending.",
        "stand_kopf": ("Feature", "Status"),
        "stand": [
            ("Guard, map, Telegram, monthly report, route planner, EV Cockpit", "in test use"),
            ("Setup assistant, charge cards in the car, \u201cWhere did you charge?\u201d, cost per 100 km", "in test use"),
            ("Places, switching from OverDrive, 12 V battery type, protection against deleting trips", "in test use"),
            ("Wallbox via evcc, Home Assistant, Tuya", "in test use, but only checked with demo and test devices, not yet with a real wallbox"),
            ("Wallbox directly (go-e, Shelly, KEBA, Heidelberg, openWB, Easee, Zaptec), places as navigation favourites", "built (0.1.12), only checked with test devices"),
            ("No more permanent changes to Android settings", "built (0.1.13)"),
            ("Emergency access", "built (0.1.14), off by default"),
            ("Camping mode: guard \u201coccupied\u201d, night screen, battery protection", "in test use (since 0.1.16.1), scheduling from 0.1.17"),
            ("Camping: heating (intervals by outside temperature)", "in testing, dry run by default; only heats after you allow it"),
            ("Home Assistant as its own connection", "planned"),
        ],
        "h_brauch": "What you need",
        "brauch": [
            "A BYD with DiLink 3, 4 or 5 and Android 9 or newer on the car screen.",
            "So far Panoptes has mainly been tested on the <b>BYD Dolphin Surf (DiLink 3)</b>. On other models some things may be missing or work differently; Panoptes hides what your car cannot do.",
            "Storage for camera recordings, ideally a USB stick in the car.",
            "A free Tailscale account for remote access and your own Telegram bot for notifications. Panoptes shows you how.",
        ],
        "h_dl": "Download and install",
        "dl_anker": "install",
        "dl_bald": "Test version {V}",
        "dl_text": "Panoptes {V} is a <b>test version</b>: it runs in everyday use in a test car (BYD Dolphin Surf, DiLink 3). On other models some things may be missing or work differently. Installing it is not for everyone: you need some patience, a PC, and you have to turn on a developer setting in the car. Use at your own risk, see the <a href=\"hinweise.html\">notes</a>.",
        "dl_knopf": "⬇️ Download Panoptes {V} (APK, 71 MB)",
        "hero_dl": "⬇️ Download Panoptes {V}", "hero_anl": "Guide", "kopf_dl": "⬇️ Download",
        "dl_release": "Release on GitHub", "dl_quelle": "Source code",
        "dl_pruef": "Checksum (SHA-256)", "dl_zert": "Signing certificate (SHA-256)",
        "dl_update": "<b>Important about updates:</b> From 0.1.15 on, updates come automatically from the public GitHub repository (System → App updates, only while the car is parked). From 0.1.15 on, Panoptes checks for updates itself. With 0.1.17 and 0.1.18 please install once by hand (see notice above). <b>If you still have 0.1.14.1, install {V} once by hand</b>, just like the first time (step 4); your settings and data are kept. The reason: from 0.1.15 on Panoptes is signed with a new, permanent key (with proof of origin from the old one), which 0.1.14.1 does not accept by itself yet.",
        "h_anl": "Step by step",
        "anl": [
            ("Read first.", "Panoptes is meant for your own car, for private use and at your own risk. Read the <a href=\"hinweise.html\">notes</a>. To install it you turn on developer functions in the car. If in doubt whether this matters for your warranty, ask your dealer."),
            ("Download and check.", "Download <code>{APK}</code> to your PC with the button above, then compare the checksum. On Windows type <code>certutil -hashfile {APK} SHA256</code> in a command prompt, on a Mac or Linux <code>shasum -a 256 {APK}</code>. The output must match the checksum above exactly. If it differs, do <b>not</b> install the file."),
            ("Turn on developer access (ADB) in the car.", "Panoptes starts its background services, for example for the cameras, through the car's ADB interface. This connection stays inside the car (127.0.0.1). It is off by default. You turn it on in the BYD developer menu, with the switches for USB debugging or wireless ADB. How to reach this menu depends a lot on model and software version; on newer BYD software it is locked with a code. So far we have only tested this step on the Dolphin Surf (DiLink 3). Without it Panoptes will not fully work."),
            ("Get the app onto the car.", "<b>Tested way, with a PC:</b> install Google's Android platform tools on your PC (they contain <code>adb</code>). PC and car must be on the same network, for example your phone's Wi-Fi hotspot. Then type <code>adb connect &lt;car-address&gt;:5555</code> and <code>adb install -r {APK}</code>. You find the car's address in its Wi-Fi settings or in your hotspot's device list. At the end it must say <code>Success</code>. <b>Without a PC (community reports, not tested by us):</b> some BYD software versions install APK files straight from a USB stick through the built-in installer. Folder name and procedure differ by region and software. If Android asks about “installing from unknown sources”, allow it only for this installation."),
            ("First start with the setup assistant.", "Open Panoptes on the car screen. The assistant guides you step by step through everything needed: language, confirming the notes, <b>autostart</b>, display over other apps, permissions, <b>USB access</b>, your car and cameras, guard, operating mode, map source, data sharing, speed cameras and updates. Then optional extras: Telegram, route planner, EV Cockpit and remote access. Nothing is preselected. Anything that sends data out stays off until you turn it on yourself."),
            ("Allow autostart.", "For Panoptes to start by itself when you get in, it has to be allowed in BYD's app management. The setup assistant opens the right page; untick the autostart block for Panoptes there. <b>BYD resets this switch after every installation and update.</b> Panoptes will remind you. DiLink 5 has no such app management, so the step is skipped."),
            ("Confirm USB access.", "Android asks once “Allow USB debugging?”. Tick <b>“Always allow from this computer”</b> and tap <b>Allow</b>. The “computer” is Panoptes itself in the car. Without the tick Android asks again after every restart."),
            ("Open on your phone or PC (optional).", "With remote access (Tailscale) set up, open your car's address in a browser. To log in you need the <b>access code</b>, found in the app in the car under <b>Home → Access code</b>. You allow other devices, such as the EV Cockpit, under <b>System → Pair a device</b>."),
        ],
        "h_stolper": "If something goes wrong",
        "stolper": [
            "<b>Panoptes does not start by itself after an update:</b> allow autostart again (step 6). BYD resets it after every installation.",
            "<b>Panoptes has no internet:</b> BYD's built-in traffic monitor can block the internet for other apps. Panoptes offers to switch it off; the screen then needs a restart.",
            "<b>Cameras or guard do not run:</b> check that USB access was confirmed with “Always allow” (step 7) and that ADB access is still on; a BYD software update can reset it.",
            "<b>Where to store recordings?</b> Ideally on a USB stick in the car.",
            "<b>Removing it again:</b> uninstall in the car's Android settings under Apps. Data inside the app is lost; recordings on the USB stick stay.",
        ],
        "dl_code": "<b>Source code and licence:</b> the complete source code of exactly this version is public on <a href=\"https://github.com/samuelvoltarius/panoptes\">GitHub (samuelvoltarius/panoptes)</a>. Our own code is under the MIT licence. The APK contains parts under other licences, including the program fast_cam_capture (GPL-3.0) and the YOLO detection models (AGPL-3.0). The full list is in the <a href=\"https://github.com/samuelvoltarius/panoptes/blob/main/THIRD_PARTY_NOTICES.md\">licence notices</a>. Report bugs and ideas there under Issues.",
        "dl_ds": "<b>Privacy:</b> Panoptes only sends data out if you turn it on yourself (see <a href=\"#datenschutz\">privacy</a>). The app has no ads and no tracking. The download itself is served by GitHub; GitHub's privacy rules apply to it.",
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

NEU = {   # Homepage einfach (27.10.2026): 3 Sätze oben, "Ist das was für mich?", kurze Schritte, Details aufklappbar
    "de": {
        "hero_anl": "So installierst du es",
        "drei": [("Was ist das?", "Eine kostenlose App, die am Bildschirm in deinem BYD läuft."),
                 ("Für wen?", "Für BYD-Fahrer, die Wächter mit Kamera, Fahrtenbuch und Ladekosten wollen."),
                 ("Wie fange ich an?", "Datei herunterladen und mit einem PC aufs Auto bringen. Wir zeigen dir jeden Schritt.")],
        "h_fuer_mich": "Ist das was für mich?",
        "fuer_mich": [("✅", "Du hast einen BYD", "mit einem neueren Bildschirm-System (DiLink 3, 4 oder 5). Am besten getestet ist der Dolphin Surf."),
                      ("💻", "Du hast einen PC", "und etwa eine Stunde Zeit. Am Auto schaltest du einen Entwickler-Schalter ein."),
                      ("⚠️", "Es ist eine Erprobung", "Ein privates Projekt, ohne Gewähr. Bitte lies vorher die <a href=\"hinweise.html\">Hinweise</a>.")],
        "alle_funktionen": "Alle weiteren Funktionen ansehen",
        "camp_detail": "🏕️ Camping-Modus im Detail (in Erprobung)",
        "mehr_bilder": "Mehr Bilder ansehen",
        "echtheit": "Echtheit der Datei prüfen (für Fortgeschrittene)",
        "echtheit_text": "Wie du die Prüfsumme vergleichst, steht in der ausführlichen Anleitung unten (Schritt 2).",
        "aelter": "Ich habe schon eine ältere Version",
        "h_kurz": "In 5 Schritten aufs Auto",
        "kurz": [("Hinweise lesen.", "Panoptes ist für dein eigenes Auto, privat und auf eigenes Risiko. <a href=\"hinweise.html\">Zu den Hinweisen</a>."),
                 ("Entwickler-Schalter am Auto einschalten.", "Das ist der Entwickler-Zugang (ADB). Wie du hinkommst, hängt vom Modell ab: siehe <a href=\"/guide\">Anleitungen</a>."),
                 ("Datei mit dem PC aufs Auto bringen.", "PC und Auto ins selbe WLAN, dann zwei Befehle. Sie stehen in der ausführlichen Anleitung."),
                 ("Panoptes am Auto öffnen.", "Ein Assistent fragt dich alles. Nichts ist vorausgewählt."),
                 ("Autostart erlauben.", "Damit Panoptes von selbst startet. Der Assistent öffnet die richtige Seite.")],
        "ausfuehrlich": "Ausführliche Anleitung mit allen Befehlen (8 Schritte)",
        "ds_detail": "Genau nachlesen: was geht wohin?",
        # ab 0.1.21 (Kern 12): aWATTar-Börsenpreise
        "ds_ab_0121": [
            ("aWATTar (aWATTar GmbH bzw. Deutschland GmbH, api.awattar.at / api.awattar.de)", "Panoptes holt höchstens einmal je Stunde (meist einmal am Tag) die öffentlichen Börsenstrompreise für AT bzw. DE. Es gibt kein Konto, und es werden keine Daten über dich oder dein Auto gesendet; aWATTar sieht nur die Internetadresse des Autos.", "nur wenn du im Ladeplan „Ich habe einen dynamischen Stromtarif“ einschaltest (Standard aus) und als Strompreis zu Hause „Börsenpreis“ wählst. Schalter „dynamischer Stromtarif“ aus: ab sofort kein Abruf mehr."),
        ],
        # Datenschutz-Zeilen ab 0.1.20 (Kern 12, 27.10.2026): erscheinen automatisch, sobald versionen.json >= 0.1.20 meldet
        "ds_ab_0120": [
            ("go-e Cloud (go-e GmbH, *.api.v3.go-e.io)", "Status und Befehle deiner go-e-Wallbox (laden ja/nein, Ladestrom, Leistung) und dein API-Token. Der Token wird einmal per Handy direkt an dein Auto übergeben und liegt dort verschlüsselt; er geht nie über Panoptes-Server.", "nur wenn du bei der Wallbox „go-e Charger (Cloud)“ wählst und ausdrücklich einwilligst (Standard aus). Einwilligung ausschalten oder Gerät entfernen beendet es sofort."),
            ("Wallbox-Konto (Wallbox Chargers S.L., api.wall-box.com / user-api.wall-box.com)", "Anmeldung mit deinem Wallbox-Konto (E-Mail und Passwort, verschlüsselt im Auto gespeichert), Status und Befehle deines Ladegeräts. Inoffizielle Schnittstelle (wie bei Home Assistant).", "nur wenn du „Wallbox Pulsar / Commander (Cloud)“ wählst und ausdrücklich einwilligst (Standard aus). Einwilligung ausschalten oder Gerät entfernen beendet es sofort."),
        ],
        # Bekannter Fehler (Koordination/Deploy 27.10.2026). Bleibt, bis ein Updater-Test am Auto gruen ist (Koordination).
        "bekannt": "<b>Bekannter Fehler:</b> Wer 0.1.17 oder 0.1.18 hat: bitte 0.1.19.1 einmal von Hand installieren (<a href=\"#schritte\">Anleitung</a>). In diesen Versionen funktioniert „Installieren“ unter System → App-Updates nicht. Deine Daten bleiben erhalten.",
        "zus_detail": "Wie Panoptes mit Cockpit, Routenplaner, Karte und Wallbox verbunden ist",
    },
    "en": {
        "hero_anl": "How to install",
        "drei": [("What is this?", "A free app that runs on the screen in your BYD."),
                 ("Who is it for?", "For BYD drivers who want a camera guard, a trip log and charging costs."),
                 ("How do I start?", "Download the file and put it on the car with a PC. We show you every step.")],
        "h_fuer_mich": "Is this for me?",
        "fuer_mich": [("✅", "You have a BYD", "with a newer screen system (DiLink 3, 4 or 5). Best tested on the Dolphin Surf."),
                      ("💻", "You have a PC", "and about an hour. You switch on a developer setting in the car."),
                      ("⚠️", "It is a test version", "A private project without warranty. Please read the <a href=\"hinweise.html\">notes</a> first.")],
        "alle_funktionen": "See all other features",
        "camp_detail": "🏕️ Camping mode in detail (in testing)",
        "mehr_bilder": "See more pictures",
        "echtheit": "Check that the file is genuine (advanced)",
        "echtheit_text": "How to compare the checksum is explained in the detailed guide below (step 2).",
        "aelter": "I already have an older version",
        "h_kurz": "Onto the car in 5 steps",
        "kurz": [("Read the notes.", "Panoptes is for your own car, private and at your own risk. <a href=\"hinweise.html\">Read the notes</a>."),
                 ("Switch on the developer setting in the car.", "This is the developer access (ADB). How to get there depends on the model: see the <a href=\"/en/guide\">guides</a>."),
                 ("Put the file on the car with a PC.", "PC and car on the same Wi-Fi, then two commands. They are in the detailed guide."),
                 ("Open Panoptes in the car.", "An assistant asks you everything. Nothing is preselected."),
                 ("Allow autostart.", "So Panoptes starts by itself. The assistant opens the right page.")],
        "ausfuehrlich": "Detailed guide with all commands (8 steps)",
        "ds_detail": "In detail: what goes where?",
        "ds_ab_0121": [
            ("aWATTar (aWATTar GmbH / Deutschland GmbH, api.awattar.at / api.awattar.de)", "Panoptes fetches the public exchange electricity prices for AT or DE at most once per hour (usually once a day). There is no account, and no data about you or your car is sent; aWATTar only sees the car’s internet address.", "only if you switch on “I have a dynamic electricity tariff” in the charge plan (off by default) and choose “Exchange price” as your home electricity price. Switch “dynamic electricity tariff” off: no more requests from then on."),
        ],
        "ds_ab_0120": [
            ("go-e Cloud (go-e GmbH, *.api.v3.go-e.io)", "Status and commands of your go-e wallbox (charging on/off, charging current, power) and your API token. The token is handed to your car once via your phone and stored there encrypted; it never passes through Panoptes servers.", "only if you choose “go-e Charger (Cloud)” for your wallbox and explicitly consent (off by default). Turning consent off or removing the device stops it immediately."),
            ("Wallbox account (Wallbox Chargers S.L., api.wall-box.com / user-api.wall-box.com)", "Login with your Wallbox account (e-mail and password, stored encrypted in the car), status and commands of your charger. Unofficial interface (as used by Home Assistant).", "only if you choose “Wallbox Pulsar / Commander (Cloud)” and explicitly consent (off by default). Turning consent off or removing the device stops it immediately."),
        ],
        "bekannt": "<b>Known issue:</b> If you have 0.1.17 or 0.1.18: please install 0.1.19.1 once by hand (<a href=\"#schritte\">guide</a>). In these versions ‘Install’ under System → App updates does not work. Your data is kept.",
        "zus_detail": "How Panoptes connects to the cockpit, route planner, map and wall box",
    },
}


CSS = """
:root{--card:var(--panel);--card2:var(--panel-2);--txt:var(--text);--mut:var(--muted);--grn:var(--accent-2);--grn2:var(--accent-2);--blue:var(--accent);--amber:var(--warn);--lime:var(--accent-2);--link:var(--accent);--node:var(--panel);--note-bg:var(--panel);--note-bd:var(--line-2);--note-tx:var(--text)}
*{box-sizing:border-box}
a{color:var(--link);text-decoration:none}a:hover{text-decoration:underline}
.wrap{max-width:980px;margin:0 auto;padding:22px 16px 70px}
.top{display:flex;justify-content:space-between;align-items:center;font-size:14px;margin-bottom:6px;gap:12px}
.top a{color:var(--mut);font-weight:600}
.kopfbereich{text-align:center;padding:28px 0 6px}.kopfbereich .bd-knoepfe{justify-content:center;margin:20px 0 4px}.drei{max-width:680px;margin:0 auto;text-align:left;font-size:18px}.drei p{margin:.35em 0}.bd-nav-dl{color:var(--accent-2)!important;font-weight:700!important}.wrap details.bd-auf{margin:14px 0}.wrap details.bd-auf .raster,.wrap details.bd-auf .verb,.wrap details.bd-auf .galerie{margin:6px 0 14px}
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
.reihe{display:flex;gap:12px;justify-content:center;align-items:flex-start;margin-top:22px}
.galerie .reihe{margin-top:0}
.reihe>a{display:block;min-width:0}
.reihe img{width:100%;height:100%;object-fit:cover;display:block;border-radius:12px;border:1px solid var(--line);background:var(--card)}
.reihe>a.allein.hoch{max-width:300px}.reihe>a.allein.breit{max-width:820px}
.galerie figcaption{color:var(--mut);font-size:14.5px;margin-top:8px;text-align:center}
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
table.stand{min-width:0}
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
ol.anl{padding-left:1.4em;margin:.2em 0}ol.anl li{margin:.8em 0}
.anl-h{font-size:19px;margin:26px 0 4px}
code{background:var(--card2);border:1px solid var(--line);border-radius:6px;padding:1px 5px;font-size:.9em;overflow-wrap:anywhere}
.hash{font-size:14px;color:var(--mut);overflow-wrap:anywhere;margin:12px 0}
.topr{display:flex;align-items:center;gap:14px}.topr .topdl{background:var(--grn);color:#04110a;border-radius:999px;padding:4px 12px;font-weight:700}.topr .topdl:hover{text-decoration:none;background:var(--grn2)}
.herobtns{justify-content:center;margin:22px 0 4px}.btn.gross{font-size:17px;padding:14px 22px}
.btn.dl{background:var(--grn);color:#04110a;border-color:var(--grn)}.btn.dl:hover{background:var(--grn2);text-decoration:none}
@media(max-width:720px){.reihe{flex-direction:column;align-items:center}.reihe>a{flex:none!important;width:100%}.reihe>a.hoch{max-width:260px}.hero,.galerie,.paar,.zwei{grid-template-columns:1fr}.hero .handy,.paar .handy{max-width:260px;margin:0 auto}h2{font-size:23px}}
"""


GROESSE = {"pc": (1440, 900), "handy": (780, 1688), "display": (1280, 720)}


def reihe(bilder, pfad, sofort=False):
    """Bilder einer Reihe: gleiche Hoehe, Ober- und Unterkante buendig (flex-grow = Seitenverhaeltnis), allein zentriert."""
    teile = []
    for n, a, alt in bilder:
        w, h = GROESSE[a]
        kl = ("hoch" if a == "handy" else "breit") + (" allein" if len(bilder) == 1 else "")
        stil = "flex:%.4f 1 0;aspect-ratio:%d/%d" % (w / h, w, h) if len(bilder) > 1 else "aspect-ratio:%d/%d;width:100%%" % (w, h)
        teile.append(bild(n, a, alt, pfad, klasse=kl, sofort=sofort, stil=stil))
    return '<div class="reihe">%s</div>' % "".join(teile)


def bild(name, art, alt, pfad, klasse="", sofort=False, stil=""):
    """<picture>: hell im hellen Modus (wenn es die Fassung gibt), sonst dunkel."""
    b = pfad + "bilder/" + name + "-" + art
    w, h = GROESSE[art]
    hell = os.path.exists(os.path.join(QUELLE, name + "-" + art + "-hell.webp"))
    def v(datei):                          # Inhalts-Kennung: neues Bild -> neue Adresse (Bilder sind 24 h im Cache)
        import hashlib
        return "?v=" + hashlib.sha256(open(os.path.join(QUELLE, datei), "rb").read()).hexdigest()[:8]
    dunkel = b + "-dunkel.webp" + v(name + "-" + art + "-dunkel.webp")
    quelle = ('<source media="(prefers-color-scheme: light)" srcset="%s-hell.webp%s">' % (b, v(name + "-" + art + "-hell.webp"))) if hell else ""
    return ('<a href="%s" target="_blank" rel="noopener"%s%s><picture>%s'
            '<img src="%s" alt="%s" width="%d" height="%d"%s></picture></a>'
            % (dunkel, (' class="%s"' % klasse) if klasse else "", (' style="%s"' % stil) if stil else "", quelle, dunkel, html.escape(alt), w, h,
               ' loading="eager" fetchpriority="high"' if sofort else ' loading="lazy" decoding="async"'))


def diagramm(s):
    e = html.escape
    # Knoten: (x, y, w, h, titel, zeile2, gestrichelt)
    k = {"auto": (355, 220, 200, 110, s["auto"], s["auto2"], False),
         "cockpit": (40, 40, 200, 90, s["cockpit"], s["cockpit2"], False),
         "planer": (670, 40, 210, 90, s["planer"], s["planer2"], False),
         "karte": (40, 410, 210, 90, s["karte"], s["karte2"], False),
         "tg": (690, 230, 190, 90, s["tg"], s["tg2"], False),
         "ha": (670, 410, 210, 90, s["ha"], s["ha2"], True),
         "wb": (40, 230, 190, 90, s["wb"], s["wb2"], False)}
    mitte = lambda n: (k[n][0] + k[n][2] / 2, k[n][1] + k[n][3] / 2)
    kanten = [("auto", "cockpit", "1", s["t1"], False), ("auto", "planer", "2", s["t2"], False),
              ("auto", "karte", "3", s["t3"], False), ("auto", "tg", "4", s["t4"], False),
              ("auto", "wb", "5", s["t5"], False), ("auto", "ha", "6", s["t6"], True), ("cockpit", "planer", "7", s["t7"], True)]
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
              ("5", s["wb"], s["wb2"], s["t5"], False), ("6", s["ha"], s["ha2"], s["t6"], True)]
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


# ---- Gemeinsames Aussehen (byd-design.css), gleiches Menü und gleicher Fuß wie alle Seiten von byd.serveone.at ----
# Vorlage: F:\byd-community\werkzeuge\bau_seiten.py (Homepage-Sitzung, 27.10.2026). Menü/Fuß hier gleich halten.
CSS_V = "8"
JS_V = "3"
UMAMI = ('<script defer src="https://analytics.serveone.at/script.js" data-website-id="a7e62dac-cb0b-4ff5-a0cd-4a9b0778cf3b" '
         'data-domains="byd.serveone.at" data-do-not-track="true" data-exclude-search="true"></script>')
FAVICON = ("<link rel=\"icon\" href=\"data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'%3E"
           "%3Crect width='32' height='32' rx='8' fill='%230a0e14'/%3E%3Cpath d='M18 4 8 18h6l-2 10 12-16h-7z' fill='%2338bdf8'/%3E%3C/svg%3E\">")
WA = "https://chat.whatsapp.com/BzFXEFK2hj05vxX4nVTFPv?mode=gi_t"
MENUE = {
    "de": {"start": "/", "eintraege": [("/#karte", "Karte"), ("/ev/", "Routenplaner"), ("/panoptes/", "Panoptes"),
                                       ("/ev-cockpit/", "EV-Cockpit"), ("/guide", "Anleitungen")],
           "menue": "Menü", "o": "en", "o_kurz": "EN", "o_lang": "English",
           "fuss": [("/impressum", "Impressum"), ("/datenschutz", "Datenschutz"), ("/nutzungsbedingungen", "Nutzungsbedingungen"),
                    ("/guide", "Anleitungen"), ("/community/", "Panoptes-Community"), (WA, "WhatsApp-Gruppe")],
           "klein": "Privates Freizeitprojekt, kostenlos und ohne Gewähr. Nicht verbunden mit BYD Auto Co., Ltd. "
                    "„BYD“ und Modellnamen sind Marken ihrer jeweiligen Inhaber."},
    "en": {"start": "/en/", "eintraege": [("/en/#karte", "Map"), ("/ev/", "Route planner"), ("/panoptes/en/", "Panoptes"),
                                          ("/ev-cockpit/en/", "EV Cockpit"), ("/en/guide", "Guides")],
           "menue": "Menu", "o": "de", "o_kurz": "DE", "o_lang": "Deutsch",
           "fuss": [("/en/impressum", "Imprint"), ("/en/datenschutz", "Privacy"), ("/en/nutzungsbedingungen", "Terms of use"),
                    ("/en/guide", "Guides"), ("/community/", "Panoptes community"), (WA, "WhatsApp group")],
           "klein": "Private hobby project, free and without warranty. Not affiliated with BYD Auto Co., Ltd. "
                    "“BYD” and model names are trademarks of their respective owners."},
}

# Versionen: EINZIGE Stelle ist byd-community/public/versionen.json (live: https://byd.serveone.at/versionen.json).
# Die Seite liest sie beim Laden neu (byd-seite.js); hier wird sie nur als Rückfall eingebacken.
VERSIONEN_LOKAL = os.environ.get("BYD_VERSIONEN", r"F:\byd-community\public\versionen.json")


def versionen_laden():
    import json
    if os.path.exists(VERSIONEN_LOKAL):
        return json.load(open(VERSIONEN_LOKAL, encoding="utf-8"))["panoptes"]
    import urllib.request
    with urllib.request.urlopen("https://byd.serveone.at/versionen.json", timeout=10) as r:
        return json.loads(r.read().decode("utf-8"))["panoptes"]


PV = versionen_laden()
VERSION = PV["version"]
DL_APK = PV["apk_url"]
DL_RELEASE = PV["release_url"]
DL_QUELLE = "https://github.com/samuelvoltarius/panoptes"
DL_SHA = PV["sha256"]
DL_CERT = PV["zertifikat"]


def sp(feld, wert):
    """Wert mit Markierung, damit byd-seite.js ihn aus versionen.json auffrischen kann."""
    return '<span data-ver="panoptes.%s">%s</span>' % (feld, html.escape(str(wert)))


def kopf(t, titel, desc, alt_de, alt_en, kanon, aktiv_pfad, andere_url):
    m = MENUE[t["lang"]]
    links = []
    for href, name in m["eintraege"]:
        links.append('    <a href="%s"%s>%s</a>' % (href, ' aria-current="page"' if href == aktiv_pfad else "", name))
    links.append('    <a class="bd-nav-dl" href="%s#%s" data-umami-event="download-weiter" data-umami-event-quelle="kopf">%s</a>'
                 % (aktiv_pfad, t["dl_anker"], t["kopf_dl"]))
    links.append('    <a class="bd-sprache" href="%s" hreflang="%s" lang="%s" data-sprache="%s">%s</a>'
                 % (andere_url, m["o"], m["o"], m["o"], m["o_kurz"]))
    return """<!doctype html>
<html lang="%s" class="bd-auto">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="color-scheme" content="dark light">%s
<title>%s</title>
<meta name="description" content="%s">
%s
<link rel="canonical" href="%s">
<link rel="alternate" hreflang="de" href="%s">
<link rel="alternate" hreflang="en" href="%s">
<link rel="alternate" hreflang="x-default" href="%s">
<meta property="og:title" content="%s">
<meta property="og:description" content="%s">
<link rel="stylesheet" href="/assets/byd-design.css?v=%s">
<style>%s</style>
%s
</head>
<body class="bd">
<header class="bd-kopf">
  <a class="bd-marke" href="%s">⚡ BYD&nbsp;EU&nbsp;<span>Community</span></a>
  <button class="bd-burger" type="button" aria-label="%s" aria-expanded="false" aria-controls="haupt-nav">☰</button>
  <nav class="bd-menue" id="haupt-nav">
%s
  </nav>
</header>
<div class="wrap">
""" % (t["lang"], VORSCHAU, html.escape(titel), html.escape(desc), FAVICON, kanon, alt_de, alt_en, alt_de,
       html.escape(titel), html.escape(desc), CSS_V, CSS, UMAMI, m["start"], m["menue"], "\n".join(links))


def fuss(t, andere_url):
    m = MENUE[t["lang"]]
    links = '<a href="%shinweise.html">%s</a>' % ("/panoptes/" if t["lang"] == "de" else "/panoptes/en/", t["f_hinweise"])
    links += "".join('<a href="%s"%s>%s</a>' % (h, ' target="_blank" rel="noopener"' if h.startswith("http") else "", n)
                     for h, n in m["fuss"])
    links += '<a href="%s" hreflang="%s" lang="%s" data-sprache="%s">%s</a>' % (andere_url, m["o"], m["o"], m["o"], m["o_lang"])
    return """</div>
<script>document.addEventListener('click',function(e){var a=e.target.closest('a');var i=a&&a.querySelector('picture img');
  if(i&&i.currentSrc){e.preventDefault();window.open(i.currentSrc,'_blank','noopener');}});</script>
<footer class="bd-fuss">
  <nav>%s</nav>
  <p class="bd-klein">%s<br>%s</p>
</footer>
<script src="/assets/byd-seite.js?v=%s" defer></script>
</body>
</html>
""" % (links, html.escape(t["footer"]), html.escape(t["lizenz"]), JS_V)


BASIS = "https://byd.serveone.at/panoptes/"
OBEN = ("🛡️", "📒", "🗺️", "💬", "🏠", "🏕️")      # diese 6 Funktionen sichtbar, der Rest aufklappbar


def seite(t):
    p = t["pfad"]
    de = t["lang"] == "de"
    kanon = BASIS + ("" if de else "en/")
    hier = "/panoptes/" if de else "/panoptes/en/"
    andere = "/panoptes/en/" if de else "/panoptes/"
    o = [kopf(t, t["title"], t["desc"], BASIS, BASIS + "en/", kanon, hier, andere)]
    # Kopf: 3 Sätze + große Knöpfe
    o.append('  <header class="kopfbereich"><span class="bd-eyebrow">%s</span><h1>%s – <span class="bd-grad-text">%s</span></h1>'
             % (t["eyebrow"], t["h1a"], t["h1b"]))
    o.append('  <div class="drei">%s</div>' % "".join("<p><b>%s</b> %s</p>" % x for x in t["drei"]))
    o.append('  <div class="bd-knoepfe"><a class="bd-knopf gross haupt" href="#%s" data-umami-event="download-weiter" data-umami-event-quelle="hero">%s</a>'
             '<a class="bd-knopf gross leer" href="#schritte">%s</a></div></header>' % (t["dl_anker"], t["hero_dl"], t["hero_anl"]))
    o.append("  " + reihe([("start", "pc", t["hero_alt_pc"]), ("start", "handy", t["hero_alt_handy"])], p, sofort=True))
    o.append('  <div class="bd-hinweis"><p>%s</p></div>' % t["wichtig"])
    # Ist das was für mich?
    o.append('  <h2 id="fuer-mich">%s</h2>\n  <div class="bd-kacheln">' % t["h_fuer_mich"])
    for ic, h, txt in t["fuer_mich"]:
        o.append('    <div class="bd-kachel"><span class="bd-symbol">%s</span><h3>%s</h3><p>%s</p></div>' % (ic, h, txt))
    o.append("  </div>")
    # Funktionen: 6 oben, Rest aufklappbar
    o.append('  <h2 id="funktionen">%s</h2>\n  <div class="raster">' % t["h_kann"])
    oben = [x for x in t["kann"] if x[0] in OBEN]
    rest = [x for x in t["kann"] if x[0] not in OBEN]
    for ic, h, txt in oben:
        o.append('    <div class="feat"><div class="ic">%s</div><h3>%s</h3><p>%s</p></div>' % (ic, h, txt))
    o.append('  </div>\n  <details class="bd-auf"><summary>%s (%d)</summary>\n  <div class="raster">' % (t["alle_funktionen"], len(rest)))
    for ic, h, txt in rest:
        o.append('    <div class="feat"><div class="ic">%s</div><h3>%s</h3><p>%s</p></div>' % (ic, h, txt))
    o.append("  </div></details>")
    # Camping: ganz, aber aufklappbar (Anker #camping bleibt)
    o.append('  <details class="bd-auf" id="camping"><summary>%s</summary><p class="lead">%s</p>\n  <div class="verb">'
             % (t["camp_detail"], t["camp_lead"]))
    for h, txt in t["camp"]:
        o.append('    <div class="card"><h3>%s</h3>%s</div>' % (h, txt))
    o.append("  </div>")
    o.append('  <p class="lead">%s</p>\n  <div class="galerie">' % t["camp_bilder_lead"])
    for cap, bilder in t["camp_bilder"]:
        teile = reihe([x for x in bilder if x[1] != "handy"] + [x for x in bilder if x[1] == "handy"], p)
        o.append('    <figure>%s<figcaption><b>%s</b></figcaption></figure>' % (teile, html.escape(cap)))
    o.append("  </div></details>")
    # Bilder: 3 sichtbar, Rest aufklappbar
    o.append('  <h2 id="bilder">%s</h2><p class="lead">%s</p>\n  <div class="galerie">' % (t["h_bilder"], t["bilder_lead"]))
    for i, (cap, bilder) in enumerate(t["bilder"]):
        if i == 3:
            o.append('  </div>\n  <details class="bd-auf"><summary>%s (%d)</summary>\n  <div class="galerie">'
                     % (t["mehr_bilder"], len(t["bilder"]) - 3))
        teile = reihe([x for x in bilder if x[1] != "handy"] + [x for x in bilder if x[1] == "handy"], p)
        o.append('    <figure>%s<figcaption><b>%s</b></figcaption></figure>' % (teile, html.escape(cap)))
    o.append("  </div>" + ("</details>" if len(t["bilder"]) > 3 else ""))
    # Was du brauchst
    o.append('  <h2 id="brauchst">%s</h2>\n  <div class="card"><ul class="liste">%s</ul></div>'
             % (t["h_brauch"], "".join("<li>%s</li>" % x for x in t["brauch"])))
    # Download
    o.append('  <span id="download"></span><h2 id="%s">%s<span class="bald">%s</span></h2>' % (t["dl_anker"], t["h_dl"], t["dl_bald"]))
    o.append('  <div class="card"><p style="margin-top:0">%s</p>' % t["dl_text"])
    if t.get("bekannt"):
        o.append('    <div class="bd-hinweis warn" id="bekannter-fehler"><p>%s</p></div>' % t["bekannt"])
    o.append('    <div class="bd-knoepfe"><a class="bd-knopf gross haupt" href="%s" data-ver-href="panoptes.apk_url" data-umami-event="download" data-umami-event-quelle="apk">%s</a>'
             '<a class="bd-knopf leer" href="%s" data-ver-href="panoptes.release_url">%s</a><a class="bd-knopf leer" href="%s">%s</a></div>'
             % (DL_APK, t["dl_knopf"], DL_RELEASE, t["dl_release"], DL_QUELLE, t["dl_quelle"]))
    o.append('    <details class="bd-auf"><summary>%s</summary><p class="hash">%s: <code>%s</code><br>%s: <code>%s</code></p><p>%s</p></details>'
             % (t["echtheit"], t["dl_pruef"], sp("sha256", DL_SHA), t["dl_zert"], sp("zertifikat", DL_CERT), t["echtheit_text"]))
    o.append('    <details class="bd-auf"><summary>%s</summary><p>%s</p></details></div>' % (t["aelter"], t["dl_update"]))
    # Schritte: 5 kurze, ausführlich aufklappbar
    o.append('  <h2 id="schritte">%s</h2>\n  <ol class="bd-schritte">' % t["h_kurz"])
    for h, txt in t["kurz"]:
        o.append("    <li><b>%s</b>%s</li>" % (h, txt))
    o.append("  </ol>")
    o.append('  <details class="bd-auf"><summary>%s</summary><ol class="anl">' % t["ausfuehrlich"])
    for h, txt in t["anl"]:
        o.append("    <li><b>%s</b> %s</li>" % (h, txt))
    o.append("  </ol></details>")
    o.append('  <details class="bd-auf"><summary>%s</summary><ul class="liste">%s</ul></details>'
             % (t["h_stolper"], "".join("<li>%s</li>" % x for x in t["stolper"])))
    o.append('  <div class="card"><p style="margin-top:0">%s</p><p style="margin-bottom:0">%s</p></div>' % (t["dl_code"], t["dl_ds"]))
    # Daten: Kurzfassung sichtbar, Einzelheiten aufklappbar
    o.append('  <h2 id="datenschutz">%s</h2><p class="lead">%s</p>' % (t["h_ds"], t["ds_lead"]))
    o.append('  <details class="bd-auf"><summary>%s</summary><div class="tab"><table><tr><th>%s</th><th>%s</th><th>%s</th></tr>'
             % ((t["ds_detail"],) + t["ds_kopf"]))
    zeilen = list(t["ds"])
    if tuple(int(x) for x in VERSION.split(".")[:3]) >= (0, 1, 20):   # Zeilen ab 0.1.20 vor „Weitere Dienste“
        zeilen[-1:-1] = t.get("ds_ab_0120", [])
    if tuple(int(x) for x in VERSION.split(".")[:3]) >= (0, 1, 21):
        zeilen[-1:-1] = t.get("ds_ab_0121", [])
    for wo, was, wann in zeilen:
        o.append("    <tr><td><b>%s</b></td><td>%s</td><td>%s</td></tr>" % (html.escape(wo), html.escape(was), wann))
    o.append("  </table></div></details>")
    o.append('  <details class="bd-auf" id="zusammenhang"><summary>%s</summary><p class="lead">%s</p>' % (t["zus_detail"], t["zus_lead"]))
    o.append('  <div class="diagramm"><div class="breit">%s</div><div class="schmal">%s</div></div>\n  <div class="verb">'
             % (diagramm(t["svg"]), diagramm_schmal(t["svg"])))
    for nr, h, was, nicht in t["verb"]:
        o.append('    <div class="card"><h3><span class="nr">%s</span>%s</h3><p>%s</p><p class="nicht"><b>%s:</b> %s</p></div>'
                 % (nr, html.escape(h), html.escape(was), t["nicht"], html.escape(nicht.split(": ", 1)[1] if ": " in nicht[:20] else nicht)))
    o.append("  </div></details>")
    o.append('  <details class="bd-auf" id="stand"><summary>%s</summary><p class="lead">%s</p>' % (t["h_stand"], t["stand_lead"]))
    o.append('  <div class="tab"><table class="stand"><tr><th>%s</th><th>%s</th></tr>' % t["stand_kopf"])
    for was, wie in t["stand"]:
        o.append("    <tr><td>%s</td><td>%s</td></tr>" % (html.escape(was), html.escape(wie)))
    o.append("  </table></div></details>")
    # Hinweise
    o.append('  <h2 id="hinweise">%s</h2>\n  <div class="card"><p style="margin-top:0">%s</p><p style="margin-bottom:0"><a href="hinweise.html">%s →</a></p></div>'
             % (t["h_hinweise"], html.escape(t["hinweise_kurz"]), t["alle_hinweise"]))
    o.append(fuss(t, andere))
    return "\n".join(o)


def hinweise(t):
    de = t["lang"] == "de"
    kanon = BASIS + ("" if de else "en/") + "hinweise.html"
    andere = "/panoptes/en/hinweise.html" if de else "/panoptes/hinweise.html"
    o = [kopf(t, t["hw_title"], t["hw_stand"], BASIS + "hinweise.html", BASIS + "en/hinweise.html", kanon,
              "/panoptes/" if de else "/panoptes/en/", andere)]
    o.append('  <p style="margin:18px 0 0"><a href="./">%s</a></p>' % t["hw_zurueck"])
    o.append('  <h1 style="font-size:clamp(28px,5vw,40px)">%s</h1><p class="lead">%s</p>\n  <div class="card"><ol class="hw">'
             % (t["hw_h1"], t["hw_stand"]))
    for h, txt in t["hw"]:
        o.append("    <li><b>%s</b> %s</li>" % (html.escape(h), html.escape(txt.replace("{name}", NAME))))
    o.append("  </ol></div>")
    o.append(fuss(t, andere))
    return "\n".join(o)


def version_einsetzen(x, schluessel=""):
    """{V} = Version, {APK} = Dateiname. In sichtbarem HTML mit Markierung (wird live aus versionen.json aufgefrischt)."""
    if isinstance(x, str):
        if schluessel in ("title", "desc", "hw_title", "hw_stand"):
            return x.replace("{V}", VERSION).replace("{APK}", PV["apk_datei"])
        return x.replace("{V}", sp("version", VERSION)).replace("{APK}", sp("apk_datei", PV["apk_datei"]))
    if isinstance(x, list):
        return [version_einsetzen(i, schluessel) for i in x]
    if isinstance(x, tuple):
        return tuple(version_einsetzen(i, schluessel) for i in x)
    if isinstance(x, dict):
        return {k: version_einsetzen(v, k) for k, v in x.items()}
    return x


def main(bilder_quelle):
    global QUELLE, T
    for lang in T:
        T[lang].update(NEU[lang])
    T = version_einsetzen(T)
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
