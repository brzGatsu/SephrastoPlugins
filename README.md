# SephrastoPlugins
In diesem Repo sammle ich alle meine Plugins für den Ilaris-Charaktergenerator Sephrasto. Plugins und andere Beiträge von anderen Entwicklern sind gerne gesehen, kontaktiert mich einfach auf dem Ilaris Tools Discord.
Grundsätzlich unterstützen die Plugins immer die neueste Sephrasto-Version, ältere Versionen ohne Gewähr.

## CharakterAssistent
Enthält einen Baukasten mit WdH Spezies, Kulturen und Kämpferprofessionen für Ilaris Advanced

## CharakterToText
Das Plugin sorgt dafür, dass beim PDF-Export (ab 3.2.2 beim Speichern des Charakters) zusätzlich eine Textdatei im gleichen Ordner angelegt wird. Diese Textdatei enthält alle Charakterwerte in leicht zu kopierendem Format. Ich nutze es beispielsweise, um ein digitales Charaktersheet in Form von Trello-Karten zu befüllen.

## DBToText
Das Plugin kann als Template für Datenbankexporter dienen. Es speichert die Datenbank in einer Textdatei.

## Hexalogien
Ein Ilaris-Elementarmagier hat nur wenig Motivation weitere Varianten von Hexalogie-Zaubern zu erlernen, der Mehrwert ist zu gering für die Kosten. Ich biete euch hier ein Sephrasto-Plugin, das die EP-Kosten von Talenten aus elementaren Hexalogien halbiert. Der volle EP-Preis muss nur für das teuerste erlernte Talent aus der Hexalogie bezahlt werden. Beinhaltet sind alle bestätigten Hexalogien gemäß https://de.wiki-aventurica.de/wiki/Hexalogie (nicht die vermuteten), zusätzlich noch die Herbeirufung und Macht des <Elements> Zauber. Diese Umsetzung basiert auf der DSA4-Regel, die Hexalogiezauber eine Spalte günstiger steigern lässt, solange man eine Variante auf höherem TaW besitzt.

## Manoeverkarten
Das Plugin gibt den PDF-Regelanhang eines Charakters oder gar die ganze Sephrastodatenbank in Manöverkarten aus.

Schaut euch gerne auch die handgemachten Manöverkarten auf dsaforum.de an! Die dort enthaltenen Karten sind in der Regel übersichtlicher und besser formatiert, als der Output von diesem Plugin. Zudem findet ihr dort eine Druckanleitung für der Karten. Das Plugin hat allerdings den Vorteil, dass es auch Hausregeln, Vorteile, Zauber und Liturgien ausgeben kann.

## RuestungsnPlus
Dieses Plugin teilt die drei Rüstungen auf jeweils eigene Tabs auf. Dort werden sie nach Slots (wie Arme und Kopf) aufgeteilt, sodass einzelne Rüstungsteile besser verwaltet werden können. Im Charakterbogen erscheinen aus Platzmangel weiterhin nur die berechneten kompletten Rüstungen, die Einzelteile können aber im Regelanhang ausgegeben werden: Hierzu musst du in der Datenbankeinstellung 'Regelanhang: Reihenfolge' an der gewünschten Position (z.B. nach 'W') ein 'R' einfügen.
Wenn du die Option 'Rüstungseigenschaften' aktivierst, kannst du zusätzlich Rüstungseigenschaften anlegen, optional mit Scripts versehen und Slots zuweisen.

## SephMakro
SephMakro bietet eine einfache Art, Abfragen oder Analysen der Datenbank oder von Charakteren durchzuführen. Die Einstiegshürde ist deutlich niedriger, als für jede noch so kleine Abfrage ein eigenes Plugin schreiben zu müssen. Durch die Verfügbarkeit von Datenbank und Charakteren in Form der Sephrasto-Datenstrukturen können diese schneller und einfacher durchgeführt werden als wenn erst einmal die XML-Dateien geparst werden müssten. Makros sind aber keine Grenzen gesetzt, es können beispielsweise auch Charaktere verändert und gespeichert werden. Für das Nutzen von vorgefertigten Makros benötigst du in der Regel keine Programmierkenntnisse.

Features:
- Enthält einen Code-Editor mit Zeilen-Anzeige und Syntax-Highlighting. Der Editor hat auch eine rudimentäre Autocomplete-Funktion, die allerdings keinen Kontext kennt.
- Alle Sephrasto-Python-Files können importiert werden, ihr könntet mit einem Makro theoretisch sogar den Charaktereditor nachprogrammieren.
- Der print output und eventuelle Fehler wird direkt in einem Textfeld angezeigt. 
- Auf die Datenbank kannst du direkt über die globale Variable "datenbank" zugreifen. Alles über die Struktur der Datenbank kannst du in https://github.com/Aeolitus/Sephrasto/blob/master/Datenbank.py auf github unter "__init__" und "xmlLadenInternal" nachschlagen.
- Außer Sephrasto und diesem Plugin wird nichts benötigt!

