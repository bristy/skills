# Recovery Playbook — When You're Stuck

## The 7-Point Checklist (run in order)

1. **Read the error verbatim** — every character of the traceback, not a skim. The fix is usually in line 3 of the stack trace you glossed over.
2. **Check ALL logs** — stdout is not enough. Check stderr, `journalctl -u <service>`, app-specific log files (`/tmp/*.log`, `~/.openclaw/*.log`), CI run logs. The real error is usually one level deeper.
3. **Search the exact error** — copy the error string verbatim into `web_search`. Someone has hit this before. Their fix is 30 seconds away.
4. **Read the source** — if a library or tool is misbehaving, `cat` its source file. The behaviour lives in the code, not the docs.
5. **Switch approach entirely** — if A failed twice, don't try A again. What's approach B? Approach C? Write them out before picking one.
6. **Audit assumptions** — list what you assumed (env vars set, file exists, port open, package installed). Which ones haven't you verified? Verify them now with `echo`, `ls`, `curl`, `which`.
7. **Isolate and simplify** — reproduce the failure in the smallest possible case. Fix that. Scale back up.

Only after all 7 are documented and exhausted is it acceptable to surface a blocker.

---

## Failure Pattern Library

### "Command not found" / ImportError
- Check `which <cmd>`, `pip show <pkg>`, `uv pip list`
- Is the venv active? Is PATH set? Did you use `uv run python` not `python3`?
- Install with `uv pip install <pkg>` or check TOOLS.md for the right env

### SSH timeout / connection refused
- `ssh -v` for verbose output — which step is hanging?
- Check `nc -zv <host> <port>` to test TCP reachability
- Is the service running on the remote? `ssh ... 'systemctl status <svc>'`
- Try a shorter `ConnectTimeout`: `-o ConnectTimeout=5`

### CI failure / test failure
- Read the FULL test output — not just `FAILED`. Find the assertion.
- Run just the failing test locally first: `pytest tests/test_foo.py::test_bar -v`
- Is it a mock issue? Is it an env dependency? Is it a race condition?

### Git push rejected
- `git status` first — are there uncommitted changes?
- `git log --oneline -5` — check the divergence
- Rebase: `git fetch origin && git rebase origin/main`
- Use `--admin` to bypass protection when authorised

### API / HTTP error
- `curl -v` to see full request/response including headers
- Check rate limits (429 → back off, retry after)
- Check auth headers — token expired? Wrong format?
- Test with minimal payload first to isolate field issues

### File not found
- `find ~ -name "<file>" 2>/dev/null` — it exists, just not where you think
- Check symlinks: `ls -la <path>`
- Check cwd: `pwd` — relative paths are relative to *this* directory

### Subprocess timeout
- Add explicit timeout to exec: `timeout=120`
- Use `background=True` + `process(poll)` for long-running commands
- Or use `setsid ... &` + polling pattern for fire-and-forget

---

## Phrases That Mean "I Haven't Tried Hard Enough"

Before using any of these, run the checklist above:

| Phrase | What to do instead |
|---|---|
| "I cannot solve this" | Run steps 5–7 |
| "Probably a permissions issue" | `ls -la`, `id`, `sudo -l` — verify |
| "Probably a network issue" | `curl -v`, `nc -zv`, `ping` — test it |
| "I need more context" | Search for it, read the source, grep the logs |
| "You might need to manually" | Try it yourself first |
| "This is out of scope" | Is it? Try the obvious path before saying so |

---

## Sub-Agent Priming Block

Paste this into any sub-agent task prompt for hard problems:

```
When you hit obstacles:
- Read the FULL error — every line of the traceback
- Check logs (stderr, journalctl, /tmp/*.log)
- web_search the exact error string
- Try an alternative approach before retrying the same one
- Run `uv run python` (never bare `python3`)
- Do NOT give up after 2 tries
- Do NOT ask the user to handle things you can investigate yourself
Run the 7-point checklist from agent-motivator/references/recovery-playbook.md before surfacing any blocker.
```
