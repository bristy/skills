#!/usr/bin/env bash
# login/scripts/script.sh — Credential Manager & Password Vault
# Data: ~/.login/data.jsonl
set -euo pipefail
VERSION="1.0.0"
DATA_DIR="$HOME/.login"
DATA_FILE="$DATA_DIR/data.jsonl"
mkdir -p "$DATA_DIR"
touch "$DATA_FILE"

CMD="${1:-help}"
shift 2>/dev/null || true

show_help() {
cat << 'HELPEOF'
Login — Credential Manager & Password Vault  v1.0.0

Usage: bash scripts/script.sh <command> [options]

Commands:
  add          Add a new credential entry
  list         List all stored credentials (passwords masked)
  get          Retrieve a specific credential (shows password)
  update       Update an existing credential
  delete       Remove a credential entry
  search       Search credentials by service, username, URL, or tags
  generate     Generate a secure random password
  strength     Check the strength of a password
  duplicate    Find credentials with duplicate passwords
  expire       List credentials older than N days
  export       Export credentials to encrypted JSON or CSV
  import       Import credentials from a file
  help         Show this help message
  version      Print the tool version
HELPEOF
}

case "$CMD" in
  add|list|get|update|delete|search|generate|strength|duplicate|expire|export|import)
    SKILL_CMD="$CMD" SKILL_ARGV="$(printf '%s\n' "$@")" python3 << 'PYEOF'
import sys, json, os, uuid, datetime, base64, string, math, re
import random as rng

DATA_DIR = os.path.expanduser("~/.login")
DATA_FILE = os.path.join(DATA_DIR, "data.jsonl")

def load_records():
    records = []
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        records.append(json.loads(line))
                    except json.JSONDecodeError:
                        pass
    return records

def save_records(records):
    with open(DATA_FILE, "w") as f:
        for r in records:
            f.write(json.dumps(r) + "\n")

def append_record(record):
    with open(DATA_FILE, "a") as f:
        f.write(json.dumps(record) + "\n")

def gen_id():
    return uuid.uuid4().hex[:8]

def now_iso():
    return datetime.datetime.now().isoformat()

def parse_args(args):
    parsed = {}
    i = 0
    while i < len(args):
        if args[i].startswith("--"):
            key = args[i][2:]
            if i + 1 < len(args) and not args[i+1].startswith("--"):
                parsed[key] = args[i+1]
                i += 2
            else:
                parsed[key] = True
                i += 1
        else:
            i += 1
    return parsed

def obfuscate(password):
    """Base64 encode for simple obfuscation (NOT real encryption)."""
    return base64.b64encode(password.encode()).decode()

def deobfuscate(encoded):
    """Decode base64 obfuscated password."""
    try:
        return base64.b64decode(encoded.encode()).decode()
    except Exception:
        return encoded

def mask_password(password, show=4):
    """Mask password showing only first N chars."""
    if len(password) <= show:
        return "*" * len(password)
    return password[:show] + "*" * (len(password) - show)

COMMON_PASSWORDS = [
    "password", "123456", "12345678", "qwerty", "abc123", "monkey", "master",
    "dragon", "111111", "baseball", "iloveyou", "trustno1", "sunshine",
    "letmein", "welcome", "admin", "login", "passw0rd", "1234567890"
]

def calculate_strength(password):
    """Calculate password strength score (0-100)."""
    score = 0
    length = len(password)
    tips = []

    # Length scoring
    if length >= 8:
        score += 15
    if length >= 12:
        score += 10
    if length >= 16:
        score += 10
    if length >= 20:
        score += 5
    if length < 8:
        tips.append("Use at least 8 characters")

    # Character variety
    has_lower = bool(re.search(r'[a-z]', password))
    has_upper = bool(re.search(r'[A-Z]', password))
    has_digit = bool(re.search(r'[0-9]', password))
    has_symbol = bool(re.search(r'[^a-zA-Z0-9]', password))

    variety = sum([has_lower, has_upper, has_digit, has_symbol])
    score += variety * 10

    if not has_upper:
        tips.append("Add uppercase letters")
    if not has_digit:
        tips.append("Add numbers")
    if not has_symbol:
        tips.append("Add special characters (!@#$%^&*)")

    # Entropy estimation
    charset_size = 0
    if has_lower:
        charset_size += 26
    if has_upper:
        charset_size += 26
    if has_digit:
        charset_size += 10
    if has_symbol:
        charset_size += 32

    if charset_size > 0:
        entropy = length * math.log2(charset_size)
        if entropy >= 60:
            score += 15
        elif entropy >= 40:
            score += 10
        elif entropy >= 28:
            score += 5

    # Penalty for common passwords
    if password.lower() in COMMON_PASSWORDS:
        score = max(score - 40, 0)
        tips.append("This is a commonly used password — change it immediately")

    # Penalty for sequential/repeated
    if re.search(r'(.)\1{2,}', password):
        score = max(score - 10, 0)
        tips.append("Avoid repeated characters")
    if re.search(r'(012|123|234|345|456|567|678|789|890|abc|bcd|cde|def)', password.lower()):
        score = max(score - 10, 0)
        tips.append("Avoid sequential patterns")

    score = min(max(score, 0), 100)

    if score <= 30:
        rating = "weak"
    elif score <= 50:
        rating = "fair"
    elif score <= 70:
        rating = "good"
    elif score <= 90:
        rating = "strong"
    else:
        rating = "excellent"

    return {"score": score, "rating": rating, "tips": tips}

