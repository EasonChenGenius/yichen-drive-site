"""Render actual Blender assembly poses for geometry QA, not website screenshots."""
import bpy,json,math
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[2];OUT=Path(__file__).resolve().parent
bpy.ops.wm.open_mainfile(filepath=str(OUT/'coaster-web-assembly.blend'))
if bpy.context.object and bpy.context.object.mode!='OBJECT':bpy.ops.object.mode_set(mode='OBJECT')
root=bpy.data.objects['YICHEN_Coaster_Prototype'];manifest=json.loads((ROOT/'dist/scroll-parts.json').read_text())['parts'];bases={p['node']:bpy.data.objects[p['node']].location.copy() for p in manifest}
scene=bpy.context.scene;scene.render.resolution_x=1280;scene.render.resolution_y=820;scene.render.resolution_percentage=100;scene.cycles.samples=24;scene.render.image_settings.file_format='PNG'
camera=scene.camera;camera.data.type='ORTHO';camera.data.ortho_scale=8.5;camera.location=(9,11,6);camera.rotation_euler=(Vector((0,0,1.35))-camera.location).to_track_quat('-Z','Y').to_euler()
checks=[('assembled',0,.05,1),('exploded',1,-.54,.89),('restored',0,.05,1)]
for name,amount,angle,scale in checks:
 root.rotation_euler=(0,0,angle);root.scale=(scale,scale,scale)
 for part in manifest:
  d=part['explosionDirection'];obj=bpy.data.objects[part['node']];obj.location=bases[part['node']]+Vector((d[0],-d[2],d[1]))*amount
 bpy.context.view_layer.update()
 if name=='exploded':camera.data.ortho_scale=10.8;camera.rotation_euler=(Vector((0,0,1.65))-camera.location).to_track_quat('-Z','Y').to_euler()
 else:camera.data.ortho_scale=8.5;camera.rotation_euler=(Vector((0,0,1.35))-camera.location).to_track_quat('-Z','Y').to_euler()
 scene.render.filepath=str(OUT/('scroll-'+name+'.png'));bpy.ops.render.render(write_still=True)
 if name=='restored':
  for node,base in bases.items():assert bpy.data.objects[node].location==base
print('BLENDER_SCROLL_POSE_RENDERS_COMPLETE')
