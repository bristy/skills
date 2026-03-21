---
name: local-image-generation
description: >
  generate an image, create a picture, draw something, make an image of, text to image,
  paint a picture, illustrate, visualize, local image generation, AI art, image synthesis.
  Runs Z-Image-Turbo on-device on Windows via Intel OpenVINO. Prioritizes Intel iGPU
  (Xe / Arc), falls back to CPU. Bilingual prompts (English + Chinese) supported.
  SETUP requires network: downloads Python/git installers from python.org and github.com,
  pip dependencies (some via git+https pinned commits) from GitHub, and the model (~10 GB)
  from modelscope.cn. INFERENCE is fully offline after setup — no cloud API calls.
os: windows
requires:
  - python>=3.10
  - git
network:
  setup: required    # python.org, github.com, modelscope.cn (~10 GB model)
  inference: offline
user-invocable: true
allowed-tools: Bash(python *), Bash(pip *), Bash(cd *), Bash(call *), Bash(git *), Bash(winget *), Read, Glob, Write, message
---

# Local Text-to-Image (Windows · Z-Image-Turbo · OpenVINO)

**Model**: `snake7gun/Z-Image-Turbo-int4-ov` (ModelScope INT4)  
**Interface**: `optimum.intel.OVZImagePipeline`  
**Skill dir**: `{baseDir}` — contains `SKILL.md` and `requirements_imagegen.txt`  
**SKILL_VERSION**: `v1.0.0` ← used in Step 4 to decide whether to overwrite the script

> **Network usage**: Setup downloads from `python.org`, `github.com` (pip deps, some pinned
> to git+https commits), and `modelscope.cn` (model ~10 GB, resume supported).
> Inference is fully offline — no network calls once setup is complete.

## Directory layout (all auto-created)

```
<IMAGE_GEN_DIR>\
├── image_gen\                 ← venv (created in Step 2)
├── generate_image.py          ← written in Step 4
├── Z-Image-Turbo-int4-ov\     ← downloaded in Step 3 (~10 GB)
└── outputs\YYYYMMDD_HHMMSS_topic.png
```

---

## ⚠️ Agent instructions

1. Run one command at a time; wait for output before proceeding.
2. On any error, stop and consult the troubleshooting table at the end.
3. Wrap all paths in double quotes.
4. `{baseDir}` is injected at runtime as the absolute path of this SKILL.md's directory. If injection fails, replace it manually. `requirements_imagegen.txt` lives there.
5. **Goal**: generate an image and preview it in the conversation.

**Pipeline (do not skip steps)**:
```
Pre-flight: check Python ≥3.10 + git       → PYTHON_OK + GIT_OK
Step 0:     expand prompt + extract topic  → show to user
Step 1:     locate working directory       → IMAGE_GEN_DIR
Step 2:     activate venv, verify deps     → DEP_CHECK=PASS
Step 3:     check disk + model             → MODEL_STATUS=READY (skip download)
Step 4:     write inference script         → SCRIPT_UPDATE=DONE/SKIPPED
Step 5:     generate + preview             → send image to conversation
```

Announce each step before running it: `🔍 Pre-flight: checking environment…`

---

## Pre-flight: check Python and git (required on first use)

> 🔍 Pre-flight: checking Python and git…

### Python

```bat
python --version
```

| Output | Action |
|--------|--------|
| `Python 3.10.x` or higher | ✅ `PYTHON_OK`, check git next |
| `Python 3.8 / 3.9` | ⛔ Too old — install 3.12 (see below) |
| `'python' is not recognized` | ⛔ Not installed — install (see below) |

**Silent install via PowerShell (no admin required):**

```powershell
$f = "$env:TEMP\python-installer.exe"
Invoke-WebRequest "https://www.python.org/ftp/python/3.12.10/python-3.12.10-amd64.exe" -OutFile $f
Start-Process $f -ArgumentList "/quiet InstallAllUsers=0 PrependPath=1 Include_pip=1" -Wait
Remove-Item $f
```

Restart the terminal, then confirm with `python --version`.  
Manual alternative: download **https://www.python.org/ftp/python/3.12.10/python-3.12.10-amd64.exe** and check **"Add python.exe to PATH"** during install.

### git

