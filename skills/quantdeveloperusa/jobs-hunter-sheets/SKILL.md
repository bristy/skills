---
name: job-hunter
description: Unified job hunting automation — discover new jobs, apply to positions, and track application status with activity logging. Use when: (1) searching for new job opportunities on LinkedIn/Indeed/job boards, (2) preparing and submitting job applications, (3) tracking job application status and pipeline, (4) logging interview events, recruiter contacts, or status changes, (5) querying or filtering jobs by status/company/role, (6) managing follow-ups and next actions. Integrates with Google Sheets as the canonical data store.
---

# Job Hunter

Unified skill for job hunting automation: **Discover → Apply → Track**.

## Quick Start

```bash
# View all commands
job-tracker help

# List active jobs
job-tracker list --status interview

# Add a discovered job
job-tracker add --company "Morgan Stanley" --role "AI Architect" --source LinkedIn

# Log an event
job-tracker log JOB002 --event interview_scheduled --details "3rd round Monday 10am"

# Search jobs
job-tracker search "citi" --columns company,role
```

## Architecture

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   Discovery     │────►│    Apply        │────►│     Track       │
│                 │     │                 │     │                 │
│ • Search boards │     │ • Prepare app   │     │ • Update status │
│ • Parse emails  │     │ • Submit        │     │ • Log activity  │
│ • Add to sheet  │     │ • Log applied   │     │ • Plan followup │
└─────────────────┘     └─────────────────┘     └─────────────────┘
                              │
                              ▼
                    ┌─────────────────────┐
                    │   Google Sheet      │
                    │ (Single Source)     │
                    │                     │
                    │ • Jobs tab          │
                    │ • Activity Log tab  │
                    │ • Add/Edit Form tab │
                    └─────────────────────┘
```

## Task 1: Discover New Jobs

Search job boards and add opportunities to the tracker.

### Sources to Monitor
- **LinkedIn Jobs** — search by role, location, salary
- **Indeed** — aggregate from multiple boards  
- **BuiltIn/Wellfound** — startup-focused roles
- **Email inbox** — recruiter outreach
- **Calendar** — extract job context from interview events

### Discovery Workflow

1. **Search** job boards for matching roles
2. **Extract** job details: company, role, location, salary, URL
3. **Add** to tracker with `job-tracker add`
4. **Log** discovery source for attribution

```bash
# Add from LinkedIn search
job-tracker add \
  --company "Goldman Sachs" \
  --role "VP, AI Engineering" \
  --location "NYC" \
  --salary "$200k-$275k" \
  --source "LinkedIn" \
  --url "https://linkedin.com/jobs/view/123456"

# Add from recruiter email
job-tracker add \
  --company "Jane Street" \
  --role "Quantitative Researcher" \
  --source "Recruiter Email" \
  --contacts "https://contacts.google.com/person/c123456"
```

### Email Parsing Pattern

When scanning email for job opportunities:
1. Look for recruiter signatures, job titles, company names
2. Extract compensation if mentioned
3. Note urgency signals ("immediate need", "urgent hire")
4. Create job entry and log the email as source

## Task 2: Apply for Jobs

Prepare and submit applications, tracking the transition from Discovered to Applied.

### Application Checklist
- [ ] Resume tailored for role
- [ ] Cover letter (if required)
- [ ] Application questions answered
- [ ] Referrals checked (LinkedIn connections at company)
- [ ] Application submitted
- [ ] Confirmation received

### Apply Workflow

1. **Prepare** materials for the specific role
2. **Submit** application via job board or company portal
3. **Update** status to "Applied"
4. **Log** application details

```bash
# Update status when applying
job-tracker update JOB015 \
  --status Applied \
  --resume "AI-Architect-Resume-v3" \
  --applied-date "2026-03-19"

# Log the application event
job-tracker log JOB015 \
  --event applied \
  --details "Applied via company portal. Referred by John Smith."
