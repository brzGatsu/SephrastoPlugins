# SephrastoPlugins
Dieses Repo ist die offizielle Plugin-Quelle für den Ilaris-Charaktergenerator Sephrasto. Plugins und andere Beiträge von anderen Entwicklern sind gerne gesehen, kontaktiert mich einfach auf dem Ilaris Tools Discord.

## Installationsanleitung

1. Öffne Sephrastos Einstellungen über den Zahnrad-Button im Startfenster.
2. Wechsle auf den Tab Plugins
3. Wähle das gewünschte Plugin aus und clicke auf "Installieren".
4. Starte Sephrasto neu.

### Sephrasto vor Version 4.4
1. Clicke auf github rechts auf "Releases".
2. Suche den passenden Download für deine Sephrastoversion und lade die Zipdatei unter "Assets" herunter.
3. Starte Sephrasto, gehe in die Einstellungen und notiere dir den Speicherpfad für Plugins
4. Entpacke die gewünschten Plugins aus der heruntergeladenen Zipdatei in den Plugins-Speicherpfad. Falls du noch eine ältere Version der gewünschten Plugins installiert hast, lösche diese zuerst.

## Plugins

### CharakterAssistent
Enthält einen Baukasten mit WdH Spezies, Kulturen und Kämpferprofessionen für Ilaris Advanced

### CharakterToText
Das Plugin sorgt dafür, dass beim beim Speichern des Charakters zusätzlich eine Textdatei im gleichen Ordner angelegt wird. Diese Textdatei enthält alle Charakterwerte in leicht zu kopierendem Format. Ich nutze es beispielsweise, um ein digitales Charaktersheet in Form von Trello-Karten zu befüllen.

### Drachentöter Kampfregeln
Dieses Plugin installiert die Hausregeln des Drachentöter Kampfregelwerks für Ilaris. Weitere Infos findest du auf <a href="https://dsaforum.de/viewtopic.php?t=59615">dsaforum.de</a> und dem <a href="https://discord.gg/AF3WjqvMU9">Drachentöter Discord Server</a>.

### FertigkeitenPlus
Dieses Plugin bietet bei Fertigkeiten die Möglichkeit, ein viertes Attribut anzugeben. Berechnungen für den Basiswert verwenden dann nur die 3 höchsten Attribute (siehe angepasste Einstellung "Fertigkeiten: BW Script").

### FoundryVTT
Wenn das Plugin aktiv ist, wird beim Speichern des Helden neben der `<name>.xml` automatisch eine zweite Datei `<name>_foundryvtt_<version>.json` erstellt, die in Foundry als Held importiert werden kann. Die Zielversion kann in den Plugin-Einstellungen angepasst werden. Foundry-Token der Helden können nicht zurück nach Sephrasto importiert werden. Die `.xml`-Datei also nicht löschen!

Es werden nur die für FoundryVTT relevanten Informationen in der `.json`-Datei gespeichert und auch hier gibt es noch einige Einschränkungen. Folgendes wird NICHT übertragen:

- Geld
- Zustände: Wunden, Furcht, Boni/Mali etc.
- Status von Waffen/Rüstungen (in/aktiv, haupthand/nebenhand, kampfstil)
- Einstellungen für Sephrasto (Welcher Bogen, Zonensystem, Regelanhänge usw..)
- Hausregeln (Eigene Vorteile, Talente usw. könnten aber funktionieren)
- Waffeneigenschaften

### Hexalogien
Ein Ilaris-Elementarmagier hat nur wenig Motivation weitere Varianten von Hexalogie-Zaubern zu erlernen, der Mehrwert ist zu gering für die Kosten. Ich biete euch hier ein Sephrasto-Plugin, das die EP-Kosten von Talenten aus elementaren Hexalogien halbiert. Der volle EP-Preis muss nur für das teuerste erlernte Talent aus der Hexalogie bezahlt werden. Diese Umsetzung basiert auf der DSA4-Regel, die Hexalogiezauber eine Spalte günstiger steigern lässt, solange man eine Variante auf höherem TaW besitzt.
Die Zauber sind über die Datenbankeinstellung "Hexalogien Plugin: Talente" konfigurierbar. Standardmäßig beinhaltet sind alle bestätigten Hexalogien gemäß https://de.wiki-aventurica.de/wiki/Hexalogie (nicht die vermuteten), zusätzlich noch die Herbeirufung und Macht des <Elements> Zauber. Prinzipiell können auch andere Zauber eingetragen werden, die bspw. keine Elementarzauber sind. Beispielsweise der Reptilea und der Arachnea.

### Historie
In der Historie werden Änderungen des Charakters in Textform gespeichert. Über einen Extra-Tab im Charakter-Editor lässt sich der EP Verlauf und die Änderungen von übernatürlichen, freien und profanen Fertigkeiten und Talenten, Eigenheiten, Zaubern, Vorteilen und Attributen nach verfolgen. Das Inventar und Beschreibungen, die nicht ausschlaggebend für die Generierung sind, werden nicht aufgezeichnet.