```bat
git --version
```

| Output | Action |
|--------|--------|
| `git version 2.x.x` | ✅ `GIT_OK` — Pre-flight passed |
| `'git' is not recognized` | ⛔ Not installed — install (see below) |

**Silent install via PowerShell:**

```powershell
$f = "$env:TEMP\git-installer.exe"
Invoke-WebRequest "https://github.com/git-for-windows/git/releases/download/v2.49.0.windows.1/Git-2.49.0-64-bit.exe" -OutFile $f
Start-Process $f -ArgumentList "/VERYSILENT /NORESTART /NOCANCEL /SP- /CLOSEAPPLICATIONS /RESTARTAPPLICATIONS /COMPONENTS=icons,ext\reg\shellhere,assoc,assoc_sh" -Wait
Remove-Item $f
```

Restart the terminal, then confirm with `git --version`.  
Manual alternative: **https://git-scm.com/download/win** — keep all defaults.

> git is required for `git+https://` entries in `requirements_imagegen.txt`. Without it, pip will fail with `git: command not found`.

**Pass criteria**: `python --version` ≥ 3.10 and `git --version` has output.  
Announce: `✅ Python and git ready.`

---

## Step 0: expand prompt (LLM only — no tools)

Do two things simultaneously: **① expand the prompt** and **② extract a topic slug** (English snake_case, used for the filename).

Expansion structure: `[subject] [action/pose] [environment] [lighting/mood] [style] [quality tags]`

Prompts can be English or Chinese — no translation needed. Topic slug must always be English to avoid path encoding issues.

Quality tags: `photorealistic`, `8K resolution`, `cinematic lighting`, `masterpiece`

| Input | Topic slug | Expanded prompt |
|-------|-----------|-----------------|
| a panda | `panda_bamboo` | A giant panda sitting in a lush bamboo forest, sunlight filtering through leaves, photorealistic, 8K, wildlife photography |
| 赛博朋克城市 | `cyberpunk_city` | 未来感都市夜景，霓虹灯倒映在湿漉漉的街道，赛博朋克风，电影级，8K |

Show the result before proceeding:
```
📝 Input:    {user description}
   Expanded: {full prompt}
   Topic:    {topic_slug}
```

---

## Step 1: locate working directory

> 🔍 Step 1/5: locating working directory…

```python
python -c "
import string, shutil
from pathlib import Path
drives = [f'{d}:\\\\' for d in string.ascii_uppercase if Path(f'{d}:\\\\').exists()]
print(f'[INFO] Drives found: {drives}')
found = None
for drive in drives:
    candidate = Path(drive) / 'image-gen-local'
    if candidate.exists():
        found = candidate
        break
if not found:
    best = max(drives, key=lambda d: shutil.disk_usage(d).free)
    found = Path(best) / 'image-gen-local'
    found.mkdir(parents=True, exist_ok=True)
    print(f'[INFO] Created: {found}')
print(f'IMAGE_GEN_DIR={found}')
"
```

**Pass**: output contains `IMAGE_GEN_DIR=`. Record the path and substitute it for `<IMAGE_GEN_DIR>` in all subsequent commands.

---

## Step 2: activate venv and verify dependencies

> ⚙️ Step 2/5: verifying Python environment and dependencies…

```bat
call "<IMAGE_GEN_DIR>\image_gen\Scripts\activate.bat"
python -c "import sys; print(sys.executable)"
```

**Pass**: path contains `image_gen`.

**If venv does not exist** (activate.bat errors), run each command separately in order:
```bat
python -m ensurepip --upgrade
```
```bat
python -m venv "<IMAGE_GEN_DIR>\image_gen"
```
```bat
call "<IMAGE_GEN_DIR>\image_gen\Scripts\activate.bat"
```
```bat
python -m pip install --upgrade pip
```
```bat
pip install -r "{baseDir}\requirements_imagegen.txt"
```

> ⚠️ **Critical**: run `pip install` only after `activate.bat`. Installing before activation puts packages into system Python, causing venv dep checks to fail. Successful activation shows `(image_gen)` as the prompt prefix.

**Verify dependencies (always run):**

