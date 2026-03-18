# Content Claw - TODOS

## Done

- Recipe YAML schema and 6 recipes
- SKILL.md with full pipeline (10-step spec-first generation)
- Source extractors (web, PDF, GitHub, Reddit, X)
- 8 agent prompts with spec-first two-phase generation
- fal.ai image generation with model routing (Recraft V4, Ideogram V3, Flux)
- Brand graph system (identity, audience, strategy, visual, feedback layers)
- Create recipe wizard
- Topic discovery (Exa + Reddit + X scraping)
- Publishing to Reddit and X (actually submits via Playwright)
- UTM tracking on published links
- Engagement tracking with feedback loop into brand graph
- Shared browser module (create_browser, create_browser_context)
- Shared scoped env loader (only FAL_KEY, EXA_API_KEY)
- Discord notifications via openclaw CLI
- Scheduled discovery + tracking via cron
- Content queue / inbox
- Smart recipe suggestion (source type + feedback scoring)
- Remix command (re-render for different platform)
- Configurable digest (hourly/daily/weekly)
- Recipe performance leaderboard
- Engagement alerts (threshold-based)
- Source bookmarking
- Brand graph templates (saas-b2b, dev-tools, ai-ml)
- Brand graph diff (visible feedback loop)
- A/B spec testing (variant_group/variant_label)
- Cross-platform support (Claude Code, OpenClaw, NemoClaw)
- Published on ClawHub
- MIT-0 license

## P1 - Next up

### Full test suite with browser mocking
- **What:** ~50 tests covering all pure functions plus Playwright mocking for browser interactions
- **Why:** Zero test coverage on discover_topics, publish, track_engagement. These are the most complex scripts.
- **Effort:** S (CC: ~30 min)

### Fix 5 critical failure mode gaps
- **What:** Add error handling for: cron crash silence (log + notify on failure), browser OOM (catch + restart), port conflict (retry with new port), Reddit captcha detection (detect + notify user), feedback.yaml concurrent writes (file locking, partially done)
- **Why:** Silent failures in scheduled tasks are invisible. User won't know discovery stopped.
- **Effort:** S (CC: ~20 min)

### Convert remaining 7 recipes from CSV
- **What:** The original Notion export had 13 recipes. Only 6 are converted. Convert the remaining 7.
- **Why:** More recipes means more content variety out of the box.
- **Effort:** S (CC: ~10 min)

## P2 - Should build

### Persistent browser daemon
- **What:** Single Chromium instance on the VPS, all scripts connect via CDP. Eliminates 3-sec cold start per browser launch.
- **Why:** With hourly cron running discovery + tracking + alerts, that's 10+ browser launches per cycle.
- **Effort:** M (CC: ~1 hour)

### Recipe preview / dry-run mode
- **What:** Before running a full recipe, show what will happen: blocks to generate, prerequisites, brand graph requirements.
- **Why:** Builds user trust. Especially important for the Discord bot where users can't see the pipeline.
- **Effort:** S (CC: ~10 min)

### Content calendar view
- **What:** "Show me this week's content" command: summary of generated/published content by day and platform.
- **Why:** Turns Content Claw from a tool into a content ops dashboard.
- **Effort:** M (CC: ~30 min)
- **Depends on:** Queue and digest systems (done)

## P3 - Future

### Recipe marketplace / sharing
- **What:** Community-contributed recipes, brand graph templates by industry, agent prompt sharing.
- **Why:** Network effects. More recipes = more value.
- **Effort:** XL
- **Depends on:** Stable schema, ClawHub publication (done)

### YouTube / podcast transcript extraction
- **What:** Add YouTube and podcast extractors to the source extractor registry.
- **Why:** Two of the 13 original recipes target podcasts. Currently no transcript extraction.
- **Effort:** M (CC: ~30 min)
