#!/usr/bin/env sh

# Set PYTHONPATH to the project root (parent dir of the current file)
export PYTHONPATH="$(dirname $(pwd))"

echo PYTHONPATH: $PYTHONPATH

python extract_smali.py