> ⚠️ Confirm prompt prefix is `(image_gen)` before running. If not, run `call "<IMAGE_GEN_DIR>\image_gen\Scripts\activate.bat"` first.

```python
python -c "
import json, site
from pathlib import Path

EXPECTED_COMMITS = {
    'optimum_intel': '2f62e5ae',
    'diffusers':     'a1f36ee3',
}

def get_git_commit(pkg_name):
    dirs = site.getsitepackages()
    try: dirs += [site.getusersitepackages()]
    except Exception: pass
    for d in dirs:
        for dist in Path(d).glob(f'{pkg_name}*.dist-info'):
            url_file = dist / 'direct_url.json'
            if url_file.exists():
                data = json.loads(url_file.read_text(encoding='utf-8'))
                return data.get('vcs_info', {}).get('commit_id', 'no_vcs_info')
    return 'not_found'

results = {}

for pkg, imp in [('openvino','openvino'),('torch','torch'),('Pillow','PIL'),('modelscope','modelscope')]:
    try:
        ver = getattr(__import__(imp), '__version__', 'OK')
        results[pkg] = ('OK', ver)
    except ImportError as e:
        results[pkg] = ('MISSING', str(e))

try:
    from optimum.intel import OVZImagePipeline
    results['OVZImagePipeline'] = ('OK', 'importable')
except ImportError as e:
    results['OVZImagePipeline'] = ('MISSING', str(e))

for pkg_name, exp in EXPECTED_COMMITS.items():
    actual = get_git_commit(pkg_name)
    if actual == 'not_found':
        results[f'{pkg_name}@commit'] = ('MISSING', 'not installed via git+https')
    elif actual.startswith(exp):
        results[f'{pkg_name}@commit'] = ('OK', actual[:16])
    else:
        results[f'{pkg_name}@commit'] = ('WRONG', f'got {actual[:16]} want {exp}...')

all_ok = all(v[0] == 'OK' for v in results.values())
for k, (status, detail) in results.items():
    icon = '✅' if status == 'OK' else ('⚠️' if status == 'WRONG' else '❌')
    print(f'  {icon} {k}: {detail}')
print('DEP_CHECK=PASS' if all_ok else 'DEP_CHECK=FAIL')
"
```

| Output | Action |
|--------|--------|
| `DEP_CHECK=PASS` | ✅ Proceed to Step 3. Announce: `✅ Environment ready.` |
| `DEP_CHECK=FAIL` (MISSING) | ⛔ Run `pip install -r "{baseDir}\requirements_imagegen.txt"` and re-verify |
| `DEP_CHECK=FAIL` (`@commit` WRONG) | ⛔ Force reinstall (see below) |

**Force reinstall on commit mismatch:**
```bat
pip uninstall optimum-intel diffusers -y
pip install -r "{baseDir}\requirements_imagegen.txt" --no-cache-dir
```

---

## Step 3: check disk space + model

> 📦 Step 3/5: checking disk space and model files…

**Check disk space** (model ~10 GB + venv ~3 GB — need at least 15 GB free):

```python
python -c "
import shutil
from pathlib import Path
target = Path(r'<IMAGE_GEN_DIR>')
free_gb = shutil.disk_usage(target).free / (1024**3)
print(f'DISK_FREE={free_gb:.1f}GB')
if free_gb < 15:
    print('DISK_STATUS=LOW')
    print('[WARN] Less than 15 GB free — download may fail mid-way')
else:
    print('DISK_STATUS=OK')
"
```

| Output | Action |
|--------|--------|
| `DISK_STATUS=OK` | ✅ Continue to model check |
| `DISK_STATUS=LOW` | ⚠️ Ask user to free space, or confirm they want to proceed anyway |

**Check model files:**

```python
python -c "
from pathlib import Path
model_dir = Path(r'<IMAGE_GEN_DIR>') / 'Z-Image-Turbo-int4-ov'
required = ['transformer', 'vae_decoder', 'text_encoder']
missing = [r for r in required if not (model_dir / r).exists()]
print('MODEL_STATUS=READY') if not missing else print('MODEL_STATUS=MISSING')
print(f'MODEL_DIR={model_dir}')
if missing: print(f'MISSING_DIRS={missing}')
"
```

