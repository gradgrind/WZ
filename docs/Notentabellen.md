# Fächertabellen und Notentabellen

In den Fächertabellen werden alle Fächer aufgelistet, die unterrichtet werden. Unter Umständen werden nicht für alle dieser Fächer Noten vergeben, es wird aber im Moment davon ausgegangen, dass für alle ein Textzeugnis geschrieben wird[^1].

[^1]: Es könnte sinnvoll sein, Fächer zu unterstützen, für die nur Notenzeugnisse vergeben werden. Aktuell kann das nur erreicht werden, indem alle nicht gewünschten Textzeugnisse leer gelassen werden.

Fächer, für die nur Textzeugnisse vergeben werden, werden mit einem „-“ im Fachgruppenfeld gekennzeichnet. Alle Fächer, die benotet werden, sollten eine gültige Fachgruppe in diesem Feld haben.

Es kann auch Fächer geben, die nicht unterrichtet werden, aber die eine Sammelnote aus den Ergebnissen in anderen Fächern im Zeugnis stehen. Ein Beispiel dafür wäre ein Fach „Kunst“, bei dem die Note als Durchschnitt der Noten in den tatsächlich unterrichteten Fächern Malen, Kunstgeschichte und Plastizieren gebildet wird. Auch diese sollten in der Fächertabelle erscheinen, da auch eine solche Noten einer Notengruppe (für die Platzierung im Zeugnis) zugeordnet werden muss.

Eine Notentabelle wird auch weitere Informationen enthalten müssen. Manches betrifft die ganze Gruppe: um welche Gruppe es sich handelt, das Schuljahr, ggf. Halbjahr, usw., Ausgabedatum, ggf. Notendatum. Diese haben einen eigenen Bereich in der Tabelle. Anderes ist schülerspezifisch, z.B. Art des Zeugnisses, Qualifikation, Bemerkungen. Diese werden wie Fachnoten behandelt. Diese müssen für die Gruppe definiert werden ...

Könnten diese Zusatzfelder sinnvoll in der Fächertabelle definiert werden? Da sie nicht Noten sind, muss für jedes Feld die Behandlung (Texteingabe, Auswahlliste, Datum, ...) angegeben werden. Die bestehenden Felder dieser Tabelle sind nicht wirklich passend. Einträge in der Gruppenkonfiguration sind vielleicht geeigneter.



## Abitur

Da die Bewertung des Abiturs einige Besonderheiten hat, könnte es sinnvoll sein, die Noten und Zeugnisse in einem eigenen Modul zu verwalten.

Die Fächer haben verschiedene „Ausprägungen“: Leistungskurse (eA) und Grundkurse (gA). Die Grundkurse sind dann in diejenigen mit schriftlichen Prüfungen und mündlichen Prüfungen. In manchen Fällen kann die mündliche Prüfung durch die Kursnote ersetzt werden. Zu den schriftlichen Prüfungen können bei Bedarf eine mündliche Nachprüfung dazugefügt werden. Außerdem ist die Behandlung des Abiturs von Bundesland zu Bundesland unterschiedlich.