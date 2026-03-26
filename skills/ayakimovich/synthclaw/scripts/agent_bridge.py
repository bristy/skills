import bpy
import sys
import os


def set_render_engine():
    """
    Set render engine BEFORE any rendering happens.
    Must be called before the render operation.
    """
    engine = os.environ.get("BLENDER_ENGINE", "CYCLES").upper()
    samples = int(os.environ.get("BLENDER_SAMPLES", "128"))
    
    if engine in ["EEVEE", "BLENDER_EEVEE"]:
        # Use EEVEE for fast testing
        bpy.context.scene.render.engine = 'BLENDER_EEVEE'
        print(f"[SynthClaw] Using EEVEE engine (fast mode)")
    else:
        # Use Cycles for production quality
        bpy.context.scene.render.engine = 'CYCLES'
        bpy.context.scene.cycles.samples = samples
        print(f"[SynthClaw] Using CYCLES engine with {samples} samples (production mode)")
        
        # CPU fallback for headless/server environments without GPU
        try:
            if bpy.context.scene.cycles.device not in ['CPU', 'GPU']:
                bpy.context.scene.cycles.device = 'CPU'
                print("[SynthClaw] Cycles device set to CPU (fallback)")
            else:
                print(f"[SynthClaw] Cycles device: {bpy.context.scene.cycles.device}")
        except Exception as e:
            print(f"[SynthClaw] Could not set Cycles device: {e}")
            bpy.context.scene.cycles.device = 'CPU'
            print("[SynthClaw] Falling back to CPU rendering")


def update_value_nodes(params):
    """
    Update Value Nodes in materials based on parameter dictionary.
    """
    updated_nodes = []
    missing_nodes = []
    
    for mat in bpy.data.materials:
        if not mat.use_nodes:
            continue
        
        nodes = mat.node_tree.nodes
        for key, val in params.items():
            if key in nodes and nodes[key].type == 'VALUE':
                try:
                    nodes[key].outputs[0].default_value = val
                    updated_nodes.append((key, val))
                    print(f"[SynthClaw] Updated Node '{key}' to {val}")
                except Exception as e:
                    print(f"[SynthClaw] Error updating node '{key}': {e}")
            elif key not in nodes:
                missing_nodes.append(key)
    
    if missing_nodes:
        print(f"[SynthClaw] Warning: Nodes not found: {', '.join(missing_nodes)}")
    
    return updated_nodes


def main():
    """
    Agent Bridge: Reads parameters from CLI, updates Value Nodes, sets engine, and renders.
    """
    # Parse CLI arguments
    try:
        args = sys.argv[sys.argv.index("--") + 1:]
    except ValueError:
        print("[SynthClaw] No parameters provided via CLI.")
        args = []
    
    # Parse key=value pairs
    params = {}
    for a in args:
        if '=' in a:
            try:
                k, v = a.split('=', 1)
                params[k] = float(v)
            except ValueError:
                print(f"[SynthClaw] Warning: Could not parse value for '{a}', skipping")
                continue
    
    # STEP 1: Set render engine FIRST (before any modifications)
    set_render_engine()
    
    # STEP 2: Update Value Nodes
    updated_nodes = update_value_nodes(params)
    
    # Print summary
    print(f"[SynthClaw] Updated {len(updated_nodes)} nodes:")
    for name, val in updated_nodes:
        print(f"  - {name}: {val}")
    
    print(f"[SynthClaw] Ready to render with {bpy.context.scene.render.engine}...")


if __name__ == "__main__":
    main()
