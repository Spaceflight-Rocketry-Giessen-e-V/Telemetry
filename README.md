# ASCENT II Experimentalraketen-Telemetriesystem

<img src="https://github.com/Spaceflight-Rocketry-Giessen-e-V/Telemetrie/blob/main/onboard/pcb/Telemetrie%20v2.png" width="400">

## 868 MHz Telemetriesystem mit einer Reichweite >10 km für den bidirektionalen Datenaustausch zwischen einer Experimentalrakete und einer Bodenstation

Das Telemetriesystem ist Teil des ASCENT II Flugcomputers des studentischen Raketenbauvereins Spaceflight Rocketry Gießen e.V., der für die ARCHER Experimentalrakete entwickelt wird.
Mit diesem System kann der ASCENT II Flugcomputer Sensor- und Statusdaten in hoher Quantität an die Bodenstation übertragen sowie zuverlässig Telekommandos empfangen und ausführen.

### Features

- 868 MHz Radio Transceiver
- Mindestens 18 km Reichweite
- Mindestens 1,2 kbps Datenrate
- Auf Anforderungen angepasste QFH-Antenne
- L-Netzwerk zur Anpassung der Antenne
- Software mit eigener Befehlsbibliothek

## Dokumentation

Informationen zum theoretischen Hintergrund, den verwendeten Bauteilen und mehr findet man [hier](docs/literatur.md).

Links zu den von uns verwendeten Softwarelösungen sind [hier](docs/apps.md) aufgelistet.

Die Dokumentation zur Software inklusive der Befehlsbibliothek ist [hier](docs/documentation.md) zu finden.

## Verwendung

### Repository lokal klonen:
- Git herunterladen und installieren: [Download](https://git-scm.com/downloads)
- Git CMD öffnen (z.B. über Windows Suche)
- Git Username und Email konfigurieren
```
git config --global user.name "Vorname Nachname"
git config --global user.email "Mailadresse"
```
- Repository lokal klonen
```
cd Ordnerpfad
git clone https://github.com/Spaceflight-Rocketry-Giessen-e-V/Telemetry
```
### Dateien bearbeiten und synchronisieren:
- Lokalen Repository Klon auf den neuesten Stand bringen
```
git pull
```
- Dateien bearbeiten/hinzufügen/löschen
- Updates online synchronisieren
```
git add Dateiname / git add --all
git commit -m "Kurze Beschreibung des Updates"
git push
```