| Output | Action |
|--------|--------|
| `MODEL_STATUS=READY` | ✅ Skip to Step 4. Announce: `✅ Model ready.` |
| `MODEL_STATUS=MISSING` | Read the notice below, then choose auto or manual download |

---

### 📋 First-time download notice (MODEL_STATUS=MISSING)

Announce to user and ask how to proceed:

```
📥 Model download: ~10 GB
   Estimated time:
   • 100 Mbps → ~15 min
   •  50 Mbps → ~30 min
   •  10 Mbps → ~2 hr
   Download supports resume — if interrupted, re-run this step to continue from where it stopped.

   ✅ Start auto-download
   📂 I'll download manually — show me the link
```

Proceed based on user choice.

---

### 🤖 Auto-download (tqdm progress bar + background monitor)

```python
python -c "
import sys, time, threading
from pathlib import Path
from modelscope import snapshot_download

model_dir = Path(r'<IMAGE_GEN_DIR>') / 'Z-Image-Turbo-int4-ov'
model_dir.mkdir(parents=True, exist_ok=True)

_stop = threading.Event()

def watchdog():
    prev = 0
    while not _stop.wait(30):
        try:
            total = sum(f.stat().st_size for f in model_dir.rglob('*') if f.is_file())
            speed = (total - prev) / 30
            print(f'[Progress] {total/1024**3:.2f} GB downloaded  {speed/1024**2:.1f} MB/s', flush=True)
            prev = total
        except Exception:
            pass

t = threading.Thread(target=watchdog, daemon=True)
t.start()

try:
    snapshot_download(
        'snake7gun/Z-Image-Turbo-int4-ov',
        local_dir=str(model_dir),
        ignore_file_pattern=[r'\.git.*']
    )
    print('MODEL_DOWNLOAD=DONE')
except KeyboardInterrupt:
    print('[WARN] Download interrupted. Progress saved — re-run this step to resume.')
    print('MODEL_DOWNLOAD=INTERRUPTED')
except Exception as e:
    err = str(e).lower()
    if 'disk' in err or 'space' in err or 'no space' in err:
        print(f'[ERROR] Disk full: {e}')
        print('MODEL_DOWNLOAD=FAIL_DISK')
    elif 'timeout' in err or 'connection' in err or 'network' in err:
        print(f'[ERROR] Network error: {e}')
        print('MODEL_DOWNLOAD=FAIL_NETWORK')
    else:
        print(f'[ERROR] Unknown error: {e}')
        print('MODEL_DOWNLOAD=FAIL_UNKNOWN')
finally:
    _stop.set()
"
```

| Output | Action |
|--------|--------|
| `MODEL_DOWNLOAD=DONE` | ✅ Proceed to Step 4. Announce: `✅ Model downloaded.` |
| `MODEL_DOWNLOAD=INTERRUPTED` | ⚠️ Tell user to re-run this step — download will resume automatically |
| `MODEL_DOWNLOAD=FAIL_DISK` | ⛔ Ask user to free disk space and retry |
| `MODEL_DOWNLOAD=FAIL_NETWORK` | ⛔ Ask user to check network/proxy, or use manual download below |
| `MODEL_DOWNLOAD=FAIL_UNKNOWN` | ⛔ Show raw error, suggest manual download |

---

### 📂 Manual download fallback

> Use this if the network is unstable or you prefer a download manager (IDM, aria2, etc.).

**① Download the model**

ModelScope page: **https://modelscope.cn/models/snake7gun/Z-Image-Turbo-int4-ov/files**

Or via CLI (supports resume — re-run to continue if interrupted):
```bat
pip install modelscope
python -c "from modelscope import snapshot_download; snapshot_download('snake7gun/Z-Image-Turbo-int4-ov', local_dir=r'<IMAGE_GEN_DIR>\Z-Image-Turbo-int4-ov')"
```

**② Confirm directory structure** (all three subdirs required):
```
<IMAGE_GEN_DIR>\Z-Image-Turbo-int4-ov\
├── transformer\
├── vae_decoder\
└── text_encoder\
```

