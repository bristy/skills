import os
import json
from synthclaw import analyze_blend

def test_blender_skill():
    # Attempt to resolve the path to the assets folder relative to this file
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    low_blend = os.path.join(repo_root, "assets", "low.blend")
    high_blend = os.path.join(repo_root, "assets", "high.blend")

    print(f"Testing against low.blend at: {low_blend}")
    if not os.path.exists(low_blend):
        print("ERROR: Could not find low.blend. Skipping tests.")
        return

    print("\n--- Analyzing Low Realism File ---")
    low_res = analyze_blend(low_blend)
    print(json.dumps(low_res, indent=2))

    print("\n--- Analyzing High Realism File ---")
    high_res = analyze_blend(high_blend)
    print(json.dumps(high_res, indent=2))

if __name__ == "__main__":
    test_blender_skill()
