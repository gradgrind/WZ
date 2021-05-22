# Die Benutzeroberfläche

- Schuljahr
- Modul/Funktion-Auswahl
- Jedes Modul hat eigene Bedienelemente

Ich gehe davon aus, dass Textzeugnisse einmal und Notenzeugnisse (in den betroffenen Klassen) zweimal im Jahr ausgegeben werden. Diese Häufigkeiten sollten aber nicht fest eingebaut sein.

Es gibt eine Datenbank mit den Schülerdaten und den Fachdaten (einschließlich möglicher Kurswahlen) für jedes Schuljahr. Ein „Startpunkt“ für ein neues Schuljahr kann von den Daten des alten erstellt werden (Klassenstufen um eins vergrößert, Fächer einfach übernommen auf Klassenbasis). Die Daten des aktuellen Jahres können (idealerweise) im Programm bearbeitet werden – auch mit Export und Import.

Wenn ein Zeugnissatz fertiggestellt wird (am Ende eines Jahres bzw. Halbjahres), sollten die Daten abgeschlossen und archiviert werden. Wenn es sich um Halbjahreszeugnisse handelt, können aber die Schüler- und Fachdaten des Jahres geändert werden. Wenn also ein Zeitabschnitt abgeschlossen wird (das sollte ein konkreter Vorgang sein, vom Administrator durchgeführt), sollten diese Daten – in ihren aktuellen Versionen mitarchiviert werden. So werden sie vom weiteren Verlauf des Schuljahres isoliert. Die fertiggestellten Zeugnisse und deren Daten sollten jetzt nur geändert werden, um Fehler zu korrigieren (die Zeugnisse sind schon raus!).

Vielleicht sollten insbesondere bei abgeschlossenen Zeugnissätzen Änderungen an einzelnen Zeugnissen durchgeführt werden, wenn das irgendwie sinnvoll umzusetzen ist. Die Erstellung einer PDF-Datei für eine ganze Gruppe könnte generell als Zusatzfunktion bereitgestellt werden – primär würden Einzelzeugnisse erstellt werden.

Das ist mir aber noch zu schwammig. Alte
Zeugnisse sollten auf jeden Fall als PDF-Dateien archiviert werden. Es _könnte_ sinnvoll sein, auch die ODF-Dateien zu archivieren. Für Notenzeugnisse wäre es bestimmt sinnvoll die dazugehörigen Notentabellen in irgendeiner portablen Form (ODS? CSV?) zu behalten. Ein automatischer Zugriff auf alte Tabellen wäre u.U. auch nützlich.

Test-Dateien könnten bereitgestellt werden, damit man verschiedene Bearbeitungsstufen durchlaufen kann.

Konkret könnte das heißen, es gibt ein Schuljahr, das nicht direkt zu ändern ist. Es entspricht dem aktuellen Stand der Zeugnisse (für Testzwecke könnte man ein Testdatum künstlich einstellen). Am Ende eines Schuljahres – oder vielleicht eher am Anfang des nächsten – würde man die jetzt fertigen Daten abschließen und archivieren. Dann würde sich das aktive Jahr umstellen. Ähnliches gilt für das Halbjahr, was möglicherweise nur die Notenzeugnisse betrifft. Jedenfalls ein Anzeigefeld könnte z.B. „2015 – 2016; 1. Halbjahr“ angeben. Intern gäbe es dann eine Konfiguration, die angibt, welche Daten abgeschlossen werden sollten, wenn das Halbjahr zu Ende ist. Passend wäre vielleicht eine Terminliste, die allmählich „abgearbeitet“ wird.





