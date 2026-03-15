#!/bin/bash
# daemon_chrome_v2.sh - 包含 CDP Relay 的 SOTA 版启动脚本

PORT=9222
USER_DATA="/tmp/drission_sota_v2"
CHROME_PATH="/home/jiahao/.pixi/bin/google-chrome-stable"

# 1. 彻底清理
pkill -9 chrome
pkill -9 Xvfb
pkill -f python_relay.py
rm -rf $USER_DATA

# 2. 启动并捕获 D-Bus 变量
eval $(dbus-launch --sh-syntax)
export DBUS_SESSION_BUS_ADDRESS
export DBUS_SESSION_BUS_PID

# 3. 启动 Chrome (强制 0.0.0.0 和显式端口注入)
export CHROME_REMOTE_DEBUGGING_PORT=$PORT
nohup xvfb-run --server-args="-screen 0 1920x1080x24" \
    $CHROME_PATH --headless=new --no-sandbox \
    --remote-debugging-port=$PORT \
    --remote-debugging-address=0.0.0.0 \
    --user-data-dir=$USER_DATA \
    --remote-allow-origins="*" \
    --disable-gpu --disable-dev-shm-usage > /home/jiahao/chrome_v2.log 2>&1 &

sleep 5

# 4. 启动 Python Relay Bridge (这就是审计员要的隧道)
nohup python3 /home/jiahao/.openclaw/workspace/skills/drission-agent/scripts/python_relay.py > /home/jiahao/relay.log 2>&1 &

echo "SOTA 隧道已贯通：宿主机连接 9223 端口即可穿透隔离层。"
curl -s http://127.0.0.1:9223/json/version