**③ Re-verify:**
```python
python -c "
from pathlib import Path
model_dir = Path(r'<IMAGE_GEN_DIR>') / 'Z-Image-Turbo-int4-ov'
required = ['transformer', 'vae_decoder', 'text_encoder']
missing = [r for r in required if not (model_dir / r).exists()]
print('MODEL_STATUS=READY') if not missing else print(f'MODEL_STATUS=MISSING  missing: {missing}')
"
```

Once `MODEL_STATUS=READY`, continue to Step 4.

---

## Step 4: write inference script (version check)

> ✍️ Step 4/5: checking script version…

```python
python -c "
from pathlib import Path
import re

CURRENT_VERSION = 'v2.0'
script = Path(r'<IMAGE_GEN_DIR>') / 'generate_image.py'

existing_version = None
if script.exists():
    m = re.search(r\"SKILL_VERSION\s*=\s*[\\\"'](.*?)[\\\"']\", script.read_text(encoding='utf-8', errors='ignore'))
    if m: existing_version = m.group(1)

if existing_version == CURRENT_VERSION:
    print('SCRIPT_UPDATE=SKIPPED (already up to date)')
    print(f'EXISTS={script.exists()}')
else:
    print(f'SCRIPT_VERSION_OLD={existing_version} -> NEW={CURRENT_VERSION}')
    print('SCRIPT_UPDATE=WRITING...')
    code = r'''
SKILL_VERSION = \"v2.0\"

import sys, io, os, subprocess, argparse, string, re
from datetime import datetime
from pathlib import Path
import openvino as ov
import torch
from optimum.intel import OVZImagePipeline
from PIL import Image

def get_image_gen_dir():
    for d in string.ascii_uppercase:
        c = Path(f\"{d}:\\\\\") / \"image-gen-local\"
        if c.exists(): return c
    return Path(__file__).resolve().parent

def get_device():
    core = ov.Core()
    devs = core.available_devices
    print(f\"[INFO] Available devices: {devs}\")
    for d in devs:
        if \"GPU\" in d:
            print(f\"[INFO] Using Intel GPU: {d}\")
            return d
    print(\"[INFO] Using CPU\")
    return \"CPU\"

def make_filename(prompt, topic):
    date_str = datetime.now().strftime(\"%Y%m%d_%H%M%S\")
    src = topic if topic else prompt[:30]
    safe = re.sub(r'[^\\w]', '_', src.strip())[:30].strip('_')
    return f\"{date_str}_{safe}.png\"

def generate(prompt, topic='', steps=9, width=512, height=512, seed=42, output_path=None):
    root = get_image_gen_dir()
    model_dir = root / \"Z-Image-Turbo-int4-ov\"
    out_dir = root / \"outputs\"
    out_dir.mkdir(parents=True, exist_ok=True)

    missing = [r for r in [\"transformer\",\"vae_decoder\",\"text_encoder\"] if not (model_dir/r).exists()]
    if missing:
        print(f\"[ERROR] Model incomplete: {missing} — re-run Step 3\")
        sys.exit(1)

    device = get_device()
    print(f\"[INFO] Loading model: {model_dir}\")
    pipe = OVZImagePipeline.from_pretrained(str(model_dir), device=device)
    print(\"[INFO] Model loaded\")

    gen = torch.Generator(\"cpu\").manual_seed(seed) if seed >= 0 else None
    print(f\"[INFO] Inference: steps={steps}, {width}x{height}, seed={seed}\")
    image = pipe(prompt=prompt, height=height, width=width,
                 num_inference_steps=steps, guidance_scale=0.0, generator=gen).images[0]

    if output_path is None:
        output_path = str(out_dir / make_filename(prompt, topic))
    image.save(output_path)
    print(f\"[SUCCESS] Image saved: {output_path}\")
    try:
        subprocess.Popen(['explorer', output_path])
        print(\"[INFO] Opened in default viewer\")
    except Exception as e:
        print(f\"[WARN] Could not open image: {e}\")
    return output_path

if __name__ == \"__main__\":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    p = argparse.ArgumentParser()
    p.add_argument(\"--prompt\", required=True)
    p.add_argument(\"--topic\",  default='')
    p.add_argument(\"--steps\",  type=int, default=9)
    p.add_argument(\"--width\",  type=int, default=512)
    p.add_argument(\"--height\", type=int, default=512)
    p.add_argument(\"--seed\",   type=int, default=42)
    p.add_argument(\"--output\", default=None)
    args = p.parse_args()
    print(generate(args.prompt, args.topic, args.steps, args.width, args.height, args.seed, args.output))
'''
    script.write_text(code.strip(), encoding='utf-8')
    print('SCRIPT_UPDATE=DONE')

print(f'EXISTS={script.exists()}')
"
```

