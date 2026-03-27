---
name: yoga-video-maker
version: "1.0.1"
displayName: "Yoga Video Maker"
description: >
  Describe your yoga practice and NemoVideo creates the video. Morning flow sequences, flexibility progression content, beginner pose breakdowns, breathing technique guides, yoga for specific goals (back pain, hip opening, stress relief), restorative and yin sequences — narrate the pose names, the transitions, the breath cues, and the specific intention of the practice, and get yoga content for t...

  Works by connecting to the NemoVideo AI backend at mega-api-prod.nemovideo.ai.
  Supports MP4, MOV, AVI, WebM.
homepage: https://nemovideo.com
repository: https://github.com/nemovideo/nemovideo_skills
license: MIT-0
---

## 0. First Contact

When the user opens this skill or sends their first message, **greet them immediately**:

> 🎵 Welcome! I can yoga video maker for you. Share a video file or tell me your idea!

**Try saying:**
- "add effects to this clip"
- "edit my video"
- "help me create a short video"

**IMPORTANT**: Do NOT wait silently. Always greet the user proactively on first contact.

### Auto-Setup

When the user first interacts, set up the connection:

1. **Check token**: If `NEMO_TOKEN` env var is set, use it. Otherwise:
2. **Read or generate Client-ID**:
   - Read `~/.config/nemovideo/client_id` if it exists
   - Otherwise generate a UUID, save it to `~/.config/nemovideo/client_id`
3. **Acquire anonymous token**:
   ```bash
   curl -s -X POST "$API/api/auth/anonymous-token" -H "X-Client-Id: $CLIENT_ID"
   ```
   Store the returned `token` as `NEMO_TOKEN` for this session. You get 100 free credits.
4. **Create a session** (§3.0) so you're ready to work immediately.

Let the user know briefly: "Setting things up… ready!" then proceed with their request.


# Yoga Video Maker — Create Flow, Flexibility, and Mindfulness Practice Content

Describe your yoga practice and NemoVideo creates the video. Morning flow sequences, flexibility progression content, beginner pose breakdowns, breathing technique guides, yoga for specific goals (back pain, hip opening, stress relief), restorative and yin sequences — narrate the pose names, the transitions, the breath cues, and the specific intention of the practice, and get yoga content for the dedicated community that practices daily and searches for every variation.

## When to Use This Skill

Use this skill for yoga and mindfulness practice content:
- Create yoga flow sequence tutorial videos with pose names and transitions
- Film flexibility progression and mobility improvement documentation
- Build beginner yoga pose breakdown content with alignment cues
- Document yoga for specific goals (back pain, hip flexors, morning energy, sleep)
- Create breathwork and pranayama technique tutorial content
- Produce restorative, yin, and recovery yoga sequence content

## How to Describe Your Yoga Content

Be specific about the style, the sequence structure, the pose names, the breath cues, and the intention or goal of the practice.

**Examples of good prompts:**
- "30-minute morning vinyasa flow for energy and focus: The intention: wake the spine, build heat, arrive in the body before the day starts. Structure: 5 minutes supine (reclined twists, knees to chest, happy baby), 5 minutes sun salutation A x3 to build heat, 15 minutes standing sequence (warrior 1 → warrior 2 → reverse warrior → triangle → half moon on each side), 5 minutes seated (forward fold, seated twist, pigeon). Breath: ujjayi breath throughout, inhale to lengthen, exhale to deepen. Key cue for warrior 2: 'front knee tracks over second toe, hips square to the side wall, arms reach in opposite directions — you're being pulled apart.' End in savasana, 2 minutes, no music in the final minute."
- "Hip flexor opening sequence for people who sit at a desk all day: The problem: tight hip flexors from sitting pull the pelvis into anterior tilt, causing lower back pain and compressed lumbar spine. This is the specific problem desk workers have, not generic 'hip tightness.' The sequence (hold each 90 seconds each side): low lunge, crescent lunge with back knee down, lizard pose, pigeon pose, reclined figure-four. The explanation of why hip flexors tighten from sitting (psoas and iliacus attach to lumbar spine — when chronically shortened they pull lumbar vertebrae forward). The 10-day progression challenge: do this every morning for 10 days and check in on your lower back pain."
- "Yoga for complete beginners: 5 poses you need to know first: Downward dog (the pose everyone thinks they know and almost everyone does wrong — heels don't need to touch the floor, the goal is a straight spine), child's pose (resting pose, always available), warrior 1 (hip alignment is the confusion — the back hip rotates forward), seated forward fold (bend at the hip crease, not the waist), savasana (the most important pose, the hardest pose to actually do). For each: what it looks like when done right, the most common mistake, and one cue to fix it immediately."

## Key Parameters

