#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 2 ]]; then
  echo "Usage: install.sh <telegram-bot-token> <openai-api-key>" >&2
  exit 2
fi

TELEGRAM_TOKEN="$1"
OPENAI_KEY="$2"
BOT_DIR="$HOME/transcribe-bot"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "Installing Telegram Transcribe Bot..."

# Copy bot script
mkdir -p "$BOT_DIR"
cp "$SCRIPT_DIR/bot.py" "$BOT_DIR/bot.py"

# Create venv and install deps
if [[ ! -d "$BOT_DIR/venv" ]]; then
  python3 -m venv "$BOT_DIR/venv"
fi
"$BOT_DIR/venv/bin/pip" install -q python-telegram-bot openai

# Create systemd service
mkdir -p ~/.config/systemd/user
cat > ~/.config/systemd/user/transcribe-bot.service << EOF
[Unit]
Description=Telegram Transcribe Bot (Whisper API)
After=network-online.target
Wants=network-online.target

[Service]
ExecStart=$BOT_DIR/venv/bin/python3 $BOT_DIR/bot.py
Restart=always
RestartSec=5
Environment=TELEGRAM_BOT_TOKEN=$TELEGRAM_TOKEN
Environment=OPENAI_API_KEY=$OPENAI_KEY

[Install]
WantedBy=default.target
EOF

systemctl --user daemon-reload
systemctl --user enable transcribe-bot
systemctl --user restart transcribe-bot

echo "✅ Transcribe Bot installiert und gestartet."
echo "   Status: systemctl --user status transcribe-bot"
echo "   Logs:   journalctl --user -u transcribe-bot -f"
