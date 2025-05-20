#!/bin/bash

NAME="$1"

if [ -z "$NAME" ]; then
  echo "Usage: $0 <notebook_name_without_extension>"
  exit 1
fi

NOTEBOOK_PATH="notebooks/${NAME}.ipynb"
OUTPUT_PATH="scripts/${NAME}.py"

# Check that the notebook exists
if [ ! -f "$NOTEBOOK_PATH" ]; then
  echo "Notebook not found: $NOTEBOOK_PATH"
  exit 1
fi

# Ensure scripts/ exists
mkdir -p scripts

# Convert notebook to script
jupyter nbconvert --to script "$NOTEBOOK_PATH" --output-dir=scripts --output="$NAME"

# Remove markdown-style comments
sed -i '' '/^# /d' "$OUTPUT_PATH"