### SephMakroScripts
Hier findest du einige nützliche scripts für Sephmakro.
- charakter_diff: Das Makro gibt den Unterschied zwischen zwei Charakterversionen aus. Die Idee ist, dass ihr nach jedem Steigern eine neue Datei für euren Charakter anlegt - mit diesem Makro erhaltet ihr dann eine Historie.
- fertigkeiten_sf: Rechnet bei allen Fertigkeiten für alle Traditionen die Talentkosten zusammen, bildet den Durchschnitt und gibt den Steigerungsfaktor gemäß Ilaris Blog aus. Passive Talente werden ignoriert (da PW-unabhängig) und Traditionen mit 100 oder weniger investierbaren EP werden ignoriert. Es gibt hier einige Einstellungsmöglichkeiten direkt am Anfang des Makros.
- inselfertigkeiten: Das Makro betrachtet für jede Tradition alle Fertigkeiten, deren Talent-Gesamt-EP unter 121 liegen. Dann inspiziert es jedes Talent dieser Fertigkeiten und prüft, ob es mit einer anderen Fertigkeit oberhalb der EP-Schwelle wirkbar ist. Wird ein Talent gefunden, bei dem das nicht der Fall ist, wird es zusammen mit seiner "Inselfertigkeit" ausgegeben. Passive Talente werden ignoriert (da PW-unabhängig). Es gibt hier einige Einstellungsmöglichkeiten direkt am Anfang des Makros
- waffenbewerter: Das Makro geht durch alle Waffen in der Datenbank und wendet ein Punkteschema an (ähnlich wie hier: https://dsaforum.de/viewtopic.php?f=180&t=56989&p=2012837#p2012837), wodurch Waffen besser verglichen werden können. Das hilft insbesondere dabei, eigene Waffenkreationen zu balancen. Das Standard-Bewertungsschema habe ich nach bestem Gewissen erstellt, ich erhebe keinen Anspruch auf Richtigkeit, das kann nur Curthan :D. Das Schema ist sehr einfach komplett einstellbar in der Settings-Sektion.

## Tierbegleiter
Dieses Plugin erlaubt das Erstellen von Tierbegleitern entsprechend des Ilaris Bestiariums und das Exportieren in den Tierbegleiterbogen (bereits enthalten). Optional können in der Regelbasis mittels der Einstellung "Tierbegleiter Plugin: IA Zucht und Ausbildung" die Ilaris Advanced Regeln zu Zucht und Ausbildung aktiviert werden (zusammen mit speziell angepassten Tierwerten).

## Tragkraft
Das Plugin setzt die Tragkraft der Regeln für Reisen von Alrik Normalpaktierer um (https://dsaforum.de/viewtopic.php?f=180&t=55321&hilit=reiseregeln). Die Tragkraft und der resultierende BE-Modifikator werden in der ersten Inventarzeile angezeigt. Der BE-Modifikator wird nicht(!) bei der BE oder den Kampfwerten eingerechnet. Allen anderen Zeilen kann ein Platzbedarf zugewiesen werden.

## WaffenPlus
Dieses Plugin schafft einige Anpassungsmöglichkeiten für Waffen:
- Zeigt im Waffen-Tab ein VT-WM Feld an. Waffen in der Datenbank kann die Eigenschaft Unhandlich(X) gegeben werden, wobei X von der VT abgezogen wird. Beispiel: ein WM von 2 und Unhandlich (3) bedeutet einen Gesamt-WM von 2/-1.
- Optionale Waffeneigenschaften, die mit '(\*)' am Ende des Namens markiert werden; Beispiel: die Streitaxt erhält die Eigenschaft Rüstungsbrechend (\*). Diese Markierung muss im Charaktereditor entfernt werden, ansonsten wird die Eigenschaft nicht auf dem Charakterbogen ausgegeben.
- In den Hausregeln können bestimmte Waffeneigenschaften via 'WaffenPlus Plugin: Waffeneigenschaften Gruppieren' in der PDF separat gruppiert werden. Dies kann beispielsweise genutzt werden, um bestimmte Waffeneigenschaften als Angriffsarten herauszuheben (siehe IA).
- Die Waffeneigenschaft Vielseitig gibt Waffen eine Doppelreichweite.

Diese Features (außer Vielseitig) können in den Hausregeln über diverse 'WaffenPlus Plugin' Einstellungen deaktiviert werden. Vielseitig kann einfach gelöscht werden.

## Zaubertricks
Das Plugin sorgt dafür, dass die Zaubertricks-Fertigkeit aus WeZwanzigs Hausregeln und Ilaris Advanced nicht steigerbar ist und auch im Seitenpanel entsprechend angezeigt wird. Außerdem trägt es im Charakterbogen beim PW einen Strich ein. Achtung: Das Plugin enthält keine Hausregeldatenbank mit den entsprechenden Zaubertricks, beziehe diese bitte von WeZwanzig oder Ilaris Advanced.