# Die Benutzeroberfläche

- Schuljahr
- Modul/Funktion-Auswahl
- Jedes Modul hat eigene Bedienelemente

Ich gehe davon aus, dass Textzeugnisse einmal und Notenzeugnisse (in den betroffenen Klassen) zweimal im Jahr ausgegeben werden. Diese Häufigkeiten sollten aber nicht fest eingebaut sein.

Es gibt eine Datenbank mit den Schülerdaten und den Fachdaten (einschließlich möglicher Kurswahlen) für jedes Schuljahr. Ein „Startpunkt“ für ein neues Schuljahr kann von den Daten des alten erstellt werden (Klassenstufen um eins vergrößert, Fächer einfach übernommen auf Klassenbasis). Die Daten des aktuellen Jahres können (idealerweise) im Programm bearbeitet werden – auch mit Export und Import.

Wenn ein Zeugnissatz fertiggestellt wird (am Ende eines Jahres bzw. Halbjahres), sollten die Daten abgeschlossen und archiviert werden. Wenn es sich um Halbjahreszeugnisse handelt, können aber die Schüler- und Fachdaten des Jahres geändert werden. Wenn also ein Zeitabschnitt abgeschlossen wird (das sollte ein konkreter Vorgang sein, vom Administrator durchgeführt), sollten diese Daten – in ihren aktuellen Versionen mitarchiviert werden. So werden sie vom weiteren Verlauf des Schuljahres isoliert. Die fertiggestellten Zeugnisse und deren Daten sollten jetzt nur geändert werden, um Fehler zu korrigieren (die Zeugnisse sind schon raus!).

Vielleicht sollten insbesondere bei abgeschlossenen Zeugnissätzen Änderungen an einzelnen Zeugnissen durchgeführt werden, wenn das irgendwie sinnvoll umzusetzen ist. Die Erstellung einer PDF-Datei für eine ganze Gruppe könnte generell als Zusatzfunktion bereitgestellt werden – primär würden Einzelzeugnisse erstellt werden.

Alte Zeugnisse sollten auf jeden Fall als PDF-Dateien archiviert werden. Es _könnte_ sinnvoll sein, auch die ODF-Dateien zu archivieren. Für Notenzeugnisse wäre es bestimmt sinnvoll die dazugehörigen Notentabellen in irgendeiner portablen Form (ODS? CSV?) zu behalten. Ein automatischer Zugriff auf alte Tabellen wäre u.U. auch nützlich.

Test-Dateien sollten bereitgestellt werden, damit man verschiedene Bearbeitungsstufen durchlaufen kann.

Es gibt ein „aktuelles“ Schuljahr, an dem gearbeitet wird (zu Testzwecken könnte man ein Testdatum künstlich einstellen). Am Ende eines Schuljahres – oder vielleicht eher am Anfang des nächsten – würde man die jetzt fertigen Daten abschließen und archivieren. Dann würde sich das aktive Jahr umstellen. Ähnliches gilt für das Halbjahr, was möglicherweise nur die Notenzeugnisse betrifft. Jedenfalls ein Anzeigefeld könnte z.B. „2015 – 2016; 1. Halbjahr“ angeben. Intern gäbe es dann eine Konfiguration, die angibt, welche Daten abgeschlossen werden sollten, wenn das Halbjahr zu Ende ist. Passend wäre vielleicht eine Terminliste, die allmählich „abgearbeitet“ wird.

Die Daten werden in einem alles umfassenden (aber natürlich durch Unterordner strukturierten) Ordner untergebracht – Konfigurationsdateien, Vorlagen, Schuldaten, Klassen- und Schülerdaten, erstellte Tabellen und Zeugnisse. Es sollte möglich sein, diesen Ordner auszuwechseln, aber normalerweise würde er einfach einmal festgelegt werden.

Beim ersten Start des Programms gibt es den Datenordner wahrscheinlich nicht, er muss zuerst angelegt werden. Dafür braucht man zuerst ein „Kalender“ – eine Konfigurationsdatei, die wichtige Daten für das aktuelle Schuljahr enthält, insbesondere Jahresbezeichnung, -anfang und -ende. Das Kalender aus dem Testordner kann als Vorlage dienen. Bald danach wird man Schüler- und Klassendaten (Fächer, usw.) brauchen. Diese können vielleicht anhand externe Tabellen oder manuell eingefügt werden.

Die Testdateien werden als Archiv mit dem Programm ausgeliefert. Dieses kann man entpacken, um einen Datenordner zum Ausprobieren zu erhalten.

Wenn das Programm ohne einen funktionsfähigen Datensatz startet, muss der Benutzer entweder einen schon existierenden Datenordner auswählen, oder einen neuen, leeren erstellen. Im letzteren Fall wird eine Vorlage für das Kalender in einem Editierfenster angeboten. Diese kann man anpassen und abspeichern.






