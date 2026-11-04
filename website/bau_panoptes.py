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
        "desc": "Panoptes ist eine kostenlose Community-App für BYD-Autos mit DiLink 3, 4 und 5, derzeit in der Beta-Phase: Wächter mit Kamera, Fahrten und Laden mit Kosten, Wallbox, Fernzugang, Telegram-Meldungen, Karte mit Ladesäulen und Verbindung zum Routenplaner.",
        "zurueck": "← BYD EU Community",
        "eyebrow": "Kostenlos · für BYD mit DiLink 3, 4 und 5 · Beta",
        "h1a": "Panoptes", "h1b": "dein BYD, wach und vernetzt",
        "sub": "Eine App, die direkt am Bildschirm in deinem Auto läuft. Dazu eine Oberfläche, die du am Handy oder PC öffnest: Wächter mit Kamera, Fahrten und Laden mit Kosten, deine Wallbox, Fernzugang, Meldungen über Telegram, eine eigene Karte mit Ladesäulen und die Verbindung zum Routenplaner.",
        "wichtig": "<b>Neu:</b> Panoptes gibt es jetzt öffentlich als <b>Beta-Version {V}</b>, mit Quellcode und <a href=\"#installieren\">Schritt-für-Schritt-Anleitung</a>. Getestet ist es bisher vor allem auf einem BYD Dolphin Surf (DiLink 3). Panoptes ist ein privates Freizeitprojekt und nicht von BYD. Bitte lies vor der Installation die <a href=\"hinweise.html\">Hinweise</a>.",
        "hero_alt_pc": "Panoptes 0.1.38 am Bildschirm im Auto: Seite Display mit der Auswahl Was zeigt der Tacho",
        "hero_alt_handy": "Panoptes 0.1.38 am Handy: Wächter mit großem Schalter",
        "h_camp": "Camping-Modus <span class=\"bald\">Beta</span>",
        "camp_lead": "Seit 0.1.16.1: Du schläfst im Auto, und Panoptes passt auf Strom, Wächter und Bildschirm auf. Heizen ist noch in der Beta-Phase. Ab Werk läuft nur ein Probelauf; die Heizart wählst du auf der Camping-Seite.",
        "camp": [
            ("Was er tut", "<ul class=\"liste\"><li><b>Wächter „bewohnt“:</b> Solange Camping läuft, schreckt der Wächter nicht ab (kein Bildschirm, Licht oder Hupe) und meldet keinen Erschütterungsalarm, wenn du dich bewegst.</li><li><b>Nachtbildschirm:</b> Nach einer einstellbaren Zeit ohne Berührung wird der Bildschirm fast schwarz, mit großer Uhr und ein paar Zahlen. Ohne Töne.</li><li><b>Akku-Schutz und Restdauer:</b> Du legst eine Untergrenze fest (ab Werk 20 %). Panoptes zeigt, wie lange der Akku für die Heizung reicht, und hört vor der Grenze auf. Das Auto schaltet Panoptes nie ab.</li></ul>"),
            ("Einschalten", "<ul class=\"liste\"><li>Per Tipp am Bildschirm im Auto, nur im Stand (Gang P).</li><li>Am Handy über die Oberfläche von Panoptes.</li><li>Über Telegram mit <code>/camping</code>.</li><li>Planen zu einer festen Zeit (Start und Weckzeit) geht ab 0.1.17 über die Schnittstelle von Panoptes; die Bedienung im EV-Cockpit folgt.</li><li>Beim Losfahren endet Camping von selbst.</li></ul>"),
            ("Heizen: Beta", "<p><b>Panoptes heizt erst, wenn du auf der Camping-Seite eine Heizart wählst.</b> Bis dahin läuft ein Probelauf: Panoptes zeigt nur, was es tun würde, und schaltet nichts.</p><ul class=\"liste\"><li><b>Auto an:</b> Panoptes schaltet die Klimaanlage direkt.</li><li><b>Auto aus:</b> über die BYD-Cloud, dafür brauchst du ein BYD-Konto. Das weckt das Auto bei jedem Heizgang.</li></ul>"),
            ("Grenzen", "<ul class=\"liste\"><li><b>Kein Innenraumfühler:</b> Der Dolphin Surf hat keinen. Panoptes zeigt deshalb nie eine Innentemperatur und heizt in Intervallen nach der Außentemperatur („alle x Minuten für y Minuten“). Optional kannst du einen externen Fühler dazunehmen.</li><li><b>Verbrauch:</b> Grob 1,5 bis 3 % Akku pro Stunde bei 0 °C, wenn geheizt wird. Das ist eine Schätzung, kein Messwert; Panoptes lernt aus deinem echten Verbrauch.</li><li><b>Nach DC-Ladeende:</b> BYD schaltet das Auto dann selbst ab.</li><li>Camping ersetzt keine Aufsicht. Lass nie Kinder oder Tiere allein im Auto.</li></ul>"),
        ],
        "camp_bilder_lead": "Die Bilder stammen aus einem Emulator, nicht aus einem Auto. Darum steht bei den Werten „nicht verfügbar“, und die Modellangabe oben ist die des Emulators. Im Auto siehst du hier deine echten Werte. Klick auf ein Bild zum Vergrößern.",
        "camp_bilder": [
            ("Camping-Seite am Bildschirm im Auto: Einschalten, Akku, Heizdauer; oben der Hinweis „Probelauf“.", [("camping", "display", "Camping-Seite von Panoptes: Camping ist aus, Knopf Einschalten, Hinweis Probelauf, Werte noch nicht verfügbar")]),
            ("Einstellungen: Wärme, Heizweg, Akku-Untergrenze, 12-V-Warnung.", [("camping-einstellungen", "display", "Camping-Einstellungen: Wärme, Heizweg Probelauf, Vorheizen, Akku-Untergrenze 20 Prozent, 12-Volt-Warnung")]),
            ("Nachtbildschirm: fast schwarz, große Uhr, Rückmeldung „Zu kalt / Passt / Zu warm“. Daneben die Camping-Seite am Handy.", [("nacht", "display", "Nachtbildschirm: schwarzer Hintergrund, große Uhr und Datum, Tasten Zu kalt, Passt, Zu warm"), ("camping", "handy", "Camping-Seite am Handy bei 390 Pixel Breite")]),
        ],
        # Alle Funktionen nach den 7 Bereichen (FUNKTIONEN_ABGLEICH.md, 04.11.2026). PFLEGE bei jeder Version; Zeichen nur A (nur bestimmte Autos) und B (Beta), kein „Testauto“ (Alfred 04.11.2026).
        "alle": {"h": "Alles, was Panoptes {V} kann",
                 "lead": "Nach Bereichen. Ohne Zeichen heißt: fertig.",
                 "chips": {"A": "nur bestimmte Autos", "B": "Beta"},
                 "gruppen": [
            ("Start", [
                ("Leiste mit sieben Bereichen: Start, Steuerung, Kameras & Wächter, Fahrten & Laden, Regeln, Apps & Display, Einstellungen", ""),
                ("Startseite mit Ladestand, Reichweite, Standort, Zustand des Autos, Wächter heute und letzten Fahrten", ""),
                ("Reichweite „heute“, gelernt aus deinen eigenen Fahrten", ""),
                ("Schnellknöpfe: zusperren, vorklimatisieren, Kofferraum", "A"),
                ("Großer Knopf „Heizen stoppen“", ""),
                ("Frag Panoptes (KI-Assistent), nur wenn du ihn einrichtest; darf nur Klima, Sitzheizung und Sonnenrollo bedienen", ""),
            ]),
            ("Steuerung", [
                ("Auto zu- und aufsperren, Kofferraum, Fenster, Schiebedach, Sonnenrollo", "A"),
                ("Klima, Temperatur, Gebläse; vorklimatisieren mit Zeitplan", "A"),
                ("Sitzheizung, Sitzlüftung, Lenkradheizung", "A"),
                ("Akku heizen (über die BYD-Cloud)", "A"),
                ("Laden am Auto: Ladegrenze, Ladestrom, Zeitplan, „Jetzt laden“", "A"),
                ("Auto finden (Blinken, Hupe), Tagfahrlicht, Ambientelicht", "A"),
                ("Töne nach außen (z. B. Gong), nur in P", "A"),
                ("Sitzpositionen speichern, Fahrzeugtasten selbst belegen", "A"),
                ("Sicherheitssysteme (z. B. Spurhalten) ausschalten nur nach Bestätigung", ""),
                ("3D-Auto in deiner Farbe", ""),
                ("Camping-Modus mit Nachtbildschirm und Akku-Schutz", ""),
                ("Camping-Heizen, Heizart auf der Camping-Seite wählen", "B"),
                ("Tiermodus: hält das Klima für dein Tier an (nur eine Hilfe, keine Garantie)", "A"),
            ]),
            ("Kameras & Wächter", [
                ("Wächter mit großem Schalter; du wählst, wann er aufnimmt (Erschütterung, KI überall, KI nur an privaten Orten)", ""),
                ("Abschreckung am Bildschirm, nur wenn eine Person da ist", ""),
                ("Schutz der 12-V-Batterie: Wächter legt sich rechtzeitig schlafen", ""),
                ("Zeitplan für den Wächter, Bildbereiche festlegen, private Orte", ""),
                ("Beim Einsteigen: „Während du weg warst: n Aufnahmen“", ""),
                ("Dashcam-Clip bei Vollbremsung oder Stoß, merkt sich den Auslöser (ohne Ort)", ""),
                ("Live-Bild aller Kameras", ""),
                ("Aufnahmen ansehen, nach Tag und Art (Person, Fahrzeug, Fahrrad, Tier)", ""),
                ("Aufnahme-Einstellungen: Dauer-Aufnahme beim Fahren, Qualität, Speicherort", ""),
                ("Parkprotokoll: wer neben dir stand", ""),
                ("Durchsage nach außen: sprechen oder Text", ""),
                ("Toter Winkel beim Blinken als ein Bild", "A"),
            ]),
            ("Fahrten & Laden", [
                ("Karte mit Ladesäulen und freien Plätzen; Kartenquelle wählst du", ""),
                ("Orte suchen und als Ziel ins Navi schicken; Ziel aus Google-Maps- oder Waze-Link", ""),
                ("„Reicht es noch?“ mit Ladestopp-Vorschlag", ""),
                ("Günstigste Säule in der Nähe, mit deinem Preis", ""),
                ("Fahrtenbuch mit großem Schalter, Verbrauch", ""),
                ("Fahrstil, Strecken vergleichen", ""),
                ("Verbrauch nach Außentemperatur, Verlust im Stand", ""),
                ("Fahrtenbuch als Datei (ohne Orte), verlorene Fahrten zurückholen", ""),
                ("Monatsbericht, auch zum Drucken", ""),
                ("Ladekosten mit geschätztem Ladeverlust; „Laut Säule“ eintragen", ""),
                ("Ladesäule automatisch erkennen; „Wo hast du geladen?“", ""),
                ("Ladeleistung, Zelltemperatur, Akku-Gesundheit im Verlauf", ""),
                ("Ladekarten und Netze im Auto", ""),
                ("Zu Hause laden mit Zeitfenster, auf Wunsch zum Börsenpreis", ""),
                ("Warm zur Abfahrt (ab Werk aus)", "A"),
                ("Wallbox über evcc, Home Assistant, Tuya oder direkt", "B"),
                ("Straßenzustand: Schlaglöcher erkennen und warnen", ""),
            ]),
            ("Regeln", [
                ("Regeln „Wenn … / Dann …“ selbst bauen, sichern und wiederherstellen", ""),
                ("Regeln der Community übernehmen (ab Werk aus)", ""),
                ("Gewohnheiten: Panoptes schlägt Regeln vor, die Daten bleiben im Auto", ""),
                ("Deine Orte: Zuhause, Garage, Ladeplatz mit Preis", ""),
                ("Alle Meldungen auf einer Seite: Handy und Telegram je Thema, Nachtruhe", ""),
                ("Telegram-Bot mit Befehlen (z. B. /status, /wo, /camping, /tier)", ""),
                ("Abschaltbericht in Telegram nach dem Abstellen", ""),
            ]),
            ("Apps & Display", [
                ("Alles fürs Display auf einer Seite „Display“: Tacho, Hintergrundbild, Sperre, Launcher", ""),
                ("Zwei Apps nebeneinander am Bildschirm", "A"),
                ("„Handy im Auto“: Android Auto und CarPlay, wenn dein Auto sie hat", "A"),
                ("Eigenes Bild, Bildschirm-Sperre mit Zahlencode, Apps aus und an", ""),
                ("Bildschirm reinigen, USB-Stick lesen, Dateien zwischen Handy und Auto", ""),
                ("Rotes Band, solange der Bildschirm geteilt wird", ""),
                ("Tacho: Anzeigen, Navi und Apps, läuft ruhiger; „Tacho wieder normal“", "A"),
                ("Abbiegepfeile im BYD-Tacho (ab Werk aus)", "A"),
                ("Panoptes Launcher: eigene App, frei einrichtbar, auch am Handy oder im Cockpit (nur mit Erlaubnis), mit App-Schublade und Klima im Dock", ""),
                ("Hell oder dunkel, fünf Startansichten", ""),
                ("Blitzer-Warnung (nur Österreich, ab Werk aus)", ""),
            ]),
            ("Einstellungen", [
                ("Kurze Einrichtung; freiwillige Schritte unter Einstellungen → Einrichtung → „Noch einrichten“", ""),
                ("Updates in der App; ohne WLAN fragt Panoptes vorher und nennt die Größe", ""),
                ("Fehler melden in der App", ""),
                ("Fernzugang über Tailscale, Brücke für Handy und PC (ab Werk aus)", ""),
                ("Geräte koppeln mit Prüfzahl; Rechte je Gerät, Zusatzrechte nie von selbst", ""),
                ("Protokoll „Wer hat was gemacht?“", ""),
                ("Home Assistant über MQTT, Routenplaner, EV-Cockpit", ""),
                ("ABRP-Anbindung", ""),
                ("Umstieg von OverDrive", ""),
                ("Einstellungen sichern und wiederherstellen", ""),
                ("Panoptes prüft täglich seine Rechte; Logs bleiben bei Updates", ""),
                ("Fünf Sprachen", ""),
            ]),
                 ]},
        "h_kann": "Was Panoptes kann",
        "kann": [
            ("🚗", "Am Bildschirm im Auto", "Panoptes läuft als eigene App im Vollbild, mit großen Tasten. Während der Fahrt sind Einstellungen gesperrt; Start, Karte und Wächter bleiben erreichbar."),
            ("🧩", "Einrichtungshilfe", "Beim ersten Start führen dich kurze Schritte durch das Nötigste. Alles Weitere findest du später unter „Noch einrichten“. Fast nichts ist vorausgewählt (nur „Gewohnheiten merken“ steht auf Ja, das bleibt im Auto); alles, was Daten nach außen schickt, bleibt aus, bis du es einschaltest. Was dein Auto nicht kann, überspringt er mit einer Erklärung."),
            ("🛡️", "Wächter mit KI-Erkennung", "Steht dein Auto, achten die Kameras auf das Umfeld. Du entscheidest selbst, wann aufgenommen wird: nur bei Erschütterung, mit KI-Erkennung überall oder nur an deinen privaten Orten wie Garage oder Einfahrt. Ohne Wahl nimmt er nur bei Erschütterung auf. Damit die 12-V-Batterie geschont wird, legt er sich schlafen; die Grenze richtet sich nach dem Batterietyp (Blei, AGM oder LFP)."),
            ("📹", "Dashcam <span class=\"bald\">ab 0.1.27</span>", "Bei einer Vollbremsung oder einem Stoß sichert Panoptes von selbst einen kurzen Clip aus allen Kameras, etwa 20 Sekunden davor und danach. Ohne Daueraufnahme. Die Clips bleiben im Auto oder auf dem USB-Stick und werden nie von selbst verschickt. Clips am Handy ansehen und speichern geht mit der <a href=\"/app/\">Handy-App</a> (Beta 4). Panoptes fragt dann „Behalten?“, sonst wird der Clip nach 72 Stunden gelöscht. Ab 0.1.36 merkt sich jeder Clip, was ihn ausgelöst hat (ohne Ort). In der Schweiz ist die Dashcam ab Werk aus. Ob Aufnahmen beim Fahren bei dir erlaubt sind, ist je nach Land verschieden, siehe <a href=\"hinweise.html\">Hinweise</a>."),
            ("📒", "Fahrten und Laden", "Fahrten, Verbrauch und Ladungen werden im Auto mitgeschrieben. Panoptes zeigt die Kosten je Ladung, je Monat und als Ø Kosten je 100 km, ab 0.1.35 mit geschätztem Ladeverlust (Zeichen „~“). Fehlt ein Preis, steht dort „Preis fehlt“ statt einer erfundenen Zahl; Gratis-Laden lässt sich ausdrücklich eintragen."),
            ("🔌", "„Wo hast du geladen?“", "Nach dem Laden fragt Panoptes im Stand, nie während der Fahrt, nach Station und Preis. Mit „Ort merken“ kennt es den Preis beim nächsten Mal. Mit „Laut Säule“ trägst du kWh und Kosten der Säule ein; dein Preis gilt dann bei „Günstigste in der Nähe“ (AC und DC getrennt). Die Frage lässt sich abschalten."),
            ("💳", "Deine Ladekarten im Auto", "Ladekarten und Netze, Mindestleistung, Stecker und Ankunfts-Ladestand stellst du im Auto ein. Der Routenplaner rechnet damit; gespeichert wird das nur im Auto."),
            ("🏠", "Wallbox <span class=\"bald\">Beta</span>", "Deine Wallbox über evcc, Home Assistant oder Tuya einrichten, ab Version 0.1.12 auch direkt (z. B. go-e, KEBA, openWB, Easee, Zaptec): Ladestand sehen, Modus, Ladegrenze und Strom einstellen. Steuern nur, wenn das Auto steht, mit Rückfrage und je Ladepunkt eigens freigegeben. Bisher nur mit Demo- und Testgeräten geprüft."),
            ("📍", "Deine Orte", "Eine Liste für alles: Zuhause, Garage, Arbeit oder der Ladeplatz mit eigenem Preis. Je Ort legst du fest, ob er privat ist (Wächter), ein Ladepreis gilt oder er als Ziel im Navi steht. Die Orte verlassen das Auto nicht."),
            ("🌍", "Fernzugang", "Über Tailscale erreichst du dein Auto von überall. Eingerichtet wird das mit einem QR-Code am Bildschirm im Auto und deinem eigenen Tailscale-Konto. Für Fortgeschrittene gibt es ab 0.1.14 zusätzlich einen unabhängigen Notzugang, ab Werk aus."),
            ("💬", "Meldungen über Telegram", "Dein eigener Bot meldet Wächter-Ereignisse, Laden, schwache Starterbatterie, Reifendruck und Updates. Jede Kategorie einzeln schaltbar, mit Ruhezeit für die Nacht. Bilder und Videos nur, wenn du das einschaltest."),
            ("🗺️", "Karte mit Ladesäulen", "Du wählst selbst, woher die Karte kommt: vom Community-Server (mit Gelände und freien Ladeplätzen, wo Betreiber Daten liefern), von OpenStreetMap oder gar nicht. Solange du nichts wählst, bleibt die Karte leer. Blitzer zeigt sie nur in Österreich, ab Werk aus und mit Rechtshinweis."),
            ("🔋", "„Reicht es noch?“", "Mit einer Route aus dem Routenplaner, auch mit Zwischenzielen, sagt dir Panoptes unterwegs, ob der Akku bis zum nächsten Stopp reicht, und schlägt bei Bedarf einen Ladestopp vor."),
            ("📊", "Monatsbericht", "Gefahrene Kilometer, Verbrauch, Laden und Kosten, Standverlust und Wächter-Ereignisse eines Monats auf einen Blick, auch zum Drucken. Gerechnet wird im Auto."),
            ("🔁", "Umstieg von OverDrive", "Wer bisher die App OverDrive genutzt hat, übernimmt Fahrten, Ladungen und Einstellungen, mit Vorschau und ohne Doppelte. Einwilligungen und riskante Schalter übernimmt Panoptes nie, die stellst du selbst ein."),
            ("🧭", "Verbindung zum Routenplaner", "Panoptes lässt sich mit deinem Konto auf <a href=\"/ev/\">byd.serveone.at/ev/</a> verbinden: Code am Auto anzeigen, am Handy bestätigen, fertig. Jederzeit trennbar."),
            ("🖥️", "EV-Cockpit am PC", "Das <a href=\"/ev-cockpit/\">EV-Cockpit</a> zeigt die Daten von Panoptes am PC, auch Ladungen und Kosten, und kann die Einstellungen ändern. Koppeln bestätigst du mit einem Tipp und einer vierstelligen Prüfzahl."),
            ("⬆️", "Updates in der App", "Panoptes sucht auf Wunsch selbst nach neuen Versionen. Installiert wird nur, wenn das Auto steht und die Zündung aus ist. Ab 0.1.13 verändert Panoptes von selbst keine dauerhaften Android-Einstellungen mehr (etwa „Bildschirm immer an“); früher gesetzte Werte lassen sich zurücksetzen. Was du selbst änderst (eigenes Bild, Apps ausschalten), bleibt, bis du es zurückstellst. Ab 0.1.36 bleiben die Logs bei Updates erhalten."),
            ("🏕️", "Camping-Modus <span class=\"bald\">Beta</span>", "Wächter „bewohnt“, Nachtbildschirm, Akku-Schutz mit Restdauer. Einschalten per Tipp, am Handy oder mit /camping in Telegram. Die Heizart wählst du auf der Camping-Seite; ab Werk nur Probelauf. <a href=\"#camping\">Mehr dazu</a>"),
            ("🖼️", "Bildschirm <span class=\"bald\">ab 0.1.37</span>", "Eigenes Bild für den Startbildschirm. Bildschirm mit Zahlencode sperren (nur in P). Apps aus- und einschalten. USB-Stick lesen."),
            ("🚀", "Panoptes Launcher <span class=\"bald\">ab 0.1.37</span>", "Eigene App, freiwillig: Startbildschirm mit Klima im Dock, Android Auto und CarPlay (wenn dein Auto sie hat) und Update-Hinweis. Installieren per Knopf in Panoptes, nie von selbst. Ab 0.1.38 richtest du ihn bequem am Handy oder im Cockpit ein, nur wenn du es bei der Kopplung erlaubst. Das Haus links führt immer zum BYD-Startbildschirm zurück. <a href=\"#tacho-launcher\">Bilder</a>"),
            ("🐾", "Tiermodus <span class=\"bald\">ab 0.1.36</span>", "Hält das Klima für dein Tier an und meldet Probleme aufs Handy und in Telegram. Nur eine Hilfe, keine Garantie, du bleibst verantwortlich."),
            ("🤖", "KI-Assistent", "Nur, wenn du ihn selbst einrichtest. Ab 0.1.36 darf er nur Klima, Sitzheizung und Sonnenrollo bedienen und Werte anzeigen. Nie Hupe, Licht, Blinker, Fenster, Kofferraum oder Wächter."),
            ("🧰", "Kleine Helfer <span class=\"bald\">ab 0.1.36</span>", "Bildschirm reinigen (30 Sekunden gesperrt, nur in P). Ziel aus einem Google-Maps- oder Waze-Link übernehmen. Dateien zwischen Handy und Auto (eigenes Recht, ab Werk aus, keine Apps). Panoptes prüft täglich seine Rechte und repariert, was geht."),
            ("🌐", "Fünf Sprachen", "Deutsch, Englisch, Französisch, Italienisch und Niederländisch."),
        ],
        "h_bilder": "So sieht Panoptes aus",
        "bilder_lead": "Panoptes 0.1.38 am Bildschirm im Auto und am Handy, aufgenommen im Emulator mit Musterdaten, nicht aus einem Auto. Unter „Mehr Bilder“ stehen auch ältere Bilder aus 0.1.10, bis es neue gibt. Klick auf ein Bild zum Vergrößern.",
        "bilder": [
            ("Kameras & Wächter: ein großer Schalter, darunter die Aufnahmen von heute.", [("waechter38", "display", "Wächter am Bildschirm im Auto: Wächter ist aus, großer Knopf Wächter einschalten"), ("waechter38", "handy", "Wächter am Handy mit großem Schalter")]),
            ("Apps & Display → Display: „Was zeigt der Tacho?“ Ein Bild antippen.", [("display38", "display", "Seite Display: Tacho, Hintergrund und Sperre, Launcher; Auswahl Was zeigt der Tacho"), ("display38", "handy", "Seite Display am Handy")]),
            ("Einstellungen: „Was möchtest du einstellen?“, mit Suche.", [("system38", "display", "Alle Einstellungen: Verbindungen, Auto und Anzeige, App und Daten, Erweitert"), ("system38", "handy", "Alle Einstellungen am Handy")]),
            ("Einrichtung: unter „Noch einrichten“ stehen freiwillige Schritte.", [("einrichtung38", "display", "Einrichtung: Liste Noch einrichten mit freiwilligen Schritten"), ("einrichtung38", "handy", "Noch einrichten am Handy")]),
            ("Steuerung am Handy: Kacheln für Sicherheit, Kofferraum, Klima und Sitze.", [("steuerung38", "handy", "Steuerung am Handy mit Kacheln Sicherheit, Kofferraum, Klima, Sitze")]),
            ("Älteres Bild (0.1.10): Karte mit Ladesäulen und freien Plätzen.", [("karte", "pc", "Karte mit Ladesäulen am PC"), ("karte", "display", "Karte am Bildschirm im Auto")]),
            ("Älteres Bild (0.1.10): Monatsbericht mit Kilometern, Verbrauch, Laden und Wächter.", [("monatsbericht", "pc", "Monatsbericht am PC"), ("monatsbericht", "display", "Monatsbericht am Bildschirm im Auto")]),
            ("Älteres Bild (0.1.10): Gerät koppeln mit Prüfzahl.", [("geraete", "pc", "Gerät koppeln: das EV-Cockpit möchte sich verbinden, Prüfzahl 4711")]),
            ("Älteres Bild (0.1.10): Telegram, jede Meldungsart einzeln.", [("telegram", "handy", "Telegram-Meldungen am Handy, jede Art einzeln schaltbar")]),
        ],
        "handy": "am Handy", "pc": "am PC",
        "h_zus": "Wie alles zusammenhängt",
        "zus_lead": "Panoptes läuft im Auto. Alles andere ist freiwillig und lässt sich einzeln verbinden und wieder trennen.",
        "svg": {"auto": "Panoptes", "auto2": "im Auto", "cockpit": "EV-Cockpit", "cockpit2": "am PC", "planer": "Routenplaner", "planer2": "byd.serveone.at/ev/",
                "karte": "Community-Karte", "karte2": "Kacheln, Ladesäulen", "tg": "Telegram-Bot", "tg2": "dein eigener", "ha": "Home Assistant", "ha2": "dein eigener",
                "wb": "Wallbox", "wb2": "Beta",
                "t1": "Kopplung", "t2": "Konto, Ziel, Fahrtenbuch E2E", "t3": "Karte (wenn gewählt)", "t4": "Meldungen", "t5": "Heimnetz", "t6": "direkt", "t7": "Route, Ladekarten",
                "aria": "Grafik: Panoptes im Auto in der Mitte, verbunden mit EV-Cockpit am PC, Routenplaner, Community-Karte, Telegram-Bot, Wallbox und Home Assistant"},
        "verb": [
            ("1", "Panoptes ↔ EV-Cockpit (Kopplung)", "Du erlaubst das Cockpit einmal mit einer Prüfzahl, in Telegram oder auf der Panoptes-Seite. Dann holt das Cockpit Fahrzeugwerte, Einstellungen und das Fahrtenbuch direkt aus dem Auto, über dein Heimnetz oder Tailscale.",
             "Nicht dabei: Fernzugang, Passwort und Anschlüsse. Nichts davon läuft über unsere Server, das Fahrtenbuch bleibt auf deinem PC. Den Zugang hebt das Cockpit im Schlüsselbund deines Rechners auf. Was es sonst an Server schickt (Karte, 3D-Modell, Routenplaner, Zählung), entscheidest du mit eigenen Häkchen; ohne Häkchen nichts."),
            ("2", "Panoptes ↔ Routenplaner", "Nach dem Verbinden kommt dein Ziel mit Ladestopps ins Auto. Panoptes meldet Ladestand, Verbrauchsfaktor und Fahrstatus, damit der Plan stimmt. Schaltest du es ein (standardmäßig aus) und rufst auf /ev/ dein Fahrtenbuch ab, kommt es Ende-zu-Ende verschlüsselt direkt vom Auto in deinen Browser.",
             "Nicht dabei: Der Server kann das Fahrtenbuch nicht lesen; er bekommt nur verschlüsselte Daten und hält sie laut Routenplaner höchstens 2 Minuten im Arbeitsspeicher. Die ungefähre Position geht nur mit, wenn Panoptes unterwegs einen neuen Ladestopp vorschlägt."),
            ("3", "Panoptes ↔ Community-Karte", "Wenn du sie als Kartenquelle wählst, kommen Kartenkacheln und Ladesäulen-Daten von byd.serveone.at, mit Live-Belegung, wo es offene Daten gibt. Ohne Wahl lädt Panoptes keine Karte.",
             "Nicht dabei: Fahrten und Aufnahmen. Der Server sieht nur deine IP-Adresse und den Kartenausschnitt. Geteilte Regeln gehen nur an den Community-Server, wenn du sie selbst teilst (standardmäßig aus)."),
            ("4", "Panoptes → Telegram", "Dein eigener Bot schickt dir Meldungstexte. Bilder und Videos nur, wenn du das ausdrücklich einschaltest; dann liegen sie auf den Servern von Telegram.",
             "Nicht dabei: Keine Videos auf unseren Servern, kein Umweg über das Projekt."),
            ("5", "Panoptes ↔ Wallbox (Beta)", "Panoptes spricht deine Wallbox im Heimnetz an, über evcc, Home Assistant, Tuya oder direkt. Steuern geht nur, wenn das Auto steht und du den Ladepunkt freigegeben hast, jede Änderung mit Rückfrage. Die Freigabe nimmst du jederzeit zurück.",
             "Nicht dabei: Nichts davon läuft über unsere Server. Zugangsdaten liegen verschlüsselt im Auto. Hersteller-Clouds (Easee, Zaptec, Tuya) nur mit deiner Einwilligung je Gerät."),
            ("6", "Panoptes ↔ Home Assistant", "Dein Auto verbindet sich direkt mit deinem eigenen Home Assistant, ohne unsere Server. Dort siehst du Werte wie Ladestand und Reichweite, baust eigene Automationen und bekommst Meldungen. Das geht über MQTT, das du unter Panoptes einstellst. Die eigene <a href=\"https://github.com/samuelvoltarius/panoptes-homeassistant\" target=\"_blank\" rel=\"noopener\">Integration für Home Assistant</a> ist eine Beta und lässt sich über HACS installieren. Unterwegs im Mobilfunk geht sie nur über Tailscale.",
             "Nicht dabei: Die Daten liegen bei dir, nicht bei uns."),
            ("7", "EV-Cockpit ↔ Routenplaner", "Das Cockpit zeigt die bereitliegende Route und deine Ladekarten. Ist es mit Panoptes gekoppelt, meldet nur Panoptes den Ladestand, damit nichts doppelt ankommt.",
             "Nicht dabei: Deine Fahrten bleiben auf dem PC."),
        ],
        "nicht": "Das bleibt privat",
        "h_ds": "Datenschutz: was wohin geht",
        "ds_lead": "Grundsatz: Deine Aufnahmen, Fahrten und Positionen bleiben im Auto. Schaust du Aufnahmen unterwegs am Handy an, laufen sie Ende-zu-Ende verschlüsselt durch unsere Brücke; der Server kann sie nicht lesen und speichert sie nicht. Das meiste, was Daten nach außen schickt, ist standardmäßig aus; du schaltest es einzeln ein, und Panoptes sagt dir vorher, wohin die Daten gehen. Ausnahmen sind die Update-Prüfung und die Kartensuche, beide stehen unten in der Tabelle. Es gibt keine Werbung und kein Tracking.",
        "ds_kopf": ("Wohin", "Was", "Wann"),
        "ds": [
            ("Im Auto (USB-Stick, App)", "Wächter-Aufnahmen, Fahrtenbuch, Ladungen und Preise, Monatsbericht, deine Orte, Ladekarten, Einstellungen; Zugangsdaten (z. B. für die Wallbox) verschlüsselt", "immer. Bei neuer Einrichtung löscht Panoptes Aufnahmen nach 72 Stunden, einzelne kannst du behalten. Fehlt eine Datei (z. B. USB-Stick nicht eingesteckt), wird die Fahrt markiert, nicht gelöscht."),
            ("EV-Cockpit auf deinem PC", "Fahrzeugwerte, Fahrten, Ladungen und Kosten; deine Orte nur mit Namen, nie mit Koordinaten", "nur nach dem Koppeln, direkt vom Auto über dein Heimnetz oder Tailscale"),
            ("Kartenquelle (Community-Server byd.serveone.at oder OpenStreetMap Deutschland)", "Deine IP-Adresse und der Kartenausschnitt, also ungefähr, wo dein Auto steht. Beim Community-Server zusätzlich die Abfrage freier Ladeplätze für den Ausschnitt.", "erst, wenn du unter System → Kartenquelle eine Quelle wählst. Am Bildschirm im Auto gilt die Wahl fürs ganze Auto; Handy und PC fragen getrennt."),
            ("Brücke: Handy und PC übers Internet (byd.serveone.at)", "Daten, Befehle und Aufnahmen zwischen Auto und deinen gekoppelten Geräten, Ende-zu-Ende verschlüsselt. Der Server sieht nur unlesbare Daten und speichert keine Inhalte, <a href=\"/datenschutz#bruecke\">Details</a>.", "nur, wenn du die Brücke im Auto einschaltest"),
            ("Gekoppelte Dienste und Heimserver (zum Beispiel Home Assistant)", "Meldungen zu Wächter-Ereignissen: Art und Zeit, keine Koordinaten. Mit dem Schalter „Standbild bei Ereignis“ ein Foto je Ereignis, kein Video, nichts Älteres als 15 Minuten. Wächter-Aufnahmen nur mit dem eigenen Schalter „Aufnahmen“. Fotos können Passanten zeigen.", "nur für Dienste, die du selbst koppelst; jedes Recht mit eigenem Schalter"),
            ("Meldungen aufs Handy (ntfy oder Google)", "Die Meldung, Ende-zu-Ende verschlüsselt: Der Zustelldienst sieht nur, dass eine Meldung kommt, und ihre ungefähre Größe, <a href=\"/datenschutz#handy-meldungen\">Details</a>.", "nur mit gekoppelter Handy-App und eingeschalteten Meldungen"),
            ("Web-App fürs iPhone (panoptes.serveone.at)", "Die Seite kommt von unserem Server, ohne Cookies und ohne Zugriffsprotokoll. Zum Auto geht es über die Brücke, Ende-zu-Ende verschlüsselt; der Kopplungsschlüssel bleibt auf deinem iPhone. Bei der Ortssuche geht dein Suchtext an byd.serveone.at, <a href=\"/datenschutz#handy-orte\">Details</a>.", "nur, wenn du die Web-App nutzt"),
            ("Telegram", "Meldungstexte; Bilder und Videos nur, wenn du das einschaltest (dann liegen sie bei Telegram)", "nur mit eigenem Bot"),
            ("Tailscale", "Verbindung für den Fernzugang und den Notzugang, in deinem eigenen Tailscale-Netz", "nur mit eingerichtetem Fernzugang; der Notzugang ist ab Werk aus"),
            ("Deine Wallbox", "Ladebefehle im Heimnetz; Easee, Zaptec und die Tuya-Cloud über die Hersteller-Cloud", "nur, wenn du eine Wallbox einrichtest; Hersteller-Cloud nur mit eigener Einwilligung je Gerät"),
            ("Routenplaner (byd.serveone.at/ev)", "Ladestand, Verbrauchsfaktor, Fahrstatus und deine Ladekarten für die Preisabfrage (der Server speichert sie nicht); die ungefähre Position nur für einen neu vorgeschlagenen Ladestopp oder, wenn du es erlaubst, für Preisvorschläge nach dem Laden. Das Fahrtenbuch nur, wenn du es einschaltest (standardmäßig aus) und auf /ev/ selbst abrufst: Ende-zu-Ende verschlüsselt, der Server bekommt nur verschlüsselte Daten und hält sie laut Routenplaner höchstens 2 Minuten im Arbeitsspeicher.", "nur nach dem Verbinden, jederzeit trennbar"),
            ("Community-Server (byd.serveone.at/community)", "geteilte Regeln, nur wenn du sie teilst; Straßenschäden, nur wenn du sie meldest, <a href=\"/datenschutz#panoptes-community\">Details</a>", "standardmäßig aus"),
            ("Wetter (über unseren Server byd.serveone.at, der fragt Open-Meteo)", "ein grobes Feld von etwa 10 km, ohne Kennung", "nur mit deiner Einwilligung, standardmäßig aus"),
            ("Panoptes-Zählung (freiwillig, Standard aus)", "Zufalls-ID und Version, einmal am Tag; Automodell und DiLink-Version nur, wenn du das eigens bestätigt hast. Keine IP-Speicherung, keine Fahrgestellnummer, kein Ort. Ausschalten löscht die Einträge am Server; Einträge ohne Meldung seit 90 Tagen werden anonym zu einer Monatszahl zusammengefasst.", "nur, wenn du unter Einstellungen → Datenschutz „Anonym mitzählen“ einschaltest (byd.serveone.at/panoptes/ping, ab 0.1.17)"),
            ("Fehler melden und Tacho-Test (byd.serveone.at)", "dein Text oder der Testbericht, Version, Automodell, DiLink-Version, Sprache; ein geschwärzter Diagnose-Auszug nur mit Haken. Keine Kennung, keine IP-Speicherung, kein Ort. Nach 180 Tagen gelöscht, <a href=\"/datenschutz#fehler-melden\">Details</a>.", "nur, wenn du selbst absendest"),
            ("Kartensuche und Orte entlang der Route (Karte im Auto)", "Dein Suchtext und, damit Treffer in der Nähe kommen, die auf etwa 1 km gerundete Position des Autos gehen direkt vom Auto an öffentliche Dienste: Photon (komoot), Nominatim (OpenStreetMap), je nach Einstellung Stadia Maps. Fragst du die Adresse zu einem Punkt in der Karte ab, geht dieser Punkt genau mit. Für Ladesäulen und Tankstellen entlang der Strecke geht ein gerundeter Kartenausschnitt an Overpass (overpass-api.de).", "nur, wenn du in der Karte suchst oder diese Anzeige nutzt; ab Werk an, in den Einstellungen abschaltbar"),
            ("Adressen zu Parkplätzen und Aufnahmen (Nominatim)", "die Koordinaten und die Sprache", "nur mit eingeschaltetem Online-Schalter, ab Werk aus"),
            ("Update-Prüfung (GitHub)", "GitHub sieht die IP-Adresse des Autos und die Uhrzeit. Auch die Update-Datei selbst kommt von GitHub. Über dich oder dein Auto wird nichts mitgeschickt.", "alle 6 Stunden; abschaltbar (automatische Suche nach Updates), die Einrichtung fragt danach"),
            ("Besucherzählung dieser Webseite (eigenes Umami, analytics.serveone.at)", "aufgerufene Seite, Herkunftsseite, Browser, Gerätetyp, Land; Klicks auf den Download-Knopf als Zahl. Keine Cookies, keine IP-Adresse; bei „Do Not Track“ wird nicht gezählt. Das betrifft nur diese Webseite, nicht die App.", "beim Besuch der Webseite; Details in der <a href=\"/datenschutz#zaehlung\">Datenschutzerklärung</a>"),
            ("Ziel aus einem Google-Maps-Kurzlink", "Nur der Kurzlink selbst geht vom Auto an Google (maps.app.goo.gl), um das Ziel zu lesen. Keine Position.", "nur, wenn du nach dem Einfügen auf „Nachfragen“ tippst; lange Links und Waze-Links liest Panoptes ohne Anfrage"),
            ("Weitere Dienste (BYD-Konto, MQTT/Smart Home, ABRP, Stadia Maps, KI-Assistent)", "je nach Dienst; an der Eingabe steht, wohin deine Anfragen gehen", "nur, wenn du sie selbst einrichtest"),
        ],
        "h_stand": "Stand der Entwicklung",
        # PFLEGE: Diese Tabelle bei JEDER Version mitpruefen. Nur Belegtes (FADEN_KOORDINATION.md, ROADMAP.md, FREEZE_*.md), Unsicheres nach unten.
        "stand_lead": "Ehrlich, was wo läuft, Stand 0.1.38. „Fertig“ heißt: gebaut und getestet. „Nur bestimmte Autos“ heißt: hängt vom Modell ab. „Beta“ heißt: läuft, hat aber Einschränkungen.",
        "stand_kopf": ("Funktion", "Stand"),
        "stand": [
            ("Wächter mit Personen-Erkennung, Abschreckung nur bei einer Person, Meldungen über Telegram", "Fertig"),
            ("Karte, Monatsbericht, Routenplaner, EV-Cockpit", "Fertig"),
            ("Fahrtenbuch, Ladekosten, Ladekarten im Auto, „Wo hast du geladen?“", "Fertig"),
            ("Einrichtungshilfe, Orte, Umstieg von OverDrive", "Fertig"),
            ("Handy-App über die Brücke: Auto sehen, Vorheizen, Live-Bild unterwegs", "Fertig"),
            ("Web-App fürs iPhone", "Beta: am iPhone geprüft; Aufsperren und Meldungen gehen dort nicht"),
            ("Update direkt in der App", "Fertig"),
            ("Home Assistant über MQTT", "Fertig"),
            ("Camping-Modus: Wächter „bewohnt“, Nachtbildschirm, Akku-Schutz", "Fertig"),
            ("Dashcam-Clips bei Vollbremsung oder Stoß", "Fertig"),
            ("Hinweis auf neue Versionen am Bildschirm", "Fertig"),
            ("Fehler melden in der App", "Fertig"),
            ("Navi und Apps am Tacho", "Nur bestimmte Autos: nicht am Dolphin Surf und Seagull, auf DiLink 5 vorerst gesperrt"),
            ("Videos und Fahrtenbuch-Tabelle in der Handy-App", "Fertig"),
            ("Notzugang", "Fertig; ab Werk aus"),
            ("Warnung bei schwacher 12-Volt-Batterie", "Beta: gerade nach Fehlalarmen neu abgestimmt"),
            ("Wallbox über evcc, Home Assistant, Tuya oder direkt", "Beta: Steuern an einer echten Wallbox noch nicht belegt"),
            ("Neue Leiste mit sieben Bereichen, Seite „Display“", "Fertig"),
            ("Wächter und Fahrten mit großem Schalter, Regeln als „Wenn … / Dann …“", "Fertig"),
            ("Launcher am Handy oder im Cockpit einrichten (nur mit deiner Erlaubnis)", "Fertig"),
            ("Bildschirm: eigenes Bild, Sperre mit Zahlencode, Apps aus und an, USB-Stick", "Fertig"),
            ("Tacho: „Was zeigt der Tacho?“, Anzeigen, „auch beim Fahren“ je App, „Tacho wieder normal“", "Nur bestimmte Autos: nicht am Dolphin Surf und Seagull, auf DiLink 5 vorerst gesperrt"),
            ("Panoptes Launcher (eigene App)", "Fertig"),
            ("Sicherheitssysteme ausschalten nur nach Bestätigung", "Fertig"),
            ("„Laut Säule“ und „Günstigste in der Nähe“", "Fertig"),
            ("KI-Assistent nur für Klima, Sitzheizung und Sonnenrollo", "Fertig"),
            ("Kleine Helfer: Bildschirm reinigen, Ziel aus Link, Dateien Handy ↔ Auto, Rechte-Prüfung", "Fertig"),
            ("Abschaltbericht in Telegram, Logs bleiben bei Updates, Auslöser je Clip", "Fertig"),
            ("Tiermodus: Klima für dein Tier", "Fertig. Nur eine Hilfe, keine Garantie, du bleibst verantwortlich"),
            ("Camping: Heizen", "Beta: ab Werk nur Probelauf. Heizt nach deiner Freigabe, auf eigenen Wunsch auch bei ausgeschaltetem Auto über die BYD-Cloud"),
            ("Eigene Integration für Home Assistant (über HACS)", "Beta: unterwegs im Mobilfunk nur über Tailscale"),
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
        "dl_bald": "Beta-Version {V}",
        # „Neu in …“-Kasten beim Download; erscheint nur, solange versionen.json genau diese Version meldet
        "neu_version": "0.1.38", "neu_titel": "Neu in 0.1.38",
        "neu": ["<b>Übersichtlicher:</b> neue Leiste mit sieben Bereichen. Alles fürs Display im Auto steht auf einer Seite „Display“: Tacho, Hintergrundbild, Sperre, Launcher.",
                "<b>Wächter und Fahrten</b> haben oben einen großen Schalter. Regeln stehen als „Wenn … / Dann …“ da.",
                "<b>Einrichtung:</b> unter Einstellungen → Einrichtung → „Noch einrichten“ stehen neue, freiwillige Schritte.",
                "<b>Tacho</b> läuft ruhiger.",
                "<b>Panoptes Launcher:</b> Seiten und Leiste bequem am Handy oder im Cockpit einrichten, nur wenn du es bei der Kopplung erlaubst. Installieren per Knopf in Panoptes, nie von selbst."],
        # Abschnitt „Tacho und Launcher“ ab 0.1.37 (Koordination 03.11.2026), Bilder: Vorschau/Emulator, Musterdaten
        "tl": {"h": "Tacho und Launcher <span class=\"bald\">ab 0.1.37</span>",
               "lead": "Seit 0.1.37, in 0.1.38 auf der Seite Apps &amp; Display → Display. Die Bilder sind Vorschaubilder und Emulator-Aufnahmen mit Musterdaten, nicht aus einem Auto.",
               "bilder": [("Panoptes-Tacho „Horizont“: Tempo, Akku, Reichweite und der nächste Abbiegepfeil. Es gibt fünf Anzeigen.", [("tacho-horizont", "tacho", "Panoptes-Tacho Horizont: 101 km/h, 64 Prozent Akku, 287 km Reichweite, in 350 m rechts")]),
                          ("„Was zeigt der Tacho?“: ein Bild antippen. „Normal“ holt den BYD-Tacho zurück.", [("tacho-auswahl", "kachel", "Auswahl Was zeigt der Tacho: Normal, Klar, Sport, Nacht, Horizont, Route und freigegebene Apps")]),
                          ("Panoptes Launcher: eigene App, freiwillig. Klima im Dock, Update-Hinweis. Das Haus links führt immer zum BYD-Startbildschirm zurück.", [("launcher", "lnc", "Panoptes Launcher mit Update-Hinweis, Fahrzeug, Musik und Klima im Dock")]),
                          ("Bildschirm sperren: nur in P, entsperren mit deinem Zahlencode.", [("sperre", "display", "Display gesperrt: zum Entsperren lange drücken und PIN eingeben")])]},
        # Tacho-Test (Beta), Text von Kern Tacho 30.10.2026 (TACHO_BETA_WEBTEXT.md), freigegeben mit 0.1.30
        "tacho": {
            "h": "Tacho: Navi und Apps auf dem Tacho",
            "intro": ["Auf manchen BYD zeigt Panoptes am Tacho eine eigene Anzeige, eine Navi-App wie Google Maps oder Waze oder eine andere App, die du freigibst."],
            "h_schritte": "So geht's:",
            "schritte": ["In Panoptes: <b>Apps &amp; Display</b> → <b>Display</b> → <b>Was zeigt der Tacho?</b>",
                         "Eine Anzeige, ein Navi oder eine App antippen.",
                         "Zurück zum BYD-Tacho: <b>Tacho wieder normal</b>."],
            "bekommen": "<b>Hilf uns:</b> Du hast ein anderes Modell? Schreib uns über die <a href=\"/#wunsch\">Wunsch-Box</a> dein Modell und ob es geht (ja oder nein).",
            "h_gut": "Gut zu wissen:",
            "gut": ["Ab Werk bleiben beim Fahren am Tacho nur Navi-Apps aus einer festen Liste (z. B. Google Maps, Waze, OsmAnd, ABRP). Andere Apps laufen nur im Stand.",
                    "Du kannst je App „auch beim Fahren“ einschalten, nach einem Hinweis. Dann bist du selbst verantwortlich. <b>Videos beim Fahren sind in vielen Ländern verboten.</b>",
                    "Beim ersten Mal bestätigst du einen Hinweis: Tempo und Warnleuchten müssen sichtbar bleiben.",
                    "Beim <b>Dolphin Surf</b> und <b>Seagull</b> geht es nicht. Auf Autos mit <b>DiLink 5</b> ist es vorerst gesperrt."],
        },
        "dl_text": "Panoptes {V} ist eine <b>Beta-Version</b>. Panoptes läuft im Alltag in einem Testauto (BYD Dolphin Surf, DiLink 3), neue Versionen kommen dort nach und nach dazu. Auf anderen Modellen kann manches fehlen oder anders sein. Die Installation ist nichts für jeden: Du brauchst etwas Geduld, einmalig einen PC oder Laptop und musst am Auto eine Entwickler-Freigabe einschalten. Danach kommen Updates von selbst in der App. Nutzung auf eigenes Risiko, siehe <a href=\"hinweise.html\">Hinweise</a>.",
        "dl_knopf": "⬇️ Panoptes {V} herunterladen (APK, {MB} MB)",
        "hero_dl": "⬇️ Panoptes {V} herunterladen", "hero_anl": "Anleitung", "kopf_dl": "⬇️ Download",
        "dl_release": "Release auf GitHub", "dl_quelle": "Quellcode",
        "dl_pruef": "Prüfsumme (SHA-256)", "dl_zert": "Signaturzertifikat (SHA-256)",
        "dl_update": "Ab 0.1.19.1 kommen Updates über System → App-Updates. Wer 0.1.17 oder 0.1.18 hat, installiert die aktuelle Version einmal von Hand (<a href=\"#schritte\">Anleitung</a>); die Daten bleiben erhalten.",
        "h_anl": "Schritt für Schritt",
        "anl": [
            ("Vorher lesen.", "Panoptes ist für dein eigenes Auto gedacht, privat und auf eigenes Risiko. Lies die <a href=\"hinweise.html\">Hinweise</a>. Für die Installation schaltest du am Auto Entwickler-Funktionen ein. Ob das für deine Garantie eine Rolle spielt, klärst du im Zweifel mit deinem Händler."),
            ("Herunterladen.", "Lade die Datei <code>{APK}</code> mit dem Knopf oben auf deinen PC oder Laptop. <b>Freiwillig, für Geübte:</b> Vergleiche vorher die Prüfsumme. Unter Windows tippst du in der Eingabeaufforderung <code>certutil -hashfile {APK} SHA256</code>, am Mac oder unter Linux <code>shasum -a 256 {APK}</code>. Die Ausgabe muss genau die Prüfsumme oben ergeben. Weicht sie ab, installiere die Datei <b>nicht</b>."),
            ("Entwickler-Freigabe (ADB) am Auto einschalten.", "Panoptes startet seine Hintergrunddienste, zum Beispiel für die Kameras, über die ADB-Schnittstelle des Autos. Diese Verbindung bleibt im Auto (127.0.0.1). Ab Werk ist die Schnittstelle aus. Eingeschaltet wird sie im BYD-Entwicklermenü, mit den Schaltern für USB-Debugging bzw. kabelloses ADB. Wie du in dieses Menü kommst, hängt stark von Modell und Software-Stand ab; bei neuerer BYD-Software ist es mit einem Code gesperrt. Geprüft haben wir diesen Schritt bisher nur am Dolphin Surf (DiLink 3). Ohne diese Freigabe läuft Panoptes nicht vollständig."),
            ("App aufs Auto bringen.", "<b>Geprüfter Weg, einmalig mit PC oder Laptop:</b> Installiere die Android-Plattform-Tools von Google (darin ist <code>adb</code>). PC und Auto müssen im selben Netz sein, zum Beispiel im WLAN-Hotspot deines Handys. Tippe dann <code>adb connect &lt;Adresse-des-Autos&gt;:5555</code> und <code>adb install -r {APK}</code>. Die Adresse des Autos siehst du in den WLAN-Einstellungen am Auto oder in der Geräteliste deines Hotspots. Am Ende muss <code>Success</code> erscheinen. Danach kommen Updates von selbst in der App. <b>Statt PC mit einem Android-Handy (von uns noch nicht geprüft):</b> Das geht auch mit einer adb-App am Handy, im selben WLAN oder Hotspot wie das Auto, siehe <a href=\"/guide#handy-adb\">Anleitung</a>. Mit dem iPhone geht das nicht. <b>USB-Stick oder BYD-Dateimanager: wird gerade geprüft.</b> Der Dateimanager gibt die Datei nach einer Warnung an die Installation weiter; ob sie danach durchläuft, ist noch nicht belegt. Fragt Android nach „Installation aus unbekannten Quellen“, erlaubst du das nur für diese Installation."),
            ("Erster Start mit der Einrichtungshilfe.", "Öffne Panoptes am Bildschirm im Auto. Kurze Schritte führen dich durch das Nötigste, zum Beispiel Sprache, Hinweise bestätigen, <b>Autostart</b>, Anzeige über anderen Apps, Berechtigungen und <b>USB-Freigabe</b>. Alles Weitere (Wächter, Kartenquelle, Daten teilen, Blitzer, Telegram, Routenplaner, EV-Cockpit, Fernzugang) findest du danach unter „Noch einrichten“. Fast nichts ist vorausgewählt. Was Daten nach außen schickt, bleibt aus, bis du es selbst einschaltest."),
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
        "links": [("/ev/", "🧭 Routenplaner"), ("/ev-cockpit/", "🖥️ EV-Cockpit"), ("/app/", "📱 Handy-App (BETA)"), ("/app/#iphone", "🍏 iPhone: Web-App (BETA)"), ("/", "🗺️ Community-Karte")],
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
        "desc": "Panoptes is a free community app for BYD cars with DiLink 3, 4 and 5, currently in beta: camera guard, trips and charging with costs, wallbox, remote access, Telegram notifications, a map with chargers and a link to the route planner.",
        "zurueck": "← BYD EU Community",
        "eyebrow": "Free · for BYD with DiLink 3, 4 and 5 · beta",
        "h1a": "Panoptes", "h1b": "your BYD, awake and connected",
        "sub": "An app that runs right on your car's screen, plus an interface you open on your phone or PC: a camera guard, trips and charging with costs, your wallbox, remote access, Telegram notifications, its own map with chargers and a link to the route planner.",
        "wichtig": "<b>New:</b> Panoptes is now publicly available as <b>beta version {V}</b>, with source code and a <a href=\"#install\">step-by-step guide</a>. So far it has mainly been tested on a BYD Dolphin Surf (DiLink 3). Panoptes is a private hobby project and not made by BYD. Please read the <a href=\"hinweise.html\">notes</a> before installing.",
        "hero_alt_pc": "Panoptes 0.1.38 on the car screen: page Display with the choice what the cluster shows",
        "hero_alt_handy": "Panoptes 0.1.38 on a phone: guard with a big switch",
        "h_camp": "Camping mode <span class=\"bald\">beta</span>",
        "camp_lead": "Since 0.1.16.1: you sleep in the car, and Panoptes looks after power, the guard and the screen. Heating is still in beta. By default only a dry run runs; you choose the heating type on the camping page.",
        "camp": [
            ("What it does", "<ul class=\"liste\"><li><b>Guard \u201coccupied\u201d:</b> While camping runs, the guard does not scare anyone off (no screen, lights or horn) and raises no shake alarm when you move.</li><li><b>Night screen:</b> After a time without touch that you can set, the screen turns almost black, with a big clock and a few numbers. No sounds.</li><li><b>Battery protection and time left:</b> You set a lower limit (20 % by default). Panoptes shows how long the battery lasts for heating and stops before the limit. Panoptes never switches the car off.</li></ul>"),
            ("Switching on", "<ul class=\"liste\"><li>With a tap on the car screen, only while parked (gear P).</li><li>On your phone, in Panoptes\u2019 web interface.</li><li>In Telegram with <code>/camping</code>.</li><li>Scheduling for a set time (start and wake-up time) works from 0.1.17 through Panoptes\u2019 interface; operating it from the EV Cockpit follows.</li><li>Camping ends by itself when you drive off.</li></ul>"),
            ("Heating: beta", "<p><b>Panoptes only heats once you choose a heating type on the camping page.</b> Until then it runs a dry run: it only shows what it would do and switches nothing.</p><ul class=\"liste\"><li><b>Car on:</b> Panoptes switches the climate control directly.</li><li><b>Car off:</b> through the BYD cloud, which needs a BYD account. This wakes the car for every heating run.</li></ul>"),
            ("Limits", "<ul class=\"liste\"><li><b>No cabin sensor:</b> the Dolphin Surf has none. Panoptes therefore never shows an interior temperature and heats in intervals based on the outside temperature (\u201cevery x minutes for y minutes\u201d). You can add an external sensor if you like.</li><li><b>Consumption:</b> roughly 1.5 to 3 % battery per hour at 0 \u00b0C while heating. That is an estimate, not a measurement; Panoptes learns from your real consumption.</li><li><b>After DC charging ends:</b> BYD then switches the car off by itself.</li><li>Camping is no substitute for supervision. Never leave children or animals alone in the car.</li></ul>"),
        ],
        "camp_bilder_lead": "The pictures come from an emulator, not from a car. That is why the values read \u201cnot available\u201d and the model name at the top is the emulator\u2019s. In the car you see your real values here. Click a picture to enlarge it. The interface is shown in German.",
        "camp_bilder": [
            ("Camping page on the car screen: switch on, battery, heating time; the \u201cdry run\u201d notice at the top.", [("camping", "display", "Panoptes camping page: camping is off, Switch on button, dry run notice, values not yet available")]),
            ("Settings: warmth, heating route, battery limit, 12 V warning.", [("camping-einstellungen", "display", "Camping settings: warmth, heating route dry run, pre-heating, battery limit 20 percent, 12-volt warning")]),
            ("Night screen: almost black, big clock, feedback \u201ctoo cold / fine / too warm\u201d. Next to it the camping page on a phone.", [("nacht", "display", "Night screen: black background, big clock and date, buttons too cold, fine, too warm"), ("camping", "handy", "Camping page on a phone at 390 pixels wide")]),
        ],
        "alle": {"h": "Everything Panoptes {V} can do",
                 "lead": "By area. No label means: done.",
                 "chips": {"A": "only some cars", "B": "beta"},
                 "gruppen": [
            ("Start", [
                ("Bar with seven areas: Home, Controls, Cameras & guard, Trips & charging, Rules, Apps & display, Settings", ""),
                ("Home page with charge, range, location, car status, guard today and recent trips", ""),
                ("Range \u201ctoday\u201d, learned from your own trips", ""),
                ("Quick buttons: lock, pre-condition, boot", "A"),
                ("Big \u201cstop heating\u201d button", ""),
                ("Ask Panoptes (AI assistant), only if you set it up; may only control climate, seat heating and sunshade", ""),
            ]),
            ("Control", [
                ("Lock and unlock, boot, windows, sunroof, sunshade", "A"),
                ("Climate, temperature, fan; pre-conditioning with a schedule", "A"),
                ("Seat heating, seat ventilation, steering wheel heating", "A"),
                ("Battery heating (via the BYD cloud)", "A"),
                ("Charging in the car: charge limit, current, schedule, \u201ccharge now\u201d", "A"),
                ("Find the car (flash, horn), daytime lights, ambient light", "A"),
                ("Sounds outside (e.g. a chime), only in P", "A"),
                ("Save seat positions, assign the car's buttons yourself", "A"),
                ("Safety systems (e.g. lane keeping) can only be turned off after a confirmation", ""),
                ("3D car in your colour", ""),
                ("Camping mode with night screen and battery protection", ""),
                ("Camping heating, choose the heating type on the camping page", "B"),
                ("Pet mode: keeps the climate running for your pet (only an aid, no guarantee)", "A"),
            ]),
            ("Cameras & guard", [
                ("Guard with a big switch; you choose when it records (bump, AI everywhere, AI only at private places)", ""),
                ("Deterrent on the screen, only when a person is there", ""),
                ("12-volt battery protection: the guard goes to sleep in time", ""),
                ("Guard schedule, watch areas, private places", ""),
                ("When you get in: \u201cWhile you were away: n recordings\u201d", ""),
                ("Dashcam clip on hard braking or a bump, remembers the trigger (without location)", ""),
                ("Live picture of all cameras", ""),
                ("Watch recordings by day and type (person, vehicle, bicycle, animal)", ""),
                ("Recording settings: continuous recording while driving, quality, storage", ""),
                ("Parking log: who parked next to you", ""),
                ("Announcement outside: speak or text", ""),
                ("Blind spot when indicating, as one picture", "A"),
            ]),
            ("Trips & charging", [
                ("Map with chargers and free spots; you choose the map source", ""),
                ("Search places and send them to the navigation; destination from a Google Maps or Waze link", ""),
                ("\u201cWill it reach?\u201d with a charging stop suggestion", ""),
                ("Cheapest charger nearby, with your price", ""),
                ("Trip log with a big switch, consumption", ""),
                ("Driving style, compare routes", ""),
                ("Consumption by outside temperature, loss while parked", ""),
                ("Trip log as a file (without places), recover lost trips", ""),
                ("Monthly report, also for printing", ""),
                ("Charging costs with estimated charging loss; enter \u201cLaut S\u00e4ule\u201d", ""),
                ("Recognise the charger automatically; \u201cWhere did you charge?\u201d", ""),
                ("Charging power, cell temperature, battery health over time", ""),
                ("Charge cards and networks in the car", ""),
                ("Charging at home with a time window, at the market price if you like", ""),
                ("Warm for departure (off by default)", "A"),
                ("Wallbox via evcc, Home Assistant, Tuya or directly", "B"),
                ("Road condition: detect potholes and warn", ""),
            ]),
            ("Rules", [
                ("Build your own \u201cWhen \u2026 / Then \u2026\u201d rules, back up and restore", ""),
                ("Take over community rules (off by default)", ""),
                ("Habits: Panoptes suggests rules, the data stays in the car", ""),
                ("Your places: home, garage, charging spot with price", ""),
                ("All notifications on one page: phone and Telegram per topic, quiet hours", ""),
                ("Telegram bot with commands (e.g. /status, /wo, /camping, /tier)", ""),
                ("Parked report in Telegram after parking", ""),
            ]),
            ("Apps & display", [
                ("Everything for the display on one page \u201cDisplay\u201d: cluster, background picture, lock, launcher", ""),
                ("Two apps side by side on the screen", "A"),
                ("\u201cPhone in the car\u201d: Android Auto and CarPlay if your car has them", "A"),
                ("Own picture, screen lock with a number code, apps off and on", ""),
                ("Screen cleaning, read USB sticks, files between phone and car", ""),
                ("Red band while the screen is being shared", ""),
                ("Cluster: displays, navigation and apps, runs smoothly; \u201ccluster back to normal\u201d", "A"),
                ("Turn arrows in the BYD cluster (off by default)", "A"),
                ("Panoptes Launcher: separate app, freely arranged, also on your phone or in the Cockpit (only with permission), with app drawer and climate in the dock", ""),
                ("Light or dark, five start views", ""),
                ("Speed camera warning (Austria only, off by default)", ""),
            ]),
            ("Settings", [
                ("Short setup; optional steps under Settings \u2192 Setup \u2192 \u201cNoch einrichten\u201d (still to set up)", ""),
                ("Updates in the app; without Wi-Fi Panoptes asks first and shows the size", ""),
                ("Report a problem in the app", ""),
                ("Remote access via Tailscale, bridge for phone and PC (off by default)", ""),
                ("Pair devices with a check number; permissions per device, extra permissions never by themselves", ""),
                ("Log \u201cwho did what?\u201d", ""),
                ("Home Assistant via MQTT, route planner, EV Cockpit", ""),
                ("ABRP connection", ""),
                ("Switching from OverDrive", ""),
                ("Back up and restore settings", ""),
                ("Panoptes checks its permissions daily; logs are kept through updates", ""),
                ("Five languages", ""),
            ]),
                 ]},
        "h_kann": "What Panoptes does",
        "kann": [
            ("🚗", "On the car screen", "Panoptes runs as its own full-screen app with large buttons. While driving, settings are locked; home, map and guard stay available."),
            ("🧩", "Setup assistant", "On first start, short steps guide you through the essentials. Everything else is under \u201cNoch einrichten\u201d (still to set up) later. Almost nothing is preselected (only \u201cremember habits\u201d is set to yes, and that stays in the car); anything that sends data out stays off until you turn it on. Whatever your car cannot do is skipped with an explanation."),
            ("🛡️", "Guard with AI detection", "While your car is parked, the cameras watch its surroundings. You decide when it records: only on impact, with AI detection everywhere, or only at your own private places such as your garage or driveway. Without a choice it only records on impact. To protect the 12 V battery it goes to sleep; the threshold follows the battery type (lead-acid, AGM or LFP)."),
            ("📹", "Dashcam <span class=\"bald\">from 0.1.27</span>", "On hard braking or a bump Panoptes saves a short clip from all cameras by itself, about 20 seconds before and after. No continuous recording. The clips stay in the car or on the USB stick and are never sent anywhere by themselves. You can watch and save clips on your phone with the <a href=\"/app/en/\">phone app</a> (beta 4). Panoptes then asks “Keep?”, otherwise the clip is deleted after 72 hours. From 0.1.36 every clip remembers what triggered it (without location). In Switzerland the dashcam is off by default. Whether recording while driving is allowed where you live differs by country, see the <a href=\"hinweise.html\">notes</a>."),
            ("📒", "Trips and charging", "Trips, consumption and charging sessions are recorded in the car. Panoptes shows the cost per session, per month and as average cost per 100 km, from 0.1.35 including the estimated charging loss (sign \u201c~\u201d). If a price is missing it says \u201cprice missing\u201d instead of inventing a number; free charging can be entered explicitly."),
            ("🔌", "\u201cWhere did you charge?\u201d", "After charging, Panoptes asks for the station and price while parked, never while driving. With \u201cremember place\u201d it knows the price next time. With \u201cLaut S\u00e4ule\u201d (as shown by the charger) you enter the charger's kWh and cost; your price is then used for \u201cCheapest nearby\u201d (AC and DC separately). The question can be switched off."),
            ("💳", "Your charge cards in the car", "Charge cards and networks, minimum power, plug and arrival charge level are set in the car. The route planner uses them; they are only stored in the car."),
            ("🏠", "Wallbox <span class=\"bald\">beta</span>", "Set up your wallbox via evcc, Home Assistant or Tuya, and from version 0.1.12 also directly (e.g. go-e, KEBA, openWB, Easee, Zaptec): see the status, set mode, charge limit and current. Control only while the car is parked, with confirmation and enabled per charge point. So far only checked with demo and test devices."),
            ("📍", "Your places", "One list for everything: home, garage, work or the charging spot with its own price. For each place you decide whether it is private (guard), a charging price applies or it is a destination in the navigation. Places never leave the car."),
            ("🌍", "Remote access", "Reach your car from anywhere via Tailscale. Setup uses a QR code on the car screen and your own Tailscale account. For advanced users, 0.1.14 adds an independent emergency access, off by default."),
            ("💬", "Telegram notifications", "Your own bot reports guard events, charging, a weak starter battery, tyre pressure and updates. Each category can be switched on its own, with quiet hours for the night. Pictures and videos only if you turn that on."),
            ("🗺️", "Map with chargers", "You choose where the map comes from: the community server (with terrain and free charging spots where operators provide data), OpenStreetMap, or none. Until you choose, the map stays empty. Speed cameras are shown in Austria only, off by default and with a legal notice."),
            ("🔋", "\u201cWill it make it?\u201d", "With a route from the route planner, including waypoints, Panoptes tells you on the road whether the battery will last to the next stop and suggests a charging stop if needed."),
            ("📊", "Monthly report", "Distance, consumption, charging and costs, standby loss and guard events of a month at a glance, also for printing. Calculated in the car."),
            ("🔁", "Switching from OverDrive", "If you used the OverDrive app before, you can take over trips, charging sessions and settings, with a preview and without duplicates. Panoptes never takes over consents or risky switches; you set those yourself."),
            ("🧭", "Route planner link", "Connect Panoptes to your account on <a href=\"/ev/\">byd.serveone.at/ev/</a>: show a code in the car, confirm on your phone, done. Disconnect at any time."),
            ("🖥️", "EV Cockpit on your PC", "The <a href=\"/ev-cockpit/\">EV Cockpit</a> shows Panoptes data on your PC, including charging sessions and costs, and can change its settings. You confirm the pairing with one tap and a four-digit check number."),
            ("⬆️", "Updates in the app", "If you like, Panoptes looks for new versions itself. Installing only happens while the car is parked with the ignition off. From 0.1.13 Panoptes no longer changes permanent Android settings by itself (such as \u201cscreen always on\u201d); values set earlier can be reset. What you change yourself (own picture, turning apps off) stays until you change it back. From 0.1.36 the logs are kept through updates."),
            ("🏕️", "Camping mode <span class=\"bald\">beta</span>", "Guard \u201coccupied\u201d, night screen, battery protection with time left. Switch on with a tap, on your phone or with /camping in Telegram. You choose the heating type on the camping page; by default only a dry run. <a href=\"#camping\">More</a>"),
            ("🖼️", "Screen <span class=\"bald\">from 0.1.37</span>", "Your own picture for the home screen. Lock the screen with a number code (only in P). Turn apps off and on. Read USB sticks."),
            ("🚀", "Panoptes Launcher <span class=\"bald\">from 0.1.37</span>", "Separate app, optional: home screen with climate in the dock, Android Auto and CarPlay (if your car has them) and update notice. Install by button in Panoptes, never by itself. From 0.1.38 you set it up comfortably on your phone or in the Cockpit, only if you allow it when pairing. The house on the left always takes you back to the BYD home screen. <a href=\"#tacho-launcher\">Pictures</a>"),
            ("🐾", "Pet mode <span class=\"bald\">from 0.1.36</span>", "Keeps the climate running for your pet and reports problems to your phone and Telegram. Only an aid, no guarantee, you stay responsible."),
            ("🤖", "AI assistant", "Only if you set it up yourself. From 0.1.36 it may only control climate, seat heating and sunshade and show values. Never horn, lights, indicators, windows, boot or the guard."),
            ("🧰", "Small helpers <span class=\"bald\">from 0.1.36</span>", "Screen cleaning (locked for 30 seconds, only in P). Take over a destination from a Google Maps or Waze link. Files between phone and car (own permission, off by default, no apps). Panoptes checks its permissions daily and repairs what it can."),
            ("🌐", "Five languages", "German, English, French, Italian and Dutch."),
        ],
        "h_bilder": "What Panoptes looks like",
        "bilder_lead": "Panoptes 0.1.38 on the car screen and on a phone, taken in the emulator with sample data, not from a car. Under \u201cmore pictures\u201d there are also older pictures from 0.1.10 until new ones exist. Click a picture to enlarge it.",
        "bilder": [
            ("Cameras & guard: one big switch, below it today's recordings.", [("waechter38", "display", "Guard on the car screen: guard is off, big button switch guard on"), ("waechter38", "handy", "Guard on a phone with a big switch")]),
            ("Apps & display → Display: “What does the cluster show?” Tap a picture.", [("display38", "display", "Page Display: cluster, background and lock, launcher; choice what the cluster shows"), ("display38", "handy", "Page Display on a phone")]),
            ("Settings: “What would you like to set?”, with search.", [("system38", "display", "All settings: connections, car and display, app and data, advanced"), ("system38", "handy", "All settings on a phone")]),
            ("Setup: optional steps under “Noch einrichten” (still to set up).", [("einrichtung38", "display", "Setup: list of optional steps still to set up"), ("einrichtung38", "handy", "Still to set up on a phone")]),
            ("Controls on a phone: tiles for security, boot, climate and seats.", [("steuerung38", "handy", "Controls on a phone with tiles security, boot, climate, seats")]),
            ("Older picture (0.1.10): map with chargers and free spots.", [("karte", "pc", "Map with chargers on a PC"), ("karte", "display", "Map on the car screen")]),
            ("Older picture (0.1.10): monthly report with distance, consumption, charging and guard.", [("monatsbericht", "pc", "Monthly report on a PC"), ("monatsbericht", "display", "Monthly report on the car screen")]),
            ("Older picture (0.1.10): pair a device with a check number.", [("geraete", "pc", "Pairing: the EV Cockpit wants to connect, check number 4711")]),
            ("Older picture (0.1.10): Telegram, every kind of message on its own.", [("telegram", "handy", "Telegram notifications on a phone, each kind switchable")]),
        ],
        "handy": "on a phone", "pc": "on a PC",
        "h_zus": "How it all fits together",
        "zus_lead": "Panoptes runs in the car. Everything else is optional and can be connected and disconnected one by one.",
        "svg": {"auto": "Panoptes", "auto2": "in the car", "cockpit": "EV Cockpit", "cockpit2": "on your PC", "planer": "Route planner", "planer2": "byd.serveone.at/ev/",
                "karte": "Community map", "karte2": "tiles, chargers", "tg": "Telegram bot", "tg2": "your own", "ha": "Home Assistant", "ha2": "your own",
                "wb": "Wallbox", "wb2": "beta",
                "t1": "pairing", "t2": "account, destination, trip log E2E", "t3": "map (if chosen)", "t4": "notifications", "t5": "home network", "t6": "direct", "t7": "route, charge cards",
                "aria": "Diagram: Panoptes in the car in the middle, connected to the EV Cockpit on a PC, the route planner, the community map, a Telegram bot, a wallbox and Home Assistant"},
        "verb": [
            ("1", "Panoptes ↔ EV Cockpit (pairing)", "You allow the cockpit once with a check number, in Telegram or on the Panoptes page. The cockpit then fetches vehicle data, settings and the trip log straight from the car, over your home network or Tailscale.",
             "Not included: remote access, password and ports. None of this goes through our servers; the trip log stays on your PC. The cockpit keeps the access key in your computer's keyring. Anything else it sends to servers (map, 3D model, route planner, usage count) needs its own tick; without a tick, nothing."),
            ("2", "Panoptes ↔ route planner", "Once linked, your destination with charging stops goes into the car. Panoptes reports charge level, consumption factor and driving status so the plan is right. If you turn it on (off by default) and fetch your trip log on /ev/, it comes end-to-end encrypted straight from the car to your browser.",
             "Not included: the server cannot read the trip log; it only receives encrypted data and, according to the route planner, keeps it in memory for 2 minutes at most. Your approximate position is only sent when Panoptes suggests a new charging stop on the road."),
            ("3", "Panoptes ↔ community map", "If you choose it as map source, map tiles and charger data come from byd.serveone.at, with live availability where open data exists. Without a choice Panoptes loads no map.",
             "Not included: trips and recordings. The server only sees your IP address and the map area. Shared rules only go to the community server if you share them yourself (off by default)."),
            ("4", "Panoptes → Telegram", "Your own bot sends you message texts. Pictures and videos only if you explicitly turn that on; they are then stored on Telegram's servers.",
             "Not included: no videos on our servers, no detour through the project."),
            ("5", "Panoptes ↔ wallbox (beta)", "Panoptes talks to your wallbox in your home network, via evcc, Home Assistant, Tuya or directly. Control only works while the car is parked and you have enabled the charge point, each change with confirmation. You can withdraw the permission at any time.",
             "Not included: none of this goes through our servers. Credentials are stored encrypted in the car. Manufacturer clouds (Easee, Zaptec, Tuya) only with your consent per device."),
            ("6", "Panoptes ↔ Home Assistant", "Your car connects directly to your own Home Assistant, without our servers. There you see values like charge level and range, build your own automations and get notifications. This works over MQTT, which you set up in Panoptes. The dedicated <a href=\"https://github.com/samuelvoltarius/panoptes-homeassistant\" target=\"_blank\" rel=\"noopener\">integration for Home Assistant</a> is a beta and can be installed through HACS. On the road over mobile data it only works through Tailscale.",
             "Not included: The data stays with you, not with us."),
            ("7", "EV Cockpit ↔ route planner", "The cockpit shows the route waiting for you and your charge cards. When it is paired with Panoptes, only Panoptes reports the charge level, so nothing arrives twice.",
             "Not included: your trips stay on your PC."),
        ],
        "nicht": "What stays private",
        "h_ds": "Privacy: what goes where",
        "ds_lead": "Principle: your recordings, trips and positions stay in the car. If you watch recordings on your phone on the road, they pass through our bridge end-to-end encrypted; the server cannot read them and does not store them. Most things that send data out are off by default; you turn each item on separately, and Panoptes tells you beforehand where the data goes. The exceptions are the update check and the map search, both listed in the table below. No ads, no tracking.",
        "ds_kopf": ("Where", "What", "When"),
        "ds": [
            ("In the car (USB stick, app)", "guard recordings, trip log, charging sessions and prices, monthly report, your places, charge cards, settings; credentials (e.g. for the wallbox) encrypted", "always. On a new setup Panoptes deletes recordings after 72 hours; you can keep individual ones. If a file is missing (e.g. USB stick not plugged in), the trip is marked, not deleted."),
            ("EV Cockpit on your PC", "vehicle data, trips, charging sessions and costs; your places by name only, never with coordinates", "only after pairing, straight from the car over your home network or Tailscale"),
            ("Map source (community server byd.serveone.at or OpenStreetMap Germany)", "your IP address and the map area, so roughly where your car is. With the community server also the query for free charging spots in that area.", "only once you choose a source under System → Map source. On the car screen the choice applies to the whole car; phone and PC ask separately."),
            ("Bridge: phone and PC over the internet (byd.serveone.at)", "data, commands and recordings between the car and your paired devices, end-to-end encrypted. The server only sees unreadable data and stores no content, <a href=\"/en/datenschutz#bruecke\">details</a>.", "only if you switch on the bridge in the car"),
            ("Paired services and home servers (for example Home Assistant)", "notices about guard events: type and time, no coordinates. With the switch “Standbild bei Ereignis” (still picture on event) one photo per event, no video, nothing older than 15 minutes. Guard recordings only with the separate switch “Aufnahmen” (recordings). Photos may show passers-by.", "only for services you pair yourself; each permission has its own switch"),
            ("Notifications on your phone (ntfy or Google)", "the notification, end-to-end encrypted: the delivery service only sees that a message arrives and its approximate size, <a href=\"/en/datenschutz#handy-meldungen\">details</a>.", "only with a paired phone app and notifications switched on"),
            ("Web app for iPhone (panoptes.serveone.at)", "the page comes from our server, without cookies and without an access log. It reaches the car through the bridge, end-to-end encrypted; the pairing key stays on your iPhone. For place search your search text goes to byd.serveone.at, <a href=\"/en/datenschutz#handy-orte\">details</a>.", "only when you use the web app"),
            ("Telegram", "message texts; pictures and videos only if you turn that on (they are then stored at Telegram)", "only with your own bot"),
            ("Tailscale", "connection for remote access and emergency access, in your own Tailscale network", "only with remote access set up; emergency access is off by default"),
            ("Your wallbox", "charging commands in your home network; Easee, Zaptec and the Tuya cloud via the manufacturer cloud", "only if you set up a wallbox; manufacturer cloud only with your own consent per device"),
            ("Route planner (byd.serveone.at/ev)", "charge level, consumption factor, driving status and your charge cards for the price query (the server does not store them); your approximate position only for a newly suggested charging stop or, if you allow it, for price suggestions after charging. The trip log only if you turn it on (off by default) and fetch it yourself on /ev/: end-to-end encrypted; the server only receives encrypted data and, according to the route planner, keeps it in memory for 2 minutes at most.", "only after linking, can be disconnected at any time"),
            ("Community server (byd.serveone.at/community)", "shared rules, only if you share them; road damage, only if you report it, <a href=\"/en/datenschutz#panoptes-community\">details</a>", "off by default"),
            ("Weather (via our server byd.serveone.at, which asks Open-Meteo)", "a rough area of about 10 km, no identifier", "only with your consent, off by default"),
            ("Panoptes counting (optional, off by default)", "random ID and version, once a day; car model and DiLink version only if you have confirmed that separately. No IP address stored, no VIN, no location. Switching it off deletes the entries on the server; entries without a report for 90 days are merged into an anonymous monthly number.", "only if you switch on \u201cCount anonymously\u201d under Settings \u2192 Privacy (byd.serveone.at/panoptes/ping, from 0.1.17)"),
            ("Reporting a problem and cluster test (byd.serveone.at)", "your text or the test report, version, car model, DiLink version, language; a redacted diagnostic extract only if you tick the box. No identifier, no IP address stored, no location. Deleted after 180 days, <a href=\"/en/datenschutz#fehler-melden\">details</a>.", "only when you send it yourself"),
            ("Map search and places along the route (map in the car)", "your search text and, to find results nearby, the car's position rounded to about 1 km go directly from the car to public services: Photon (komoot), Nominatim (OpenStreetMap), depending on settings Stadia Maps. If you ask for the address of a point on the map, that exact point is sent. For chargers and fuel stations along the route, a rounded map area goes to Overpass (overpass-api.de).", "only when you search in the map or use this display; on by default, can be switched off in the settings"),
            ("Addresses for parking spots and recordings (Nominatim)", "the coordinates and the language", "only with the online switch turned on, off by default"),
            ("Update check (GitHub)", "GitHub sees the car's IP address and the time. The update file itself also comes from GitHub. Nothing about you or your car is sent.", "every 6 hours; can be switched off (automatic search for updates), the setup asks about it"),
            ("Visitor counting on this website (own Umami, analytics.serveone.at)", "page viewed, referring page, browser, device type, country; clicks on the download button as a number. No cookies, no IP address; nothing is counted with “Do Not Track”. This only concerns this website, not the app.", "when you visit the website; details in the <a href=\"/datenschutz#zaehlung\">privacy policy</a> (German)"),
            ("Destination from a Google Maps short link", "only the short link itself goes from the car to Google (maps.app.goo.gl) to read the destination. No position.", "only if you tap \u201cNachfragen\u201d (ask) after pasting; long links and Waze links are read without any request"),
            ("Other services (BYD account, MQTT/smart home, ABRP, Stadia Maps, AI assistant)", "depends on the service; the input field tells you where your requests go", "only if you set them up yourself"),
        ],
        "h_stand": "Development status",
        "stand_lead": "Honestly, what runs where, as of 0.1.38. \u201cDone\u201d means: built and tested. \u201cOnly some cars\u201d means: depends on the model. \u201cBeta\u201d means: it runs, but has limits.",
        "stand_kopf": ("Feature", "Status"),
        "stand": [
            ("Guard with person detection, deterrent only for a person, Telegram notifications", "Done"),
            ("Map, monthly report, route planner, EV Cockpit", "Done"),
            ("Trip log, charging costs, charge cards in the car, \u201cWhere did you charge?\u201d", "Done"),
            ("Setup assistant, places, switching from OverDrive", "Done"),
            ("Phone app over the bridge: see the car, preheat, live picture on the road", "Done"),
            ("Web app for iPhone", "Beta: checked on an iPhone; unlocking and notifications do not work there"),
            ("Update right in the app", "Done"),
            ("Home Assistant over MQTT", "Done"),
            ("Camping mode: guard \u201coccupied\u201d, night screen, battery protection", "Done"),
            ("Dashcam clips on hard braking or a bump", "Done"),
            ("Notice about new versions on the screen", "Done"),
            ("Reporting a problem in the app", "Done"),
            ("Navigation and apps on the cluster", "Only some cars: not on the Dolphin Surf and Seagull, locked on DiLink 5 for now"),
            ("Videos and trip log table in the phone app", "Done"),
            ("Emergency access", "Done; off by default"),
            ("Warning for a weak 12-volt battery", "Beta: just retuned after false alarms"),
            ("Wallbox via evcc, Home Assistant, Tuya or directly", "Beta: control on a real wallbox not confirmed yet"),
            ("New bar with seven areas, page \u201cDisplay\u201d", "Done"),
            ("Guard and trips with a big switch, rules as \u201cWhen \u2026 / Then \u2026\u201d", "Done"),
            ("Set up the launcher on your phone or in the Cockpit (only with your permission)", "Done"),
            ("Screen: own picture, lock with number code, apps off and on, USB stick", "Done"),
            ("Cluster: \u201cWhat does the cluster show?\u201d, displays, \u201calso while driving\u201d per app, \u201cCluster back to normal\u201d", "Only some cars: not on the Dolphin Surf and Seagull, locked on DiLink 5 for now"),
            ("Panoptes Launcher (separate app)", "Done"),
            ("Turning off safety systems only after a confirmation", "Done"),
            ("\u201cLaut S\u00e4ule\u201d and \u201cCheapest nearby\u201d", "Done"),
            ("AI assistant only for climate, seat heating and sunshade", "Done"),
            ("Small helpers: screen cleaning, destination from a link, files phone \u2194 car, permission check", "Done"),
            ("Parked report in Telegram, logs kept through updates, trigger per clip", "Done"),
            ("Pet mode: climate for your pet", "Done. Only an aid, no guarantee, you stay responsible"),
            ("Camping: heating", "Beta: dry run by default. Heats after you allow it, if you choose also with the car off via the BYD cloud"),
            ("Own integration for Home Assistant (via HACS)", "Beta: on the road over mobile data only through Tailscale"),
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
        "dl_bald": "Beta version {V}",
        "neu_version": "0.1.38", "neu_titel": "New in 0.1.38",
        "neu": ["<b>Clearer:</b> a new bar with seven areas. Everything for the car display is on one page “Display”: cluster, background picture, lock, launcher.",
                "<b>Guard and trips</b> have a big switch at the top. Rules read as “When … / Then …”.",
                "<b>Setup:</b> under Settings → Setup → “Noch einrichten” (still to set up) there are new optional steps.",
                "<b>Cluster</b> runs more smoothly.",
                "<b>Panoptes Launcher:</b> set up pages and dock comfortably on your phone or in the Cockpit, only if you allow it when pairing. Install by button in Panoptes, never by itself."],
        "tl": {"h": "Cluster and launcher <span class=\"bald\">from 0.1.37</span>",
               "lead": "Since 0.1.37, in 0.1.38 on the page Apps &amp; display → Display. The pictures are previews and emulator shots with sample data, not from a car.",
               "bilder": [("Panoptes cluster “Horizont”: speed, battery, range and the next turn arrow. There are five displays.", [("tacho-horizont", "tacho", "Panoptes cluster Horizont: 101 km/h, 64 percent battery, 287 km range, turn right in 350 m")]),
                          ("“What does the cluster show?”: tap a picture. “Normal” brings back the BYD cluster.", [("tacho-auswahl", "kachel", "Choice What does the cluster show: Normal, Klar, Sport, Nacht, Horizont, Route and allowed apps")]),
                          ("Panoptes Launcher: separate app, optional. Climate in the dock, update notice. The house on the left always takes you back to the BYD home screen.", [("launcher", "lnc", "Panoptes Launcher with update notice, vehicle, music and climate in the dock")]),
                          ("Lock the screen: only in P, unlock with your number code.", [("sperre", "display", "Screen locked: long press and enter the PIN to unlock")])]},
        "tacho": {
            "h": "Cluster: navigation and apps on the instrument cluster",
            "intro": ["On some BYD models Panoptes shows its own display, a navigation app like Google Maps or Waze, or another app you allow on the instrument cluster."],
            "h_schritte": "How it works:",
            "schritte": ["In Panoptes: <b>Apps &amp; display</b> → <b>Display</b> → <b>What does the cluster show?</b>",
                         "Tap a display, a navigation app or an app.",
                         "Back to the BYD cluster: <b>Cluster back to normal</b>."],
            "bekommen": "<b>Help us:</b> Do you have a different model? Tell us through the <a href=\"/en/#wunsch\">wish box</a> your model and whether it works (yes or no).",
            "h_gut": "Good to know:",
            "gut": ["By default, while driving the cluster only shows navigation apps from a fixed list (e.g. Google Maps, Waze, OsmAnd, ABRP). Other apps only run while parked.",
                    "You can switch on \u201calso while driving\u201d for each app after a notice. You are then responsible yourself. <b>Watching videos while driving is illegal in many countries.</b>",
                    "The first time, you confirm a notice: the speed and warning lights must stay visible.",
                    "It does not work on the <b>Dolphin Surf</b> and <b>Seagull</b>. On cars with <b>DiLink 5</b> it is locked for now."],
        },
        "dl_text": "Panoptes {V} is a <b>beta version</b>. Panoptes runs in everyday use in a test car (BYD Dolphin Surf, DiLink 3), new versions are added there step by step. On other models some things may be missing or work differently. Installing it is not for everyone: you need some patience, a PC or laptop once, and you have to turn on a developer setting in the car. After that, updates arrive in the app by themselves. Use at your own risk, see the <a href=\"hinweise.html\">notes</a>.",
        "dl_knopf": "⬇️ Download Panoptes {V} (APK, {MB} MB)",
        "hero_dl": "⬇️ Download Panoptes {V}", "hero_anl": "Guide", "kopf_dl": "⬇️ Download",
        "dl_release": "Release on GitHub", "dl_quelle": "Source code",
        "dl_pruef": "Checksum (SHA-256)", "dl_zert": "Signing certificate (SHA-256)",
        "dl_update": "From 0.1.19.1 on, updates arrive via System → App updates. If you have 0.1.17 or 0.1.18, install the current version once by hand (<a href=\"#schritte\">guide</a>); your data is kept.",
        "h_anl": "Step by step",
        "anl": [
            ("Read first.", "Panoptes is meant for your own car, for private use and at your own risk. Read the <a href=\"hinweise.html\">notes</a>. To install it you turn on developer functions in the car. If in doubt whether this matters for your warranty, ask your dealer."),
            ("Download.", "Download <code>{APK}</code> to your PC or laptop with the button above. <b>Optional, for experienced users:</b> compare the checksum first. On Windows type <code>certutil -hashfile {APK} SHA256</code> in a command prompt, on a Mac or Linux <code>shasum -a 256 {APK}</code>. The output must match the checksum above exactly. If it differs, do <b>not</b> install the file."),
            ("Turn on developer access (ADB) in the car.", "Panoptes starts its background services, for example for the cameras, through the car's ADB interface. This connection stays inside the car (127.0.0.1). It is off by default. You turn it on in the BYD developer menu, with the switches for USB debugging or wireless ADB. How to reach this menu depends a lot on model and software version; on newer BYD software it is locked with a code. So far we have only tested this step on the Dolphin Surf (DiLink 3). Without it Panoptes will not fully work."),
            ("Get the app onto the car.", "<b>Tested way, once with a PC or laptop:</b> install Google's Android platform tools (they contain <code>adb</code>). PC and car must be on the same network, for example your phone's Wi-Fi hotspot. Then type <code>adb connect &lt;car-address&gt;:5555</code> and <code>adb install -r {APK}</code>. You find the car's address in its Wi-Fi settings or in your hotspot's device list. At the end it must say <code>Success</code>. After that, updates arrive in the app by themselves. <b>An Android phone instead of a PC (not yet tested by us):</b> this also works with an adb app on the phone, on the same Wi-Fi or hotspot as the car, see the <a href=\"/en/guide#handy-adb\">guide</a>. It does not work with an iPhone. <b>USB stick or BYD file manager: being checked.</b> The file manager passes the file to the installer after a warning; whether it then completes is not confirmed yet. If Android asks about “installing from unknown sources”, allow it only for this installation."),
            ("First start with the setup assistant.", "Open Panoptes on the car screen. Short steps guide you through the essentials, for example language, confirming the notes, <b>autostart</b>, display over other apps, permissions and <b>USB access</b>. Everything else (guard, map source, data sharing, speed cameras, Telegram, route planner, EV Cockpit, remote access) is under \u201cNoch einrichten\u201d (still to set up) afterwards. Almost nothing is preselected. Anything that sends data out stays off until you turn it on yourself."),
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
        "links": [("/ev/", "🧭 Route planner"), ("/ev-cockpit/", "🖥️ EV Cockpit"), ("/app/en/", "📱 Phone app (BETA)"), ("/app/en/#iphone", "🍏 iPhone: web app (BETA)"), ("/", "🗺️ Community map")],
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
                 ("Wie fange ich an?", "Datei herunterladen und einmalig mit PC oder Laptop aufs Auto bringen. Wir zeigen dir jeden Schritt.")],
        "h_fuer_mich": "Ist das was für mich?",
        "handy_link": "<b>Dein Auto am Handy:</b> als <a href=\"/app/\">Android-App</a> oder als <a href=\"/app/#iphone\">Web-App fürs iPhone</a>, beide BETA.",
        "wa_h": "WhatsApp-Community", "wa_knopf": "In die WhatsApp-Community",
        "wa_was": "Was es gibt: Ankündigungen, Treffpunkt, Hilfe bei der Installation, Beta-Test und Tacho, Fehler und Wünsche, Wächter und Dashcam, Laden und Wallbox.",
        "wa_hinweis": "Wer beitritt, sieht die Telefonnummer des Admins. Auch deine Nummer kann für andere sichtbar sein.",
        "wa_frei": "Privates Projekt, nicht von BYD. Mehr dazu im <a href=\"/datenschutz#whatsapp\">Datenschutz</a>.",
        "fuer_mich": [("✅", "Du hast einen BYD", "mit einem neueren Bildschirm-System (DiLink 3, 4 oder 5). Am besten getestet ist der Dolphin Surf."),
                      ("💻", "Du hast einmalig einen PC oder Laptop", "und etwa eine Stunde Zeit. Am Auto schaltest du einen Entwickler-Schalter ein, die Einrichtung führt dich durch."),
                      ("⚠️", "Panoptes ist noch in der Testphase", "Ein privates Freizeitprojekt, kostenlos und ohne Gewähr. Bitte lies vorher die <a href=\"hinweise.html\">Hinweise</a>.")],
        "alle_funktionen": "Alle weiteren Funktionen ansehen",
        "camp_detail": "🏕️ Camping-Modus im Detail (Beta)",
        "mehr_bilder": "Mehr Bilder ansehen",
        "echtheit": "Echtheit der Datei prüfen (für Fortgeschrittene)",
        "echtheit_text": "Das ist freiwillig. Wie du die Prüfsumme vergleichst, steht in der ausführlichen Anleitung unten (Schritt 2).",
        "aelter": "Ich habe schon eine ältere Version",
        "h_kurz": "In 5 Schritten aufs Auto",
        "kurz": [("Hinweise lesen.", "Panoptes ist für dein eigenes Auto, privat und auf eigenes Risiko. <a href=\"hinweise.html\">Zu den Hinweisen</a>."),
                 ("Entwickler-Schalter am Auto einschalten.", "Das ist der Entwickler-Zugang (ADB). Wie du hinkommst, hängt vom Modell ab: siehe <a href=\"/guide\">Anleitungen</a>."),
                 ("Datei mit PC oder Laptop aufs Auto bringen.", "PC und Auto ins selbe WLAN, dann zwei Befehle. Sie stehen in der ausführlichen Anleitung. Das ist nur einmal nötig. Der Weg mit USB-Stick wird gerade geprüft."),
                 ("Panoptes am Auto öffnen.", "Kurze Schritte fragen dich das Nötigste. Fast nichts ist vorausgewählt."),
                 ("Autostart erlauben.", "Damit Panoptes von selbst startet. Der Assistent öffnet die richtige Seite.")],
        "ausfuehrlich": "Ausführliche Anleitung (8 Schritte)",
        "ds_detail": "Genau nachlesen: was geht wohin?",
        # ab 0.1.21 (Kern 12): aWATTar-Börsenpreise; Telegram-Anmeldung, /wo, HTTPS/CT, Sitzheizung (Kern 12, DATENSCHUTZ_0.1.21_ENTWURF.md)
        # ab 0.1.22 (Kern 11, DATENSCHUTZ_GEWOHNHEITEN_ZEILE.md): Gewohnheiten, nur lokal im Auto
        "ds_ab_0122": [
            ('Nirgends – bleibt im Auto', 'Gewohnheiten: welche Bedienung (z. B. Klima, Sitzheizung, Wallbox, Wächter) wann, an welchem Ort (zu Hause oder ein gespeicherter Ort, keine Koordinaten), Außentemperatur, Akkustand, von wo bedient (Bildschirm, Handy, Cockpit, Tasten im Auto)', 'Nur wenn du beim Einrichten „Gewohnheiten merken“ bejaht hast. 60 Tage aufbewahrt, „Alles vergessen“ löscht sofort, jederzeit abschaltbar'),
        ],
        "ds_ab_0121": [
            ("aWATTar (aWATTar GmbH bzw. Deutschland GmbH, api.awattar.at / api.awattar.de)", "Panoptes holt höchstens einmal je Stunde (meist einmal am Tag) die öffentlichen Börsenstrompreise für AT bzw. DE. Es gibt kein Konto, und es werden keine Daten über dich oder dein Auto gesendet; aWATTar sieht nur die Internetadresse des Autos.", "nur wenn du im Ladeplan „Ich habe einen dynamischen Stromtarif“ einschaltest (Standard aus) und als Strompreis zu Hause „Börsenpreis“ wählst. Schalter „dynamischer Stromtarif“ aus: ab sofort kein Abruf mehr."),
            ('Telegram: Anmeldung an der Weboberfläche', 'Eine kurze Nachricht an deinen eigenen Telegram-Chat mit einer 4-stelligen Prüfzahl und zwei Knöpfen (Erlauben/Ablehnen). Kein Gerätename, kein Browsername, keine IP-Adresse.', 'Nur wenn du im Browser auf „Per Telegram anmelden“ drückst und Telegram in Panoptes eingerichtet ist.'),
            ('Telegram: Standort bei /wo', 'Die Parkposition des Autos.', 'Nur wenn du /wo schickst UND die Standort-Freigabe dafür eingeschaltet hast. Sonst antwortet Panoptes ohne Position.'),
            ("Let's Encrypt und öffentliche Certificate-Transparency-Protokolle (über Tailscale)", "Für die App am Handy über HTTPS: Tailscale holt für dein Auto ein Zertifikat bei Let's Encrypt. Dabei wird der Tailscale-Name deines Autos (z. B. auto.dein-tailnet.ts.net) öffentlich und dauerhaft in den Certificate-Transparency-Protokollen eingetragen. Jeder kann diese Namen einsehen. Erreichbar ist das Auto dadurch nicht: Ins Tailnet kommen weiter nur deine eigenen Geräte.", 'Nur wenn du HTTPS in Panoptes selbst einschaltest. Ab Werk ist es aus.'),
            ('BYD-Cloud: Steuern bei ausgeschaltetem Auto', 'Der Befehl über deine BYD-Anmeldung, zum Beispiel Sitzheizung, Klima und Vorheizen oder Heizen im Camping-Modus. Das Auto wird dafür geweckt.', 'Nur wenn das Auto aus ist, du die BYD-Cloud eingerichtet und die Funktion gewählt hast. Ist das Auto an, schaltet Panoptes direkt im Auto und schickt nichts in die Cloud.'),
        ],
        # Datenschutz-Zeilen ab 0.1.20 (Kern 12, 27.10.2026): erscheinen automatisch, sobald versionen.json >= 0.1.20 meldet
        "ds_ab_0120": [
            ("go-e Cloud (go-e GmbH, *.api.v3.go-e.io)", "Status und Befehle deiner go-e-Wallbox (laden ja/nein, Ladestrom, Leistung) und dein API-Token. Der Token wird einmal per Handy direkt an dein Auto übergeben und liegt dort verschlüsselt; er geht nie über Panoptes-Server.", "nur wenn du bei der Wallbox „go-e Charger (Cloud)“ wählst und ausdrücklich einwilligst (Standard aus). Einwilligung ausschalten oder Gerät entfernen beendet es sofort."),
            ("Wallbox-Konto (Wallbox Chargers S.L., api.wall-box.com / user-api.wall-box.com)", "Anmeldung mit deinem Wallbox-Konto (E-Mail und Passwort, verschlüsselt im Auto gespeichert), Status und Befehle deines Ladegeräts. Inoffizielle Schnittstelle (wie bei Home Assistant).", "nur wenn du „Wallbox Pulsar / Commander (Cloud)“ wählst und ausdrücklich einwilligst (Standard aus). Einwilligung ausschalten oder Gerät entfernen beendet es sofort."),
        ],
        # Brücke (Koordination 28.10.2026): eigener Anker #bruecke, der Zustimmungssatz in Panoptes 0.1.24 verlinkt hierher
        "bruecke_h": "Handy und PC übers Internet (Brücke)",
        "bruecke": "Unterwegs erreicht die Handy-App oder das EV-Cockpit am PC dein Auto über einen kleinen Vermittlungsdienst auf unserem Server. Er ist aus, bis du ihn im Auto einschaltest. <b>Ende-zu-Ende verschlüsselt</b>: Der Server reicht nur unlesbare Daten weiter und sieht keine Fahrzeugdaten, Orte oder Befehle. <b>Keine IP-Protokolle</b>, pro Stunde nur eine Zählzeile für den ganzen Dienst. Server im Rechenzentrum von Hetzner in Falkenstein, Deutschland. Schaltest du die Brücke aus, wird dein Postfach gelöscht. Rechtsgrundlage: Art. 6 Abs. 1 lit. b DSGVO (eine Funktion, die du selbst einschaltest). <a href=\"/datenschutz#bruecke\">Alle Einzelheiten</a>",
        "zus_detail": "Wie Panoptes mit Cockpit, Routenplaner, Karte und Wallbox verbunden ist",
    },
    "en": {
        "hero_anl": "How to install",
        "drei": [("What is this?", "A free app that runs on the screen in your BYD."),
                 ("Who is it for?", "For BYD drivers who want a camera guard, a trip log and charging costs."),
                 ("How do I start?", "Download the file and put it on the car once with a PC or laptop. We show you every step.")],
        "h_fuer_mich": "Is this for me?",
        "handy_link": "<b>Your car on your phone:</b> as an <a href=\"/app/en/\">Android app</a> or as a <a href=\"/app/en/#iphone\">web app for iPhone</a>, both BETA.",
        "wa_h": "WhatsApp community", "wa_knopf": "Join the WhatsApp community",
        "wa_was": "What you get: announcements, a meeting place, help with installing, beta test and cluster, bugs and wishes, guard and dashcam, charging and wallbox.",
        "wa_hinweis": "Anyone who joins sees the admin's phone number. Your number may also be visible to others.",
        "wa_frei": "Private project, not made by BYD. More in the <a href=\"/en/datenschutz#whatsapp\">privacy policy</a>.",
        "fuer_mich": [("✅", "You have a BYD", "with a newer screen system (DiLink 3, 4 or 5). Best tested on the Dolphin Surf."),
                      ("💻", "You have a PC or laptop once", "and about an hour. You switch on a developer setting in the car, the setup guides you through it."),
                      ("⚠️", "Panoptes is still being tested", "A private hobby project, free and without warranty. Please read the <a href=\"hinweise.html\">notes</a> first.")],
        "alle_funktionen": "See all other features",
        "camp_detail": "🏕️ Camping mode in detail (beta)",
        "mehr_bilder": "See more pictures",
        "echtheit": "Check that the file is genuine (advanced)",
        "echtheit_text": "This is optional. How to compare the checksum is explained in the detailed guide below (step 2).",
        "aelter": "I already have an older version",
        "h_kurz": "Onto the car in 5 steps",
        "kurz": [("Read the notes.", "Panoptes is for your own car, private and at your own risk. <a href=\"hinweise.html\">Read the notes</a>."),
                 ("Switch on the developer setting in the car.", "This is the developer access (ADB). How to get there depends on the model: see the <a href=\"/en/guide\">guides</a>."),
                 ("Put the file on the car with a PC or laptop.", "PC and car on the same Wi-Fi, then two commands. They are in the detailed guide. You only need this once. The way with a USB stick is being checked."),
                 ("Open Panoptes in the car.", "Short steps ask you the essentials. Almost nothing is preselected."),
                 ("Allow autostart.", "So Panoptes starts by itself. The assistant opens the right page.")],
        "ausfuehrlich": "Detailed guide (8 steps)",
        "ds_detail": "In detail: what goes where?",
        "ds_ab_0122": [
            ('Nowhere – stays in the car', 'Habits: which control (e.g. climate, seat heating, wallbox, guardian) at what time, at which place (home or a saved place, no coordinates), outside temperature, battery level, where it was operated from (screen, phone, cockpit, car buttons)', 'Only if you said yes to “Remember habits” during setup. Kept for 60 days, “Forget everything” deletes it at once, can be switched off at any time'),
        ],
        "ds_ab_0121": [
            ("aWATTar (aWATTar GmbH / Deutschland GmbH, api.awattar.at / api.awattar.de)", "Panoptes fetches the public exchange electricity prices for AT or DE at most once per hour (usually once a day). There is no account, and no data about you or your car is sent; aWATTar only sees the car’s internet address.", "only if you switch on “I have a dynamic electricity tariff” in the charge plan (off by default) and choose “Exchange price” as your home electricity price. Switch “dynamic electricity tariff” off: no more requests from then on."),
            ('Telegram: web interface sign-in', 'A short message to your own Telegram chat with a 4-digit check number and two buttons (Allow/Deny). No device name, no browser name, no IP address.', 'Only when you tap “Sign in with Telegram” in the browser and Telegram is set up in Panoptes.'),
            ('Telegram: location with /wo', "The car's parking position.", 'Only when you send /wo AND have switched on location sharing for it. Otherwise Panoptes replies without a position.'),
            ("Let's Encrypt and public Certificate Transparency logs (via Tailscale)", "For the phone app over HTTPS: Tailscale gets a certificate for your car from Let's Encrypt. This puts your car's Tailscale name (e.g. car.your-tailnet.ts.net) into the Certificate Transparency logs, publicly and permanently. Anyone can see these names. It does not make the car reachable: only your own devices can get into your tailnet.", 'Only if you switch HTTPS on yourself. It is off by default.'),
            ('BYD cloud: control while the car is off', 'The command via your BYD login, for example seat heating, climate and preheating, or heating in camping mode. The car is woken for this.', 'Only when the car is off and you have set up the BYD cloud and chosen the function. When the car is on, Panoptes switches directly in the car and sends nothing to the cloud.'),
        ],
        "ds_ab_0120": [
            ("go-e Cloud (go-e GmbH, *.api.v3.go-e.io)", "Status and commands of your go-e wallbox (charging on/off, charging current, power) and your API token. The token is handed to your car once via your phone and stored there encrypted; it never passes through Panoptes servers.", "only if you choose “go-e Charger (Cloud)” for your wallbox and explicitly consent (off by default). Turning consent off or removing the device stops it immediately."),
            ("Wallbox account (Wallbox Chargers S.L., api.wall-box.com / user-api.wall-box.com)", "Login with your Wallbox account (e-mail and password, stored encrypted in the car), status and commands of your charger. Unofficial interface (as used by Home Assistant).", "only if you choose “Wallbox Pulsar / Commander (Cloud)” and explicitly consent (off by default). Turning consent off or removing the device stops it immediately."),
        ],
        "bruecke_h": "Phone and PC over the internet (bridge)",
        "bruecke": "On the road, the phone app or EV Cockpit on your PC reaches your car through a small relay service on our server. It is off until you switch it on in the car. <b>End-to-end encrypted</b>: the server only forwards unreadable data and cannot see vehicle data, places or commands. <b>No IP logs</b>, only one count line per hour for the whole service. Server in the Hetzner data centre in Falkenstein, Germany. If you switch the bridge off, your mailbox is deleted. Legal basis: Art. 6(1)(b) GDPR (a feature you switch on yourself). <a href=\"/en/datenschutz#bruecke\">All details</a>",
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


GROESSE = {"pc": (1440, 900), "handy": (780, 1688), "display": (1280, 720), "tacho": (960, 432), "kachel": (768, 600), "lnc": (1280, 696)}


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
         "ha": (670, 410, 210, 90, s["ha"], s["ha2"], False),
         "wb": (40, 230, 190, 90, s["wb"], s["wb2"], False)}
    mitte = lambda n: (k[n][0] + k[n][2] / 2, k[n][1] + k[n][3] / 2)
    kanten = [("auto", "cockpit", "1", s["t1"], False), ("auto", "planer", "2", s["t2"], False),
              ("auto", "karte", "3", s["t3"], False), ("auto", "tg", "4", s["t4"], False),
              ("auto", "wb", "5", s["t5"], False), ("auto", "ha", "6", s["t6"], False), ("cockpit", "planer", "7", s["t7"], True)]
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
              ("5", s["wb"], s["wb2"], s["t5"], False), ("6", s["ha"], s["ha2"], s["t6"], False)]
    h = 130 + len(knoten) * 96
    o = ['<svg viewBox="0 0 400 %d" role="img" aria-label="%s" xmlns="http://www.w3.org/2000/svg">' % (h, e(s["aria"])),
         '<style>.kn{fill:var(--node);stroke:var(--line);stroke-width:1.5}.kn.haupt{stroke:var(--grn);stroke-width:2.5}'
         '.kn.bald{stroke-dasharray:6 5}.t1{fill:var(--txt);font:700 18px system-ui,sans-serif}.t2{fill:var(--mut);font:14px system-ui,sans-serif}'
         '.t3{fill:var(--grn);font:600 14px system-ui,sans-serif}.li{stroke:var(--grn);stroke-width:2.4;fill:none}'
         '.li.bald{stroke:var(--mut);stroke-dasharray:6 5}.nk{fill:var(--grn)}.nt{fill:#04110a;font:800 13px system-ui,sans-serif}</style>']
    letzte = 130 + (len(knoten) - 1) * 96 + 38
    o.append('<line class="li" x1="34" y1="60" x2="34" y2="%d"/><line class="li" x1="34" y1="60" x2="80" y2="60"/>' % (letzte - 96))
    o.append('<line class="li" x1="34" y1="%d" x2="34" y2="%d"/>' % (letzte - 96, letzte))
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
                                       ("/ev-cockpit/", "EV-Cockpit"), ("/app/", "Handy-App"), ("/guide", "Anleitungen")],
           "menue": "Menü", "o": "en", "o_kurz": "EN", "o_lang": "English",
           "fuss": [("/impressum", "Impressum"), ("/datenschutz", "Datenschutz"), ("/nutzungsbedingungen", "Nutzungsbedingungen"),
                    ("/guide", "Anleitungen"), ("/community/", "Panoptes-Community"), (WA, "WhatsApp-Gruppe")],
           "klein": "Privates Freizeitprojekt, kostenlos und ohne Gewähr. Nicht verbunden mit BYD Auto Co., Ltd. "
                    "„BYD“ und Modellnamen sind Marken ihrer jeweiligen Inhaber."},
    "en": {"start": "/en/", "eintraege": [("/en/#karte", "Map"), ("/ev/", "Route planner"), ("/panoptes/en/", "Panoptes"),
                                          ("/ev-cockpit/en/", "EV Cockpit"), ("/app/en/", "Phone app"), ("/en/guide", "Guides")],
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
WHATSAPP = "https://chat.whatsapp.com/IQRtn9JViH4FhypAQsS3yK"
OBEN = ("🛡️", "📹", "📒", "🗺️", "💬", "🏠", "🏕️")      # diese 7 Funktionen sichtbar, der Rest aufklappbar


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
    o.append("  " + reihe([("display38", "display", t["hero_alt_pc"]), ("waechter38", "handy", t["hero_alt_handy"])], p, sofort=True))
    o.append('  <div class="bd-hinweis"><p>%s</p></div>' % t["wichtig"])
    # Ist das was für mich?
    o.append('  <h2 id="fuer-mich">%s</h2>\n  <div class="bd-kacheln">' % t["h_fuer_mich"])
    for ic, h, txt in t["fuer_mich"]:
        o.append('    <div class="bd-kachel"><span class="bd-symbol">%s</span><h3>%s</h3><p>%s</p></div>' % (ic, h, txt))
    o.append("  </div>")
    # Funktionen: 6 oben, Rest aufklappbar
    o.append('  <p>%s</p>' % t["handy_link"])
    # WhatsApp-Community (Alfred, 30.10.2026): Link sichtbar im HTML, ohne Zaehlung
    o.append('  <h2 id="whatsapp">%s</h2>\n  <p>%s</p>' % (t["wa_h"], t["wa_was"]))
    o.append('  <div class="bd-knoepfe"><a class="bd-knopf gross leer" href="%s" target="_blank" rel="noopener">💬 %s</a></div>' % (WHATSAPP, t["wa_knopf"]))
    o.append('  <div class="bd-hinweis"><p>%s</p><p>%s</p></div>' % (t["wa_hinweis"], t["wa_frei"]))
    o.append('  <h2 id="funktionen">%s</h2>\n  <div class="raster">' % t["h_kann"])
    oben = [x for x in t["kann"] if x[0] in OBEN]
    rest = [x for x in t["kann"] if x[0] not in OBEN]
    for ic, h, txt in oben:
        o.append('    <div class="feat"><div class="ic">%s</div><h3>%s</h3><p>%s</p></div>' % (ic, h, txt))
    o.append('  </div>\n  <details class="bd-auf"><summary>%s (%d)</summary>\n  <div class="raster">' % (t["alle_funktionen"], len(rest)))
    for ic, h, txt in rest:
        o.append('    <div class="feat"><div class="ic">%s</div><h3>%s</h3><p>%s</p></div>' % (ic, h, txt))
    o.append("  </div></details>")
    # Alle Funktionen nach Bereichen, je Bereich aufklappbar (ab 0.1.37)
    if t.get("alle"):
        al = t["alle"]
        o.append('  <h2 id="alle-funktionen">%s</h2><p class="lead">%s</p>' % (al["h"], al["lead"]))
        for titel, punkte in al["gruppen"]:
            zeilen = "".join("<li>%s%s</li>" % (html.escape(x), (' <span class="bald">%s</span>' % al["chips"][c]) if c else "") for x, c in punkte)
            o.append('  <details class="bd-auf"><summary>%s (%d)</summary><ul class="liste">%s</ul></details>' % (html.escape(titel), len(punkte), zeilen))
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
    # Tacho und Launcher (Bilder), ab 0.1.37
    if t.get("tl"):
        tl = t["tl"]
        o.append('  <h2 id="tacho-launcher">%s</h2><p class="lead">%s</p>\n  <div class="galerie">' % (tl["h"], tl["lead"]))
        for cap, bilder in tl["bilder"]:
            o.append('    <figure>%s<figcaption><b>%s</b></figcaption></figure>' % (reihe(bilder, p), html.escape(cap)))
        o.append("  </div>")
    # Tacho-Test (Beta), ab 0.1.30
    if t.get("tacho"):
        tc = t["tacho"]
        o.append('  <h2 id="tacho-test">%s</h2>' % tc["h"])
        o.append('  <div class="card">%s<h3>%s</h3><ol class="liste">%s</ol><p>%s</p><h3>%s</h3><ul class="liste">%s</ul></div>'
                 % ("".join("<p>%s</p>" % x for x in tc["intro"]), tc["h_schritte"], "".join("<li>%s</li>" % x for x in tc["schritte"]),
                    tc["bekommen"], tc["h_gut"], "".join("<li>%s</li>" % x for x in tc["gut"])))
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
    if t.get("neu") and t.get("neu_version") == VERSION:
        o.append('    <h3>%s</h3><ul class="liste">%s</ul>' % (t["neu_titel"], "".join("<li>%s</li>" % x for x in t["neu"])))
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
    if tuple(int(x) for x in VERSION.split(".")[:3]) >= (0, 1, 22):
        zeilen[-1:-1] = t.get("ds_ab_0122", [])
    for wo, was, wann in zeilen:
        o.append("    <tr><td><b>%s</b></td><td>%s</td><td>%s</td></tr>" % (html.escape(wo), html.escape(was), wann))
    o.append("  </table></div></details>")
    o.append('  <div class="card" id="bruecke"><h3 style="margin-top:0">%s</h3><p style="margin-bottom:0">%s</p></div>' % (t["bruecke_h"], t["bruecke"]))
    o.append('  <details class="bd-auf" id="zusammenhang"><summary>%s</summary><p class="lead">%s</p>' % (t["zus_detail"], t["zus_lead"]))
    o.append('  <div class="diagramm"><div class="breit">%s</div><div class="schmal">%s</div></div>\n  <div class="verb">'
             % (diagramm(t["svg"]), diagramm_schmal(t["svg"])))
    for nr, h, was, nicht in t["verb"]:
        o.append('    <div class="card"><h3><span class="nr">%s</span>%s</h3><p>%s</p><p class="nicht"><b>%s:</b> %s</p></div>'
                 % (nr, html.escape(h), was if "<a " in was else html.escape(was), t["nicht"], html.escape(nicht.split(": ", 1)[1] if ": " in nicht[:20] else nicht)))
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
            return x.replace("{V}", VERSION).replace("{APK}", PV["apk_datei"]).replace("{MB}", str(PV["groesse_mb"]))
        return x.replace("{V}", sp("version", VERSION)).replace("{APK}", sp("apk_datei", PV["apk_datei"])).replace("{MB}", sp("groesse_mb", PV["groesse_mb"]))
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
