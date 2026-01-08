# FoundryVTTRuleExtension Plugin

Ein Plugin für Sephrasto, das die Integration von Regeln und Manövern mit Foundry VTT erweitert.

## Features

### Manöver-Konfiguration
- Definiere Modifikatoren für Manöver (Angriff, Verteidigung, Schaden, etc.)
- Konfiguriere Eingabefelder für den Würfeldialog
- Setze Icons für visuelle Darstellung
- Spezielle Unterstützung für Verteidigungsmanöver
- Automatische Integration mit Foundry VTT's Kampfsystem

### Unterstützte Kategorien
- Nahkampfmanöver
- Fernkampfmanöver
- Magische Modifikationen
- Karmale Modifikationen
- Dämonische Modifikationen

## Verwendung

### Regel/Manöver bearbeiten
1. Öffne den Datenbankeditor
2. Wähle eine Regel/Manöver zum Bearbeiten
3. Wenn die Kategorie unterstützt wird (siehe oben), erscheint der "Foundry Regel Erweiterungen" Bereich
4. Konfiguriere die gewünschten Modifikatoren:
   - Wähle den Typ des Modifikators
   - Setze den Wert und Operator
   - Optional: Definiere ein Ziel (z.B. actor.system...)
   - Aktiviere "Durch Input beeinflusst" wenn der Modifikator durch Benutzereingaben verändert werden soll
5. Konfiguriere das Eingabefeld für den Würfeldialog (optional)
6. Setze ein Icon für die visuelle Darstellung
7. Speichere die Regel

### Manöver aktualisieren
Die Manöver-Definitionen für Vanilla Manöver (für den Fall jemand merged seine Hausregeln mit dem Regelwerk) werden in `maneuver_foundry_extensions.json` gespeichert. Ein Entwicklungsskript (`extract_maneuvers.py`) ist verfügbar, um diese aus den Foundry VTT Quelldateien zu aktualisieren.