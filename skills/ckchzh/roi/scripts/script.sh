#!/usr/bin/env bash
set -euo pipefail

# roi — skill script
# Powered by BytesAgain | bytesagain.com | hello@bytesagain.com

DATA_DIR="${HOME}/.roi"
mkdir -p "$DATA_DIR"

show_help() {
    cat << 'HELPEOF'
roi — command-line tool

Commands:
  calculate      Run calculate operation
  compare        Run compare operation
  forecast       Run forecast operation
  annualize      Run annualize operation
  project        Run project operation
  scenario       Run scenario operation
  report         Run report operation
  history        Run history operation
  export         Run export operation
  config         Run config operation
  stats      Show statistics
  export     Export data (json|csv|txt)
  search     Search across entries
  recent     Show recent entries
  status     Show current status
  help       Show this help message
  version    Show version number

Data stored in: ~/.roi/
HELPEOF
}

show_version() {
    echo "roi v1.0.0 — Powered by BytesAgain"
}

cmd_stats() {
    echo "=== roi Statistics ==="
    local total=0
    for f in "$DATA_DIR"/*.log; do
        [ -f "$f" ] || continue
        local name=$(basename "$f" .log)
        local c=$(wc -l < "$f" 2>/dev/null || echo 0)
        total=$((total + c))
        echo "  $name: $c entries"
    done
    echo "  Total: $total entries"
    echo "  Data size: $(du -sh "$DATA_DIR" 2>/dev/null | cut -f1 || echo 'N/A')"
    echo "  Since: $(head -1 "$DATA_DIR/history.log" 2>/dev/null | cut -d'|' -f1 || echo 'N/A')"
}

cmd_export() {
    local fmt="${1:-json}"
    local out="roi-export.$fmt"
    case "$fmt" in
        json)
            echo "[" > "$out"
            local first=1
            for f in "$DATA_DIR"/*.log; do
                [ -f "$f" ] || continue
                while IFS= read -r line; do
                    [ $first -eq 1 ] && first=0 || echo "," >> "$out"
                    local ts=$(echo "$line" | cut -d'|' -f1)
                    local cmd=$(echo "$line" | cut -d'|' -f2)
                    local data=$(echo "$line" | cut -d'|' -f3-)
                    printf '  {"timestamp":"%s","command":"%s","data":"%s"}' "$ts" "$cmd" "$data" >> "$out"
                done < "$f"
            done
            echo "" >> "$out"
            echo "]" >> "$out"
            ;;
        csv)
            echo "timestamp,command,data" > "$out"
            for f in "$DATA_DIR"/*.log; do
                [ -f "$f" ] || continue
                while IFS= read -r line; do
                    echo "$line" | awk -F'|' '{printf "\"%s\",\"%s\",\"%s\"\n", $1, $2, $3}' >> "$out"
                done < "$f"
            done
            ;;
        txt)
            > "$out"
            for f in "$DATA_DIR"/*.log; do
                [ -f "$f" ] || continue
                echo "--- $(basename "$f" .log) ---" >> "$out"
                cat "$f" >> "$out"
                echo "" >> "$out"
            done
            ;;
        *)
            echo "Unknown format: $fmt (use json, csv, or txt)"
            return 1
            ;;
    esac
    echo "Exported to $out ($(wc -c < "$out" 2>/dev/null || echo 0) bytes)"
}

cmd_search() {
    local term="${1:-}"
    [ -z "$term" ] && { echo "Usage: roi search <term>"; return 1; }
    echo "=== Search: $term ==="
    local found=0
    for f in "$DATA_DIR"/*.log; do
        [ -f "$f" ] || continue
        local matches=$(grep -i "$term" "$f" 2>/dev/null || true)
        if [ -n "$matches" ]; then
            echo "--- $(basename "$f" .log) ---"
            echo "$matches"
            found=$((found + 1))
        fi
    done
    [ $found -eq 0 ] && echo "No matches found."
}

cmd_recent() {
    local n="${1:-10}"
    echo "=== Recent $n entries ==="
    for f in "$DATA_DIR"/*.log; do
        [ -f "$f" ] || continue
        tail -n "$n" "$f" 2>/dev/null
    done | sort -t'|' -k1 | tail -n "$n"
}

cmd_status() {
    echo "=== roi Status ==="
    echo "  Entries: $(cat "$DATA_DIR"/*.log 2>/dev/null | wc -l || echo 0)"
    echo "  Disk: $(du -sh "$DATA_DIR" 2>/dev/null | cut -f1 || echo 'N/A')"
    local last=$(tail -1 "$DATA_DIR/history.log" 2>/dev/null || echo "never")
    echo "  Last activity: $last"
}

# Main
CMD="${1:-help}"
shift 2>/dev/null || true

case "$CMD" in
    calculate)
        local ts=$(date '+%Y-%m-%d %H:%M')
        echo "$ts|calculate|${*}" >> "$DATA_DIR/calculate.log"
        local total=$(wc -l < "$DATA_DIR/calculate.log" 2>/dev/null || echo 0)
        echo "[roi] calculate recorded (entry #$total)"
        ;;
    compare)
        local ts=$(date '+%Y-%m-%d %H:%M')
        echo "$ts|compare|${*}" >> "$DATA_DIR/compare.log"
        local total=$(wc -l < "$DATA_DIR/compare.log" 2>/dev/null || echo 0)
        echo "[roi] compare recorded (entry #$total)"
        ;;
    forecast)
        local ts=$(date '+%Y-%m-%d %H:%M')
        echo "$ts|forecast|${*}" >> "$DATA_DIR/forecast.log"
        local total=$(wc -l < "$DATA_DIR/forecast.log" 2>/dev/null || echo 0)
        echo "[roi] forecast recorded (entry #$total)"
        ;;
    annualize)
        local ts=$(date '+%Y-%m-%d %H:%M')
        echo "$ts|annualize|${*}" >> "$DATA_DIR/annualize.log"
        local total=$(wc -l < "$DATA_DIR/annualize.log" 2>/dev/null || echo 0)
        echo "[roi] annualize recorded (entry #$total)"
        ;;
    project)
        local ts=$(date '+%Y-%m-%d %H:%M')
        echo "$ts|project|${*}" >> "$DATA_DIR/project.log"
        local total=$(wc -l < "$DATA_DIR/project.log" 2>/dev/null || echo 0)
        echo "[roi] project recorded (entry #$total)"
        ;;
    scenario)
        local ts=$(date '+%Y-%m-%d %H:%M')
        echo "$ts|scenario|${*}" >> "$DATA_DIR/scenario.log"
        local total=$(wc -l < "$DATA_DIR/scenario.log" 2>/dev/null || echo 0)
        echo "[roi] scenario recorded (entry #$total)"
        ;;
    report)
        local ts=$(date '+%Y-%m-%d %H:%M')
        echo "$ts|report|${*}" >> "$DATA_DIR/report.log"
        local total=$(wc -l < "$DATA_DIR/report.log" 2>/dev/null || echo 0)
        echo "[roi] report recorded (entry #$total)"
        ;;
    history)
        local ts=$(date '+%Y-%m-%d %H:%M')
        echo "$ts|history|${*}" >> "$DATA_DIR/history.log"
        local total=$(wc -l < "$DATA_DIR/history.log" 2>/dev/null || echo 0)
        echo "[roi] history recorded (entry #$total)"
        ;;
    export)
        local ts=$(date '+%Y-%m-%d %H:%M')
        echo "$ts|export|${*}" >> "$DATA_DIR/export.log"
        local total=$(wc -l < "$DATA_DIR/export.log" 2>/dev/null || echo 0)
        echo "[roi] export recorded (entry #$total)"
        ;;
    config)
        local ts=$(date '+%Y-%m-%d %H:%M')
        echo "$ts|config|${*}" >> "$DATA_DIR/config.log"
        local total=$(wc -l < "$DATA_DIR/config.log" 2>/dev/null || echo 0)
        echo "[roi] config recorded (entry #$total)"
        ;;
    stats)
        cmd_stats
        ;;
    export)
        cmd_export "$@"
        ;;
    search)
        cmd_search "$@"
        ;;
    recent)
        cmd_recent "$@"
        ;;
    status)
        cmd_status
        ;;
    help|--help|-h)
        show_help
        ;;
    version|--version|-v)
        show_version
        ;;
    *)
        echo "Unknown command: $CMD"
        echo "Run 'roi help' for usage."
        exit 1
        ;;
esac
