# Technical Fix Reference

## Edge Microphone Button Not Working

### Symptoms
- Clicking mic button in Control UI does nothing
- Console shows: `Permissions policy violation: microphone is not allowed in this document`
- `document.featurePolicy.allowsFeature('microphone')` returns `false`

### Root Cause
OpenClaw Gateway (`gateway-cli-Dsd9gHBa.js`) hardcodes `microphone=()` in the Permissions-Policy header, blocking ALL session microphones.

Original code:
```javascript
res.setHeader("Permissions-Policy", "camera=(), microphone=(), geolocation=()");
```

### Fix (Option 1 — From Backup)
```powershell
copy "C:\Users\samuel\.openclaw\workspace-english-teacher\gateway-cli-Dsd9gHBa.js" "C:\Users\samuel\AppData\Roaming\npm\node_modules\openclaw\dist\gateway-cli-Dsd9gHBa.js"
openclaw gateway restart
```

### Fix (Option 2 — Manual Patch)
If backup is unavailable, re-download the same version and patch:

1. Find current version: `openclaw --version`
2. `npm pack openclaw@<version>` to download .tgz
3. Extract and modify `gateway-cli-Dsd9gHBa.js`:
   ```python
   content = content.replace('camera=(), microphone=(), geolocation=()',
                             'camera=(), microphone=*, geolocation=()')
   ```
4. Copy patched file to `dist/`

### After Fix
1. Restart gateway: `openclaw gateway restart`
2. Refresh Control UI (Ctrl+Shift+R)
3. Verify: `document.featurePolicy.allowsFeature('microphone')` should return `true`

### IMPORTANT: OpenClaw Update Will Break This
Every time OpenClaw is updated, the patch is lost. Re-apply from backup.

---

## TTS Voice Settings

### Current Working Config
```json
{
  "messages": {
    "tts": {
      "auto": "always",
      "provider": "microsoft",
      "microsoft": {
        "enabled": true,
        "voice": "en-US-JennyNeural",
        "lang": "en-US",
        "outputFormat": "audio-24khz-48kbitrate-mono-mp3",
        "rate": "+25%",
        "pitch": "0%"
      }
    }
  }
}
```

### Adjust Speech Rate
```bash
openclaw config set messages.tts.edge.rate "+25%"
openclaw gateway restart
```

### Available Microsoft Neural Voices (English)
- `en-US-JennyNeural` — Female, friendly (current)
- `en-US-MichelleNeural` — Female, formal
- `en-US-GuyNeural` — Male
- `en-US-AriaNeural` — Female, engaging
- `en-US-StefanNeural` — Male
- `en-GB-SoniaNeural` — British female
- `en-AU-NatashaNeural` — Australian female

---

## Voice Input (STT) Settings
```bash
openclaw config set tools.media.audio.enabled true
openclaw gateway restart
```

Web Speech API (SpeechRecognition) is used by the Control UI mic button. It works in Chrome; Edge may have issues.

---

## Alt Key Microphone Shortcut

### What It Does
Adds **Alt** key as a shortcut to toggle the microphone in Control UI, when the chat input is empty and focused.

- **Recording on** → press Alt to stop
- **Recording off** → press Alt to start

### How to Apply
After every OpenClaw update, run:
```powershell
powershell -File C:\Users\samuel\.openclaw\workspace\skills\english-oral-tutor\scripts\fix-microphone-shortcut.ps1
```
Then refresh the Control UI page.

The script is **idempotent** — safe to run even if already patched.

### Manual Patch (if script fails)
File: `C:\Users\samuel\AppData\Roaming\npm\node_modules\openclaw\dist\control-ui\assets\index-sc9GrLxu.js`

Find (inside textarea `@keydown`, after the `ArrowDown` handler):
```javascript
if(n.key===`ArrowDown`){let t=f.down();n.preventDefault(),e.onDraftChange(t??``);return}
```

Insert right after:
```javascript
if(n.altKey&&!n.ctrlKey&&!n.metaKey&&!n.shiftKey){n.preventDefault();if(X.sttRecording){od(),X.sttRecording=!1,X.sttInterimText=``,g()}else{rd()&&e.connected&&ad({onTranscript:(t,n)=>{if(n){let n=_(),r=n&&!n.endsWith(` `)?` `:``;e.onDraftChange(n+r+t),X.sttInterimText=``}else X.sttInterimText=t;g()},onStart:()=>{X.sttRecording=!0,g()},onEnd:()=>{X.sttRecording=!1,X.sttInterimText=``,g()},onError:()=>{X.sttRecording=!1,X.sttInterimText=``,g()}})&&(X.sttRecording=!0,g())}}}
```
