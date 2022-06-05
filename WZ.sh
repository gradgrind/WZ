#!/bin/bash

thisfile=$( realpath "$0"  )
thisdir=$( dirname "$thisfile" )
cd "$thisdir/program/ui"
#"$thisdir/venv/bin/python" "$thisdir/wz/ui/WZ.py" "$thisdir/DATA"
~/bin/venv/bin/python "wz_window.py"