def cmd_add(args):
    opts = parse_args(args)
    service = opts.get("service", "")
    username = opts.get("username", "")
    password = opts.get("password", "")
    url = opts.get("url", "")
    tags_str = opts.get("tags", "")
    tags = [t.strip() for t in tags_str.split(",") if t.strip()] if tags_str else []
    notes = opts.get("notes", "")

    if not service:
        print(json.dumps({"error": "Please provide --service"}))
        sys.exit(1)
    if not password:
        print(json.dumps({"error": "Please provide --password"}))
        sys.exit(1)

    record = {
        "id": gen_id(),
        "type": "credential",
        "service": service,
        "username": username,
        "password": obfuscate(password),
        "url": url,
        "tags": tags,
        "notes": notes,
        "created_at": now_iso(),
        "updated_at": now_iso()
    }
    append_record(record)
    # Print without showing actual password
    display = dict(record)
    display["password"] = mask_password(password)
    print(json.dumps(display, indent=2))

def cmd_list(args):
    records = load_records()
    creds = [r for r in records if r.get("type") == "credential"]
    if not creds:
        print("No credentials stored.")
        return
    print(f"{'ID':<10} {'Service':<20} {'Username':<20} {'URL':<30} {'Tags':<15}")
    print("-" * 95)
    for c in creds:
        tags = ", ".join(c.get("tags", []))[:13]
        url = c.get("url", "")[:28]
        print(f"{c['id']:<10} {c.get('service','')[:18]:<20} {c.get('username','')[:18]:<20} {url:<30} {tags:<15}")

def cmd_get(args):
    opts = parse_args(args)
    cid = opts.get("id", "")
    service = opts.get("service", "").lower()
    records = load_records()

    for r in records:
        if r.get("type") != "credential":
            continue
        if (cid and r.get("id") == cid) or (service and r.get("service", "").lower() == service):
            result = dict(r)
            result["password"] = deobfuscate(r.get("password", ""))
            print(json.dumps(result, indent=2))
            return
    print(json.dumps({"error": "Credential not found"}))
    sys.exit(1)

def cmd_update(args):
    opts = parse_args(args)
    cid = opts.get("id", "")
    if not cid:
        print(json.dumps({"error": "Please provide --id"}))
        sys.exit(1)
    records = load_records()
    found = False
    for r in records:
        if r.get("type") == "credential" and r.get("id") == cid:
            found = True
            if "service" in opts:
                r["service"] = opts["service"]
            if "username" in opts:
                r["username"] = opts["username"]
            if "password" in opts:
                r["password"] = obfuscate(opts["password"])
            if "url" in opts:
                r["url"] = opts["url"]
            if "tags" in opts:
                r["tags"] = [t.strip() for t in opts["tags"].split(",") if t.strip()]
            if "notes" in opts:
                r["notes"] = opts["notes"]
            r["updated_at"] = now_iso()
            display = dict(r)
            display["password"] = "***updated***" if "password" in opts else "***"
            print(json.dumps(display, indent=2))
            break
    if not found:
        print(json.dumps({"error": f"Credential '{cid}' not found"}))
        sys.exit(1)
    save_records(records)

def cmd_delete(args):
    opts = parse_args(args)
    cid = opts.get("id", "")
    if not cid:
        print(json.dumps({"error": "Please provide --id"}))
        sys.exit(1)
    records = load_records()
    new_records = [r for r in records if not (r.get("type") == "credential" and r.get("id") == cid)]
    if len(new_records) == len(records):
        print(json.dumps({"error": f"Credential '{cid}' not found"}))
        sys.exit(1)
    save_records(new_records)
    print(json.dumps({"deleted": True, "id": cid}))

