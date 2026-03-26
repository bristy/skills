import subprocess
import json
import os

MODULE_DIR = os.path.dirname(os.path.abspath(__file__))
SCRIPTS_DIR = os.path.abspath(os.path.join(MODULE_DIR, "..", "..", "scripts"))
SCRIPT_PATH = os.path.join(SCRIPTS_DIR, "analyze_blends.py")

def analyze_blender_file(blend_file: str):
    """
    OpenClaw Skill: Executes Blender in background mode to analyze scene settings.
    """
    command = [
        "blender", 
        "-b", blend_file, 
        "-P", SCRIPT_PATH
    ]

    try:
        result = subprocess.run(command, capture_output=True, text=True, check=True)
        # Parse output between markers
        output = result.stdout
        if "---ANALYSIS_START---" in output and "---ANALYSIS_END---" in output:
            start = output.find("---ANALYSIS_START---") + len("---ANALYSIS_START---\n")
            end = output.find("---ANALYSIS_END---")
            json_str = output[start:end].strip()
            return {"status": "success", "data": json.loads(json_str)}
        else:
            return {"status": "error", "message": "Failed to find analysis markers in output.", "log": output[-500:]}
    except subprocess.CalledProcessError as e:
        return {"status": "error", "message": e.stderr}
