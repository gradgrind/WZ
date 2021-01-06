# -*- coding: utf-8 -*-

"""
local/attendance_config.py

Last updated:  2021-01-06

Configuration items for attendance tables.
===========================================
"""

# In RESOURCES/templates:
TEMPLATE = 'Vorlage_Klassenbuch'    # .xlsx

# Filename for attendance table:
ATTENDANCE_FILE = 'Klassenbuch_{klass}_{year}'  # .xlsx

# Tabellentitle der Seite für Notizen (Klassenfahrten, Auslandsaufenthalte, usw.)
attendance_sheet_notes = 'Notizen'

# Zellenbezeichnungen besonderer Zellen:
attendance_cell_class = 'N3'
attendance_cell_classM = 'C1'
attendance_cell_daysum = 'AN2'
attendance_cell_date1 = 'U3'
attendance_cell_date2 = 'X3'
attendance_cell_totaldays = 'G2'
attendance_cell_monthM = 'B1'
attendance_row_codes = '1'
attendance_row_days = '2'
attendance_row_pupils = '3'
attendance_col_daystart = 'E'
# Bezeichnung der ersten Spalte der Summenspalten, Tabellen 0 und 1:
attendance_datacol0 = 'D'
attendance_datacol1 = 'AK'
# Anzahl der Summenspalten:
attendance_datacols = '5'
# Zellenbezeichnungen der Formatierungszellen:
attendance_style_id = 'A3'
attendance_style_name = 'B3'
attendance_style_sum = 'D3'
attendance_style_N = 'K5'
attendance_style_W = 'K6'
attendance_style_F = 'K7'
attendance_style_X = 'K8'
attendance_style_T = 'K10'
