
# SynthClaw: OpenClaw Agent for Blender Procedural Data Render Skill

This project transforms static Blender files into **agentic tools**. By bridging OpenClaw with Blender’s Python API (`bpy`), an LLM can autonomously manipulate procedural nodes (like noise scale, roughness, or color intensity) and trigger high-quality Cycles renders based on natural language prompts.

## 🛠 Project Purpose

The goal is to move away from manual "slider-pushing." Instead of opening Blender to tweak a material, you can tell the agent:

> *"Generate a render where the texture is much grainier and the surface looks like wet marble."*

The agent identifies the correct **Value Nodes**, updates their defaults, and returns a rendered image for review.

### Supported Render Engines
- **CYCLES**: Production quality, photorealistic (slower, 30 min timeout)
- **EEVEE**: Fast real-time rendering (testing, 1 min timeout)

---

## 📂 Project Structure

This repository is designed as an installable Python package for OpenClaw agents:

* `src/synthclaw/`: Contains the OpenClaw execution wrappers (`blender_skill.py`, `analyze_skill.py`) that trigger background system processes.
* `scripts/`: Internal Blender execution code (`agent_bridge.py`, `analyze_blends.py`). These are loaded directly into Blender by the wrappers.
* `config/`: JSON tool schemas provided to your LLM agent (`render_schema.json`, `analyze_schema.json`).
* `assets/`: Contains `low.blend` and `high.blend` required for testing agent configurations.
* `tests/`: Automated unit tests for validating Blender environment setup and output.
* `pyproject.toml`: Local package definition.

---

## 🚀 Setup Instructions

### 1. Blender File Preparation (Blender 4.0+)

For the agent to "see" your controls, you must explicitly name your **Value Nodes**:

1. Open your `.blend` file.
2. In the **Shader Editor**, add an **Input > Value** node.
3. Connect it to your procedural math/texture inputs.
4. **Critical Step:** Select the Value node, press `N` for the sidebar, and under **Item > Name**, set a unique name (e.g., `GrainScale`).
* *Note: The script looks at the internal Name, not just the Label.*



### 2. Environment Configuration

Ensure `blender` is in your system `$PATH`. Test this by running:

```bash
blender --version

```

*Requirement: Version 4.0.0 or higher.*

### 3. Installation

1. Place `agent_bridge.py` in your project root or a known scripts directory.
2. Register the `blender_skill.py` function within your OpenClaw worker.
3. Update the `blend_file` path in your tool call to point to your specific `.blend` assets.

---

## 🤖 Agentic Workflow

### Node Manipulation and Rendering
1. **User Input:** "Make the displacement more aggressive."
2. **LLM Reasoning:** The LLM looks at the tool schema, sees a parameter named `DisplacementStrength`, and decides to increase its value from `1.0` to `2.5`.
3. **Execution:** OpenClaw runs Blender in **Headless Mode** (`-b`).
4. **Modification:** `agent_bridge.py` iterates through all materials, finds the node named `DisplacementStrength`, and updates it.
5. **Output:** A `.png` is rendered and the path is returned to the user.

### Scene Complexity Analysis
Before rendering, the agent can run `analyze_blend`. This script parses the `.blend` file without launching GUI overhead. It examines poly-count, material configurations, lighting rigs, and rendering setups to produce a **Complexity & Realism Score**. This gives agents foresight on the visual quality they can generate.

### Image Quality Metrics
When generating outputs, the tool supports quantitative evaluation of the rendered image:
- **Naturalness (GraNatPy):** When `compute_metrics: true` is passed, the skill leverages `granatpy` to compute the naturalness factor of the generated image.
- **Reference Image Similarity (LPIPS):** If an optional `reference_image` path (a real-world photo) is provided alongside `compute_metrics: true`, the skill dynamically compares the render against the real photo. It returns the Learned Perceptual Image Patch Similarity (LPIPS) score and the delta Naturalness Factor (dNf), measuring how close the synthetic image is to reality.

---

## ⚠️ Limitations & Safety

* **Cycles Rendering:** This skill defaults to the Cycles engine. If running on a headless server without a GPU, the script is configured to fallback to CPU rendering to prevent driver crashes.
* **Injection Safety:** The bridge uses `sys.argv` filtering. However, ensure the LLM is restricted from passing arbitrary string commands into the `parameters` dictionary.
* **Version Lock:** This project uses `bpy` syntax specific to the **4.0+** mesh and node system. It is not backwards compatible with 2.7x or early 2.8x versions.

---

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.