"""
ui/timetable/constraints_class.py

Last updated:  2022-04-26

Manage class constraints.


=+LICENCE=============================
Copyright 2022 Michael Towers

   Licensed under the Apache License, Version 2.0 (the "License");
   you may not use this file except in compliance with the License.
   You may obtain a copy of the License at

       http://www.apache.org/licenses/LICENSE-2.0

   Unless required by applicable law or agreed to in writing, software
   distributed under the License is distributed on an "AS IS" BASIS,
   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
   See the License for the specific language governing permissions and
   limitations under the License.

=-LICENCE========================================
"""



T = TRANSLATIONS("timetable.constraints_class")

### +++++


def period_validator(value):
    """Validator for class period availability table.
    """
    if value in ("+", "-", "*"):
        return None
    return T["INVALID_AVAILABILITY"].format(val=value)


CONSTRAINT_FIELDS = [(f, T[f]) for f in (
        "MINDAILY",
        "MAXGAPSWEEKLY",
        "NOTAFTER",
        "PAIRGAP",
        "AVAILABLE"
    )
]

#for testing only
#CONSTRAINT_FIELDS += [("X1", "TX1"), ("X2", "TX2"), ("X3", "TX3"), ("X4", "TX4"), ("X5", "TX5"), ("X6", "TX6")]

# Feldwerte der Stundenplanung:
#   leer ⇒ keine Angabe
#   * ⇒ Standardwert (DEFAULT)
#   sonst eigener Wert
# Normalerweise sollte ein Lehrer nur in einer der Spalten Mittag
# und Blocklänge einen Wert haben.

#TABLE_FIELDS: [
#    {NAME: DAY              DISPLAY_NAME: Tag       REQUIRED: true}
#    {NAME: FULL_DAY         DISPLAY_NAME: Tag_voll}
# Die Felder für die Stundenverfügbarkeit werden automatisch hinzugefügt.
#]

#DEFAULTS: {
### Alle Werte sind Zeichenketten. Sie dürfen leer sein, dann wird die
### Bedingung nicht angewendet.
### Sie dürfen Anhang "@n" haben: n ist eine Zahl im Bereich 0 bis 10,
### die „Gewichtung“ der Bedingung.
# min. Unterrichtsstunden pro Tag (außer an freien Tagen):
#    MINPERDAY:          [2      RANGE 0 10]
# max. Lücken pro Tag:
#    MAXGAPSPERDAY:      [""     RANGE 0 10]
# max. Lücken pro Woche:
#    MAXGAPSPERWEEK:     [4      RANGE 0 10]
# max. nacheinanderfolgende Unterrichtsstunden:
#    MAXBLOCK:           [6@5    RANGE 0 10]
#}

