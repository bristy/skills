---
name: synthclaw
version: 0.1.3
license: MIT
description: Render Blender files with agent-controlled procedural parameters for synthetic data generation. Use when generating training data with controlled variations, creating procedural image datasets, or automating Blender renders via natural language. Supports CYCLES (production) and EEVEE (fast testing) render engines.
---

## When to Use

- Generate synthetic training data with controlled parameter variations
- Create procedural image datasets with ground truth metadata
- Automate rendering workflows for ML training data
- When you need parameter-sweep renders without manual Blender interaction

## When NOT to Use

- Real-time rendering or interactive preview needs (this is batch/offline)
- Complex scene manipulation beyond Value Node adjustments
- If Blender is not installed or unavailable in PATH

## Requirements

- Blender 4.0+ installed and available in `$PATH`
- Python 3.10+ for the synthclaw package
- Cycles or EEVEE render engine (auto-selected)

## Configuration

No additional configuration required. Ensure `blender` command is available:

```bash
blender --version
```

## Tools

### render_procedural_scene

Adjusts procedural Value Nodes and renders a frame in Blender.

**Parameters:**
- `blend_file` (string, required): Absolute path to the .blend file
- `parameters` (object, required): Key-value pairs of Value Node names and float values (e.g., `{"GrainScale": 2.5, "Roughness": 0.3}`)
- `output_path` (string, required): Where to save the rendered image (e.g., `/path/to/output.png`)
- `samples` (integer, optional): Cycles samples (default: 128). Ignored for EEVEE.
- `engine` (string, optional): Render engine - `"CYCLES"` (default) or `"EEVEE"`
- `timeout` (integer, optional): Custom timeout in seconds. Defaults: 1800 for CYCLES, 60 for EEVEE.
- `reference_image` (string, optional): Complete path to a real-world reference image. Used for computing LPIPS similarity and Naturalness Delta.
- `compute_metrics` (boolean, optional): Set to `true` to compute Naturalness/LPIPS metrics after rendering. Default `false`.

**Returns:**
- On success: `{"status": "success", "output": "/path/to/output.png", "log": "...", "engine": "CYCLES", "samples": 128, "metrics": {"naturalness_mean": 0.85, "lpips_alex": 0.12}}`
- On error: `{"status": "error", "message": "..."}`

**Examples:**

*Production quality (CYCLES):*
```json
{
  "blend_file": "/home/user/project/assets/test.blend",
  "output_path": "/home/user/output/render_01.png",
  "parameters": {
    "GrainScale": 3.0,
    "DisplacementStrength": 1.5
  },
  "engine": "CYCLES",
  "samples": 256
}
```

*Fast testing (EEVEE):*
```json
{
  "blend_file": "/home/user/project/assets/test.blend",
  "output_path": "/home/user/output/test_render.png",
  "parameters": {
    "GrainScale": 3.0
  },
  "engine": "EEVEE"
}
```

### render_procedural_scene_fast

Convenience function for fast EEVEE rendering. Same as `render_procedural_scene` with `engine="EEVEE"`.

**Parameters:**
- `blend_file` (string, required): Absolute path to the .blend file
- `parameters` (object, required): Key-value pairs of Value Node names and float values
- `output_path` (string, required): Where to save the rendered image

### render_procedural_scene_production

Convenience function for production Cycles rendering. Same as `render_procedural_scene` with `engine="CYCLES"` and higher samples.

**Parameters:**
- `blend_file` (string, required): Absolute path to the .blend file
- `parameters` (object, required): Key-value pairs of Value Node names and float values
- `output_path` (string, required): Where to save the rendered image
- `samples` (integer, optional): Cycles samples (default: 512)

### analyze_blend

Analyzes a .blend file and returns available Value Nodes that can be manipulated.

**Parameters:**
- `blend_file` (string, required): Absolute path to the .blend file

**Returns:** Dict containing `status`, a `complexity` object evaluating scene realism, and `value_nodes` (available parameter names with current values).

## Engine Comparison

| Feature | CYCLES | EEVEE |
|---------|--------|-------|
| Quality | Photorealistic | Real-time |
| Speed | Slow (minutes) | Fast (seconds) |
| Timeout | 30 minutes | 1 minute |
| Use case | Production | Testing |
| Samples | Configurable | N/A |

## Safety & Limitations

- **Headless execution:** Blender runs with `-b` flag for security
- **Parameter validation:** Only float values accepted; non-numeric input is rejected
- **No shell injection:** Uses `subprocess.run(shell=False)` with `--` separator
- **CPU fallback:** Automatically uses CPU rendering for Cycles if no GPU available
- **Timeout protection:** Long renders are killed after timeout to prevent hanging

## Files

| File | Purpose |
|------|---------|
| `src/synthclaw/blender_skill.py` | OpenClaw execution wrapper with engine selection |
| `scripts/agent_bridge.py` | Blender-side Python script (handles both engines) |
| `scripts/analyze_blends.py` | Blender-side analysis script |
| `config/render_schema.json` | Tool schema for LLM function calling |
| `config/analyze_schema.json` | Schema for blend file analysis |

## Example Workflow

1. User: "Render with grain scale increased and surface rougher"
2. Agent calls `analyze_blend` to see available parameters
3. Agent calls `render_procedural_scene_fast` (EEVEE) for quick preview
4. If preview looks good, agent calls `render_procedural_scene_production` (CYCLES) for final output
5. Render completes, path returned to user

## Version

Compatible with Blender 4.0+. Not backwards compatible with 2.7x.
