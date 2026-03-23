#!/usr/bin/env python3
"""
163/126/yeah.net (Coremail) Mail Client
Handles the Coremail-specific IMAP ID command requirement.
"""
import imaplib
import smtplib
import email
import os
import sys
import json
import argparse
from email.header import decode_header
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from datetime import datetime, timedelta
from pathlib import Path


def load_env(env_path=None):
    """Load config from .env file."""
    if env_path is None:
        env_path = os.path.expanduser("~/.openclaw/email-monitor/.env")
    config = {}
    if not os.path.exists(env_path):
        print(f"❌ Config not found: {env_path}")
        sys.exit(1)
    with open(env_path) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                config[k.strip()] = v.strip()
    return {
        "imap_server": config.get("IMAP_SERVER", "imap.163.com"),
        "imap_port": int(config.get("IMAP_PORT", "993")),
        "smtp_server": config.get("SMTP_SERVER", "smtp.163.com"),
        "smtp_port": int(config.get("SMTP_PORT", "465")),
        "email": config.get("EMAIL_ADDRESS", ""),
        "password": config.get("EMAIL_PASSWORD", ""),
    }


def decode_str(s):
    """Decode email header string."""
    if s is None:
        return ""
    parts = decode_header(s)
    result = []
    for value, charset in parts:
        if isinstance(value, bytes):
            result.append(value.decode(charset or "utf-8", errors="ignore"))
        else:
            result.append(value)
    return " ".join(result)


def get_body(msg):
    """Extract plain text body from email message."""
    if msg.is_multipart():
        for part in msg.walk():
            ct = part.get_content_type()
            if ct == "text/plain":
                payload = part.get_payload(decode=True)
                charset = part.get_content_charset() or "utf-8"
                return payload.decode(charset, errors="ignore")
            elif ct == "text/html":
                payload = part.get_payload(decode=True)
                charset = part.get_content_charset() or "utf-8"
                html = payload.decode(charset, errors="ignore")
                # Strip HTML tags (basic)
                import re
                text = re.sub(r"<[^>]+>", "", html)
                text = re.sub(r"\s+", " ", text).strip()
                return text[:2000]
    else:
        payload = msg.get_payload(decode=True)
        if payload:
            charset = msg.get_content_charset() or "utf-8"
            return payload.decode(charset, errors="ignore")
    return ""


def connect_imap(config):
    """Connect to IMAP with Coremail ID command."""
    mail = imaplib.IMAP4_SSL(config["imap_server"], config["imap_port"])

    # Critical: Coremail requires ID command before mailbox operations
    tag = mail._new_tag()
    mail.send(tag + b' ID ("name" "IMAPClient" "version" "1.0.0")\r\n')
    mail.readline()
    mail.readline()

    mail.login(config["email"], config["password"])
    return mail


def cmd_read(args, config):
    """Read emails from inbox."""
    mail = connect_imap(config)
    mail.select("INBOX", readonly=True)

    if args.unread:
        status, nums = mail.search(None, "UNSEEN")
    else:
        status, nums = mail.search(None, "ALL")

    if status != "OK":
        print("❌ Search failed")
        mail.close()
        mail.logout()
        return

    ids = nums[0].split()
    if not ids:
        print("📭 No emails found")
        mail.close()
        mail.logout()
        return

    # Get latest N
    limit = args.latest or len(ids)
    target_ids = ids[-limit:]

    results = []
    print(f"📧 Found {len(ids)} emails, showing {len(target_ids)}\n")

    for num in target_ids:
        try:
            _, msg_data = mail.fetch(num, "(RFC822)")
            msg = email.message_from_bytes(msg_data[0][1])
            subject = decode_str(msg["Subject"])
            from_addr = decode_str(msg["From"])
            date = decode_str(msg["Date"])
            body = get_body(msg) if args.body else ""

            entry = {
                "id": num.decode(),
                "subject": subject,
                "from": from_addr,
                "date": date,
            }
            if body:
                entry["body"] = body[:500]
            results.append(entry)

            print(f"{'─'*60}")
            print(f"📧 {subject}")
            print(f"   From: {from_addr}")
            print(f"   Date: {date}")
            if body:
                print(f"   Body: {body[:200]}...")
        except Exception as e:
            continue

    mail.close()
    mail.logout()

    if args.json:
        print("\n" + json.dumps(results, ensure_ascii=False, indent=2))

    print(f"\n✅ Done. {len(results)} emails retrieved.")


