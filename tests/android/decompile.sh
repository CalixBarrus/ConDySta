#!/usr/bin/env sh

# Set PYTHONPATH to the project root (2nd parent dir of the current file)
export PYTHONPATH="$(dirname "$(dirname $(pwd))")"

echo PYTHONPATH: $PYTHONPATH

python decompile.py