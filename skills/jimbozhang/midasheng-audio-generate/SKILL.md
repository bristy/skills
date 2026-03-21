---
name: midasheng-audio-generate
description: Developed by Xiaomi and Shanghai Jiao Tong University. Transform text into high‑quality audio scenes with speech, SFX, music, and ambiance. Demo: https://nieeim.github.io/Dasheng-AudioGen-Web/
endpoint:
  - url: https://llmplus.ai.xiaomi.com/dasheng/audio/gen
    purpose: Primary audio generation interface
  - url: https://llmplus.ai.xiaomi.com/metrics
    purpose: Query service queue status
authentication: none
privacy:
  data_sent: User-provided text prompts and any agent-generated enhancements
  data_retained: Unknown (dependent on third-party provider's policy)
  recommendation: >
    1. DO NOT include any personally identifiable information (PII), sensitive,
       or confidential content in prompts.
    2. The agent must NOT invent or add PII/sensitive data when enriching prompts.
    3. All generated content is transmitted to external endpoints without encryption
       beyond HTTPS. Assume no data protection guarantees.
links:
  - name: Demo Page
    url: https://nieeim.github.io/Dasheng-AudioGen-Web/
  - name: Hugging Face Demo
    url: https://huggingface.co/spaces/mispeech/Dasheng-AudioGen
  - name: Code Repository
    url: https://github.com/NieeiM/Dasheng-Audiogen
requirements:
  - curl
---

# midasheng-audio-generate

Audio scene generation from text descriptions. Generates WAV audio with speech, sound effects, music, and environmental sounds.

## 1. Trigger
Use this skill when the user requests audio, sound effects, or music generation based on a text description.

## 2. Execution Steps

### Step 1: Design the Audio Scene (Prompt Refinement)
Before calling the API, you must act as an expert Audio Scene Architect and Foley Designer. Deeply understand the user's natural language input (which may be in any language) and translate it into a highly structured tagged string based on real-world acoustic logic and scene realism.

**Prompt Tag Definition:**
* `<|caption|>`: The overall, comprehensive description of the audio scene.
* `<|speech|>`: Speaker identity (e.g., middle-aged man, energetic girl) and speaking style.
* `<|asr|>`: The actual transcript / spoken dialogue.
* `<|sfx|>`: Specific sound effects present in the audio (e.g., footsteps, doorbell, dog barking).
* `<|music|>`: Description of background music (e.g., soft jazz, tense orchestral).
* `<|env|>`: Environmental or ambient background noise (e.g., city bustle, forest wind and crickets).

**Crucial Generation Rules:**
1.  **Scene Enrichment**: Do not merely copy the user's input! Act as a sound designer and logically enrich the scene.
2.  **Speech & Dialogue Generation**: If the user explicitly mentions speech or implies a speaking scenario, creatively generate a reasonable and vivid transcript for the `<|speech|>` and `<|asr|>` fields.
3.  **Strict ASR Formatting**: For the `<|asr|>` tag, output **only the raw spoken text**. Do not include any speaker labels or narration, such as “man:”, “speaker1:”, or “a man says”.
4.  **Omit Missing Elements**: If any element is not relevant, **directly omit its corresponding tag**.
5.  **Language & Case Constraint**: The entire generated prompt string MUST be in **lowercase English**, including `<|asr|>` content. 
6.  **Strict Output**: Output ONLY the formatted tagged string internally for the next step.

### Step 2: Execute Command
```bash
curl -X POST "https://llmplus.ai.xiaomi.com/dasheng/audio/gen" \
  -H "Content-Type: application/json" \
  -d "{\"text\": \"<FORMATTED_PROMPT_STRING>\"}" \
  -o <FILENAME.wav>
```

## 3. Queue Status

### Query Command
```bash
curl -X POST "https://llmplus.ai.xiaomi.com/metrics?path=/dasheng/audio/gen"
```

### Returned Fields
- `active`: Number of currently active requests
- `avg_latency_ms`: Average processing latency (milliseconds)
- Estimated wait time = active × avg_latency_ms

### When to Call
1. **When the IM is about to timeout but the audiogen service has not returned a result**: Check the queue status and inform the user, asking them to inquire again later.
2. **When the user asks about task progress later but the service still hasn't returned**: Check the latest queue status and report it back to the user.

### Status Levels
- 🟢 active=0 or estimated wait <5s → Service idle
- 🟡 Estimated wait 5-30s → Slight queue
- 🔴 Estimated wait >30s → Queue is long, recommend trying again later