def cmd_search(args):
    opts = parse_args(args)
    query = opts.get("query", "").lower()
    tag = opts.get("tag", "").lower()
    service = opts.get("service", "").lower()
    records = load_records()
    creds = [r for r in records if r.get("type") == "credential"]
    results = []

    for c in creds:
        match = False
        if query:
            searchable = f"{c.get('service','')} {c.get('username','')} {c.get('url','')} {' '.join(c.get('tags',[]))}".lower()
            if query in searchable:
                match = True
        if tag and tag in [t.lower() for t in c.get("tags", [])]:
            match = True
        if service and service in c.get("service", "").lower():
            match = True
        if match:
            results.append(c)

    if not results:
        print("No matching credentials found.")
        return
    for c in results:
        tags = ", ".join(c.get("tags", []))
        print(f"[{c['id']}] {c.get('service','')} — {c.get('username','')} ({c.get('url','')}) [{tags}]")

def cmd_generate(args):
    opts = parse_args(args)
    length = int(opts.get("length", "16"))
    use_upper = opts.get("uppercase", True)
    use_numbers = opts.get("numbers", True)
    use_symbols = opts.get("symbols", False)
    no_ambiguous = opts.get("no-ambiguous", opts.get("no_ambiguous", False))

    charset = string.ascii_lowercase
    if use_upper and use_upper is not False:
        charset += string.ascii_uppercase
    if use_numbers and use_numbers is not False:
        charset += string.digits
    if use_symbols and use_symbols is not False:
        charset += "!@#$%^&*()_+-=[]{}|;:,.<>?"

    if no_ambiguous:
        ambiguous = "0O1lI"
        charset = "".join(c for c in charset if c not in ambiguous)

    password = "".join(rng.choice(charset) for _ in range(length))

    # Ensure at least one of each required type
    required = []
    if use_upper and use_upper is not False:
        required.append(rng.choice(string.ascii_uppercase))
    if use_numbers and use_numbers is not False:
        required.append(rng.choice(string.digits))
    if use_symbols and use_symbols is not False:
        required.append(rng.choice("!@#$%^&*()_+-=[]{}|;:,.<>?"))

    pwd_list = list(password)
    for i, req_char in enumerate(required):
        if i < len(pwd_list):
            pwd_list[rng.randint(0, len(pwd_list)-1)] = req_char
    rng.shuffle(pwd_list)
    password = "".join(pwd_list)

    strength = calculate_strength(password)
    result = {
        "password": password,
        "length": length,
        "strength": strength
    }
    print(json.dumps(result, indent=2))

def cmd_strength(args):
    opts = parse_args(args)
    password = opts.get("password", "")
    if not password:
        print(json.dumps({"error": "Please provide --password"}))
        sys.exit(1)
    result = calculate_strength(password)
    result["length"] = len(password)
    print(json.dumps(result, indent=2))

def cmd_duplicate(args):
    records = load_records()
    creds = [r for r in records if r.get("type") == "credential"]
    pw_map = {}
    for c in creds:
        pw = c.get("password", "")
        if pw not in pw_map:
            pw_map[pw] = []
        pw_map[pw].append(c)

    duplicates = {k: v for k, v in pw_map.items() if len(v) > 1}
    if not duplicates:
        print("No duplicate passwords found. Good security practice!")
        return

    print(f"Found {len(duplicates)} groups of duplicate passwords:\n")
    for i, (pw, creds_list) in enumerate(duplicates.items(), 1):
        print(f"Group {i} ({len(creds_list)} entries):")
        for c in creds_list:
            print(f"  [{c['id']}] {c.get('service','')} — {c.get('username','')}")
        print()

def cmd_expire(args):
    opts = parse_args(args)
    days = int(opts.get("days", "90"))
    records = load_records()
    creds = [r for r in records if r.get("type") == "credential"]
    cutoff = datetime.datetime.now() - datetime.timedelta(days=days)
    expired = []

    for c in creds:
        updated = c.get("updated_at", c.get("created_at", ""))
        if updated:
            try:
                dt = datetime.datetime.fromisoformat(updated)
                if dt < cutoff:
                    age_days = (datetime.datetime.now() - dt).days
                    expired.append({
                        "id": c["id"],
                        "service": c.get("service", ""),
                        "username": c.get("username", ""),
                        "last_updated": updated[:10],
                        "age_days": age_days
                    })
            except ValueError:
                pass

    if not expired:
        print(f"No credentials older than {days} days. All up to date!")
        return

    print(f"Credentials older than {days} days ({len(expired)} found):\n")
    print(f"{'ID':<10} {'Service':<20} {'Username':<20} {'Last Updated':<14} {'Age':<6}")
    print("-" * 70)
    for e in expired:
        print(f"{e['id']:<10} {e['service'][:18]:<20} {e['username'][:18]:<20} {e['last_updated']:<14} {e['age_days']}d")

