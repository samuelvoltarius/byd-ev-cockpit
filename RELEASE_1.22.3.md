# EV-Cockpit 1.22.3 – vorbereiteter Patchrelease

Stand: 1. November 2026. Dieser Stand ist lokal vorbereitet und noch nicht
gepusht, getaggt oder veröffentlicht.

## Änderungen

### Deutsch

- Der gemeinsame Fahrzeugkatalog steht auf Version 17. Der BYD Seal 6 DM-i
  Touring ist ein eigenständiges Kombi-Modell und kein Alias des Seal U DM-i.
- Solange kein rechtlich nutzbares 3D-Asset vorliegt, verwendet das Cockpit für
  den Seal 6 Touring bewusst die neutrale 2D-Silhouette statt eines falschen
  Fahrzeugmodells.
- Ein lokal bereits validierter Katalog v17 bleibt nach Ablauf der normalen
  Cachezeit bei Netz-, JSON- oder älteren Katalogantworten offline nutzbar. Das
  Cockpit kennzeichnet diesen Zustand und versucht die Aktualisierung später
  erneut.
- Ein absichtlich nicht verfügbares 3D-Modell wird als stabiler Fallback
  behandelt und löst keine irreführende Download-Warnung oder Retry-Schleife aus.

### English

- The shared vehicle catalogue is now version 17. The BYD Seal 6 DM-i Touring
  is a distinct estate model and is not aliased to the Seal U DM-i.
- Until a legally usable 3D asset is available, the cockpit deliberately uses
  the neutral 2D silhouette instead of showing the wrong vehicle model.
- A locally validated v17 catalogue remains available offline after its normal
  cache lifetime when the network, JSON response, or an older catalogue refresh
  fails. The cockpit marks the state and retries the refresh later.
- An intentionally unavailable 3D model is treated as a stable fallback and no
  longer causes a misleading download warning or retry loop.

## Vorgesehene Release-Artefakte

- `ev-cockpit-windows.zip`: Cockpit mit der unveränderten eingebetteten
  Python-3.12-Laufzeit des veröffentlichten 1.22.2-Pakets und aktualisiertem
  Anwendungs-/Static-Payload.
- `ev-cockpit-linux-mac.zip`: Quellpaket mit `start.sh`.
- `ev-cockpit-linux-mac.tar.gz`: inhaltlich gleiches Quellpaket für
  Linux/macOS.

Lokale Ausgabe: `dist/1.22.3/` (die Binärarchive sind gemäß `.gitignore` keine
Git-Inhalte).

SHA-256:

- `ev-cockpit-windows.zip`:
  `666ca8e8a4def4368155e19767f2216a4d8f30ed544f32dec9c0571b2b7c0daf`
- `ev-cockpit-linux-mac.zip`:
  `daca527d7983697f1433c7d00ae6d3f1aa5bd984035c15f01bcf470acb4bd042`
- `ev-cockpit-linux-mac.tar.gz`:
  `a4340a284d4852a26a6b06541256d8548660424a6d017f69a3b8a9e55317b585`

Die Windows-Laufzeitbasis war das veröffentlichte und vor dem Entpacken
geprüfte `ev-cockpit-windows.zip` aus v1.22.2 mit SHA-256
`d0749eb25bf4323d39745cd563843dcb5183eb7d0d53fcaf72da452df6f910eb`.

Veröffentlichung und Aktivierung des bereitliegenden Update-Manifests sind
nicht Teil dieses Vorbereitungsschritts.