Aus dem aufgezeichneten Verlauf ist es nicht möglich alte Versionen des Charakters wieder herzustellen. Zu diesem Zweck bietet das Plugin jedoch die Möglichkeit automatische Backups nach EP-Stand oder Datum anzulegen. Verschiedene Dateien können mit dem charakter_diff-Makro verglichen werden.

### Kreaturen
Mit dem Kreaturen Plugin können neben Charakteren auch Kreaturen als Gegner oder NSCs erstellt werden. Die Generierung ist weniger kompliziert und folgt keinen Regeln. Fertige Kreaturen können als Statblock exportiert oder mit dem IlarisOnline Plugin auf ilaris-online.de veröffentlicht werden.

### Manoeverkarten
Das Plugin gibt im Charaktereditor den Regelanhang eines Charakters und im Datenbankeditor die ganze Sephrastodatenbank in Manöverkarten aus. Im Datenbankeditor erscheint außerdem ein zusätzliches Datenbankelement "Manöverkarte" mit dem eigene Karten erstellt und automatisch generierte Karten angepasst werden können. Eine Anleitung kann im Hilfemenu des Datenbankeditors gefunden werden.

### RuestungenPlus
Dieses Plugin teilt die drei Rüstungen auf jeweils eigene Tabs auf. Dort werden sie nach Slots (wie Arme und Kopf) aufgeteilt, sodass einzelne Rüstungsteile besser verwaltet werden können. Im Charakterbogen erscheinen aus Platzmangel weiterhin nur die berechneten kompletten Rüstungen, die Einzelteile können aber im Regelanhang ausgegeben werden: Hierzu musst du in der Datenbankeinstellung 'Regelanhang: Reihenfolge' an der gewünschten Position (z.B. nach 'W') ein 'R' einfügen.
Wenn du die Option 'Rüstungseigenschaften' aktivierst, kannst du zusätzlich im Datenbankeditor Rüstungseigenschaften anlegen, optional mit Scripts versehen und Slots zuweisen.

### SephMakro
SephMakro bietet eine einfache Art, Abfragen oder Analysen der Datenbank oder von Charakteren durchzuführen. Die Einstiegshürde ist deutlich niedriger, als für jede noch so kleine Abfrage ein eigenes Plugin schreiben zu müssen. Durch die Verfügbarkeit von Datenbank und Charakteren in Form der Sephrasto-Datenstrukturen können diese schneller und einfacher durchgeführt werden als wenn erst einmal die XML-Dateien geparst werden müssten. Makros sind aber keine Grenzen gesetzt, es können beispielsweise auch Charaktere verändert und gespeichert werden. Für das Nutzen von vorgefertigten Makros benötigst du in der Regel keine Programmierkenntnisse.

Features:
- Enthält einen Code-Editor mit Zeilen-Anzeige und Syntax-Highlighting. Der Editor hat auch eine rudimentäre Autocomplete-Funktion, die allerdings keinen Kontext kennt.
- Alle Sephrasto-Python-Files können importiert werden, ihr könntet mit einem Makro theoretisch sogar den Charaktereditor nachprogrammieren.
- Der print output und eventuelle Fehler wird direkt in einem Textfeld angezeigt. 
- Auf die Datenbank kannst du direkt über die globale Variable "datenbank" zugreifen. Sie hat für jedes Datenbankelement ein dict<name, objekt> als Attribut. So kannst du beispielsweise mit datenbank.vorteile["Achaz"] an das Objekt des Vorteils "Achaz" gelangen. Die Struktur der Datenbankobjekte kannst du hier nachschlagen: https://github.com/Aeolitus/Sephrasto/tree/master/src/Sephrasto/Core.
- Außer Sephrasto und diesem Plugin wird nichts benötigt!

