#!/bin/bash

thisfile=$( realpath "$0"  )
thisdir=$( dirname "$thisfile" )
cd "$thisdir/wz/ui"
"$thisdir/venv/bin/python" "$thisdir/wz/ui/WZ.py" "$thisdir/DATA"