```

### Cover Letter Pattern

When preparing applications:
1. Research company recent news/projects
2. Match resume bullets to job requirements
3. Personalize opening paragraph
4. Include specific achievements with metrics

## Task 3: Track & Update Jobs

Maintain accurate pipeline status and log all activity.

### Status Lifecycle

```
Discovered → Applied → Screening → Interview → Offer → Accepted
                 │          │          │         └──► Rejected
                 │          │          └──────────► Rejected  
                 │          └─────────────────────► Rejected
                 └───────────────────────────────► Withdrawn
```

### Valid Statuses (Title Case)
- `Discovered` — Found but not yet applied
- `Applied` — Application submitted
- `Screening` — Initial review/HR screen
- `Interview` — Active interview process
- `Karat Test Scheduled` — Technical assessment pending
- `Offer` — Offer received
- `Rejected` — Not selected
- `Withdrawn` — Candidate withdrew
- `Accepted` — Offer accepted
- `Closed` — Position no longer available

### Activity Logging

Log every meaningful event for pipeline visibility.

```bash
# Log recruiter contact
job-tracker log JOB002 --event recruiter_contact \
  --details "Call with Jane from HR. Moving to technical round."

# Log interview
job-tracker log JOB002 --event interview_completed \
  --details "System design interview with VP Engineering. Discussed microservices architecture."

# Log status change
job-tracker update JOB002 --status Offer
# (automatically logs status_change event)

# Log follow-up needed
job-tracker log JOB002 --event follow_up \
  --details "Send thank-you email to interviewers"
```

### Valid Event Types (lowercase)
- `discovered` — Initial job discovery
- `applied` — Application submitted
- `recruiter_contact` — Recruiter reached out
- `user_reply` — You responded to recruiter
- `interview_scheduled` — Interview booked
- `interview_completed` — Interview done
- `test_scheduled` — Assessment booked
- `test_completed` — Assessment done
- `offer_received` — Offer extended
- `rejection` — Application rejected
- `follow_up` — Follow-up needed
- `status_change` — Status updated
- `note` — General note

### Pipeline Queries

```bash
# Jobs needing action
job-tracker list --status discovered

# Active interviews
job-tracker list --status interview

# Search by company
job-tracker search "goldman" --columns company

# Search by role pattern
job-tracker search "AI.*Architect" --regex --columns role

# Recent activity
job-tracker logs --limit 20

# Activity for specific job
job-tracker logs JOB002
```

## Validation Rules

The CLI enforces these rules (matching the Google Sheet form):

### Status Validation
- Must be one of the 10 valid statuses
- Auto-normalizes to Title Case (`interview` → `Interview`)

### Contacts Validation
- Must be Google Contacts links: `https://contacts.google.com/person/c[alphanumeric]`
- Multiple links separated by comma/semicolon/space
- Bypass with `--no-strict-contacts` flag

### Required Fields
- `--company` — Company name
- `--role` — Job title/role

## Resources

### scripts/job-tracker

Bash CLI for CRUD operations on the Google Sheet. Run `job-tracker help` for usage.

Key commands:
- `add` — Create new job entry
- `update` — Modify existing job
- `log` — Add activity entry
- `show` — Display job details
- `list` — List/filter jobs
- `search` — Search with regex/fuzzy
- `logs` — View activity history
- `schema` — Show valid values

### scripts/job-tracker-appscript.gs

Google Apps Script for the "Add or Edit Job" form tab. Install in Google Sheets via Extensions → Apps Script.

Provides:
- 🎯 Job Tracker menu with form automation
- Data validation dropdowns for Status and Event Type
- Contact link validation
- Auto-generated Job IDs

### references/google-sheet-setup.md

Setup instructions for the Google Sheet tracker. See [references/google-sheet-setup.md](references/google-sheet-setup.md).

## Configuration

The skill requires a Google Sheet with these tabs:

| Tab | Purpose |
|-----|---------|
| **Jobs** | Main tracker (columns A-P) |
| **Activity Log** | Timestamped event history |
| **Add or Edit Job** | Form interface (optional) |

Set `SPREADSHEET_ID` in the job-tracker script or configure via environment.
