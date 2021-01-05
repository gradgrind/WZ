#!/bin/bash

thisfile=$( realpath "$0"  )
thisdir=$( dirname "$thisfile" )
"$thisdir/venv/bin/python" "$thisdir/wz/gui/WZ.py" "$thisdir/DATA"

