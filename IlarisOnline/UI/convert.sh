#!/bin/bash

for file in *.ui; do
    [ -e "$file" ] || continue  # skip if no .ui files
    outfile="../${file%.ui}.py"
    echo "Converting $file -> $outfile"
    /mnt/data/ilaris-tools/sephrasto/Sephrasto/.venv/bin/pyside6-uic "$file" -o "$outfile"
done