#### SephMakroScripts
Hier findest du einige nützliche scripts für Sephmakro.
- charakter_diff: Das Makro gibt den Unterschied zwischen zwei Charakterversionen aus. Die Idee ist, dass ihr nach jedem Steigern eine neue Datei für euren Charakter anlegt - mit diesem Makro erhaltet ihr dann eine Historie.
- drachentoeter_simulator: Dies ist eine Simulation für die Drachentöter-Kampfregeln hauptsächlich zum Testen des Balancings. Drachentöter kann hier gefunden werden: https://dsaforum.de/viewtopic.php?t=59615
- fertigkeiten_sf: Rechnet bei allen Fertigkeiten für alle Traditionen die Talentkosten zusammen, bildet den Durchschnitt und gibt den Steigerungsfaktor gemäß Ilaris Blog aus. Passive Talente werden ignoriert (da PW-unabhängig) und Traditionen mit 100 oder weniger investierbaren EP werden ignoriert. Es gibt hier einige Einstellungsmöglichkeiten direkt am Anfang des Makros.
- inselfertigkeiten: Das Makro betrachtet für jede Tradition alle Fertigkeiten, deren Talent-Gesamt-EP unter 121 liegen. Dann inspiziert es jedes Talent dieser Fertigkeiten und prüft, ob es mit einer anderen Fertigkeit oberhalb der EP-Schwelle wirkbar ist. Wird ein Talent gefunden, bei dem das nicht der Fall ist, wird es zusammen mit seiner "Inselfertigkeit" ausgegeben. Passive Talente werden ignoriert (da PW-unabhängig). Es gibt hier einige Einstellungsmöglichkeiten direkt am Anfang des Makros
- talent_seitenzahlen_update: Das Makro aktualisiert die Seitenzahl-Angaben von übernatürlichen Talenten in der Sephrasto-Datenbank. Dazu werden die Lesezeichen einer gewählten PDF-Datei ausgewertet. Diese müssen exakt gleich, wie die Talente heißen. PDFs ohne Talentnamen in den Lesezeichen werden nicht unterstützt!
- template_db_batch_update: Mit diesem Template können Elemente der in SephMakro aktivierten Datenbank massenhaft per code bearbeitet werden. Am Ende wird die Datenbank überspeichert, also besser vorher eine Sicherheitskopie machen.
- waffenbewerter: Das Makro geht durch alle Waffen in der Datenbank und wendet ein Punkteschema an (ähnlich wie hier: https://dsaforum.de/viewtopic.php?f=180&t=56989&p=2012837#p2012837), wodurch Waffen besser verglichen werden können. Das hilft insbesondere dabei, eigene Waffenkreationen zu balancen. Das Standard-Bewertungsschema habe ich nach bestem Gewissen erstellt, ich erhebe keinen Anspruch auf Richtigkeit, das kann nur Curthan :D. Das Schema ist sehr einfach komplett einstellbar in der Settings-Sektion.
- zufälligeZauber: Das Makro würfelt auf die Verbreitungsangabe aller Zauber für eine angegebene Tradition.
- zufälligeZauberNumpy: Wie zufälligeZauber mit etwas anderer Wahrscheinlichkeitsverteilung, aber benötigt Python und das Paket Numpy.

### Tierbegleiter
Dieses Plugin erlaubt das Erstellen von Tierbegleitern entsprechend des Ilaris Bestiariums und das Exportieren in den enthaltenen Tierbegleiterbogen. Optional können in der Regelbasis mittels der Einstellung "Tierbegleiter Plugin: IA Zucht und Ausbildung" die Ilaris Advanced Regeln zu Zucht und Ausbildung aktiviert werden (zusammen mit speziell angepassten Tierwerten).

### WaffenPlus
Dieses Plugin schafft einige Anpassungsmöglichkeiten für Waffen:
- Zeigt im Waffen-Tab des Charaktereditors und im Datenbank-Waffeneditor zwei statt nur einem WM Feld an - eines für die AT und eines für die VT. Wichtig: Wenn du die Einstellung "Waffen: Waffenwerte Script" modifiziert hast, musst du dort händisch bei "vt = ..." waffe.wm durch waffe.wmVt ersetzen.
- Support für optionale Waffeneigenschaften, indem sie mit '(\*)' am Ende des Namens markiert werden; Beispiel: die Streitaxt erhält die Eigenschaft Rüstungsbrechend (\*). Diese Markierung muss im Charaktereditor entfernt werden, ansonsten wird die Eigenschaft nicht auf dem Charakterbogen ausgegeben.
- In den Hausregeln können bestimmte Waffeneigenschaften via 'WaffenPlus Plugin: Waffeneigenschaften Gruppieren' in der PDF separat gruppiert werden. Dies kann beispielsweise genutzt werden, um bestimmte Waffeneigenschaften als Angriffsarten herauszuheben (siehe IA).

Diese Features können in den Hausregeln über diverse 'WaffenPlus Plugin' Einstellungen deaktiviert werden.

### Zaubertricks
Das Plugin sorgt dafür, dass die Zaubertricks-Fertigkeit aus WeZwanzigs Hausregeln und Ilaris Advanced nicht steigerbar ist und auch im Seitenpanel entsprechend angezeigt wird. Außerdem trägt es im Charakterbogen beim PW einen Strich ein. Achtung: Das Plugin enthält keine Hausregeldatenbank mit den entsprechenden Zaubertricks, beziehe diese bitte von WeZwanzig oder Ilaris Advanced.

## Templates für Plugin-Entwickler

### DBToText
Das Plugin kann als Template für Datenbankexporter dienen. Es speichert die Datenbank in einer Textdatei.