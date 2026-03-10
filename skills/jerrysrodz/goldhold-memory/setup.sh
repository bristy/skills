#!/usr/bin/env bash
# GoldHold skill setup
# Creates config directory if needed

set -e

CONFIG_DIR="$HOME/.goldhold"
CONFIG_FILE="$CONFIG_DIR/config.json"

mkdir -p "$CONFIG_DIR"

if [ ! -f "$CONFIG_FILE" ]; then
  echo '{"api_key": ""}' > "$CONFIG_FILE"
  echo "Created $CONFIG_FILE -- add your API key from goldhold.ai/account"
else
  echo "$CONFIG_FILE already exists"
fi

echo "GoldHold skill ready. Set your API key in $CONFIG_FILE or GOLDHOLD_API_KEY env var."