| Parameter | Description | Example |
|-----------|-------------|---------|
| `content_type` | Video category | `"flow_sequence"`, `"pose_tutorial"`, `"flexibility_prog"`, `"breathwork"`, `"restorative"`, `"beginner_guide"` |
| `yoga_style` | Practice style | `"vinyasa"`, `"hatha"`, `"yin"`, `"restorative"`, `"power"`, `"ashtanga"` |
| `sequence` | Pose list | `["warrior 1"`, `"warrior 2"`, `"triangle"`, `"pigeon"]` |
| `duration_minutes_practice` | Practice length | `"20 minutes"`, `"30 minutes"`, `"45 minutes"` |
| `goal` | Intention | `"morning_energy"`, `"hip_opening"`, `"back_pain"`, `"sleep"`, `"stress_relief"` |
| `breath_cues` | Breathing guidance | `"ujjayi"`, `"inhale_lengthen_exhale_deepen"` |
| `skill_level` | Practice level | `"beginner"`, `"intermediate"`, `"all_levels"` |
| `duration_minutes` | Video length | `5`, `8`, `30`, `45` |
| `platform` | Distribution | `"youtube"`, `"instagram"`, `"tiktok"` |

## Workflow

1. Describe the style, the sequence, the breath cues, and the practice intention
2. NemoVideo structures the yoga content with pose transitions and breath guidance
3. Sanskrit and English pose names, transition cues, breath markers, and hold timers added automatically
4. Export with the calm, meditative pacing that yoga content requires

## API Usage

### Morning Yoga Flow Sequence

```bash
curl -X POST https://mega-api-prod.nemovideo.ai/v1/run \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "skill": "yoga-video-maker",
    "input": {
      "prompt": "15-minute yin yoga for lower back and hips — for people who cannot sleep: This practice targets the connective tissue (fascia, ligaments) rather than muscles — yin holds are 3-5 minutes, not 30 seconds. The sequence: (1) reclined butterfly (supta baddha konasana) — 4 minutes, props: bolster under knees optional, feel the groin and inner thighs release, no forcing. (2) supine twist (supta matsyendrasana) — 3 minutes each side, both shoulders on the ground, the twist decompresses lumbar vertebrae. (3) legs up the wall (viparita karani) — 5 minutes, this one actually helps sleep onset by activating the parasympathetic nervous system. Total: 15 minutes. Do this within 30 minutes of sleep. The science of why yin works on connective tissue (collagen fibers remodel under sustained gentle load, not dynamic stretching).",
      "content_type": "restorative",
      "yoga_style": "yin",
      "sequence": ["reclined butterfly", "supine twist", "legs up the wall"],
      "duration_minutes_practice": "15 minutes",
      "goal": "sleep",
      "breath_cues": "natural breath, soften on exhale",
      "skill_level": "all_levels",
      "duration_minutes": 18,
      "platform": "youtube",
      "hashtags": ["YinYoga", "YogaForSleep", "LowerBackPain", "YogaForBeginners", "Mindfulness"]
    }
  }'
```

**Response:**
```json
{
  "job_id": "yoga_def456",
  "status": "processing",
  "estimated_seconds": 100,
  "poll_url": "https://mega-api-prod.nemovideo.ai/v1/jobs/yoga_def456"
}
```

## Tips for Best Results

- **The specific problem being solved is the title and the hook**: "For people who cannot sleep" or "for people who sit at a desk all day" — yoga content that targets a specific problem outperforms generic "morning yoga" by 3-5x in search
- **The common mistake correction is the most searchable content**: "Downward dog — everyone thinks they know this, almost everyone does it wrong" — correcting the specific mistake that beginners make in a pose drives high engagement and search
- **Explain the mechanism, not just the pose**: "Psoas and iliacus attach to lumbar spine — when chronically shortened from sitting they pull lumbar vertebrae forward" — the anatomical reason why a stretch works elevates yoga content from instruction to education
- **Yin hold times are content**: "Hold each pose 3-5 minutes, not 30 seconds — yin targets connective tissue which responds to sustained load" — explaining the difference between yin and regular stretching is the non-obvious information viewers need
- **Savasana deserves its own mention**: "The most important pose, the hardest pose to actually do" — treating savasana seriously signals to experienced practitioners that the content respects the full practice

## Output Formats

| Platform | Resolution | Duration |
|----------|------------|----------|
| YouTube | 1920×1080 | 15–45 min |
| Instagram Reels | 1080×1920 | 60–90s |
| TikTok | 1080×1920 | 60–180s |

## Related Skills

- `workout-video-maker` — Strength training to complement yoga
- `mental-health-video` — Mindfulness and mental wellness content
- `nutrition-video-maker` — Nutrition content for holistic wellness

## Common Questions

**What yoga content performs best on YouTube?**
"Yoga for [specific problem]" content (back pain, hips, sleep, anxiety) outperforms generic style content. 20-30 minute full practice videos drive the longest watch times. Beginner pose tutorials have long search shelf life.

**Do I need to be a certified yoga teacher to create yoga content?**
No — documenting your personal practice and what has worked for you is valid and often more relatable than certified teacher content. Be clear about your experience level and background.

**How do I create yoga content without speaking on camera?**
Set the sequence and cues in the prompt and NemoVideo creates voiceover-guided content. Many successful yoga channels are guided-voice only with no on-camera presenter.