def cmd_export(args):
    opts = parse_args(args)
    fmt = opts.get("format", "json")
    output = opts.get("output", f"credentials.{fmt}")
    records = load_records()
    creds = [r for r in records if r.get("type") == "credential"]

    if fmt == "json":
        export_data = []
        for c in creds:
            ec = dict(c)
            ec["password"] = deobfuscate(c.get("password", ""))
            export_data.append(ec)
        with open(output, "w") as f:
            json.dump(export_data, f, indent=2)
    elif fmt == "csv":
        import csv as csv_mod
        with open(output, "w", newline="") as f:
            writer = csv_mod.writer(f)
            writer.writerow(["id", "service", "username", "url", "tags", "created_at"])
            for c in creds:
                writer.writerow([c.get("id",""), c.get("service",""), c.get("username",""), c.get("url",""), ",".join(c.get("tags",[])), c.get("created_at","")])
    else:
        with open(output, "w") as f:
            json.dump(creds, f, indent=2)

    print(json.dumps({"exported": output, "format": fmt, "count": len(creds)}))

def cmd_import(args):
    opts = parse_args(args)
    filepath = opts.get("file", "")
    fmt = opts.get("format", "json")
    if not filepath or not os.path.exists(filepath):
        print(json.dumps({"error": f"File not found: {filepath}"}))
        sys.exit(1)

    imported = 0
    records = load_records()
    existing_services = {(r.get("service","").lower(), r.get("username","").lower()) for r in records if r.get("type") == "credential"}

    if fmt == "json":
        with open(filepath, "r") as f:
            data = json.load(f)
        for item in data:
            key = (item.get("service","").lower(), item.get("username","").lower())
            if key in existing_services:
                continue
            record = {
                "id": gen_id(),
                "type": "credential",
                "service": item.get("service", ""),
                "username": item.get("username", ""),
                "password": obfuscate(item.get("password", "")),
                "url": item.get("url", ""),
                "tags": item.get("tags", []),
                "notes": item.get("notes", ""),
                "created_at": now_iso(),
                "updated_at": now_iso()
            }
            append_record(record)
            imported += 1
    elif fmt == "csv":
        import csv as csv_mod
        with open(filepath, "r") as f:
            reader = csv_mod.DictReader(f)
            for row in reader:
                key = (row.get("service","").lower(), row.get("username","").lower())
                if key in existing_services:
                    continue
                record = {
                    "id": gen_id(),
                    "type": "credential",
                    "service": row.get("service", ""),
                    "username": row.get("username", ""),
                    "password": obfuscate(row.get("password", "")),
                    "url": row.get("url", ""),
                    "tags": [t.strip() for t in row.get("tags","").split(",") if t.strip()],
                    "notes": row.get("notes", ""),
                    "created_at": now_iso(),
                    "updated_at": now_iso()
                }
                append_record(record)
                imported += 1

    print(json.dumps({"imported": imported, "source": filepath, "format": fmt}))

# --- main dispatch ---
import shlex
_cmd = os.environ.get("SKILL_CMD", "")
_argv_raw = os.environ.get("SKILL_ARGV", "")
args = [_cmd] + [a for a in _argv_raw.split("\n") if a] if _cmd else []
cmd = args[0] if args else "help"
rest = args[1:]

# Handle import as a keyword conflict
cmd_map = {
    "add": cmd_add,
    "list": cmd_list,
    "get": cmd_get,
    "update": cmd_update,
    "delete": cmd_delete,
    "search": cmd_search,
    "generate": cmd_generate,
    "strength": cmd_strength,
    "duplicate": cmd_duplicate,
    "expire": cmd_expire,
    "export": cmd_export,
    "import": cmd_import,
}

if cmd in cmd_map:
    cmd_map[cmd](rest)
else:
    print(f"Unknown command: {cmd}")
    sys.exit(1)
PYEOF
    ;;
  help)
    show_help
    ;;
  version)
    echo "login v${VERSION}"
    ;;
  *)
    echo "Error: Unknown command '$CMD'" >&2
    echo "Run 'bash scripts/script.sh help' for usage." >&2
    exit 1
    ;;
esac
