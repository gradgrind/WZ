

CONSTRAINT_FIELDS = [
    ("MINPERDAY", "min_Stunden_pro_Tag"),
    ("MAXGAPSPERDAY", "max_Lücken_pro_Tag"),
    ("MAXGAPSPERWEEK", "max_Lücken_pro_Woche"),
    ("MAXBLOCK", "Blocklänge")
]
# Feldwerte der Stundenplanung:
#   leer ⇒ keine Angabe
#   * ⇒ Standardwert (DEFAULT)
#   sonst eigener Wert
# Normalerweise sollte ein Lehrer nur in einer der Spalten Mittag
# und Blocklänge einen Wert haben.

TABLE_FIELDS: [
    {NAME: DAY              DISPLAY_NAME: Tag       REQUIRED: true}
    {NAME: FULL_DAY         DISPLAY_NAME: Tag_voll}
# Die Felder für die Stundenverfügbarkeit werden automatisch hinzugefügt.
]

DEFAULTS: {
### Alle Werte sind Zeichenketten. Sie dürfen leer sein, dann wird die
### Bedingung nicht angewendet.
### Sie dürfen Anhang "@n" haben: n ist eine Zahl im Bereich 0 bis 10,
### die „Gewichtung“ der Bedingung.
# min. Unterrichtsstunden pro Tag (außer an freien Tagen):
    MINPERDAY:          [2      RANGE 0 10]
# max. Lücken pro Tag:
    MAXGAPSPERDAY:      [""     RANGE 0 10]
# max. Lücken pro Woche:
    MAXGAPSPERWEEK:     [4      RANGE 0 10]
# max. nacheinanderfolgende Unterrichtsstunden:
    MAXBLOCK:           [6@5    RANGE 0 10]
}

