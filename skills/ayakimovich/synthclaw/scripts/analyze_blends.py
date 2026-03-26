import bpy
import json


def assess_complexity():
    # 1. Geometry Complexity
    total_polygons = sum([len(m.polygons) for m in bpy.data.meshes])
    num_objects = len(bpy.data.objects)
    
    # 2. Material Complexity
    num_materials = len(bpy.data.materials)
    node_count = sum([len(m.node_tree.nodes) for m in bpy.data.materials if m.use_nodes])
    
    # 3. Lighting & Render Engine
    engine = bpy.context.scene.render.engine
    num_lights = len(bpy.data.lights)
    
    # Heuristic Scoring
    score = 0
    if engine == 'CYCLES': score += 3
    if total_polygons > 10000: score += 1
    if total_polygons > 100000: score += 1
    if num_materials > 3: score += 1
    if node_count > 15: score += 1
    if num_lights > 0: score += 1
    
    if score >= 6:
        rating = "Photorealistic"
        desc = f"Very high complexity scene using {engine}. Advanced geometry ({total_polygons} polys) and rich material node trees."
    elif score >= 4:
        rating = "High Quality"
        desc = f"Detailed scene capable of strong renders. Good lighting logic and {num_materials} materials."
    elif score >= 2:
        rating = "Medium (Stylized/Real-time)"
        desc = f"Moderate complexity using {engine}. Likely a real-time game asset or stylized object."
    else:
        rating = "Low"
        desc = "Very simple scene. Flat shading or extremely basic geometry. Not recommended for photorealism."
        
    return {
        "rating": rating,
        "score": score,
        "polygons": total_polygons,
        "objects": num_objects,
        "materials": num_materials,
        "lights": num_lights,
        "engine": engine,
        "description": desc
    }


def main():
    """
    Analyzes a Blender file and outputs realism metrics and available Value Nodes as JSON.
    """
    value_nodes = {}
    
    # Iterate through all materials
    for mat in bpy.data.materials:
        if not mat.use_nodes:
            continue
        
        nodes = mat.node_tree.nodes
        for node in nodes:
            # Look for Value nodes that can be manipulated
            if node.type == 'VALUE':
                node_name = node.name
                current_value = node.outputs[0].default_value
                value_nodes[node_name] = {
                    "value": current_value,
                    "material": mat.name
                }
    
    # Also check for geometry nodes if present
    try:
        if hasattr(bpy.data, "node_groups"):
            for group in bpy.data.node_groups:
                for node in group.nodes:
                    if node.type == 'VALUE':
                        node_name = node.name
                        current_value = node.outputs[0].default_value
                        value_nodes[f"{group.name}.{node_name}"] = {
                            "value": current_value,
                            "node_group": group.name
                        }
    except Exception:
        pass
    
    output_data = {
        "complexity": assess_complexity(),
        "value_nodes": value_nodes
    }
    
    # Output as JSON for easy parsing between markers
    print("---ANALYSIS_START---")
    print(json.dumps(output_data, indent=2))
    print("---ANALYSIS_END---")


if __name__ == "__main__":
    main()