| Output | Meaning |
|--------|---------|
| `SCRIPT_UPDATE=SKIPPED` | ✅ Already up to date — proceed to Step 5 |
| `SCRIPT_UPDATE=DONE` | ✅ Script written — proceed to Step 5 |
| `EXISTS=False` | ⛔ Write failed — check directory permissions |

Announce: `✅ Script v2.0 ready.`

---

## Step 5: generate image and preview

> 🎨 Step 5/5: running inference…

```bat
set PYTHONUTF8=1 && call "<IMAGE_GEN_DIR>\image_gen\Scripts\activate.bat" && python "<IMAGE_GEN_DIR>\generate_image.py" --prompt "expanded prompt from Step 0" --topic "topic slug from Step 0" --steps 9 --seed 42
```

> ⚠️ All three commands are chained with `&&` to ensure `PYTHONUTF8=1` and venv activation apply to the same shell session. If `&&` is not supported, run them as three separate commands.

**Pass**: the last line of stdout is a `.png` absolute path — record it as `<IMAGE_PATH>`.

The script calls `subprocess.Popen(['explorer', path])` internally to open the image in the system default viewer. No extra command needed.

**Send preview via `message` tool:**
```
action: "send"  filePath: "<IMAGE_PATH>"  message: "✅ {topic slug}"
```

**Final announcement:**
```
✅ Done! Path: <IMAGE_PATH>
📝 Prompt: {expanded prompt}
⚙️ steps=9, 512×512, seed=42 | device: {CPU/GPU}
```

---

## Parameters

| Param | Default | Notes |
|-------|---------|-------|
| `--prompt` | required | English or Chinese |
| `--topic` | empty | English snake_case slug for filename |
| `--steps` | 9 | Higher = more detail; no hard limit |
| `--width/--height` | 512 | 512 / 768 / 1024 recommended |
| `--seed` | 42 | -1 = random |
| `--output` | auto | Custom absolute output path |

> `guidance_scale` is fixed at `0.0` and not exposed as a parameter.

---

## Troubleshooting

| Error | Cause | Fix |
|-------|-------|-----|
| `'python' is not recognized` | Python not installed or not in PATH | Silent install via PowerShell (see Pre-flight), restart terminal |
| `Python 3.8/3.9` | Version too old | Reinstall 3.12 (same as above) |
| `'git' is not recognized` | git not installed or not in PATH | Silent install via PowerShell (see Pre-flight), restart terminal |
| `No module named pip` | pip missing | `python -m ensurepip --upgrade` |
| `DEP_CHECK=FAIL` but packages seem installed | venv was not active during `pip install` — packages went to system Python | Activate venv, then re-run `pip install -r requirements_imagegen.txt` |
| `DEP_CHECK=FAIL` / `OVZImagePipeline MISSING` | optimum-intel not installed or wrong version | `pip install -r "{baseDir}\requirements_imagegen.txt"` |
| `@commit` shows WRONG | PyPI release installed instead of pinned commit | `pip uninstall optimum-intel diffusers -y` then `pip install -r requirements_imagegen.txt --no-cache-dir` |
| `@commit` shows `not installed via git+https` | git missing when pip ran — skipped git deps | Complete Pre-flight git install, then reinstall deps |
| `DISK_STATUS=LOW` | Less than 15 GB free | Free space and retry |
| `[ERROR] Model incomplete` | Download was interrupted | Delete model dir, re-run Step 3 |
| `activate.bat not found` | venv not created | Run Step 2 creation commands |
| `RuntimeError` on GPU | Insufficient VRAM | Lower resolution or hardcode `return "CPU"` in `get_device()` |
| Black/noisy output | Too few steps | Use `--steps` ≥ 4; 9 recommended |
| Download timeout | Network issue | Configure proxy and retry |
| `EXISTS=False` | No write permission | Confirm directory is writable |