def cmd_search(args, config):
    """Search emails with local filtering (Coremail IMAP search is unreliable)."""
    mail = connect_imap(config)
    mail.select("INBOX", readonly=True)

    # Use IMAP date filters if available, otherwise fetch all
    criteria = []
    if args.since:
        criteria.append(f'SINCE {args.since}')
    if args.before:
        criteria.append(f'BEFORE {args.before}')

    if criteria:
        search_str = " ".join(criteria)
        status, nums = mail.search(None, search_str)
    else:
        status, nums = mail.search(None, "ALL")

    if status != "OK" or not nums[0]:
        print("📭 No emails found")
        mail.close()
        mail.logout()
        return

    ids = nums[0].split()
    # Scan from newest, collect up to scan_limit for local filtering
    scan_limit = min(len(ids), args.scan or 200)
    target_ids = ids[-scan_limit:]

    query_lower = args.query.lower() if args.query else None
    sender_lower = args.sender.lower() if args.sender else None
    limit = args.latest or 20

    results = []
    print(f"🔍 Scanning {len(target_ids)} emails...\n")

    for num in reversed(target_ids):
        if len(results) >= limit:
            break
        try:
            _, msg_data = mail.fetch(num, "(RFC822)")
            msg = email.message_from_bytes(msg_data[0][1])
            subject = decode_str(msg["Subject"])
            from_addr = decode_str(msg["From"])
            date = decode_str(msg["Date"])

            # Local filtering
            if query_lower:
                searchable = (subject + " " + from_addr).lower()
                if query_lower not in searchable:
                    body_text = get_body(msg).lower()
                    if query_lower not in body_text:
                        continue

            if sender_lower and sender_lower not in from_addr.lower():
                continue

            body = get_body(msg) if args.body else ""
            entry = {
                "id": num.decode(),
                "subject": subject,
                "from": from_addr,
                "date": date,
            }
            if body:
                entry["body"] = body[:500]
            results.append(entry)

            print(f"{'─'*60}")
            print(f"📧 {subject}")
            print(f"   From: {from_addr}")
            print(f"   Date: {date}")
        except Exception as e:
            continue

    mail.close()
    mail.logout()

    if not results:
        print("📭 No matching emails")
        return

    if args.json:
        print("\n" + json.dumps(results, ensure_ascii=False, indent=2))

    print(f"\n✅ Done. {len(results)} results.")


def cmd_send(args, config):
    """Send email via SMTP."""
    if args.attach:
        msg = MIMEMultipart()
        msg.attach(MIMEText(args.body or "", "plain", "utf-8"))
        for filepath in args.attach:
            filepath = os.path.expanduser(filepath)
            if not os.path.exists(filepath):
                print(f"❌ Attachment not found: {filepath}")
                return
            part = MIMEBase("application", "octet-stream")
            with open(filepath, "rb") as f:
                part.set_payload(f.read())
            encoders.encode_base64(part)
            filename = os.path.basename(filepath)
            part.add_header("Content-Disposition", f"attachment; filename={filename}")
            msg.attach(part)
    else:
        msg = MIMEText(args.body or "", "plain", "utf-8")

    msg["From"] = config["email"]
    msg["To"] = args.to
    msg["Subject"] = args.subject or "(No Subject)"
    if args.cc:
        msg["Cc"] = args.cc

    try:
        smtp = smtplib.SMTP_SSL(config["smtp_server"], config["smtp_port"])
        smtp.login(config["email"], config["password"])

        recipients = [args.to]
        if args.cc:
            recipients.extend(args.cc.split(","))

        smtp.sendmail(config["email"], recipients, msg.as_string())
        smtp.quit()
        print(f"✅ Email sent to {args.to}")
        if args.cc:
            print(f"   CC: {args.cc}")
    except Exception as e:
        print(f"❌ Send failed: {e}")


def main():
    parser = argparse.ArgumentParser(description="163/Coremail Email Client")
    parser.add_argument("--env", help="Path to .env config file")
    sub = parser.add_subparsers(dest="command")

    # read
    p_read = sub.add_parser("read", help="Read emails")
    p_read.add_argument("--unread", action="store_true", help="Only unread emails")
    p_read.add_argument("--latest", type=int, help="Latest N emails")
    p_read.add_argument("--body", action="store_true", help="Include body text")
    p_read.add_argument("--json", action="store_true", help="Output as JSON")

    # search
    p_search = sub.add_parser("search", help="Search emails")
    p_search.add_argument("query", nargs="?", help="Search in subject")
    p_search.add_argument("--from", dest="sender", help="Filter by sender")
    p_search.add_argument("--since", help="Since date (DD-Mon-YYYY)")
    p_search.add_argument("--before", help="Before date (DD-Mon-YYYY)")
    p_search.add_argument("--latest", type=int, default=20, help="Max results")
    p_search.add_argument("--scan", type=int, default=200, help="Max emails to scan")
    p_search.add_argument("--body", action="store_true", help="Include body text")
    p_search.add_argument("--json", action="store_true", help="Output as JSON")

    # send
    p_send = sub.add_parser("send", help="Send email")
    p_send.add_argument("--to", required=True, help="Recipient")
    p_send.add_argument("--subject", help="Subject line")
    p_send.add_argument("--body", help="Email body")
    p_send.add_argument("--cc", help="CC recipients (comma-separated)")
    p_send.add_argument("--attach", nargs="+", help="Attachment file paths")

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        sys.exit(1)

    config = load_env(args.env)

    if args.command == "read":
        cmd_read(args, config)
    elif args.command == "search":
        cmd_search(args, config)
    elif args.command == "send":
        cmd_send(args, config)


if __name__ == "__main__":
    main()
