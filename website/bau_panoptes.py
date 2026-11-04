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
        "hero_alt_pc": "Panoptes 0.1.38 am Bildschirm im Auto: Startseite mit Ladestand, Reichweite und Schnellknöpfen",
        "hero_alt_handy": "Panoptes 0.1.38 am Handy: Startseite",
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
            ("Camping-Seite am Bildschirm im Auto: Einschalten, Akku, Heizdauer; oben der Hinweis „Probelauf“.", [("camping38", "display", "Camping-Seite von Panoptes: Camping ist aus, Knopf Einschalten, Hinweis Probelauf, Werte noch nicht verfügbar")]),
            ("Einstellungen: Wärme, Heizweg, Akku-Untergrenze, 12-V-Warnung.", [("camping-einstellungen", "display", "Camping-Einstellungen: Wärme, Heizweg Probelauf, Vorheizen, Akku-Untergrenze 20 Prozent, 12-Volt-Warnung")]),
            ("Nachtbildschirm: fast schwarz, große Uhr, Rückmeldung „Zu kalt / Passt / Zu warm“. Daneben die Camping-Seite am Handy.", [("nacht", "display", "Nachtbildschirm: schwarzer Hintergrund, große Uhr und Datum, Tasten Zu kalt, Passt, Zu warm"), ("camping38", "handy", "Camping-Seite am Handy bei 390 Pixel Breite")]),
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
                ("Telegram-Bot mit Menü und großen Knöpfen; Befehle wie /status, /wo, /camping gehen weiter", ""),
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
                ("Updates in der App, per Knopf aus Telegram, vom Handy oder Cockpit (nur mit Erlaubnis); ohne WLAN fragt Panoptes vorher; danach richtet es sich selbst wieder ein", ""),
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
            ("🧩", "Einrichtungshilfe", "Beim ersten Start führen dich drei kurze Bildschirme durch das Nötigste, alle Freigaben stehen auf einem Bildschirm. Alles Weitere findest du später unter „Noch einrichten“. Fast nichts ist vorausgewählt (nur „Gewohnheiten merken“ steht auf Ja, das bleibt im Auto); alles, was Daten nach außen schickt, bleibt aus, bis du es einschaltest. Was dein Auto nicht kann, überspringt er mit einer Erklärung."),
            ("🛡️", "Wächter mit KI-Erkennung", "Steht dein Auto, achten die Kameras auf das Umfeld. Du entscheidest selbst, wann aufgenommen wird: nur bei Erschütterung, mit KI-Erkennung überall oder nur an deinen privaten Orten wie Garage oder Einfahrt. Ohne Wahl nimmt er nur bei Erschütterung auf. Damit die 12-V-Batterie geschont wird, legt er sich schlafen; die Grenze richtet sich nach dem Batterietyp (Blei, AGM oder LFP)."),
            ("📹", "Dashcam <span class=\"bald\">ab 0.1.27</span>", "Bei einer Vollbremsung oder einem Stoß sichert Panoptes von selbst einen kurzen Clip aus allen Kameras, etwa 20 Sekunden davor und danach. Ohne Daueraufnahme. Die Clips bleiben im Auto oder auf dem USB-Stick und werden nie von selbst verschickt. Clips am Handy ansehen und speichern geht mit der <a href=\"/app/\">Handy-App</a> (Beta 4). Panoptes fragt dann „Behalten?“, sonst wird der Clip nach 72 Stunden gelöscht. Ab 0.1.36 merkt sich jeder Clip, was ihn ausgelöst hat (ohne Ort). In der Schweiz ist die Dashcam ab Werk aus. Ob Aufnahmen beim Fahren bei dir erlaubt sind, ist je nach Land verschieden, siehe <a href=\"hinweise.html\">Hinweise</a>."),
            ("📒", "Fahrten und Laden", "Fahrten, Verbrauch und Ladungen werden im Auto mitgeschrieben. Panoptes zeigt die Kosten je Ladung, je Monat und als Ø Kosten je 100 km, ab 0.1.35 mit geschätztem Ladeverlust (Zeichen „~“). Fehlt ein Preis, steht dort „Preis fehlt“ statt einer erfundenen Zahl; Gratis-Laden lässt sich ausdrücklich eintragen."),
            ("🔌", "„Wo hast du geladen?“", "Nach dem Laden fragt Panoptes im Stand, nie während der Fahrt, nach Station und Preis. Mit „Ort merken“ kennt es den Preis beim nächsten Mal. Mit „Laut Säule“ trägst du kWh und Kosten der Säule ein; dein Preis gilt dann bei „Günstigste in der Nähe“ (AC und DC getrennt). Die Frage lässt sich abschalten."),
            ("💳", "Deine Ladekarten im Auto", "Ladekarten und Netze, Mindestleistung, Stecker und Ankunfts-Ladestand stellst du im Auto ein. Der Routenplaner rechnet damit; gespeichert wird das nur im Auto."),
            ("🏠", "Wallbox <span class=\"bald\">Beta</span>", "Deine Wallbox über evcc, Home Assistant oder Tuya einrichten, ab Version 0.1.12 auch direkt (z. B. go-e, KEBA, openWB, Easee, Zaptec): Ladestand sehen, Modus, Ladegrenze und Strom einstellen. Steuern nur, wenn das Auto steht, mit Rückfrage und je Ladepunkt eigens freigegeben. Bisher nur mit Demo- und Testgeräten geprüft."),
            ("📍", "Deine Orte", "Eine Liste für alles: Zuhause, Garage, Arbeit oder der Ladeplatz mit eigenem Preis. Je Ort legst du fest, ob er privat ist (Wächter), ein Ladepreis gilt oder er als Ziel im Navi steht. Die Orte verlassen das Auto nicht."),
            ("🌍", "Fernzugang", "Über Tailscale erreichst du dein Auto von überall. Eingerichtet wird das mit einem QR-Code am Bildschirm im Auto und deinem eigenen Tailscale-Konto. Für Fortgeschrittene gibt es ab 0.1.14 zusätzlich einen unabhängigen Notzugang, ab Werk aus."),
            ("💬", "Meldungen über Telegram", "Dein eigener Bot meldet Wächter-Ereignisse, Laden, schwache Starterbatterie, Reifendruck und Updates. Jede Kategorie einzeln schaltbar, mit Ruhezeit für die Nacht. Ab 0.1.38.2: Schreib dem Bot irgendetwas, dann kommt ein Menü mit großen Knöpfen. Bilder und Videos nur, wenn du das einschaltest. <a href=\"telegram.html\">So verbindest du Telegram</a>"),
            ("🗺️", "Karte mit Ladesäulen", "Du wählst selbst, woher die Karte kommt: vom Community-Server (mit Gelände und freien Ladeplätzen, wo Betreiber Daten liefern), von OpenStreetMap oder gar nicht. Solange du nichts wählst, bleibt die Karte leer. Blitzer zeigt sie nur in Österreich, ab Werk aus und mit Rechtshinweis."),
            ("🔋", "„Reicht es noch?“", "Mit einer Route aus dem Routenplaner, auch mit Zwischenzielen, sagt dir Panoptes unterwegs, ob der Akku bis zum nächsten Stopp reicht, und schlägt bei Bedarf einen Ladestopp vor."),
            ("📊", "Monatsbericht", "Gefahrene Kilometer, Verbrauch, Laden und Kosten, Standverlust und Wächter-Ereignisse eines Monats auf einen Blick, auch zum Drucken. Gerechnet wird im Auto."),
            ("🔁", "Umstieg von OverDrive", "Wer bisher die App OverDrive genutzt hat, übernimmt Fahrten, Ladungen und Einstellungen, mit Vorschau und ohne Doppelte. Einwilligungen und riskante Schalter übernimmt Panoptes nie, die stellst du selbst ein."),
            ("🧭", "Verbindung zum Routenplaner", "Panoptes lässt sich mit deinem Konto auf <a href=\"/ev/\">byd.serveone.at/ev/</a> verbinden: Code am Auto anzeigen, am Handy bestätigen, fertig. Jederzeit trennbar."),
            ("🖥️", "EV-Cockpit am PC", "Das <a href=\"/ev-cockpit/\">EV-Cockpit</a> zeigt die Daten von Panoptes am PC, auch Ladungen und Kosten, und kann die Einstellungen ändern. Koppeln bestätigst du mit einem Tipp und einer vierstelligen Prüfzahl. Ab Cockpit 1.23 auch Tacho wählen, Launcher einrichten und Updates installieren, nur mit deiner Erlaubnis. Ab 1.24 planst du im Cockpit auch eine Route und schickst sie ins Auto."),
            ("⬆️", "Updates in der App", "Panoptes sucht auf Wunsch selbst nach neuen Versionen. Unter Einstellungen → Alle Einstellungen → App-Updates wählst du: „Nur melden“, „Kleine Updates von selbst, große melden“ (Standard) oder „Alles automatisch“. Kleine Updates (nur die letzte Zahl ändert sich) kommen still, große meldet Panoptes vorher mit einer Zusammenfassung. Wer „Nur melden“ hatte, wurde einmal umgestellt und hat das gesagt bekommen. Installiert wird nie während der Fahrt: Startest du ein Update selbst, läuft es sofort, wenn das Auto in P steht, auch mit Zündung an; von selbst erst, wenn das Auto mindestens 10 Minuten aus ist; geht etwas schief, kommt die vorige Version nach spätestens 30 Minuten von selbst zurück. Ab 0.1.38.2 auch per Knopf aus Telegram, vom Handy oder Cockpit, nur mit deiner Erlaubnis. Nach einem Update richtet sich Panoptes selbst wieder ein und meldet, wenn alles läuft. Ab 0.1.13 verändert Panoptes von selbst keine dauerhaften Android-Einstellungen mehr (etwa „Bildschirm immer an“); früher gesetzte Werte lassen sich zurücksetzen. Was du selbst änderst (eigenes Bild, Apps ausschalten), bleibt, bis du es zurückstellst. Ab 0.1.36 bleiben die Logs bei Updates erhalten."),
            ("🏕️", "Camping-Modus <span class=\"bald\">Beta</span>", "Wächter „bewohnt“, Nachtbildschirm, Akku-Schutz mit Restdauer. Einschalten per Tipp, am Handy oder mit /camping in Telegram. Die Heizart wählst du auf der Camping-Seite; ab Werk nur Probelauf. <a href=\"#camping\">Mehr dazu</a>"),
            ("🖼️", "Bildschirm <span class=\"bald\">ab 0.1.37</span>", "Eigenes Bild für den Startbildschirm. Bildschirm mit Zahlencode sperren (nur in P). Apps aus- und einschalten. USB-Stick lesen."),
            ("🚀", "Panoptes Launcher <span class=\"bald\">ab 0.1.37</span>", "Eigene App, freiwillig: Startbildschirm mit Klima im Dock, Android Auto und CarPlay (wenn dein Auto sie hat) und Update-Hinweis. Installieren per Knopf in Panoptes, nie von selbst. Ab 0.1.38 richtest du ihn bequem am Handy oder im Cockpit ein, nur wenn du es bei der Kopplung erlaubst. Das Haus links führt immer zum BYD-Startbildschirm zurück. <a href=\"#tacho-launcher\">Bilder</a>"),
            ("🐾", "Tiermodus <span class=\"bald\">ab 0.1.36</span>", "Hält das Klima für dein Tier an und meldet Probleme aufs Handy und in Telegram. Nur eine Hilfe, keine Garantie, du bleibst verantwortlich."),
            ("🤖", "KI-Assistent", "Nur, wenn du ihn selbst einrichtest. Ab 0.1.36 darf er nur Klima, Sitzheizung und Sonnenrollo bedienen und Werte anzeigen. Nie Hupe, Licht, Blinker, Fenster, Kofferraum oder Wächter."),
            ("🧰", "Kleine Helfer <span class=\"bald\">ab 0.1.36</span>", "Bildschirm reinigen (30 Sekunden gesperrt, nur in P). Ziel aus einem Google-Maps- oder Waze-Link übernehmen. Dateien zwischen Handy und Auto (eigenes Recht, ab Werk aus, keine Apps). Panoptes prüft täglich seine Rechte und repariert, was geht."),
            ("🌐", "Fünf Sprachen", "Deutsch, Englisch, Französisch, Italienisch und Niederländisch."),
        ],
        "h_bilder": "So sieht Panoptes aus",
        "bilder_lead": "Panoptes 0.1.38 am Bildschirm im Auto und am Handy, aufgenommen im Emulator mit Musterdaten, nicht aus einem Auto. Bilder mit gelbem Band „Musterdaten“ kommen aus einem Demo-Profil: keine echten Fahrten, Orte oder Befehle, die Karte ist eine vereinfachte Musterkarte. Andere Seiten ohne Daten zeigen „nicht verfügbar“ oder „--“. Klick auf ein Bild zum Vergrößern.",
        "bilder": [
            ("Start: Ladestand, Reichweite und Schnellknöpfe.", [("startd38", "display", "Startseite mit Musterdaten: 86 Prozent, 236 km, Schnellknöpfe, Standort-Karte und Ladekosten"), ("startd38", "handy", "Startseite am Handy mit Musterdaten")]),
            ("Fahrtenbuch: jede Fahrt mit Strecke, Dauer, Verbrauch und Kosten.", [("fahrt38", "display", "Eine Fahrt mit Musterdaten: 22 km, 25 Minuten, 14,56 kWh pro 100 km"), ("fahrt38", "handy", "Fahrt am Handy mit Musterdaten")]),
            ("Karte und Navigation, hier mit einer vereinfachten Musterkarte.", [("karte38", "display", "Navigation mit vereinfachter Musterkarte, Suchfeld Wohin und Favoriten"), ("karte38", "handy", "Navigation am Handy mit Musterkarte")]),
            ("Laden: Ladungen, Energie, Kosten und Wallbox.", [("laden38", "display", "Laden mit Musterdaten: Wallbox, 6 Ladungen, 149 kWh"), ("laden38", "handy", "Laden am Handy mit Musterdaten")]),
            ("Kameras & Wächter: ein großer Schalter, darunter die Aufnahmen von heute.", [("waechter38", "display", "Wächter am Bildschirm im Auto: Wächter ist aus, großer Knopf Wächter einschalten"), ("waechter38", "handy", "Wächter am Handy mit großem Schalter")]),
            ("Apps & Display → Display: „Was zeigt der Tacho?“ Ein Bild antippen.", [("display38", "display", "Seite Display: Tacho, Hintergrund und Sperre, Launcher; Auswahl Was zeigt der Tacho"), ("display38", "handy", "Seite Display am Handy")]),
            ("Monatsbericht: Kilometer, Verbrauch, Laden, Standverlust und Wächter, auch zum Drucken.", [("berichtd38", "display", "Monatsbericht Oktober 2026 mit Musterdaten: 1010 km, 14,6 kWh pro 100 km, 149 kWh geladen"), ("berichtd38", "handy", "Monatsbericht am Handy mit Musterdaten")]),
            ("Regeln: „Wenn … / Dann …“ selbst bauen.", [("regeln38", "display", "Wenn-dann-Regeln: noch keine Regel, Knopf Neue Regel"), ("regeln38", "handy", "Regeln am Handy")]),
            ("Telegram: in drei kurzen Schritten einrichten.", [("telegram38", "display", "Telegram-Meldungen einrichten in drei Schritten"), ("telegram38", "handy", "Telegram einrichten am Handy")]),
            ("Gerät koppeln: Handy oder EV-Cockpit, nur mit deiner Bestätigung.", [("koppeln38", "display", "Gerät koppeln: Knopf Neues Gerät koppeln, noch kein Gerät gekoppelt"), ("koppeln38", "handy", "Gerät koppeln am Handy")]),
            ("Einstellungen: „Was möchtest du einstellen?“, mit Suche.", [("system38", "display", "Alle Einstellungen: Verbindungen, Auto und Anzeige, App und Daten, Erweitert"), ("system38", "handy", "Alle Einstellungen am Handy")]),
            ("Einrichtung: unter „Noch einrichten“ stehen freiwillige Schritte.", [("einrichtung38", "display", "Einrichtung: Liste Noch einrichten mit freiwilligen Schritten"), ("einrichtung38", "handy", "Noch einrichten am Handy")]),
            ("Steuerung am Handy: Kacheln für Sicherheit, Kofferraum, Klima und Sitze.", [("steuerung38", "handy", "Steuerung am Handy mit Kacheln Sicherheit, Kofferraum, Klima, Sitze")]),
            ("Apps & Display: zwei Apps nebeneinander am Bildschirm.", [("apps38", "display", "Apps nebeneinander mit Musterdaten: Fotos und Hörbücher"), ("apps38", "handy", "Apps nebeneinander am Handy")]),
        ],
        "handy": "am Handy", "pc": "am PC",
        "zus_block": '<style>\n/* So gehört alles zusammen – Fassung 2 (04.11.2026). Farben aus dem Seiten-Theme. */\n.zus{--za:var(--accent-2,#c6f24e);--zl:var(--accent,#4fd1e8);--zp:var(--panel,rgba(127,127,127,.08));--zb:var(--line,rgba(127,127,127,.3));--zt:var(--text,currentColor);--zu:var(--muted,#8aa);position:relative}\n.zus h2{font-size:clamp(1.7rem,3.2vw,2.4rem);letter-spacing:-.02em;margin:0 0 .35em}\n.zus .zlead{max-width:62ch;color:var(--zu);font-size:1.08rem;margin:0 0 28px}\n.zus .zi{width:26px;height:26px;flex:none}\n.zus .znetz{position:relative;display:grid;grid-template-columns:1fr minmax(220px,.8fr) 1fr;grid-template-rows:auto auto;gap:28px 64px;align-items:stretch}\n.zus .zlinien{position:absolute;inset:0;width:100%;height:100%;pointer-events:none;z-index:0}\n.zus .zlinien line{stroke:var(--zl);stroke-opacity:.55;stroke-width:2;vector-effect:non-scaling-stroke}\n.zus .zlinien circle{fill:var(--za)}\n.zus .zk{position:relative;z-index:1;background:var(--zp);border:1px solid var(--zb);border-radius:16px;padding:20px 20px 18px;display:flex;flex-direction:column}\n.zus .zk .zkopf{display:flex;align-items:center;gap:12px;margin:0 0 10px}\n.zus .zk .zkopf .zi{color:var(--zl)}\n.zus .zk h3{margin:0;font-size:1.12rem;line-height:1.25}\n.zus .zk .zart{display:block;font-size:.74rem;letter-spacing:.08em;text-transform:uppercase;color:var(--zu);margin-top:2px}\n.zus .zk p{margin:0 0 10px;line-height:1.5}\n.zus .zk .zmehr{margin-top:auto;font-weight:600}\n.zus .zk.zh{grid-column:2;grid-row:1/3;align-self:center;border:2px solid var(--za);padding:26px 22px;text-align:left}\n.zus .zk.zh .zgross{width:56px;height:56px;color:var(--za);margin:0 0 12px}\n.zus .zk.zh h3{font-size:1.5rem}\n.zus .zk.zh .zart{color:var(--za)}\n.zus .p1{grid-column:1;grid-row:1}.zus .p2{grid-column:3;grid-row:1}.zus .p3{grid-column:1;grid-row:2}.zus .p4{grid-column:3;grid-row:2}\n.zus .zfakten{display:grid;grid-template-columns:repeat(4,1fr);gap:22px;margin:36px 0 0;padding:22px 0 0;list-style:none;border-top:1px solid var(--zb)}\n.zus .zfakten li{display:flex;gap:12px;align-items:flex-start;line-height:1.45}\n.zus .zfakten .zi{width:22px;height:22px;color:var(--zl);margin-top:2px}\n@media(max-width:1080px){.zus .znetz{grid-template-columns:1fr 1fr;gap:18px}.zus .zlinien{display:none}\n .zus .zk.zh{grid-column:1/3;grid-row:auto}.zus .p1,.zus .p2,.zus .p3,.zus .p4{grid-column:auto;grid-row:auto}\n .zus .zfakten{grid-template-columns:1fr 1fr}}\n@media(max-width:640px){.zus .znetz{grid-template-columns:1fr;gap:0;padding-left:22px}\n .zus .znetz::before{content:"";position:absolute;left:6px;top:28px;bottom:28px;width:2px;background:var(--zb)}\n .zus .zk.zh{grid-column:auto;margin-left:-22px;margin-bottom:18px}\n .zus .zk:not(.zh){margin-bottom:14px}\n .zus .zk:not(.zh)::before{content:"";position:absolute;left:-21px;top:30px;width:12px;height:12px;border-radius:50%;background:var(--za);box-shadow:0 0 0 4px var(--bg,#0b1620)}\n .zus .zfakten{grid-template-columns:1fr}}\n</style>\n<div class="zus" id="zusammen"><h2>So gehört alles zusammen</h2><p class="zlead">Panoptes ist ein Projekt. In der Mitte steht die App im Auto. Alles andere ist freiwillig: Du verbindest es nur, wenn du willst, und kannst es jederzeit wieder trennen.</p><div class="znetz"><svg class="zlinien" viewBox="0 0 100 100" preserveAspectRatio="none" aria-hidden="true"><line x1="38" y1="50" x2="31" y2="25"/><line x1="62" y1="50" x2="69" y2="25"/><line x1="38" y1="50" x2="31" y2="75"/><line x1="62" y1="50" x2="69" y2="75"/></svg><div class="zk zh"><svg class="zi zgross" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M19 17h2c.6 0 1-.4 1-1v-3c0-.9-.7-1.7-1.5-1.9C18.7 10.6 16 10 16 10s-1.3-1.4-2.2-2.3c-.5-.4-1.1-.7-1.8-.7H5c-.6 0-1.1.4-1.4.9l-1.4 2.9A3.7 3.7 0 0 0 2 12v4c0 .6.4 1 1 1h2"/><circle cx="7" cy="17" r="2"/><path d="M9 17h6"/><circle cx="17" cy="17" r="2"/></svg><h3>Panoptes im Auto</h3><span class="zart">brauchst du</span><p style="margin-top:10px">Die App läuft am Bildschirm in deinem BYD. Sie ist die Mitte: Wächter mit Kamera, Fahrten, Laden, Karte, Tacho. Alle anderen Teile holen ihre Daten von hier.</p><a class="zmehr" href="/panoptes/">Panoptes ansehen →</a></div><div class="zk p1"><div class="zkopf"><svg class="zi" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect width="14" height="20" x="5" y="2" rx="2"/><path d="M12 18h.01"/></svg><div><h3>Handy-App</h3><span class="zart">freiwillig</span></div></div><p>Dein Auto am Handy sehen und steuern, zum Beispiel vorheizen. Du verbindest das Handy einmal mit einem QR-Code am Auto. Android als App, iPhone als Web-App.</p><a class="zmehr" href="/app/">Zur Handy-App →</a></div><div class="zk p2"><div class="zkopf"><svg class="zi" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect width="20" height="14" x="2" y="3" rx="2"/><path d="M8 21h8"/><path d="M12 17v4"/></svg><div><h3>EV-Cockpit</h3><span class="zart">freiwillig</span></div></div><p>Alles am PC, groß und übersichtlich. Du erlaubst das Cockpit einmal mit einer Prüfzahl am Auto. Es geht auch ohne Panoptes, dann mit Daten aus der BYD-Cloud oder Home Assistant.</p><a class="zmehr" href="/ev-cockpit/">Zum EV-Cockpit →</a></div><div class="zk p3"><div class="zkopf"><svg class="zi" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="6" cy="19" r="3"/><path d="M9 19h8.5a3.5 3.5 0 0 0 0-7h-11a3.5 3.5 0 0 1 0-7H15"/><circle cx="18" cy="5" r="3"/></svg><div><h3>Routenplaner</h3><span class="zart">freiwillig</span></div></div><p><b>Unser Routenplaner, die Alternative zu ABRP</b> (A Better Route Planner): Er plant deine Fahrt mit Ladestopps nach Akku und Ladekurve. Wetter, Wind und Berge rechnet er in den Verbrauch ein. Er zeigt die Kosten je Ladekarte, Land und Uhrzeit, und in Österreich, der Schweiz und Deutschland, ob eine Säule gerade frei ist. Für Europa und Asien, im Browser, ohne Anmeldung.</p><p>Die Ankunftszeit rechnet bekannte Staus mit ein. Verbindest du ihn einmal mit deinem Auto, kommt das Ziel mit Ladestopps direkt ins Auto, und Panoptes sagt dir unterwegs mit „Reicht es noch?“, ob der Akku reicht.</p><a class="zmehr" href="/ev/">Zum Routenplaner →</a></div><div class="zk p4"><div class="zkopf"><svg class="zi" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect width="7" height="7" x="3" y="3" rx="1"/><rect width="7" height="7" x="14" y="3" rx="1"/><rect width="7" height="7" x="14" y="14" rx="1"/><rect width="7" height="7" x="3" y="14" rx="1"/></svg><div><h3>Panoptes Launcher</h3><span class="zart">freiwillig</span></div></div><p>Ein eigener Startbildschirm für den Bildschirm im Auto, mit Klima und Apps unten in der Leiste. Du installierst ihn per Knopf in Panoptes. Er braucht Panoptes.</p><a class="zmehr" href="/panoptes/#tacho-launcher">Bilder ansehen →</a></div></div><ul class="zfakten"><li><svg class="zi" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71"/><path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71"/></svg><span><b>Ein Projekt.</b> Alle Teile sind von uns, kostenlos und passen zusammen.</span></li><li><svg class="zi" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect width="20" height="12" x="2" y="6" rx="6"/><circle cx="16" cy="12" r="2"/></svg><span><b>Du entscheidest.</b> Jede Verbindung schaltest du selbst ein, mit Rückfrage am Auto. Trennen geht jederzeit.</span></li><li><svg class="zi" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect width="18" height="11" x="3" y="11" rx="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/></svg><span><b>Unterwegs.</b> Handy und PC erreichen das Auto auch übers Internet, verschlüsselt, über die Verbindung, die du einrichtest.</span></li><li><svg class="zi" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="12" cy="12" r="10"/><path d="M8 12h8"/><path d="M12 8v8"/></svg><span><b>Noch dabei, wenn du willst:</b> Meldungen über deinen eigenen Telegram-Bot, Home Assistant, deine Wallbox.</span></li></ul></div>',
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
            ("Kartenquelle (Community-Server byd.serveone.at oder OpenStreetMap Deutschland)", "Deine IP-Adresse und der Kartenausschnitt, also ungefähr, wo dein Auto steht. Beim Community-Server zusätzlich die Abfrage freier Ladeplätze für den Ausschnitt.", "erst, wenn du unter Einstellungen → Alle Einstellungen → Kartenquelle eine Quelle wählst. Am Bildschirm im Auto gilt die Wahl fürs ganze Auto; Handy und PC fragen getrennt."),
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
        "stand_lead": "Ehrlich, was wo läuft, Stand 0.1.38.8. „Fertig“ heißt: gebaut und getestet. „Nur bestimmte Autos“ heißt: hängt vom Modell ab. „Beta“ heißt: läuft, hat aber Einschränkungen.",
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
            ("Telegram mit Menü und großen Knöpfen", "Fertig"),
            ("Updates per Knopf aus Telegram, vom Handy oder Cockpit (nur mit Erlaubnis, nur im Stand)", "Fertig"),
            ("Panoptes richtet sich nach einem Update selbst wieder ein und meldet, wenn alles läuft", "Fertig"),
            ("Neue Leiste mit sieben Bereichen, Seite „Display“", "Fertig"),
            ("Wächter und Fahrten mit großem Schalter, Regeln als „Wenn … / Dann …“", "Fertig"),
            ("Launcher am Handy oder im Cockpit einrichten (nur mit deiner Erlaubnis)", "Fertig"),
            ("Bildschirm: eigenes Bild, Sperre mit Zahlencode, Apps aus und an, USB-Stick", "Fertig"),
            ("Tacho: „Was zeigt der Tacho?“, Anzeigen, „auch beim Fahren“ je App, „Tacho wieder normal“", "Nur bestimmte Autos: nicht am Dolphin Surf und Seagull, auf DiLink 5 vorerst gesperrt"),
            ("Panoptes Launcher (eigene App)", "Fertig"),
            ("Launcher: Sitzheizung, Sitzlüftung, Lenkradheizung, Umluft, Entfrosten", "Nur bestimmte Autos: nur, was dein Auto meldet"),
            ("Updates: Nur melden, Kleine Updates von selbst (Standard) oder Alles automatisch", "Fertig"),
            ("Akku: Gesundheitswert von BYD neben der eigenen Schätzung", "Fertig"),
            ("Launcher als Startbildschirm (Schalter)", "Beta: ab Werk aus"),
            ("Home Assistant meldet smarte Geräte, Panoptes zeigt sie an", "Beta: ab Werk aus, nur Anzeige"),
            ("Home Assistant schaltet freigegebene Tore und Haustüren", "Beta: ab Werk aus, je Gerät einzeln erlauben"),
            ("Eigene Schalter für Hupe, Licht, Warnblinker, Aufsperren; Notaus /aktionen in Telegram", "Fertig; ab Werk aus, einschalten nur am Auto"),
            ("Kleine Updates von selbst, wenn das Auto 10 Minuten steht", "Fertig"),
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
        "neu_version": "0.1.38.8", "neu_titel": "Neu in 0.1.38.8",
        "neu": ["<b>Kleine Updates von selbst:</b> Ändert sich nur die letzte Zahl, kommt das Update von selbst, wenn das Auto 10 Minuten steht. „Nur melden“ wird dafür einmal umgestellt, mit Nachricht. Ändern: Einstellungen → Alle Einstellungen → App-Updates.", "<b>Eigene Schalter</b> für Hupe, Licht, Warnblinker und Aufsperren (ab Werk aus), einschalten nur am Auto. „<code>/aktionen aus</code>“ in Telegram (oder der Knopf dort) schaltet diese Freigaben (Hupe, Licht, Warnblinker, Aufsperren) sofort ab.", "<b>Erstes Handy:</b> Es kann alles einstellen und weitere Geräte koppeln, aber nichts am Auto auslösen. Rechte fürs Auto vergibst du nur am Display.", "<b>Home Assistant</b> kann freigegebene Tore und Haustüren schalten, auf Wunsch das Tor beim Heimkommen. Alles bleibt aus, bis du es einzeln erlaubst.", "<b>Wächter:</b> bei neuer Einrichtung an; wer ihn nie eingerichtet hat, wird einmal gefragt. Weniger Fehlalarme durch vorbeifahrende Autos.", "<b>Schneller:</b> Panoptes startet schneller. Der Telegram-Bot sagt, wenn Panoptes im Auto noch startet, und ist auf Wunsch auch bei abgestelltem Auto erreichbar.", "<b>Sicherer:</b> Gespeicherte Zugangsdaten sind zusätzlich verschlüsselt. Sicherungen enthalten den Geräteschlüssel nur, wenn du das ausdrücklich wählst.", "<b>Launcher 0.1.38.8:</b> ruht bei ausgeschaltetem Display und zeigt die Akku-Gesundheit laut Auto und geschätzt nebeneinander.", "<b>Aus 0.1.38.7:</b> Launcher als Startbildschirm (Schalter, ab Werk aus), Fernklima ehrlich, Spotify neben dem Launcher."],
        # Abschnitt „Tacho und Launcher“ ab 0.1.37 (Koordination 03.11.2026), Bilder: Vorschau/Emulator, Musterdaten
        "tl": {"h": "Tacho und Launcher <span class=\"bald\">ab 0.1.37</span>",
               "lead": "Seit 0.1.37, in 0.1.38 auf der Seite Apps &amp; Display → Display. Die Bilder sind Vorschaubilder und Emulator-Aufnahmen mit Musterdaten, nicht aus einem Auto. <a href=\"launcher.html\">Alles zum Panoptes Launcher</a>",
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
            "bekommen": "<b>Hilf uns:</b> Unter Apps &amp; Display → „Was kann mein Tacho?“ siehst du, was dein Tacho kann. Du hast ein anderes Modell? Schreib uns über die <a href=\"/#wunsch\">Wunsch-Box</a> dein Modell und ob es geht (ja oder nein).",
            "h_gut": "Gut zu wissen:",
            "gut": ["Ab Werk bleiben beim Fahren am Tacho nur Navi-Apps aus einer festen Liste (z. B. Google Maps, Waze, OsmAnd, ABRP). Andere Apps laufen nur im Stand.",
                    "Du kannst je App „auch beim Fahren“ einschalten, nach einem einmaligen Hinweis. Dann bist du selbst verantwortlich. <b>Videos beim Fahren sind in vielen Ländern verboten.</b>",
                    "Beim ersten Mal bestätigst du einen Hinweis: Tempo und Warnleuchten müssen sichtbar bleiben.",
                    "Beim <b>Dolphin Surf</b> und <b>Seagull</b> geht es nicht. Auf Autos mit <b>DiLink 5</b> ist es vorerst gesperrt."],
        },
        "dl_text": "Panoptes {V} ist eine <b>Beta-Version</b>. Panoptes läuft im Alltag in einem Testauto (BYD Dolphin Surf, DiLink 3), neue Versionen kommen dort nach und nach dazu. Auf anderen Modellen kann manches fehlen oder anders sein. Die Installation ist nichts für jeden: Du brauchst etwas Geduld, einmalig einen PC oder Laptop und musst am Auto eine Entwickler-Freigabe einschalten. Danach kommen Updates von selbst in der App. Nutzung auf eigenes Risiko, siehe <a href=\"hinweise.html\">Hinweise</a>.",
        "dl_knopf": "⬇️ Panoptes {V} herunterladen (APK, {MB} MB)",
        "hero_dl": "⬇️ Panoptes {V} herunterladen", "hero_anl": "Anleitung", "kopf_dl": "⬇️ Download",
        "dl_release": "Release auf GitHub", "dl_quelle": "Quellcode",
        "dl_pruef": "Prüfsumme (SHA-256)", "dl_zert": "Signaturzertifikat (SHA-256)",
        "dl_update": "Ab 0.1.19.1 kommen Updates über Einstellungen → Alle Einstellungen → App-Updates. Wer 0.1.17 oder 0.1.18 hat, installiert die aktuelle Version einmal von Hand (<a href=\"#schritte\">Anleitung</a>); die Daten bleiben erhalten.",
        "h_anl": "Schritt für Schritt",
        "anl": [
            ("Vorher lesen.", "Panoptes ist für dein eigenes Auto gedacht, privat und auf eigenes Risiko. Lies die <a href=\"hinweise.html\">Hinweise</a>. Für die Installation schaltest du am Auto Entwickler-Funktionen ein. Ob das für deine Garantie eine Rolle spielt, klärst du im Zweifel mit deinem Händler."),
            ("Herunterladen.", "Lade die Datei <code>{APK}</code> mit dem Knopf oben auf deinen PC oder Laptop. <b>Freiwillig, für Geübte:</b> Vergleiche vorher die Prüfsumme. Unter Windows tippst du in der Eingabeaufforderung <code>certutil -hashfile {APK} SHA256</code>, am Mac oder unter Linux <code>shasum -a 256 {APK}</code>. Die Ausgabe muss genau die Prüfsumme oben ergeben. Weicht sie ab, installiere die Datei <b>nicht</b>."),
            ("Entwickler-Freigabe (ADB) am Auto einschalten.", "Panoptes startet seine Hintergrunddienste, zum Beispiel für die Kameras, über die ADB-Schnittstelle des Autos. Diese Verbindung bleibt im Auto (127.0.0.1). Ab Werk ist die Schnittstelle aus. Eingeschaltet wird sie im BYD-Entwicklermenü, mit den Schaltern für USB-Debugging bzw. kabelloses ADB. Wie du in dieses Menü kommst, hängt stark von Modell und Software-Stand ab; bei neuerer BYD-Software ist es mit einem Code gesperrt. Geprüft haben wir diesen Schritt bisher nur am Dolphin Surf (DiLink 3). Ohne diese Freigabe läuft Panoptes nicht vollständig."),
            ("App aufs Auto bringen.", "<b>Geprüfter Weg, einmalig mit PC oder Laptop:</b> Installiere die Android-Plattform-Tools von Google (darin ist <code>adb</code>). PC und Auto müssen im selben Netz sein, zum Beispiel im WLAN-Hotspot deines Handys. Tippe dann <code>adb connect &lt;Adresse-des-Autos&gt;:5555</code> und <code>adb install -r {APK}</code>. Die Adresse des Autos siehst du in den WLAN-Einstellungen am Auto oder in der Geräteliste deines Hotspots. Am Ende muss <code>Success</code> erscheinen. Danach kommen Updates von selbst in der App. <b>Statt PC mit einem Android-Handy (von uns noch nicht geprüft):</b> Das geht auch mit einer adb-App am Handy, im selben WLAN oder Hotspot wie das Auto, siehe <a href=\"/guide#handy-adb\">Anleitung</a>. Mit dem iPhone geht das nicht. <b>USB-Stick oder BYD-Dateimanager: wird gerade geprüft.</b> Der Dateimanager gibt die Datei nach einer Warnung an die Installation weiter; ob sie danach durchläuft, ist noch nicht belegt. Fragt Android nach „Installation aus unbekannten Quellen“, erlaubst du das nur für diese Installation."),
            ("Erster Start mit der Einrichtungshilfe.", "Öffne Panoptes am Bildschirm im Auto. Kurze Schritte führen dich durch das Nötigste, zum Beispiel Sprache, Hinweise bestätigen, <b>Autostart</b>, Anzeige über anderen Apps, Berechtigungen und <b>USB-Freigabe</b>. Alles Weitere (Wächter, Kartenquelle, Daten teilen, Blitzer, Telegram, Routenplaner, EV-Cockpit, Fernzugang) findest du danach unter „Noch einrichten“. Fast nichts ist vorausgewählt. Was Daten nach außen schickt, bleibt aus, bis du es selbst einschaltest."),
            ("Autostart freigeben.", "Damit Panoptes nach dem Einsteigen von selbst läuft, muss es in der BYD-App-Verwaltung erlaubt sein. Die Einrichtungshilfe öffnet die richtige Seite; dort nimmst du bei Panoptes den Haken bei der Autostart-Sperre weg. <b>BYD setzt diesen Schalter nach jeder Installation und jedem Update zurück.</b> Panoptes gibt ihn nach einem Update selbst wieder frei und sagt Bescheid, falls das nicht klappt. Auf DiLink 5 gibt es diese Verwaltung nicht, der Schritt entfällt."),
            ("USB-Freigabe bestätigen.", "Android fragt einmal „USB-Debugging zulassen?“. Setze den Haken bei <b>„Immer von diesem Computer zulassen“</b> und tippe auf <b>Zulassen</b>. Der „Computer“ ist dabei Panoptes selbst im Auto. Ohne Haken fragt Android nach jedem Neustart wieder."),
            ("Am Handy oder PC öffnen (freiwillig).", "Mit eingerichtetem Fernzugang (Tailscale) öffnest du die Adresse deines Autos im Browser. Zum Anmelden brauchst du den <b>Zugangscode</b>, den du in der App am Auto unter <b>Start → Zugangscode</b> findest. Weitere Geräte, etwa das EV-Cockpit, erlaubst du unter <b>Einstellungen → Alle Einstellungen → Gerät koppeln</b>."),
        ],
        "h_stolper": "Wenn etwas hakt",
        "stolper": [
            "<b>Panoptes startet nach einem Update nicht von selbst:</b> Autostart wieder freigeben (Schritt 6). BYD setzt ihn nach jeder Installation zurück. Panoptes macht das nach einem Update selbst. Kommt eine Meldung, am Display „Autostart wieder einschalten“ antippen.",
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
        "hero_alt_pc": "Panoptes 0.1.38 on the car screen: home page with charge level, range and quick buttons",
        "hero_alt_handy": "Panoptes 0.1.38 on a phone: home page",
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
            ("Camping page on the car screen: switch on, battery, heating time; the \u201cdry run\u201d notice at the top.", [("camping38", "display", "Panoptes camping page: camping is off, Switch on button, dry run notice, values not yet available")]),
            ("Settings: warmth, heating route, battery limit, 12 V warning.", [("camping-einstellungen", "display", "Camping settings: warmth, heating route dry run, pre-heating, battery limit 20 percent, 12-volt warning")]),
            ("Night screen: almost black, big clock, feedback \u201ctoo cold / fine / too warm\u201d. Next to it the camping page on a phone.", [("nacht", "display", "Night screen: black background, big clock and date, buttons too cold, fine, too warm"), ("camping38", "handy", "Camping page on a phone at 390 pixels wide")]),
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
                ("Telegram bot with a menu and big buttons; commands like /status, /wo, /camping still work", ""),
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
                ("Updates in the app, by button from Telegram, phone or Cockpit (only with permission); without Wi-Fi Panoptes asks first; afterwards it sets itself up again", ""),
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
            ("🧩", "Setup assistant", "On first start, three short screens guide you through the essentials, with all permissions on one screen. Everything else is under \u201cNoch einrichten\u201d (still to set up) later. Almost nothing is preselected (only \u201cremember habits\u201d is set to yes, and that stays in the car); anything that sends data out stays off until you turn it on. Whatever your car cannot do is skipped with an explanation."),
            ("🛡️", "Guard with AI detection", "While your car is parked, the cameras watch its surroundings. You decide when it records: only on impact, with AI detection everywhere, or only at your own private places such as your garage or driveway. Without a choice it only records on impact. To protect the 12 V battery it goes to sleep; the threshold follows the battery type (lead-acid, AGM or LFP)."),
            ("📹", "Dashcam <span class=\"bald\">from 0.1.27</span>", "On hard braking or a bump Panoptes saves a short clip from all cameras by itself, about 20 seconds before and after. No continuous recording. The clips stay in the car or on the USB stick and are never sent anywhere by themselves. You can watch and save clips on your phone with the <a href=\"/app/en/\">phone app</a> (beta 4). Panoptes then asks “Keep?”, otherwise the clip is deleted after 72 hours. From 0.1.36 every clip remembers what triggered it (without location). In Switzerland the dashcam is off by default. Whether recording while driving is allowed where you live differs by country, see the <a href=\"hinweise.html\">notes</a>."),
            ("📒", "Trips and charging", "Trips, consumption and charging sessions are recorded in the car. Panoptes shows the cost per session, per month and as average cost per 100 km, from 0.1.35 including the estimated charging loss (sign \u201c~\u201d). If a price is missing it says \u201cprice missing\u201d instead of inventing a number; free charging can be entered explicitly."),
            ("🔌", "\u201cWhere did you charge?\u201d", "After charging, Panoptes asks for the station and price while parked, never while driving. With \u201cremember place\u201d it knows the price next time. With \u201cLaut S\u00e4ule\u201d (as shown by the charger) you enter the charger's kWh and cost; your price is then used for \u201cCheapest nearby\u201d (AC and DC separately). The question can be switched off."),
            ("💳", "Your charge cards in the car", "Charge cards and networks, minimum power, plug and arrival charge level are set in the car. The route planner uses them; they are only stored in the car."),
            ("🏠", "Wallbox <span class=\"bald\">beta</span>", "Set up your wallbox via evcc, Home Assistant or Tuya, and from version 0.1.12 also directly (e.g. go-e, KEBA, openWB, Easee, Zaptec): see the status, set mode, charge limit and current. Control only while the car is parked, with confirmation and enabled per charge point. So far only checked with demo and test devices."),
            ("📍", "Your places", "One list for everything: home, garage, work or the charging spot with its own price. For each place you decide whether it is private (guard), a charging price applies or it is a destination in the navigation. Places never leave the car."),
            ("🌍", "Remote access", "Reach your car from anywhere via Tailscale. Setup uses a QR code on the car screen and your own Tailscale account. For advanced users, 0.1.14 adds an independent emergency access, off by default."),
            ("💬", "Telegram notifications", "Your own bot reports guard events, charging, a weak starter battery, tyre pressure and updates. Each category can be switched on its own, with quiet hours for the night. From 0.1.38.2: write anything to the bot and you get a menu with big buttons. Pictures and videos only if you turn that on. <a href=\"telegram.html\">How to connect Telegram</a>"),
            ("🗺️", "Map with chargers", "You choose where the map comes from: the community server (with terrain and free charging spots where operators provide data), OpenStreetMap, or none. Until you choose, the map stays empty. Speed cameras are shown in Austria only, off by default and with a legal notice."),
            ("🔋", "\u201cWill it make it?\u201d", "With a route from the route planner, including waypoints, Panoptes tells you on the road whether the battery will last to the next stop and suggests a charging stop if needed."),
            ("📊", "Monthly report", "Distance, consumption, charging and costs, standby loss and guard events of a month at a glance, also for printing. Calculated in the car."),
            ("🔁", "Switching from OverDrive", "If you used the OverDrive app before, you can take over trips, charging sessions and settings, with a preview and without duplicates. Panoptes never takes over consents or risky switches; you set those yourself."),
            ("🧭", "Route planner link", "Connect Panoptes to your account on <a href=\"/ev/\">byd.serveone.at/ev/</a>: show a code in the car, confirm on your phone, done. Disconnect at any time."),
            ("🖥️", "EV Cockpit on your PC", "The <a href=\"/ev-cockpit/\">EV Cockpit</a> shows Panoptes data on your PC, including charging sessions and costs, and can change its settings. You confirm the pairing with one tap and a four-digit check number. From Cockpit 1.23 also choose the cluster display, set up the launcher and install updates, only with your permission. From 1.24 you can also plan a route in the Cockpit and send it to the car."),
            ("⬆️", "Updates in the app", "If you like, Panoptes looks for new versions itself. Under Settings → All settings → App updates you choose: “Only notify”, “Small updates on their own, report big ones” (default) or “Everything automatically”. Small updates (only the last number changes) arrive quietly; Panoptes announces big ones first with a summary. If you had “Only notify”, you were switched over once and told so. It never installs while driving: if you start an update yourself, it runs right away when the car is in P, even with the ignition on; on its own only once the car has been off for at least 10 minutes; if something goes wrong, the previous version comes back by itself within 30 minutes. From 0.1.38.2 also by button from Telegram, your phone or the Cockpit, only with your permission. After an update Panoptes sets itself up again and reports when everything runs. From 0.1.13 Panoptes no longer changes permanent Android settings by itself (such as \u201cscreen always on\u201d); values set earlier can be reset. What you change yourself (own picture, turning apps off) stays until you change it back. From 0.1.36 the logs are kept through updates."),
            ("🏕️", "Camping mode <span class=\"bald\">beta</span>", "Guard \u201coccupied\u201d, night screen, battery protection with time left. Switch on with a tap, on your phone or with /camping in Telegram. You choose the heating type on the camping page; by default only a dry run. <a href=\"#camping\">More</a>"),
            ("🖼️", "Screen <span class=\"bald\">from 0.1.37</span>", "Your own picture for the home screen. Lock the screen with a number code (only in P). Turn apps off and on. Read USB sticks."),
            ("🚀", "Panoptes Launcher <span class=\"bald\">from 0.1.37</span>", "Separate app, optional: home screen with climate in the dock, Android Auto and CarPlay (if your car has them) and update notice. Install by button in Panoptes, never by itself. From 0.1.38 you set it up comfortably on your phone or in the Cockpit, only if you allow it when pairing. The house on the left always takes you back to the BYD home screen. <a href=\"#tacho-launcher\">Pictures</a>"),
            ("🐾", "Pet mode <span class=\"bald\">from 0.1.36</span>", "Keeps the climate running for your pet and reports problems to your phone and Telegram. Only an aid, no guarantee, you stay responsible."),
            ("🤖", "AI assistant", "Only if you set it up yourself. From 0.1.36 it may only control climate, seat heating and sunshade and show values. Never horn, lights, indicators, windows, boot or the guard."),
            ("🧰", "Small helpers <span class=\"bald\">from 0.1.36</span>", "Screen cleaning (locked for 30 seconds, only in P). Take over a destination from a Google Maps or Waze link. Files between phone and car (own permission, off by default, no apps). Panoptes checks its permissions daily and repairs what it can."),
            ("🌐", "Five languages", "German, English, French, Italian and Dutch."),
        ],
        "h_bilder": "What Panoptes looks like",
        "bilder_lead": "Panoptes 0.1.38 on the car screen and on a phone, taken in the emulator with sample data, not from a car. Pictures with a yellow \u201csample data\u201d band come from a demo profile: no real trips, places or commands, the map is a simplified sample map. Other pages without data show \u201cnot available\u201d or \u201c--\u201d. Click a picture to enlarge it.",
        "bilder": [
            ("Home: charge level, range and quick buttons.", [("startd38", "display", "Home page with sample data: 86 percent, 236 km, quick buttons, location map and charging costs"), ("startd38", "handy", "Home page on a phone with sample data")]),
            ("Trip log: every trip with distance, duration, consumption and cost.", [("fahrt38", "display", "One trip with sample data: 22 km, 25 minutes, 14.56 kWh per 100 km"), ("fahrt38", "handy", "Trip on a phone with sample data")]),
            ("Map and navigation, here with a simplified sample map.", [("karte38", "display", "Navigation with a simplified sample map, search field and favourites"), ("karte38", "handy", "Navigation on a phone with a sample map")]),
            ("Charging: sessions, energy, costs and wallbox.", [("laden38", "display", "Charging with sample data: wallbox, 6 sessions, 149 kWh"), ("laden38", "handy", "Charging on a phone with sample data")]),
            ("Cameras & guard: one big switch, below it today's recordings.", [("waechter38", "display", "Guard on the car screen: guard is off, big button switch guard on"), ("waechter38", "handy", "Guard on a phone with a big switch")]),
            ("Apps & display → Display: “What does the cluster show?” Tap a picture.", [("display38", "display", "Page Display: cluster, background and lock, launcher; choice what the cluster shows"), ("display38", "handy", "Page Display on a phone")]),
            ("Monthly report: distance, consumption, charging, standby loss and guard, also for printing.", [("berichtd38", "display", "Monthly report October 2026 with sample data: 1010 km, 14.6 kWh per 100 km, 149 kWh charged"), ("berichtd38", "handy", "Monthly report on a phone with sample data")]),
            ("Rules: build your own “When … / Then …”.", [("regeln38", "display", "When-then rules: no rule yet, button new rule"), ("regeln38", "handy", "Rules on a phone")]),
            ("Telegram: set up in three short steps.", [("telegram38", "display", "Set up Telegram notifications in three steps"), ("telegram38", "handy", "Set up Telegram on a phone")]),
            ("Pair a device: phone or EV Cockpit, only with your confirmation.", [("koppeln38", "display", "Pair a device: button pair new device, no device paired yet"), ("koppeln38", "handy", "Pair a device on a phone")]),
            ("Settings: “What would you like to set?”, with search.", [("system38", "display", "All settings: connections, car and display, app and data, advanced"), ("system38", "handy", "All settings on a phone")]),
            ("Setup: optional steps under “Noch einrichten” (still to set up).", [("einrichtung38", "display", "Setup: list of optional steps still to set up"), ("einrichtung38", "handy", "Still to set up on a phone")]),
            ("Controls on a phone: tiles for security, boot, climate and seats.", [("steuerung38", "handy", "Controls on a phone with tiles security, boot, climate, seats")]),
            ("Apps & display: two apps side by side on the screen.", [("apps38", "display", "Apps side by side with sample data: photos and audiobooks"), ("apps38", "handy", "Apps side by side on a phone")]),
        ],
        "handy": "on a phone", "pc": "on a PC",
        "zus_block": '<style>\n/* So gehört alles zusammen – Fassung 2 (04.11.2026). Farben aus dem Seiten-Theme. */\n.zus{--za:var(--accent-2,#c6f24e);--zl:var(--accent,#4fd1e8);--zp:var(--panel,rgba(127,127,127,.08));--zb:var(--line,rgba(127,127,127,.3));--zt:var(--text,currentColor);--zu:var(--muted,#8aa);position:relative}\n.zus h2{font-size:clamp(1.7rem,3.2vw,2.4rem);letter-spacing:-.02em;margin:0 0 .35em}\n.zus .zlead{max-width:62ch;color:var(--zu);font-size:1.08rem;margin:0 0 28px}\n.zus .zi{width:26px;height:26px;flex:none}\n.zus .znetz{position:relative;display:grid;grid-template-columns:1fr minmax(220px,.8fr) 1fr;grid-template-rows:auto auto;gap:28px 64px;align-items:stretch}\n.zus .zlinien{position:absolute;inset:0;width:100%;height:100%;pointer-events:none;z-index:0}\n.zus .zlinien line{stroke:var(--zl);stroke-opacity:.55;stroke-width:2;vector-effect:non-scaling-stroke}\n.zus .zlinien circle{fill:var(--za)}\n.zus .zk{position:relative;z-index:1;background:var(--zp);border:1px solid var(--zb);border-radius:16px;padding:20px 20px 18px;display:flex;flex-direction:column}\n.zus .zk .zkopf{display:flex;align-items:center;gap:12px;margin:0 0 10px}\n.zus .zk .zkopf .zi{color:var(--zl)}\n.zus .zk h3{margin:0;font-size:1.12rem;line-height:1.25}\n.zus .zk .zart{display:block;font-size:.74rem;letter-spacing:.08em;text-transform:uppercase;color:var(--zu);margin-top:2px}\n.zus .zk p{margin:0 0 10px;line-height:1.5}\n.zus .zk .zmehr{margin-top:auto;font-weight:600}\n.zus .zk.zh{grid-column:2;grid-row:1/3;align-self:center;border:2px solid var(--za);padding:26px 22px;text-align:left}\n.zus .zk.zh .zgross{width:56px;height:56px;color:var(--za);margin:0 0 12px}\n.zus .zk.zh h3{font-size:1.5rem}\n.zus .zk.zh .zart{color:var(--za)}\n.zus .p1{grid-column:1;grid-row:1}.zus .p2{grid-column:3;grid-row:1}.zus .p3{grid-column:1;grid-row:2}.zus .p4{grid-column:3;grid-row:2}\n.zus .zfakten{display:grid;grid-template-columns:repeat(4,1fr);gap:22px;margin:36px 0 0;padding:22px 0 0;list-style:none;border-top:1px solid var(--zb)}\n.zus .zfakten li{display:flex;gap:12px;align-items:flex-start;line-height:1.45}\n.zus .zfakten .zi{width:22px;height:22px;color:var(--zl);margin-top:2px}\n@media(max-width:1080px){.zus .znetz{grid-template-columns:1fr 1fr;gap:18px}.zus .zlinien{display:none}\n .zus .zk.zh{grid-column:1/3;grid-row:auto}.zus .p1,.zus .p2,.zus .p3,.zus .p4{grid-column:auto;grid-row:auto}\n .zus .zfakten{grid-template-columns:1fr 1fr}}\n@media(max-width:640px){.zus .znetz{grid-template-columns:1fr;gap:0;padding-left:22px}\n .zus .znetz::before{content:"";position:absolute;left:6px;top:28px;bottom:28px;width:2px;background:var(--zb)}\n .zus .zk.zh{grid-column:auto;margin-left:-22px;margin-bottom:18px}\n .zus .zk:not(.zh){margin-bottom:14px}\n .zus .zk:not(.zh)::before{content:"";position:absolute;left:-21px;top:30px;width:12px;height:12px;border-radius:50%;background:var(--za);box-shadow:0 0 0 4px var(--bg,#0b1620)}\n .zus .zfakten{grid-template-columns:1fr}}\n</style>\n<div class="zus" id="zusammen"><h2>How it all belongs together</h2><p class="zlead">Panoptes is one project. In the middle is the app in the car. Everything else is optional: you only connect it if you want to, and you can disconnect it at any time.</p><div class="znetz"><svg class="zlinien" viewBox="0 0 100 100" preserveAspectRatio="none" aria-hidden="true"><line x1="38" y1="50" x2="31" y2="25"/><line x1="62" y1="50" x2="69" y2="25"/><line x1="38" y1="50" x2="31" y2="75"/><line x1="62" y1="50" x2="69" y2="75"/></svg><div class="zk zh"><svg class="zi zgross" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M19 17h2c.6 0 1-.4 1-1v-3c0-.9-.7-1.7-1.5-1.9C18.7 10.6 16 10 16 10s-1.3-1.4-2.2-2.3c-.5-.4-1.1-.7-1.8-.7H5c-.6 0-1.1.4-1.4.9l-1.4 2.9A3.7 3.7 0 0 0 2 12v4c0 .6.4 1 1 1h2"/><circle cx="7" cy="17" r="2"/><path d="M9 17h6"/><circle cx="17" cy="17" r="2"/></svg><h3>Panoptes in the car</h3><span class="zart">you need it</span><p style="margin-top:10px">The app runs on the screen in your BYD. It is the centre: guard with camera, trips, charging, map, cluster. All other parts get their data from here.</p><a class="zmehr" href="/panoptes/en/">See Panoptes →</a></div><div class="zk p1"><div class="zkopf"><svg class="zi" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect width="14" height="20" x="5" y="2" rx="2"/><path d="M12 18h.01"/></svg><div><h3>Phone app</h3><span class="zart">optional</span></div></div><p>See and control your car on your phone, for example preheat it. You connect the phone once with a QR code in the car. Android as an app, iPhone as a web app.</p><a class="zmehr" href="/app/en/">To the phone app →</a></div><div class="zk p2"><div class="zkopf"><svg class="zi" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect width="20" height="14" x="2" y="3" rx="2"/><path d="M8 21h8"/><path d="M12 17v4"/></svg><div><h3>EV Cockpit</h3><span class="zart">optional</span></div></div><p>Everything on your PC, big and clear. You allow the Cockpit once with a check number in the car. It also works without Panoptes, then with data from the BYD cloud or Home Assistant.</p><a class="zmehr" href="/ev-cockpit/en/">To the EV Cockpit →</a></div><div class="zk p3"><div class="zkopf"><svg class="zi" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="6" cy="19" r="3"/><path d="M9 19h8.5a3.5 3.5 0 0 0 0-7h-11a3.5 3.5 0 0 1 0-7H15"/><circle cx="18" cy="5" r="3"/></svg><div><h3>Route planner</h3><span class="zart">optional</span></div></div><p><b>Our route planner, the alternative to ABRP</b> (A Better Route Planner): it plans your trip with charging stops based on battery and charging curve. It includes weather, wind and hills in the consumption. It shows the cost per charge card, country and time of day, and in Austria, Switzerland and Germany whether a charger is free right now. For Europe and Asia, in the browser, without signing up.</p><p>The arrival time includes known traffic jams. Once you connect it to your car, the destination with charging stops goes straight into the car, and on the road Panoptes tells you with “Reicht es noch?” (will it still be enough?) whether the battery will last.</p><a class="zmehr" href="/ev/">To the route planner →</a></div><div class="zk p4"><div class="zkopf"><svg class="zi" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect width="7" height="7" x="3" y="3" rx="1"/><rect width="7" height="7" x="14" y="3" rx="1"/><rect width="7" height="7" x="14" y="14" rx="1"/><rect width="7" height="7" x="3" y="14" rx="1"/></svg><div><h3>Panoptes Launcher</h3><span class="zart">optional</span></div></div><p>Its own home screen for the car screen, with climate and apps in the bottom bar. You install it by button in Panoptes. It needs Panoptes.</p><a class="zmehr" href="/panoptes/en/#tacho-launcher">See pictures →</a></div></div><ul class="zfakten"><li><svg class="zi" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71"/><path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71"/></svg><span><b>One project.</b> All parts are ours, free and made to work together.</span></li><li><svg class="zi" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect width="20" height="12" x="2" y="6" rx="6"/><circle cx="16" cy="12" r="2"/></svg><span><b>You decide.</b> You switch on every connection yourself, with a confirmation in the car. You can disconnect at any time.</span></li><li><svg class="zi" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect width="18" height="11" x="3" y="11" rx="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/></svg><span><b>On the road.</b> Phone and PC also reach the car over the internet, encrypted, through the connection you set up.</span></li><li><svg class="zi" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="12" cy="12" r="10"/><path d="M8 12h8"/><path d="M12 8v8"/></svg><span><b>Also there if you want:</b> notifications through your own Telegram bot, Home Assistant, your wallbox.</span></li></ul></div>',
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
            ("Map source (community server byd.serveone.at or OpenStreetMap Germany)", "your IP address and the map area, so roughly where your car is. With the community server also the query for free charging spots in that area.", "only once you choose a source under Settings → All settings → Map source. On the car screen the choice applies to the whole car; phone and PC ask separately."),
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
        "stand_lead": "Honestly, what runs where, as of 0.1.38.8. \u201cDone\u201d means: built and tested. \u201cOnly some cars\u201d means: depends on the model. \u201cBeta\u201d means: it runs, but has limits.",
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
            ("Telegram with a menu and big buttons", "Done"),
            ("Updates by button from Telegram, phone or Cockpit (only with permission, only when parked)", "Done"),
            ("Panoptes sets itself up again after an update and reports when everything runs", "Done"),
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
        "neu_version": "0.1.38.8", "neu_titel": "New in 0.1.38.8",
        "neu": ["<b>Small updates on their own:</b> if only the last number changes, the update installs by itself once the car has been parked for 10 minutes. “Only notify” is switched over once, with a message. Change it under Settings → All settings → App updates.", "<b>Own switches</b> for horn, lights, hazard lights and unlocking (off by default), switched on only in the car. “<code>/aktionen aus</code>” in Telegram (or the button there) turns these permissions (horn, lights, hazard lights, unlocking) off at once.", "<b>First phone:</b> it can change all settings and pair more devices, but never trigger anything on the car. Car permissions are granted only on the car display.", "<b>Home Assistant</b> can operate gates and front doors you release, optionally the gate when you come home. Everything stays off until you allow each one.", "<b>Guard:</b> on for new setups; if you never set it up, you are asked once. Fewer false alarms from passing cars.", "<b>Faster:</b> Panoptes starts faster. The Telegram bot tells you when Panoptes in the car is still starting and, if you want, stays reachable while the car is parked.", "<b>Safer:</b> stored credentials are additionally encrypted. Backups only contain the device key if you explicitly choose so.", "<b>Launcher 0.1.38.8:</b> rests while the display is off and shows battery health from the car and Panoptes’ estimate side by side.", "<b>From 0.1.38.7:</b> launcher as home screen (switch, off by default), honest remote climate, Spotify next to the launcher."],
        "tl": {"h": "Cluster and launcher <span class=\"bald\">from 0.1.37</span>",
               "lead": "Since 0.1.37, in 0.1.38 on the page Apps &amp; display → Display. The pictures are previews and emulator shots with sample data, not from a car. <a href=\"launcher.html\">All about the Panoptes Launcher</a>",
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
            "bekommen": "<b>Help us:</b> Under Apps &amp; display → “What can my cluster do?” you see what your cluster can do. Do you have a different model? Tell us through the <a href=\"/en/#wunsch\">wish box</a> your model and whether it works (yes or no).",
            "h_gut": "Good to know:",
            "gut": ["By default, while driving the cluster only shows navigation apps from a fixed list (e.g. Google Maps, Waze, OsmAnd, ABRP). Other apps only run while parked.",
                    "You can switch on \u201calso while driving\u201d for each app after a one-time notice. You are then responsible yourself. <b>Watching videos while driving is illegal in many countries.</b>",
                    "The first time, you confirm a notice: the speed and warning lights must stay visible.",
                    "It does not work on the <b>Dolphin Surf</b> and <b>Seagull</b>. On cars with <b>DiLink 5</b> it is locked for now."],
        },
        "dl_text": "Panoptes {V} is a <b>beta version</b>. Panoptes runs in everyday use in a test car (BYD Dolphin Surf, DiLink 3), new versions are added there step by step. On other models some things may be missing or work differently. Installing it is not for everyone: you need some patience, a PC or laptop once, and you have to turn on a developer setting in the car. After that, updates arrive in the app by themselves. Use at your own risk, see the <a href=\"hinweise.html\">notes</a>.",
        "dl_knopf": "⬇️ Download Panoptes {V} (APK, {MB} MB)",
        "hero_dl": "⬇️ Download Panoptes {V}", "hero_anl": "Guide", "kopf_dl": "⬇️ Download",
        "dl_release": "Release on GitHub", "dl_quelle": "Source code",
        "dl_pruef": "Checksum (SHA-256)", "dl_zert": "Signing certificate (SHA-256)",
        "dl_update": "From 0.1.19.1 on, updates arrive via Settings → All settings → App updates. If you have 0.1.17 or 0.1.18, install the current version once by hand (<a href=\"#schritte\">guide</a>); your data is kept.",
        "h_anl": "Step by step",
        "anl": [
            ("Read first.", "Panoptes is meant for your own car, for private use and at your own risk. Read the <a href=\"hinweise.html\">notes</a>. To install it you turn on developer functions in the car. If in doubt whether this matters for your warranty, ask your dealer."),
            ("Download.", "Download <code>{APK}</code> to your PC or laptop with the button above. <b>Optional, for experienced users:</b> compare the checksum first. On Windows type <code>certutil -hashfile {APK} SHA256</code> in a command prompt, on a Mac or Linux <code>shasum -a 256 {APK}</code>. The output must match the checksum above exactly. If it differs, do <b>not</b> install the file."),
            ("Turn on developer access (ADB) in the car.", "Panoptes starts its background services, for example for the cameras, through the car's ADB interface. This connection stays inside the car (127.0.0.1). It is off by default. You turn it on in the BYD developer menu, with the switches for USB debugging or wireless ADB. How to reach this menu depends a lot on model and software version; on newer BYD software it is locked with a code. So far we have only tested this step on the Dolphin Surf (DiLink 3). Without it Panoptes will not fully work."),
            ("Get the app onto the car.", "<b>Tested way, once with a PC or laptop:</b> install Google's Android platform tools (they contain <code>adb</code>). PC and car must be on the same network, for example your phone's Wi-Fi hotspot. Then type <code>adb connect &lt;car-address&gt;:5555</code> and <code>adb install -r {APK}</code>. You find the car's address in its Wi-Fi settings or in your hotspot's device list. At the end it must say <code>Success</code>. After that, updates arrive in the app by themselves. <b>An Android phone instead of a PC (not yet tested by us):</b> this also works with an adb app on the phone, on the same Wi-Fi or hotspot as the car, see the <a href=\"/en/guide#handy-adb\">guide</a>. It does not work with an iPhone. <b>USB stick or BYD file manager: being checked.</b> The file manager passes the file to the installer after a warning; whether it then completes is not confirmed yet. If Android asks about “installing from unknown sources”, allow it only for this installation."),
            ("First start with the setup assistant.", "Open Panoptes on the car screen. Short steps guide you through the essentials, for example language, confirming the notes, <b>autostart</b>, display over other apps, permissions and <b>USB access</b>. Everything else (guard, map source, data sharing, speed cameras, Telegram, route planner, EV Cockpit, remote access) is under \u201cNoch einrichten\u201d (still to set up) afterwards. Almost nothing is preselected. Anything that sends data out stays off until you turn it on yourself."),
            ("Allow autostart.", "For Panoptes to start by itself when you get in, it has to be allowed in BYD's app management. The setup assistant opens the right page; untick the autostart block for Panoptes there. <b>BYD resets this switch after every installation and update.</b> Panoptes turns it back on by itself after an update and tells you if that fails. DiLink 5 has no such app management, so the step is skipped."),
            ("Confirm USB access.", "Android asks once “Allow USB debugging?”. Tick <b>“Always allow from this computer”</b> and tap <b>Allow</b>. The “computer” is Panoptes itself in the car. Without the tick Android asks again after every restart."),
            ("Open on your phone or PC (optional).", "With remote access (Tailscale) set up, open your car's address in a browser. To log in you need the <b>access code</b>, found in the app in the car under <b>Home → Access code</b>. You allow other devices, such as the EV Cockpit, under <b>Settings → All settings → Pair a device</b>."),
        ],
        "h_stolper": "If something goes wrong",
        "stolper": [
            "<b>Panoptes does not start by itself after an update:</b> allow autostart again (step 6). BYD resets it after every installation. Panoptes does this itself after an update. If a message appears, tap “Autostart wieder einschalten” (turn autostart back on) on the display.",
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
# Community-Abschnitt mit QR (04.11.2026), QR lokal erzeugt (Python qrcode), kein fremder QR-Dienst
WA_BLOCK = {'de': '  <style>.wa-box{display:flex;gap:28px;align-items:center;flex-wrap:wrap;margin:14px 0}.wa-box .wa-qr-fig{display:none;margin:0;text-align:center}.wa-box .wa-qr{display:block;width:180px;height:180px;border-radius:12px;padding:0;background:#fff}.wa-box figcaption{font-size:.9rem;opacity:.8;margin-top:6px;max-width:200px}@media(min-width:720px){.wa-box .wa-qr-fig{display:block}}</style>\n  <h2 id="whatsapp">Community</h2>\n  <p>Was es gibt: Ankündigungen, Treffpunkt, Hilfe bei der Installation, Beta-Test und Tacho, Fehler und Wünsche, Wächter und Dashcam, Laden und Wallbox.</p>\n  <div class="wa-box"><div class="bd-knoepfe"><a class="bd-knopf gross leer" href="https://chat.whatsapp.com/IQRtn9JViH4FhypAQsS3yK" target="_blank" rel="noopener">💬 WhatsApp-Gruppe beitreten</a></div><figure class="wa-qr-fig"><svg class="wa-qr" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 41 41" width="200" height="200" role="img" aria-label="QR-Code: WhatsApp-Gruppe beitreten" shape-rendering="crispEdges"><rect width="41" height="41" fill="#fff"/><path fill="#000" d="M4 4h1v1h-1zM5 4h1v1h-1zM6 4h1v1h-1zM7 4h1v1h-1zM8 4h1v1h-1zM9 4h1v1h-1zM10 4h1v1h-1zM14 4h1v1h-1zM15 4h1v1h-1zM16 4h1v1h-1zM22 4h1v1h-1zM24 4h1v1h-1zM25 4h1v1h-1zM30 4h1v1h-1zM31 4h1v1h-1zM32 4h1v1h-1zM33 4h1v1h-1zM34 4h1v1h-1zM35 4h1v1h-1zM36 4h1v1h-1zM4 5h1v1h-1zM10 5h1v1h-1zM12 5h1v1h-1zM13 5h1v1h-1zM14 5h1v1h-1zM17 5h1v1h-1zM18 5h1v1h-1zM21 5h1v1h-1zM25 5h1v1h-1zM28 5h1v1h-1zM30 5h1v1h-1zM36 5h1v1h-1zM4 6h1v1h-1zM6 6h1v1h-1zM7 6h1v1h-1zM8 6h1v1h-1zM10 6h1v1h-1zM12 6h1v1h-1zM13 6h1v1h-1zM14 6h1v1h-1zM16 6h1v1h-1zM17 6h1v1h-1zM21 6h1v1h-1zM22 6h1v1h-1zM25 6h1v1h-1zM26 6h1v1h-1zM27 6h1v1h-1zM30 6h1v1h-1zM32 6h1v1h-1zM33 6h1v1h-1zM34 6h1v1h-1zM36 6h1v1h-1zM4 7h1v1h-1zM6 7h1v1h-1zM7 7h1v1h-1zM8 7h1v1h-1zM10 7h1v1h-1zM12 7h1v1h-1zM13 7h1v1h-1zM25 7h1v1h-1zM26 7h1v1h-1zM27 7h1v1h-1zM30 7h1v1h-1zM32 7h1v1h-1zM33 7h1v1h-1zM34 7h1v1h-1zM36 7h1v1h-1zM4 8h1v1h-1zM6 8h1v1h-1zM7 8h1v1h-1zM8 8h1v1h-1zM10 8h1v1h-1zM19 8h1v1h-1zM21 8h1v1h-1zM22 8h1v1h-1zM25 8h1v1h-1zM26 8h1v1h-1zM30 8h1v1h-1zM32 8h1v1h-1zM33 8h1v1h-1zM34 8h1v1h-1zM36 8h1v1h-1zM4 9h1v1h-1zM10 9h1v1h-1zM16 9h1v1h-1zM18 9h1v1h-1zM20 9h1v1h-1zM21 9h1v1h-1zM24 9h1v1h-1zM25 9h1v1h-1zM26 9h1v1h-1zM30 9h1v1h-1zM36 9h1v1h-1zM4 10h1v1h-1zM5 10h1v1h-1zM6 10h1v1h-1zM7 10h1v1h-1zM8 10h1v1h-1zM9 10h1v1h-1zM10 10h1v1h-1zM12 10h1v1h-1zM14 10h1v1h-1zM16 10h1v1h-1zM18 10h1v1h-1zM20 10h1v1h-1zM22 10h1v1h-1zM24 10h1v1h-1zM26 10h1v1h-1zM28 10h1v1h-1zM30 10h1v1h-1zM31 10h1v1h-1zM32 10h1v1h-1zM33 10h1v1h-1zM34 10h1v1h-1zM35 10h1v1h-1zM36 10h1v1h-1zM12 11h1v1h-1zM13 11h1v1h-1zM14 11h1v1h-1zM16 11h1v1h-1zM22 11h1v1h-1zM26 11h1v1h-1zM27 11h1v1h-1zM28 11h1v1h-1zM4 12h1v1h-1zM10 12h1v1h-1zM12 12h1v1h-1zM17 12h1v1h-1zM18 12h1v1h-1zM19 12h1v1h-1zM20 12h1v1h-1zM21 12h1v1h-1zM24 12h1v1h-1zM26 12h1v1h-1zM28 12h1v1h-1zM29 12h1v1h-1zM30 12h1v1h-1zM33 12h1v1h-1zM34 12h1v1h-1zM35 12h1v1h-1zM5 13h1v1h-1zM6 13h1v1h-1zM7 13h1v1h-1zM8 13h1v1h-1zM9 13h1v1h-1zM11 13h1v1h-1zM16 13h1v1h-1zM18 13h1v1h-1zM22 13h1v1h-1zM23 13h1v1h-1zM26 13h1v1h-1zM27 13h1v1h-1zM28 13h1v1h-1zM32 13h1v1h-1zM33 13h1v1h-1zM34 13h1v1h-1zM35 13h1v1h-1zM36 13h1v1h-1zM4 14h1v1h-1zM10 14h1v1h-1zM11 14h1v1h-1zM12 14h1v1h-1zM13 14h1v1h-1zM15 14h1v1h-1zM16 14h1v1h-1zM19 14h1v1h-1zM20 14h1v1h-1zM22 14h1v1h-1zM28 14h1v1h-1zM30 14h1v1h-1zM32 14h1v1h-1zM34 14h1v1h-1zM35 14h1v1h-1zM5 15h1v1h-1zM7 15h1v1h-1zM8 15h1v1h-1zM9 15h1v1h-1zM14 15h1v1h-1zM15 15h1v1h-1zM18 15h1v1h-1zM26 15h1v1h-1zM31 15h1v1h-1zM32 15h1v1h-1zM33 15h1v1h-1zM34 15h1v1h-1zM36 15h1v1h-1zM4 16h1v1h-1zM9 16h1v1h-1zM10 16h1v1h-1zM17 16h1v1h-1zM18 16h1v1h-1zM19 16h1v1h-1zM20 16h1v1h-1zM21 16h1v1h-1zM22 16h1v1h-1zM23 16h1v1h-1zM24 16h1v1h-1zM27 16h1v1h-1zM30 16h1v1h-1zM31 16h1v1h-1zM35 16h1v1h-1zM4 17h1v1h-1zM6 17h1v1h-1zM7 17h1v1h-1zM8 17h1v1h-1zM11 17h1v1h-1zM12 17h1v1h-1zM14 17h1v1h-1zM15 17h1v1h-1zM17 17h1v1h-1zM18 17h1v1h-1zM20 17h1v1h-1zM24 17h1v1h-1zM25 17h1v1h-1zM26 17h1v1h-1zM27 17h1v1h-1zM29 17h1v1h-1zM30 17h1v1h-1zM31 17h1v1h-1zM33 17h1v1h-1zM34 17h1v1h-1zM35 17h1v1h-1zM36 17h1v1h-1zM7 18h1v1h-1zM8 18h1v1h-1zM9 18h1v1h-1zM10 18h1v1h-1zM11 18h1v1h-1zM13 18h1v1h-1zM14 18h1v1h-1zM17 18h1v1h-1zM18 18h1v1h-1zM21 18h1v1h-1zM22 18h1v1h-1zM23 18h1v1h-1zM25 18h1v1h-1zM29 18h1v1h-1zM30 18h1v1h-1zM31 18h1v1h-1zM32 18h1v1h-1zM35 18h1v1h-1zM4 19h1v1h-1zM5 19h1v1h-1zM7 19h1v1h-1zM8 19h1v1h-1zM11 19h1v1h-1zM12 19h1v1h-1zM13 19h1v1h-1zM14 19h1v1h-1zM15 19h1v1h-1zM16 19h1v1h-1zM17 19h1v1h-1zM18 19h1v1h-1zM19 19h1v1h-1zM23 19h1v1h-1zM26 19h1v1h-1zM28 19h1v1h-1zM29 19h1v1h-1zM31 19h1v1h-1zM32 19h1v1h-1zM33 19h1v1h-1zM34 19h1v1h-1zM36 19h1v1h-1zM5 20h1v1h-1zM6 20h1v1h-1zM7 20h1v1h-1zM8 20h1v1h-1zM10 20h1v1h-1zM12 20h1v1h-1zM14 20h1v1h-1zM20 20h1v1h-1zM21 20h1v1h-1zM23 20h1v1h-1zM24 20h1v1h-1zM26 20h1v1h-1zM29 20h1v1h-1zM31 20h1v1h-1zM32 20h1v1h-1zM36 20h1v1h-1zM4 21h1v1h-1zM6 21h1v1h-1zM9 21h1v1h-1zM11 21h1v1h-1zM15 21h1v1h-1zM17 21h1v1h-1zM20 21h1v1h-1zM21 21h1v1h-1zM22 21h1v1h-1zM23 21h1v1h-1zM24 21h1v1h-1zM25 21h1v1h-1zM27 21h1v1h-1zM30 21h1v1h-1zM33 21h1v1h-1zM34 21h1v1h-1zM4 22h1v1h-1zM5 22h1v1h-1zM6 22h1v1h-1zM10 22h1v1h-1zM12 22h1v1h-1zM13 22h1v1h-1zM14 22h1v1h-1zM19 22h1v1h-1zM23 22h1v1h-1zM25 22h1v1h-1zM26 22h1v1h-1zM27 22h1v1h-1zM29 22h1v1h-1zM31 22h1v1h-1zM33 22h1v1h-1zM34 22h1v1h-1zM36 22h1v1h-1zM4 23h1v1h-1zM5 23h1v1h-1zM7 23h1v1h-1zM8 23h1v1h-1zM11 23h1v1h-1zM12 23h1v1h-1zM14 23h1v1h-1zM15 23h1v1h-1zM16 23h1v1h-1zM18 23h1v1h-1zM21 23h1v1h-1zM22 23h1v1h-1zM26 23h1v1h-1zM28 23h1v1h-1zM29 23h1v1h-1zM32 23h1v1h-1zM33 23h1v1h-1zM34 23h1v1h-1zM35 23h1v1h-1zM5 24h1v1h-1zM7 24h1v1h-1zM8 24h1v1h-1zM9 24h1v1h-1zM10 24h1v1h-1zM12 24h1v1h-1zM13 24h1v1h-1zM15 24h1v1h-1zM20 24h1v1h-1zM24 24h1v1h-1zM25 24h1v1h-1zM26 24h1v1h-1zM29 24h1v1h-1zM31 24h1v1h-1zM33 24h1v1h-1zM36 24h1v1h-1zM4 25h1v1h-1zM12 25h1v1h-1zM14 25h1v1h-1zM16 25h1v1h-1zM20 25h1v1h-1zM21 25h1v1h-1zM22 25h1v1h-1zM24 25h1v1h-1zM26 25h1v1h-1zM29 25h1v1h-1zM31 25h1v1h-1zM32 25h1v1h-1zM4 26h1v1h-1zM6 26h1v1h-1zM10 26h1v1h-1zM14 26h1v1h-1zM15 26h1v1h-1zM18 26h1v1h-1zM19 26h1v1h-1zM20 26h1v1h-1zM21 26h1v1h-1zM24 26h1v1h-1zM25 26h1v1h-1zM31 26h1v1h-1zM33 26h1v1h-1zM34 26h1v1h-1zM35 26h1v1h-1zM4 27h1v1h-1zM9 27h1v1h-1zM11 27h1v1h-1zM12 27h1v1h-1zM14 27h1v1h-1zM18 27h1v1h-1zM26 27h1v1h-1zM28 27h1v1h-1zM29 27h1v1h-1zM30 27h1v1h-1zM31 27h1v1h-1zM33 27h1v1h-1zM34 27h1v1h-1zM4 28h1v1h-1zM5 28h1v1h-1zM6 28h1v1h-1zM7 28h1v1h-1zM10 28h1v1h-1zM12 28h1v1h-1zM15 28h1v1h-1zM19 28h1v1h-1zM20 28h1v1h-1zM23 28h1v1h-1zM24 28h1v1h-1zM27 28h1v1h-1zM28 28h1v1h-1zM29 28h1v1h-1zM30 28h1v1h-1zM31 28h1v1h-1zM32 28h1v1h-1zM33 28h1v1h-1zM34 28h1v1h-1zM35 28h1v1h-1zM36 28h1v1h-1zM12 29h1v1h-1zM13 29h1v1h-1zM16 29h1v1h-1zM18 29h1v1h-1zM20 29h1v1h-1zM22 29h1v1h-1zM23 29h1v1h-1zM24 29h1v1h-1zM25 29h1v1h-1zM26 29h1v1h-1zM28 29h1v1h-1zM32 29h1v1h-1zM34 29h1v1h-1zM35 29h1v1h-1zM36 29h1v1h-1zM4 30h1v1h-1zM5 30h1v1h-1zM6 30h1v1h-1zM7 30h1v1h-1zM8 30h1v1h-1zM9 30h1v1h-1zM10 30h1v1h-1zM15 30h1v1h-1zM17 30h1v1h-1zM18 30h1v1h-1zM19 30h1v1h-1zM20 30h1v1h-1zM22 30h1v1h-1zM24 30h1v1h-1zM27 30h1v1h-1zM28 30h1v1h-1zM30 30h1v1h-1zM32 30h1v1h-1zM34 30h1v1h-1zM4 31h1v1h-1zM10 31h1v1h-1zM13 31h1v1h-1zM17 31h1v1h-1zM18 31h1v1h-1zM19 31h1v1h-1zM23 31h1v1h-1zM24 31h1v1h-1zM27 31h1v1h-1zM28 31h1v1h-1zM32 31h1v1h-1zM33 31h1v1h-1zM34 31h1v1h-1zM4 32h1v1h-1zM6 32h1v1h-1zM7 32h1v1h-1zM8 32h1v1h-1zM10 32h1v1h-1zM13 32h1v1h-1zM15 32h1v1h-1zM17 32h1v1h-1zM18 32h1v1h-1zM22 32h1v1h-1zM25 32h1v1h-1zM28 32h1v1h-1zM29 32h1v1h-1zM30 32h1v1h-1zM31 32h1v1h-1zM32 32h1v1h-1zM33 32h1v1h-1zM35 32h1v1h-1zM36 32h1v1h-1zM4 33h1v1h-1zM6 33h1v1h-1zM7 33h1v1h-1zM8 33h1v1h-1zM10 33h1v1h-1zM15 33h1v1h-1zM17 33h1v1h-1zM20 33h1v1h-1zM21 33h1v1h-1zM24 33h1v1h-1zM28 33h1v1h-1zM29 33h1v1h-1zM31 33h1v1h-1zM32 33h1v1h-1zM35 33h1v1h-1zM36 33h1v1h-1zM4 34h1v1h-1zM6 34h1v1h-1zM7 34h1v1h-1zM8 34h1v1h-1zM10 34h1v1h-1zM13 34h1v1h-1zM14 34h1v1h-1zM16 34h1v1h-1zM17 34h1v1h-1zM18 34h1v1h-1zM20 34h1v1h-1zM21 34h1v1h-1zM24 34h1v1h-1zM25 34h1v1h-1zM27 34h1v1h-1zM29 34h1v1h-1zM31 34h1v1h-1zM32 34h1v1h-1zM33 34h1v1h-1zM34 34h1v1h-1zM35 34h1v1h-1zM36 34h1v1h-1zM4 35h1v1h-1zM10 35h1v1h-1zM13 35h1v1h-1zM14 35h1v1h-1zM16 35h1v1h-1zM17 35h1v1h-1zM18 35h1v1h-1zM19 35h1v1h-1zM20 35h1v1h-1zM23 35h1v1h-1zM24 35h1v1h-1zM28 35h1v1h-1zM31 35h1v1h-1zM32 35h1v1h-1zM34 35h1v1h-1zM4 36h1v1h-1zM5 36h1v1h-1zM6 36h1v1h-1zM7 36h1v1h-1zM8 36h1v1h-1zM9 36h1v1h-1zM10 36h1v1h-1zM12 36h1v1h-1zM16 36h1v1h-1zM17 36h1v1h-1zM18 36h1v1h-1zM21 36h1v1h-1zM22 36h1v1h-1zM23 36h1v1h-1zM24 36h1v1h-1zM26 36h1v1h-1zM27 36h1v1h-1zM28 36h1v1h-1zM31 36h1v1h-1zM33 36h1v1h-1zM35 36h1v1h-1z"/></svg><figcaption>Am PC: mit dem Handy scannen.</figcaption></figure></div>\n  <div class="bd-hinweis"><p>WhatsApp ist ein fremder Dienst (Meta). Deine Telefonnummer ist für die Gruppe sichtbar.</p><p>Privates Projekt, nicht von BYD. Mehr dazu im <a href="/datenschutz#whatsapp">Datenschutz</a>.</p></div>', 'en': '  <style>.wa-box{display:flex;gap:28px;align-items:center;flex-wrap:wrap;margin:14px 0}.wa-box .wa-qr-fig{display:none;margin:0;text-align:center}.wa-box .wa-qr{display:block;width:180px;height:180px;border-radius:12px;padding:0;background:#fff}.wa-box figcaption{font-size:.9rem;opacity:.8;margin-top:6px;max-width:200px}@media(min-width:720px){.wa-box .wa-qr-fig{display:block}}</style>\n  <h2 id="whatsapp">Community</h2>\n  <p>What you get: announcements, a meeting place, help with installing, beta test and cluster, bugs and wishes, guard and dashcam, charging and wallbox.</p>\n  <div class="wa-box"><div class="bd-knoepfe"><a class="bd-knopf gross leer" href="https://chat.whatsapp.com/IQRtn9JViH4FhypAQsS3yK" target="_blank" rel="noopener">💬 Join the WhatsApp group</a></div><figure class="wa-qr-fig"><svg class="wa-qr" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 41 41" width="200" height="200" role="img" aria-label="QR code: join the WhatsApp group" shape-rendering="crispEdges"><rect width="41" height="41" fill="#fff"/><path fill="#000" d="M4 4h1v1h-1zM5 4h1v1h-1zM6 4h1v1h-1zM7 4h1v1h-1zM8 4h1v1h-1zM9 4h1v1h-1zM10 4h1v1h-1zM14 4h1v1h-1zM15 4h1v1h-1zM16 4h1v1h-1zM22 4h1v1h-1zM24 4h1v1h-1zM25 4h1v1h-1zM30 4h1v1h-1zM31 4h1v1h-1zM32 4h1v1h-1zM33 4h1v1h-1zM34 4h1v1h-1zM35 4h1v1h-1zM36 4h1v1h-1zM4 5h1v1h-1zM10 5h1v1h-1zM12 5h1v1h-1zM13 5h1v1h-1zM14 5h1v1h-1zM17 5h1v1h-1zM18 5h1v1h-1zM21 5h1v1h-1zM25 5h1v1h-1zM28 5h1v1h-1zM30 5h1v1h-1zM36 5h1v1h-1zM4 6h1v1h-1zM6 6h1v1h-1zM7 6h1v1h-1zM8 6h1v1h-1zM10 6h1v1h-1zM12 6h1v1h-1zM13 6h1v1h-1zM14 6h1v1h-1zM16 6h1v1h-1zM17 6h1v1h-1zM21 6h1v1h-1zM22 6h1v1h-1zM25 6h1v1h-1zM26 6h1v1h-1zM27 6h1v1h-1zM30 6h1v1h-1zM32 6h1v1h-1zM33 6h1v1h-1zM34 6h1v1h-1zM36 6h1v1h-1zM4 7h1v1h-1zM6 7h1v1h-1zM7 7h1v1h-1zM8 7h1v1h-1zM10 7h1v1h-1zM12 7h1v1h-1zM13 7h1v1h-1zM25 7h1v1h-1zM26 7h1v1h-1zM27 7h1v1h-1zM30 7h1v1h-1zM32 7h1v1h-1zM33 7h1v1h-1zM34 7h1v1h-1zM36 7h1v1h-1zM4 8h1v1h-1zM6 8h1v1h-1zM7 8h1v1h-1zM8 8h1v1h-1zM10 8h1v1h-1zM19 8h1v1h-1zM21 8h1v1h-1zM22 8h1v1h-1zM25 8h1v1h-1zM26 8h1v1h-1zM30 8h1v1h-1zM32 8h1v1h-1zM33 8h1v1h-1zM34 8h1v1h-1zM36 8h1v1h-1zM4 9h1v1h-1zM10 9h1v1h-1zM16 9h1v1h-1zM18 9h1v1h-1zM20 9h1v1h-1zM21 9h1v1h-1zM24 9h1v1h-1zM25 9h1v1h-1zM26 9h1v1h-1zM30 9h1v1h-1zM36 9h1v1h-1zM4 10h1v1h-1zM5 10h1v1h-1zM6 10h1v1h-1zM7 10h1v1h-1zM8 10h1v1h-1zM9 10h1v1h-1zM10 10h1v1h-1zM12 10h1v1h-1zM14 10h1v1h-1zM16 10h1v1h-1zM18 10h1v1h-1zM20 10h1v1h-1zM22 10h1v1h-1zM24 10h1v1h-1zM26 10h1v1h-1zM28 10h1v1h-1zM30 10h1v1h-1zM31 10h1v1h-1zM32 10h1v1h-1zM33 10h1v1h-1zM34 10h1v1h-1zM35 10h1v1h-1zM36 10h1v1h-1zM12 11h1v1h-1zM13 11h1v1h-1zM14 11h1v1h-1zM16 11h1v1h-1zM22 11h1v1h-1zM26 11h1v1h-1zM27 11h1v1h-1zM28 11h1v1h-1zM4 12h1v1h-1zM10 12h1v1h-1zM12 12h1v1h-1zM17 12h1v1h-1zM18 12h1v1h-1zM19 12h1v1h-1zM20 12h1v1h-1zM21 12h1v1h-1zM24 12h1v1h-1zM26 12h1v1h-1zM28 12h1v1h-1zM29 12h1v1h-1zM30 12h1v1h-1zM33 12h1v1h-1zM34 12h1v1h-1zM35 12h1v1h-1zM5 13h1v1h-1zM6 13h1v1h-1zM7 13h1v1h-1zM8 13h1v1h-1zM9 13h1v1h-1zM11 13h1v1h-1zM16 13h1v1h-1zM18 13h1v1h-1zM22 13h1v1h-1zM23 13h1v1h-1zM26 13h1v1h-1zM27 13h1v1h-1zM28 13h1v1h-1zM32 13h1v1h-1zM33 13h1v1h-1zM34 13h1v1h-1zM35 13h1v1h-1zM36 13h1v1h-1zM4 14h1v1h-1zM10 14h1v1h-1zM11 14h1v1h-1zM12 14h1v1h-1zM13 14h1v1h-1zM15 14h1v1h-1zM16 14h1v1h-1zM19 14h1v1h-1zM20 14h1v1h-1zM22 14h1v1h-1zM28 14h1v1h-1zM30 14h1v1h-1zM32 14h1v1h-1zM34 14h1v1h-1zM35 14h1v1h-1zM5 15h1v1h-1zM7 15h1v1h-1zM8 15h1v1h-1zM9 15h1v1h-1zM14 15h1v1h-1zM15 15h1v1h-1zM18 15h1v1h-1zM26 15h1v1h-1zM31 15h1v1h-1zM32 15h1v1h-1zM33 15h1v1h-1zM34 15h1v1h-1zM36 15h1v1h-1zM4 16h1v1h-1zM9 16h1v1h-1zM10 16h1v1h-1zM17 16h1v1h-1zM18 16h1v1h-1zM19 16h1v1h-1zM20 16h1v1h-1zM21 16h1v1h-1zM22 16h1v1h-1zM23 16h1v1h-1zM24 16h1v1h-1zM27 16h1v1h-1zM30 16h1v1h-1zM31 16h1v1h-1zM35 16h1v1h-1zM4 17h1v1h-1zM6 17h1v1h-1zM7 17h1v1h-1zM8 17h1v1h-1zM11 17h1v1h-1zM12 17h1v1h-1zM14 17h1v1h-1zM15 17h1v1h-1zM17 17h1v1h-1zM18 17h1v1h-1zM20 17h1v1h-1zM24 17h1v1h-1zM25 17h1v1h-1zM26 17h1v1h-1zM27 17h1v1h-1zM29 17h1v1h-1zM30 17h1v1h-1zM31 17h1v1h-1zM33 17h1v1h-1zM34 17h1v1h-1zM35 17h1v1h-1zM36 17h1v1h-1zM7 18h1v1h-1zM8 18h1v1h-1zM9 18h1v1h-1zM10 18h1v1h-1zM11 18h1v1h-1zM13 18h1v1h-1zM14 18h1v1h-1zM17 18h1v1h-1zM18 18h1v1h-1zM21 18h1v1h-1zM22 18h1v1h-1zM23 18h1v1h-1zM25 18h1v1h-1zM29 18h1v1h-1zM30 18h1v1h-1zM31 18h1v1h-1zM32 18h1v1h-1zM35 18h1v1h-1zM4 19h1v1h-1zM5 19h1v1h-1zM7 19h1v1h-1zM8 19h1v1h-1zM11 19h1v1h-1zM12 19h1v1h-1zM13 19h1v1h-1zM14 19h1v1h-1zM15 19h1v1h-1zM16 19h1v1h-1zM17 19h1v1h-1zM18 19h1v1h-1zM19 19h1v1h-1zM23 19h1v1h-1zM26 19h1v1h-1zM28 19h1v1h-1zM29 19h1v1h-1zM31 19h1v1h-1zM32 19h1v1h-1zM33 19h1v1h-1zM34 19h1v1h-1zM36 19h1v1h-1zM5 20h1v1h-1zM6 20h1v1h-1zM7 20h1v1h-1zM8 20h1v1h-1zM10 20h1v1h-1zM12 20h1v1h-1zM14 20h1v1h-1zM20 20h1v1h-1zM21 20h1v1h-1zM23 20h1v1h-1zM24 20h1v1h-1zM26 20h1v1h-1zM29 20h1v1h-1zM31 20h1v1h-1zM32 20h1v1h-1zM36 20h1v1h-1zM4 21h1v1h-1zM6 21h1v1h-1zM9 21h1v1h-1zM11 21h1v1h-1zM15 21h1v1h-1zM17 21h1v1h-1zM20 21h1v1h-1zM21 21h1v1h-1zM22 21h1v1h-1zM23 21h1v1h-1zM24 21h1v1h-1zM25 21h1v1h-1zM27 21h1v1h-1zM30 21h1v1h-1zM33 21h1v1h-1zM34 21h1v1h-1zM4 22h1v1h-1zM5 22h1v1h-1zM6 22h1v1h-1zM10 22h1v1h-1zM12 22h1v1h-1zM13 22h1v1h-1zM14 22h1v1h-1zM19 22h1v1h-1zM23 22h1v1h-1zM25 22h1v1h-1zM26 22h1v1h-1zM27 22h1v1h-1zM29 22h1v1h-1zM31 22h1v1h-1zM33 22h1v1h-1zM34 22h1v1h-1zM36 22h1v1h-1zM4 23h1v1h-1zM5 23h1v1h-1zM7 23h1v1h-1zM8 23h1v1h-1zM11 23h1v1h-1zM12 23h1v1h-1zM14 23h1v1h-1zM15 23h1v1h-1zM16 23h1v1h-1zM18 23h1v1h-1zM21 23h1v1h-1zM22 23h1v1h-1zM26 23h1v1h-1zM28 23h1v1h-1zM29 23h1v1h-1zM32 23h1v1h-1zM33 23h1v1h-1zM34 23h1v1h-1zM35 23h1v1h-1zM5 24h1v1h-1zM7 24h1v1h-1zM8 24h1v1h-1zM9 24h1v1h-1zM10 24h1v1h-1zM12 24h1v1h-1zM13 24h1v1h-1zM15 24h1v1h-1zM20 24h1v1h-1zM24 24h1v1h-1zM25 24h1v1h-1zM26 24h1v1h-1zM29 24h1v1h-1zM31 24h1v1h-1zM33 24h1v1h-1zM36 24h1v1h-1zM4 25h1v1h-1zM12 25h1v1h-1zM14 25h1v1h-1zM16 25h1v1h-1zM20 25h1v1h-1zM21 25h1v1h-1zM22 25h1v1h-1zM24 25h1v1h-1zM26 25h1v1h-1zM29 25h1v1h-1zM31 25h1v1h-1zM32 25h1v1h-1zM4 26h1v1h-1zM6 26h1v1h-1zM10 26h1v1h-1zM14 26h1v1h-1zM15 26h1v1h-1zM18 26h1v1h-1zM19 26h1v1h-1zM20 26h1v1h-1zM21 26h1v1h-1zM24 26h1v1h-1zM25 26h1v1h-1zM31 26h1v1h-1zM33 26h1v1h-1zM34 26h1v1h-1zM35 26h1v1h-1zM4 27h1v1h-1zM9 27h1v1h-1zM11 27h1v1h-1zM12 27h1v1h-1zM14 27h1v1h-1zM18 27h1v1h-1zM26 27h1v1h-1zM28 27h1v1h-1zM29 27h1v1h-1zM30 27h1v1h-1zM31 27h1v1h-1zM33 27h1v1h-1zM34 27h1v1h-1zM4 28h1v1h-1zM5 28h1v1h-1zM6 28h1v1h-1zM7 28h1v1h-1zM10 28h1v1h-1zM12 28h1v1h-1zM15 28h1v1h-1zM19 28h1v1h-1zM20 28h1v1h-1zM23 28h1v1h-1zM24 28h1v1h-1zM27 28h1v1h-1zM28 28h1v1h-1zM29 28h1v1h-1zM30 28h1v1h-1zM31 28h1v1h-1zM32 28h1v1h-1zM33 28h1v1h-1zM34 28h1v1h-1zM35 28h1v1h-1zM36 28h1v1h-1zM12 29h1v1h-1zM13 29h1v1h-1zM16 29h1v1h-1zM18 29h1v1h-1zM20 29h1v1h-1zM22 29h1v1h-1zM23 29h1v1h-1zM24 29h1v1h-1zM25 29h1v1h-1zM26 29h1v1h-1zM28 29h1v1h-1zM32 29h1v1h-1zM34 29h1v1h-1zM35 29h1v1h-1zM36 29h1v1h-1zM4 30h1v1h-1zM5 30h1v1h-1zM6 30h1v1h-1zM7 30h1v1h-1zM8 30h1v1h-1zM9 30h1v1h-1zM10 30h1v1h-1zM15 30h1v1h-1zM17 30h1v1h-1zM18 30h1v1h-1zM19 30h1v1h-1zM20 30h1v1h-1zM22 30h1v1h-1zM24 30h1v1h-1zM27 30h1v1h-1zM28 30h1v1h-1zM30 30h1v1h-1zM32 30h1v1h-1zM34 30h1v1h-1zM4 31h1v1h-1zM10 31h1v1h-1zM13 31h1v1h-1zM17 31h1v1h-1zM18 31h1v1h-1zM19 31h1v1h-1zM23 31h1v1h-1zM24 31h1v1h-1zM27 31h1v1h-1zM28 31h1v1h-1zM32 31h1v1h-1zM33 31h1v1h-1zM34 31h1v1h-1zM4 32h1v1h-1zM6 32h1v1h-1zM7 32h1v1h-1zM8 32h1v1h-1zM10 32h1v1h-1zM13 32h1v1h-1zM15 32h1v1h-1zM17 32h1v1h-1zM18 32h1v1h-1zM22 32h1v1h-1zM25 32h1v1h-1zM28 32h1v1h-1zM29 32h1v1h-1zM30 32h1v1h-1zM31 32h1v1h-1zM32 32h1v1h-1zM33 32h1v1h-1zM35 32h1v1h-1zM36 32h1v1h-1zM4 33h1v1h-1zM6 33h1v1h-1zM7 33h1v1h-1zM8 33h1v1h-1zM10 33h1v1h-1zM15 33h1v1h-1zM17 33h1v1h-1zM20 33h1v1h-1zM21 33h1v1h-1zM24 33h1v1h-1zM28 33h1v1h-1zM29 33h1v1h-1zM31 33h1v1h-1zM32 33h1v1h-1zM35 33h1v1h-1zM36 33h1v1h-1zM4 34h1v1h-1zM6 34h1v1h-1zM7 34h1v1h-1zM8 34h1v1h-1zM10 34h1v1h-1zM13 34h1v1h-1zM14 34h1v1h-1zM16 34h1v1h-1zM17 34h1v1h-1zM18 34h1v1h-1zM20 34h1v1h-1zM21 34h1v1h-1zM24 34h1v1h-1zM25 34h1v1h-1zM27 34h1v1h-1zM29 34h1v1h-1zM31 34h1v1h-1zM32 34h1v1h-1zM33 34h1v1h-1zM34 34h1v1h-1zM35 34h1v1h-1zM36 34h1v1h-1zM4 35h1v1h-1zM10 35h1v1h-1zM13 35h1v1h-1zM14 35h1v1h-1zM16 35h1v1h-1zM17 35h1v1h-1zM18 35h1v1h-1zM19 35h1v1h-1zM20 35h1v1h-1zM23 35h1v1h-1zM24 35h1v1h-1zM28 35h1v1h-1zM31 35h1v1h-1zM32 35h1v1h-1zM34 35h1v1h-1zM4 36h1v1h-1zM5 36h1v1h-1zM6 36h1v1h-1zM7 36h1v1h-1zM8 36h1v1h-1zM9 36h1v1h-1zM10 36h1v1h-1zM12 36h1v1h-1zM16 36h1v1h-1zM17 36h1v1h-1zM18 36h1v1h-1zM21 36h1v1h-1zM22 36h1v1h-1zM23 36h1v1h-1zM24 36h1v1h-1zM26 36h1v1h-1zM27 36h1v1h-1zM28 36h1v1h-1zM31 36h1v1h-1zM33 36h1v1h-1zM35 36h1v1h-1z"/></svg><figcaption>On a PC: scan with your phone.</figcaption></figure></div>\n  <div class="bd-hinweis"><p>WhatsApp is a third-party service (Meta). Your phone number is visible to the group.</p><p>Private project, not made by BYD. More in the <a href="/en/datenschutz#whatsapp">privacy policy</a>.</p></div>'}
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
    o.append("  " + reihe([("startd38", "display", t["hero_alt_pc"]), ("startd38", "handy", t["hero_alt_handy"])], p, sofort=True))
    o.append('  <div class="bd-hinweis"><p>%s</p></div>' % t["wichtig"])
    # Ist das was für mich?
    o.append('  <h2 id="fuer-mich">%s</h2>\n  <div class="bd-kacheln">' % t["h_fuer_mich"])
    for ic, h, txt in t["fuer_mich"]:
        o.append('    <div class="bd-kachel"><span class="bd-symbol">%s</span><h3>%s</h3><p>%s</p></div>' % (ic, h, txt))
    o.append("  </div>")
    # Funktionen: 6 oben, Rest aufklappbar
    o.append('  <p>%s</p>' % t["handy_link"])
    # WhatsApp-Community (Alfred, 30.10.2026): Link sichtbar im HTML, ohne Zaehlung
    o.append(WA_BLOCK[t["lang"]])
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
    if t.get("zus_block"):                  # „So gehört alles zusammen“ (04.11.2026)
        o.append("  " + t["zus_block"])
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


# Unterseite „Telegram verbinden“ (04.11.2026). Fakten nur aus dem Code rel-0.1.38.5 (Belege: TELEGRAM_FAKTEN.md im Notizordner).
TG = {
    "de": {
        "title": "Telegram verbinden – Panoptes",
        "desc": "Was Panoptes über Telegram kann und wie du deinen eigenen Bot in wenigen Minuten verbindest.",
        "zurueck": "← Zurück zu Panoptes",
        "h1": "Telegram verbinden",
        "lead": "Panoptes meldet sich über deinen <b>eigenen</b> Telegram-Bot. Den legst du einmal selbst an, kostenlos und ohne Programmieren. Dann koppelst du ihn mit einer PIN. Fertig.",
        "kann_h": "Was kann Telegram?",
        "kann": [
            ("Meldungen", "Wächter-Alarm, Laden fertig oder Ladefehler, schwache Starterbatterie, Reifendruck, neue Updates, ein kurzer Bericht nach dem Abstellen. Jede Art schaltest du einzeln ein oder aus. Für die Nacht gibt es eine Ruhezeit."),
            ("Menü mit großen Knöpfen", "Schreib dem Bot irgendetwas, zum Beispiel „Hallo“. Dann kommt ein Menü. Du tippst nur noch auf Knöpfe."),
            ("Nachsehen", "Wie geht’s dem Auto? Wo steht es? Wie voll ist der Akku? Dazu ein Kamerabild und deine Aufnahmen, wenn du danach fragst."),
            ("Wächter und Camping", "Den Wächter wecken oder schlafen legen. Camping ein- oder ausschalten, nur im Stand."),
            ("Update-Meldungen", "Bei „Nur melden“ schreibt der Bot „Panoptes … ist da“ mit dem Knopf „Jetzt installieren“ und fragt vorher noch einmal nach. Bei „Kleine Updates von selbst, große melden“ (Standard) kommen kleine Updates still, wenn das Auto mindestens 10 Minuten aus ist. Große meldet Panoptes vorher mit einer Zusammenfassung, du entscheidest. Nie während der Fahrt."),
            ("Bilder und Videos", "Automatisch nur, wenn du „Bilder und Videos an Telegram senden“ einschaltest. Ab Werk ist das aus, dann kommt nur Text."),
        ],
        "nicht_h": "Was bewusst nicht geht",
        "nicht": "Über Telegram kannst du das Auto <b>nicht</b> aufsperren oder zusperren. Auch Klima, Hupe, Licht, Fenster und Laden starten oder stoppen gehen nicht. Den Tiermodus kannst du ansehen, aber nicht ein- oder ausschalten.",
        "menue_h": "So sieht das Menü aus",
        "menue_lead": "Skizze, kein echter Chat. Knöpfe zu Befehlen, die du ausgeschaltet hast, siehst du gar nicht.",
        "menue": ["Wie geht’s dem Auto?", "Wächter", "Wo steht es?", "Kamerabild", "Aufnahmen", "Akku", "Updates", "Mehr"],
        "menue_mehr": "Unter „Mehr“: Camping, Tier im Auto, Link zu Panoptes, Dienste, Einstellungen sichern, Hilfe.",
        "schritte_h": "So verbindest du es",
        "vorher": "Du brauchst Telegram am Handy und Panoptes im Auto. Den Schlüssel trägst du in der Panoptes-Oberfläche ein, am Bildschirm im Auto oder am PC. Mit einer Anmeldung per Telegram am Handy geht das Einrichten nicht.",
        "schritte": [
            ("Seite öffnen.", "In Panoptes: <b>Regeln → Meldungen → Telegram-Meldungen</b>. Dort steht „Noch nicht eingerichtet“ und drei Schritte."),
            ("Bot anlegen.", "Öffne in Telegram den Chat mit <b>@BotFather</b>. Das ist das offizielle Telegram-Konto mit blauem Haken. Schick ihm <code>/newbot</code>. Gib einen Namen ein, zum Beispiel <code>Mein Auto</code>. Dann einen Benutzernamen, der auf <code>bot</code> endet."),
            ("Schlüssel einfügen.", "BotFather antwortet mit einem langen Schlüssel. Er sieht so aus: <code>123456789:AAH…</code>. Kopiere ihn, füge ihn in Panoptes ein und tippe auf <b>„Prüfen und speichern“</b>."),
            ("PIN holen.", "Tippe auf <b>„Kopplung starten“</b>. Panoptes zeigt eine PIN mit 6 Ziffern."),
            ("Koppeln.", "Am Handy auf <b>„In Telegram öffnen und „Start“ tippen“</b> tippen. Geht der Link nicht, schick dem Bot die Nachricht <code>/koppeln</code> und deine PIN, zum Beispiel <code>/koppeln 123456</code>."),
            ("Fertig.", "Der Bot antwortet „Gekoppelt!“. Panoptes merkt das von selbst. Mit <b>„Testnachricht schicken“</b> prüfst du, ob alles ankommt."),
        ],
        "tipp": "<b>Tipp:</b> Schalte „Auch bei abgestelltem Auto erreichbar“ ein. Sonst kommen deine Befehle nur an, solange das Auto an ist.",
        "bilder": [("telegram38", "display", "Panoptes mit Musterdaten: Telegram-Meldungen, noch nicht eingerichtet, drei Schritte"), ("telegram38", "handy", "Telegram einrichten am Handy, Musterdaten")],
        "bilder_cap": "Die Seite Telegram-Meldungen in Panoptes (Musterdaten).",
        "sicher_h": "Ist das sicher?",
        "sicher": [
            ("Nur du.", "Es ist dein eigener Bot. Genau ein Telegram-Konto kann gekoppelt sein. Nachrichten von anderen beachtet der Bot nicht."),
            ("PIN.", "Die PIN gilt 10 Minuten und nur einmal. Danach holst du dir eine neue."),
            ("Schlüssel.", "Der Schlüssel bleibt verschlüsselt im Auto. Wer ihn hat, kann deinen Bot steuern. Gib ihn niemandem weiter."),
            ("Du entscheidest.", "Unter „Fernbefehle“ schaltest du einzelne Befehle aus: Wächter, Kamera, Standort, Akku, Dienste, Sicherung. Schickst du einen ausgeschalteten Befehl, sagt der Bot nur, dass er ausgeschaltet ist."),
            ("Updates.", "Nie während der Fahrt. Ab 0.1.38.8 kommen kleine Updates von selbst, wenn das Auto 10 Minuten steht. Alles andere nur so, wie du es unter Einstellungen → Alle Einstellungen → App-Updates einstellst."),
            ("Bilder.", "Schickst du Bilder oder Videos, liegen sie bei Telegram."),
            ("Notaus.", "Ab 0.1.38.8 schaltet <code>/aktionen aus</code> alle Fahrzeug-Aktionen (Hupe, Licht, Aufsperren) sofort ab. Einschalten geht nur am Auto."),
            ("Abkoppeln.", "Nur in Panoptes, unter „Bot wechseln oder entfernen“: „Anderes Telegram koppeln“ löst nur dein Konto, „Bot entfernen“ löscht auch den Schlüssel. Über Telegram selbst geht das nicht."),
        ],
    },
    "en": {
        "title": "Connect Telegram – Panoptes",
        "desc": "What Panoptes can do through Telegram and how to connect your own bot in a few minutes.",
        "zurueck": "← Back to Panoptes",
        "h1": "Connect Telegram",
        "lead": "Panoptes talks to you through your <b>own</b> Telegram bot. You create it once yourself, free and without coding. Then you pair it with a PIN. Done.",
        "kann_h": "What can Telegram do?",
        "kann": [
            ("Alerts", "Guard alarm, charging finished or a charging error, weak starter battery, tyre pressure, new updates, a short report after you park. You switch each kind on or off on its own. There are quiet hours for the night."),
            ("Menu with big buttons", "Write anything to the bot, for example “Hello”. A menu appears. From then on you just tap buttons."),
            ("Check on the car", "How is the car? Where is it? How full is the battery? Plus a camera picture and your recordings when you ask for them."),
            ("Guard and camping", "Wake the guard or let it sleep. Switch camping on or off, only while parked."),
            ("Update messages", "With “Only notify”, the bot writes “Panoptes … is here” with an “Install now” button and asks once more first. With “Small updates on their own, report big ones” (default), small updates arrive quietly once the car has been off for at least 10 minutes. Panoptes announces big ones first with a summary, and you decide. Never while driving."),
            ("Pictures and videos", "Sent automatically only if you switch on “Send pictures and videos to Telegram”. It is off by default; then you get text only."),
        ],
        "nicht_h": "What deliberately does not work",
        "nicht": "Through Telegram you <b>cannot</b> unlock or lock the car. Climate, horn, lights, windows and starting or stopping charging do not work either. You can look at pet mode, but not switch it on or off.",
        "menue_h": "What the menu looks like",
        "menue_lead": "A sketch, not a real chat. Buttons for commands you switched off are not shown at all.",
        "menue": ["How is the car?", "Guard", "Where is it?", "Camera picture", "Recordings", "Battery", "Updates", "More"],
        "menue_mehr": "Under “More”: camping, pet in the car, link to Panoptes, services, back up settings, help.",
        "schritte_h": "How to connect it",
        "vorher": "You need Telegram on your phone and Panoptes in the car. You enter the key in the Panoptes interface, on the car screen or on a PC. Setting up does not work if you signed in on your phone via Telegram.",
        "schritte": [
            ("Open the page.", "In Panoptes: <b>Rules → Alerts → Telegram alerts</b>. It says “Not set up yet” and shows three steps."),
            ("Create a bot.", "In Telegram, open the chat with <b>@BotFather</b>, Telegram’s official account with the blue tick. Send it <code>/newbot</code>. Enter a name, for example <code>My car</code>. Then a username ending in <code>bot</code>."),
            ("Paste the key.", "BotFather replies with a long key that looks like <code>123456789:AAH…</code>. Copy it, paste it into Panoptes and tap <b>“Check and save”</b>."),
            ("Get the PIN.", "Tap <b>“Start pairing”</b>. Panoptes shows a 6-digit PIN."),
            ("Pair.", "On your phone, tap <b>“Open in Telegram and tap ‘Start’”</b>. If the link does not work, send the bot <code>/pair</code> and your PIN, for example <code>/pair 123456</code>."),
            ("Done.", "The bot replies “Paired!”. Panoptes notices this by itself. Use <b>“Send a test message”</b> to check that everything arrives."),
        ],
        "tipp": "<b>Tip:</b> Switch on “Reachable while the car is off”. Otherwise your commands only arrive while the car is on.",
        "bilder": [("telegram38", "display", "Panoptes with sample data: Telegram alerts, not set up yet, three steps"), ("telegram38", "handy", "Setting up Telegram on a phone, sample data")],
        "bilder_cap": "The Telegram alerts page in Panoptes (sample data, shown in German).",
        "sicher_h": "Is it safe?",
        "sicher": [
            ("Only you.", "It is your own bot. Exactly one Telegram account can be paired. The bot ignores messages from anyone else."),
            ("PIN.", "The PIN is valid for 10 minutes and only once. After that you get a new one."),
            ("Key.", "The key stays encrypted in the car. Anyone who has it can control your bot. Never share it."),
            ("You decide.", "Under “Remote commands” you switch off single commands: guard, camera, location, battery, services, backup. If you send a switched-off command, the bot only tells you it is switched off."),
            ("Updates.", "Never while driving. From 0.1.38.8 small updates install by themselves once the car has been parked for 10 minutes. Everything else only the way you set it under Settings → All settings → App updates."),
            ("Pictures.", "If you send pictures or videos, they are stored at Telegram."),
            ("Emergency off.", "From 0.1.38.8, <code>/aktionen aus</code> turns off all vehicle actions (horn, lights, unlocking) at once. Switching them on only works in the car."),
            ("Unpair.", "Only in Panoptes, under “Change or remove the bot”: “Pair a different Telegram” only unlinks your account, “Remove bot” also deletes the key. You cannot do this from Telegram itself."),
        ],
    },
}

TG_CSS = """<style>
.tgk{display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:14px;margin:14px 0}
.tgk .card{margin:0}.tgk h3{margin:0 0 6px;font-size:19px}.tgk p{margin:0}
ol.tgs{list-style:none;counter-reset:s;padding:0;margin:14px 0}
ol.tgs li{counter-increment:s;position:relative;padding:4px 0 14px 58px;margin:0;font-size:18px;line-height:1.55}
ol.tgs li::before{content:counter(s);position:absolute;left:0;top:0;width:40px;height:40px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-weight:800;font-size:20px;background:var(--accent-2,#c6f24e);color:#0b1620}
.tgm{max-width:420px;border:1px solid var(--line);border-radius:18px;padding:14px;background:var(--card)}
.tgm .tgq{margin:0 0 10px;color:var(--muted)}
.tgm .tgb{display:grid;grid-template-columns:1fr 1fr;gap:8px}
.tgm span{display:block;text-align:center;padding:12px 8px;border-radius:12px;border:1px solid var(--line);background:var(--card2);font-weight:600}
ul.tgsi{list-style:none;padding:0;margin:14px 0}ul.tgsi li{padding:10px 0;border-bottom:1px solid var(--line);font-size:18px;line-height:1.5}
.tgnicht{border-left:4px solid var(--accent-2,#c6f24e)}
</style>"""


def telegram_seite(t):
    de = t["lang"] == "de"
    g = TG[t["lang"]]
    kanon = BASIS + ("" if de else "en/") + "telegram.html"
    andere = "/panoptes/en/telegram.html" if de else "/panoptes/telegram.html"
    o = [kopf(t, g["title"], g["desc"], BASIS + "telegram.html", BASIS + "en/telegram.html", kanon,
              "/panoptes/" if de else "/panoptes/en/", andere)]
    o.append(TG_CSS)
    o.append('  <p style="margin:18px 0 0"><a href="./">%s</a></p>' % g["zurueck"])
    o.append('  <h1 style="font-size:clamp(30px,5vw,44px)">%s</h1><p class="lead">%s</p>' % (g["h1"], g["lead"]))
    o.append('  <h2 id="kann">%s</h2>\n  <div class="tgk">' % g["kann_h"])
    for h, txt in g["kann"]:
        o.append('    <div class="card"><h3>%s</h3><p>%s</p></div>' % (h, txt))
    o.append('  </div>\n  <div class="card tgnicht"><h3 style="margin:0 0 6px">%s</h3><p style="margin:0">%s</p></div>' % (g["nicht_h"], g["nicht"]))
    o.append('  <h2 id="menue">%s</h2><p>%s</p>\n  <div class="tgm" role="img" aria-label="%s"><p class="tgq">%s</p><div class="tgb">%s</div></div><p>%s</p>'
             % (g["menue_h"], g["menue_lead"], html.escape(g["menue_h"]), "Was möchtest du tun?" if de else "What would you like to do?",
                "".join("<span>%s</span>" % html.escape(b) for b in g["menue"]), g["menue_mehr"]))
    o.append('  <h2 id="verbinden">%s</h2><p>%s</p>\n  <ol class="tgs">' % (g["schritte_h"], g["vorher"]))
    for h, txt in g["schritte"]:
        o.append("    <li><b>%s</b> %s</li>" % (h, txt))
    o.append('  </ol>\n  <div class="card">%s</div>' % g["tipp"])
    o.append('  <figure style="margin:18px 0">%s<figcaption>%s</figcaption></figure>' % (reihe(g["bilder"], t["pfad"]), g["bilder_cap"]))
    o.append('  <h2 id="sicher">%s</h2>\n  <ul class="tgsi">' % g["sicher_h"])
    for h, txt in g["sicher"]:
        o.append("    <li><b>%s</b> %s</li>" % (h, txt))
    o.append("  </ul>")
    o.append(fuss(t, andere))
    return "\n".join(o)


# Unterseite „Panoptes Launcher“ (04.11.2026). Fakten nur aus Code v0.1.38.6 und Release-Notizen (Belege: LAUNCHER_FAKTEN.md).
LNC = {
    "de": {
        "title": "Panoptes Launcher – Panoptes",
        "desc": "Der Panoptes Launcher: eigener Startbildschirm im Auto mit Klima, Komfort und Apps. Was er kann, wie du ihn installierst und wie du zurückkommst.",
        "h1": "Panoptes Launcher",
        "lead": "Ein eigener Startbildschirm für den Bildschirm in deinem Auto, im Panoptes-Stil. Er läuft als eigene App neben dem BYD-Startbildschirm, auf Wunsch auch als Startbildschirm. Er ist freiwillig und braucht Panoptes.",
        "kann_h": "Was kann der Launcher?",
        "kann": [
            ("Seiten mit Kacheln", "Akku und Reichweite, Navigation, Musik, Wächter, Uhr und deine Apps auf einen Blick. Kacheln kannst du verschieben und vergrößern."),
            ("Leiste unten", "Haus-Knopf, Panoptes, deine Lieblings-Apps, Klima, alle Apps und Einstellungen. Immer am gleichen Platz."),
            ("Klima in der Leiste", "Temperatur und Gebläse mit Plus und Minus, dazu An und Aus. Bei manchen Autos zeigt er Stufen wie „Heizen 2“, „Neutral“ oder „Kühlen 1“."),
            ("Komfort", "Tipp auf „Komfort: Sitze, Lenkrad, Entfrosten“: Sitzheizung und Sitzlüftung für Fahrer und Beifahrer, Lenkradheizung, Umluft oder Frischluft, Front- und Heckscheibe entfrosten. Nur, soweit dein Auto das meldet. Kann Panoptes einen Wert nicht lesen, wird nichts geraten."),
            ("Apps nebeneinander", "Spotify und andere Medien-Apps öffnen neben dem Launcher. Geht nebeneinander nicht, öffnet die App im Vollbild."),
            ("Bequem einrichten", "Am Auto im Stand, in der Panoptes-Oberfläche unter „Launcher einrichten“ oder am PC im EV-Cockpit ab 1.23."),
        ],
        "bilder": [("launcher386", "display", "Panoptes Launcher mit Musterdaten: Akku 86 Prozent, 262 km, Navigation in 40 km Ziel Wien, Wächter an, Uhr, unten die Leiste mit Haus-Knopf und Klima")],
        "bilder_cap": "Der Launcher mit Musterdaten, zweite Seite. Kein echtes Auto.",
        "inst_h": "So installierst du ihn",
        "inst_vorher": "Du brauchst Panoptes im Auto. Den Launcher holst du direkt aus Panoptes, du musst nichts herunterladen.",
        "inst": [
            ("Panoptes öffnen.", "Am Bildschirm im Auto: <b>Apps &amp; Display → Display</b>."),
            ("Installieren.", "In der Karte <b>„Panoptes Launcher“</b> auf <b>„Installieren und aktivieren“</b> tippen. Ohne WLAN fragt Panoptes vorher, ob es über mobile Daten laden darf."),
            ("Öffnen.", "Danach steht dort <b>„Öffnen“</b>. Der Launcher startet."),
            ("Updates.", "Gibt es eine neue Version, steht in der Karte <b>„Aktualisieren“</b>. Das geht auch über Telegram, das Handy oder das EV-Cockpit, nur wenn du es erlaubst."),
        ],
        "inst_nb": "Installieren und Entfernen gehen nur am Auto, nicht aus der Ferne, und nie während der Fahrt.",
        "zur_h": "Zurück zum BYD-Bildschirm",
        "zur": [
            ("Haus-Knopf.", "Das Haus ganz links in der Leiste führt immer zurück zum BYD-Startbildschirm. Es lässt sich nicht entfernen."),
            ("Als Startbildschirm.", "Ab 0.1.38.7 gibt es dafür einen Schalter, ab Werk aus. Schaltest du ihn ein, fragt der Launcher „Panoptes Launcher als Startbildschirm?“. Mit „Ja, behalten“ öffnet die Home-Taste den Launcher, mit „Nein, zurück zu BYD“ bleibt alles, wie es war. Von selbst stellt Panoptes nichts um."),
            ("Entfernen.", "In Panoptes unter Apps &amp; Display → Display in der Karte „Panoptes Launcher“ auf „Entfernen“ tippen. Dein Launcher-Layout geht dabei verloren."),
        ],
        "nicht_h": "Was noch nicht geht",
        "nicht": [
                        "Die Temperatur ist nicht bei jedem Modell bestätigt. Dann gehen Gebläse und An und Aus trotzdem.",
            "Nebeneinander klappt nicht mit jeder App; dann öffnet sie im Vollbild.",
            "Fehlt ein Wert, zeigt er einen Strich. Er rät nichts.",
        ],
        "sicher": "<b>Beim Fahren:</b> Bearbeiten geht nur im Stand (Gang P). Video-Apps startet er nur in P, außer du hast in Panoptes den Hinweis „Verstanden, ich entscheide selbst“ bestätigt.",
        "erprobt": "Erprobt vor allem auf einem BYD Dolphin Surf (DiLink 3). Auf anderen Modellen kann manches fehlen oder anders sein.",
    },
    "en": {
        "title": "Panoptes Launcher – Panoptes",
        "desc": "The Panoptes Launcher: your own home screen in the car with climate, comfort and apps. What it does, how to install it and how to get back.",
        "h1": "Panoptes Launcher",
        "lead": "Your own home screen for the screen in your car, in the Panoptes style. It runs as a separate app next to the BYD home screen, or as your home screen if you want. It is optional and needs Panoptes.",
        "kann_h": "What can the launcher do?",
        "kann": [
            ("Pages with tiles", "Battery and range, navigation, music, guard, clock and your apps at a glance. You can move and resize tiles."),
            ("Bar at the bottom", "Home button, Panoptes, your favourite apps, climate, all apps and settings. Always in the same place."),
            ("Climate in the bar", "Temperature and fan with plus and minus, plus on and off. On some cars it shows heating and cooling levels instead of degrees."),
            ("Comfort", "Tap “Comfort: seats, steering wheel, defrost”: seat heating and seat ventilation for driver and passenger, steering wheel heating, recirculation or fresh air, defrost front and rear window. Only as far as your car reports it. If Panoptes cannot read a value, it does not guess."),
            ("Apps side by side", "Spotify and other media apps open next to the launcher. If side by side is not possible, the app opens full screen."),
            ("Easy to set up", "In the car while parked, in the Panoptes interface under “Set up launcher”, or on your PC in the EV Cockpit from 1.23."),
        ],
        "bilder": [("launcher386", "display", "Panoptes Launcher with sample data: battery 86 percent, 262 km, navigation in 40 km to Vienna, guard on, clock, bottom bar with home button and climate")],
        "bilder_cap": "The launcher with sample data, second page, shown in German. Not a real car.",
        "inst_h": "How to install it",
        "inst_vorher": "You need Panoptes in the car. You get the launcher straight from Panoptes, there is nothing to download yourself.",
        "inst": [
            ("Open Panoptes.", "On the car screen: <b>Apps &amp; display → Display</b>."),
            ("Install.", "In the <b>“Panoptes Launcher”</b> card, tap <b>“Install and activate”</b>. Without Wi-Fi, Panoptes asks first whether it may use mobile data."),
            ("Open.", "Afterwards the card shows <b>“Open”</b>. The launcher starts."),
            ("Updates.", "When there is a new version, the card shows <b>“Update”</b>. This also works via Telegram, your phone or the EV Cockpit, only if you allow it."),
        ],
        "inst_nb": "Installing and removing only work in the car, not remotely, and never while driving.",
        "zur_h": "Back to the BYD screen",
        "zur": [
            ("Home button.", "The house icon on the far left of the bar always leads back to the BYD home screen. It cannot be removed."),
            ("As home screen.", "From 0.1.38.7 there is a switch for this, off by default. If you switch it on, the launcher asks “Use Panoptes Launcher as home screen?”. With “Yes, keep” the Home key opens the launcher, with “No, back to BYD” everything stays as it was. Panoptes never switches anything by itself."),
            ("Remove.", "In Panoptes under Apps &amp; display → Display, tap “Remove” in the “Panoptes Launcher” card. Your launcher layout is lost."),
        ],
        "nicht_h": "What does not work yet",
        "nicht": [
                        "Temperature control is not confirmed for every model. Fan and on/off still work.",
            "Side by side does not work with every app; it then opens full screen.",
            "If a value is missing, it shows a dash. It does not guess.",
        ],
        "sicher": "<b>While driving:</b> editing only works while parked (gear P). Video apps only start in P, unless you confirmed the notice “Verstanden, ich entscheide selbst” (I understand, I decide myself) in Panoptes.",
        "erprobt": "Tested mainly on a BYD Dolphin Surf (DiLink 3). On other models some things may be missing or different.",
    },
}


def launcher_seite(t):
    de = t["lang"] == "de"
    g = LNC[t["lang"]]
    kanon = BASIS + ("" if de else "en/") + "launcher.html"
    andere = "/panoptes/en/launcher.html" if de else "/panoptes/launcher.html"
    o = [kopf(t, g["title"], g["desc"], BASIS + "launcher.html", BASIS + "en/launcher.html", kanon,
              "/panoptes/" if de else "/panoptes/en/", andere)]
    o.append(TG_CSS)
    o.append('  <p style="margin:18px 0 0"><a href="./">%s</a></p>' % TG[t["lang"]]["zurueck"])
    o.append('  <h1 style="font-size:clamp(30px,5vw,44px)">%s</h1><p class="lead">%s</p>' % (g["h1"], g["lead"]))
    o.append('  <figure style="margin:18px 0">%s<figcaption>%s</figcaption></figure>' % (reihe(g["bilder"], t["pfad"], sofort=True), g["bilder_cap"]))
    o.append('  <h2 id="kann">%s</h2>\n  <div class="tgk">' % g["kann_h"])
    for h, txt in g["kann"]:
        o.append('    <div class="card"><h3>%s</h3><p>%s</p></div>' % (h, txt))
    o.append("  </div>")
    o.append('  <h2 id="installieren">%s</h2><p>%s</p>\n  <ol class="tgs">' % (g["inst_h"], g["inst_vorher"]))
    for h, txt in g["inst"]:
        o.append("    <li><b>%s</b> %s</li>" % (h, txt))
    o.append('  </ol>\n  <div class="card">%s</div>' % g["inst_nb"])
    o.append('  <h2 id="zurueck">%s</h2>\n  <ul class="tgsi">' % g["zur_h"])
    for h, txt in g["zur"]:
        o.append("    <li><b>%s</b> %s</li>" % (h, txt))
    o.append("  </ul>")
    o.append('  <h2 id="noch-nicht">%s</h2>\n  <ul class="tgsi">%s</ul>' % (g["nicht_h"], "".join("<li>%s</li>" % x for x in g["nicht"])))
    o.append('  <div class="card tgnicht">%s</div><p>%s</p>' % (g["sicher"], g["erprobt"]))
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
        for name, inhalt in (("index.html", seite(t)), ("hinweise.html", hinweise(t)), ("telegram.html", telegram_seite(t)), ("launcher.html", launcher_seite(t))):
            with open(os.path.join(ZIEL, unter, name), "w", encoding="utf-8", newline="\n") as f:
                f.write(inhalt)
    print("ok:", n, "Bilder, 8 Seiten in", ZIEL)


if __name__ == "__main__":
    if "--vorschau" in sys.argv:
        VORSCHAU = '\n<meta name="robots" content="noindex, nofollow">'
    main(sys.argv[1])
