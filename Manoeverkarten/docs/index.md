# Manöverkarten Plugin
Du hast zwei Möglichkeiten, um Manöverkartendecks zu erstellen:
1. Export im Charaktereditor: Mit einem Klick auf "Manöverkarten erstellen" unten rechts erscheint der Exportdialog. Selbst wenn du alles auswählst werden hier nur die Karten exportiert, die für deinen Charakter relevant sind - ähnlich dem Regelanhang.
2. Export im Regeleditor: Mit einem Klick auf "Export->Manöverkarten" in der oberen Menuleiste erscheint der Exportdialog mit welchem du die gesamte Datenbank in Kartenform exportieren kannst.
  
Wie die Karten zu den unterschiedlichen Decks zusammengeführt werden hängt - wie beim Regelanhang - von der Einstellung "Regelanhang: Reihenfolge" ab. Dabei beginnt mit jedem Titel ein neues Deck.

Manöverkarten werden **automatisch** für Vorteile, Regeln, übernatürliche Talente und Waffeneigenschaften erstellt. Im Karteneditor kannst du eine **neue Karte** erstellen, die nicht im regulären Regelanhang auftauchen soll. Alternativ kannst du die automatisch generierte Karten hier **anpassen** oder **löschen**. Hierzu muss der Name der Karte identisch zu einem existierenden Vorteil etc. sein.

## Das $original$ Makro
Bei allen Feldern kannst du das Makro **$original$** eintragen, um den ursprünglichen Text einzusetzen; davor und danach kannst du zusätzlichen Inhalt einfügen. Bei neuen Karten funktioniert das Makro allerdings nur bei der Fußzeile - dabei wird in der Regel der Subtyp eingesetzt.

## Der Typ "Deck" und "Benutzerdefiniert"
Diese beiden Kartentypen werden hauptsächlich verwendet, um eigene Decks zu erstellen. Das funktioniert wie folgt:
- Erstelle zunächst eine Karte vom Typ "Deck" und gib ihr einen passenden Namen. Dies wird die Titelkarte für das Deck - in der Vorschau kannst du bereits sehen, dass sie ein etwas anderes Layout hat. Als nächstes kannst du eine Deckfarbe festlegen und in der Beschreibung beispielsweise ein Bild einfügen.
- Sobald du die Karte erstellt hast, kannst du weitere Karten vom Typ "Benutzerdefiniert" erstellen und dort dieses Deck als Subtyp auswählen. Wenn du dann die Manöverkarten exportieren möchtest, wirst du das Deck als auswählbaren Eintrag sehen.
  
**Wichtig:** Wie oben erwähnt werden für jeden Titel in der Einstellung "Regelanhang: Reihenfolge" automatisch Decks erstellt. Die Titelkarten dieser Decks können angepasst werden, indem eine Karte vom Typ "Deck" erstellt wird, deren Name dem Titel aus der Einstellung entspricht. Das Manöverkartenplugin kommt bereits mit vorkonfigurierten Titelkarten für Sephrastos Standardeinstellungen.