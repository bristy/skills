# Google Sheet Setup

## Initial Setup

1. Create a new Google Sheet or copy the template
2. Name it "Job Applications Tracker" (or similar)
3. Note the Spreadsheet ID from the URL: `docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/edit`

## Tab Structure

### Tab 1: Jobs

Main tracker with 16 columns (A-P):

| Column | Header | Description |
|--------|--------|-------------|
| A | Our Job ID | Internal ID (JOB001, JOB002, ...) |
| B | Employer Job ID | Employer's requisition number |
| C | Company | Company name |
| D | Role | Job title |
| E | Location | City, Remote, Hybrid |
| F | Salary | Compensation range |
| G | Source | How discovered |
| H | URL | Job posting link |
| I | Status | Current status (see valid values) |
| J | Applied Date | YYYY-MM-DD |
| K | Contacts | Google Contacts links |
| L | Next Action | Next step to take |
| M | Next Date | Date for next action |
| N | Resume | Resume version used |
| O | Cover Letter | Y/N or filename |
| P | Log (Latest 3) | **FORMULA** — auto-populated |

**Column P Formula** (per row, starting row 2):
```
=IFERROR(TEXTJOIN(CHAR(10),TRUE,QUERY('Activity Log'!A:D,"SELECT A,C,D WHERE B='"&A2&"' ORDER BY A DESC LIMIT 3")),"")
```

### Tab 2: Activity Log

Timestamped event history with 4 columns:

| Column | Header | Description |
|--------|--------|-------------|
| A | Timestamp | YYYY-MM-DD HH:MM |
| B | Our Job ID | Links to Jobs tab |
| C | Event Type | See valid event types |
| D | Details | Event description |

### Tab 3: Add or Edit Job (Optional)

Form interface for manual entry. See Apps Script installation below.

## Apps Script Installation

1. Open your Google Sheet
2. Go to **Extensions → Apps Script**
3. Delete any existing code in `Code.gs`
4. Paste contents of `scripts/job-tracker-appscript.gs`
5. Click **Save** (💾 icon)
6. Close Apps Script editor
7. Refresh the Google Sheet
8. Run **🎯 Job Tracker → 🔄 Refresh Next ID** to initialize

### First Run Authorization

When you first run any function:
1. Click "Review permissions"
2. Choose your Google account
3. Click "Advanced" → "Go to Untitled project (unsafe)"
4. Click "Allow"

This grants the script access to edit spreadsheets.

## CLI Configuration

Update the `SPREADSHEET_ID` in `scripts/job-tracker`:

```bash
SPREADSHEET_ID="your-spreadsheet-id-here"
```

Or set via environment variable (if the script supports it).

## gog CLI Dependency

The job-tracker script uses `gog` (Google Workspace CLI). Ensure it's installed and authenticated:

```bash
# Check gog is available
gog --version

# Authenticate if needed
gog auth login
```

## Valid Values Reference

### Statuses (Title Case)
- Discovered
- Applied  
- Screening
- Interview
- Karat Test Scheduled
- Offer
- Rejected
- Withdrawn
- Accepted
- Closed

### Event Types (lowercase)
- discovered
- applied
- recruiter_contact
- user_reply
- interview_scheduled
- interview_completed
- test_scheduled
- test_completed
- offer_received
- rejection
- follow_up
- status_change
- note
- historical_note (migration only)

### Contact Format
Google Contacts links only:
```
https://contacts.google.com/person/c1234567890abcdef
```

Multiple contacts: comma, semicolon, or space separated.

## Template Sheet

A template sheet is available at:
[TODO: Add template link when published]

Copy the template to your own Google Drive to get started quickly.
