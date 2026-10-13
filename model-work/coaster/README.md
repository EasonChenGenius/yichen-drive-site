# Coaster material review

This folder contains a local Blender revision script for the existing Coaster blockout. It changes the body material to match the user's light champagne brown reference, removes unverified seating geometry, and separates editable parts.

The blockout is not an exact Coaster model. Do not publish it as a verified vehicle model or use it to establish equipment/capacity. Exact year/variant geometry and actual interior references are still required.

The script must be executed inside Blender, not ordinary Python. Expected outputs are a packed .blend source, embedded .glb model, a static material review render and an execution record. The generated files are deliverables only after successful execution and inspection. No Lux3D cloud task or credit is fabricated for this local work.

## Executed output

Local Blender 4.5.9 LTS successfully saved and exported the material revision. The source file was reopened to check named part collections, the packed reference image, material settings and removal of unverified seat geometry. The GLB passed structural inspection. The material review render was visually inspected for full framing and visibility. Geometry is still an unverified blockout and is not integrated into the customer website. `source-blockout.glb` preserves the original concept input for reproducibility; its metadata is not actual fleet configuration.
