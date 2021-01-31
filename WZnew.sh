#!/bin/bash

thisfile=$( realpath "$0"  )
thisdir=$( dirname "$thisfile" )
cd "$thisdir/wz/gui"
"$thisdir/venv/bin/python" "$thisdir/wz/ui/WZ.py" "$thisdir/DATA"

