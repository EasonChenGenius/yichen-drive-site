"""Blender-only material revision of the existing Coaster blockout.
This does not establish exact model geometry or actual seating capacity.
"""
import bpy, bmesh, math, json, hashlib
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[2]
OUT=Path(__file__).resolve().parent
SOURCE=OUT/'source-blockout.glb'
REFERENCE=ROOT/'dist/coaster-reference-v2.png'

def object_mode():
 if bpy.context.object and bpy.context.object.mode!='OBJECT':bpy.ops.object.mode_set(mode='OBJECT')

def select_only(objects):
 object_mode();bpy.ops.object.select_all(action='DESELECT')
 for obj in objects:obj.select_set(True)
 if objects:bpy.context.view_layer.objects.active=objects[0]

def srgb(v):return v/12.92 if v<=.04045 else ((v+.055)/1.055)**2.4

def rgba(hexcolor):return tuple(srgb(int(hexcolor[i:i+2],16)/255) for i in (1,3,5))+(1,)

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=str(SOURCE))
vehicle=list(bpy.context.scene.objects)
seat_roots=[o for o in vehicle if o.get('seat') or o.name.startswith('seat-')]
removed=set()
for obj in seat_roots:
 removed.add(obj);removed.update(obj.children_recursive)
for obj in list(removed):bpy.data.objects.remove(obj,do_unlink=True)
removed_count=len(removed)
vehicle=list(bpy.context.scene.objects)
for obj in vehicle:
 for key in ['seats','seatMeshCount','seat']:
  if key in obj:del obj[key]
vehicle=[o for o in vehicle if o.name in bpy.context.scene.objects]
# Material modification is done in Object mode; no speculative reshaping.
object_mode()
paint=[]
for material in bpy.data.materials:
 if material.name.startswith('body-paint'):
  paint.append(material.name);material.diffuse_color=rgba('#bdad94')
  if material.use_nodes:
   bsdf=next((n for n in material.node_tree.nodes if n.type=='BSDF_PRINCIPLED'),None)
   if bsdf:
    bsdf.inputs['Base Color'].default_value=rgba('#bdad94')
    bsdf.inputs['Metallic'].default_value=.42
    bsdf.inputs['Roughness'].default_value=.28
    if 'Coat Weight' in bsdf.inputs:bsdf.inputs['Coat Weight'].default_value=.7
assert paint,'Paint material not found'
# Organize independently editable imported parts.
parts={name:bpy.data.collections.new(name) for name in ['Body','Glass','Wheels','Lights','Details']}
for col in parts.values():bpy.context.scene.collection.children.link(col)
for obj in vehicle:
 if obj.type!='MESH':continue
 name=obj.name.lower()
 group='Glass' if 'window' in name or 'windscreen' in name else 'Wheels' if any(x in name for x in ['tire','rim','wheel','hub']) else 'Lights' if any(x in name for x in ['headlight','tail-light']) else 'Body' if 'body' in name or 'door' in name else 'Details'
 for col in list(obj.users_collection):col.objects.unlink(obj)
 parts[group].objects.link(obj)
# Repair the old blockout windshield's occlusion using a separate editable quad.
# Coordinates are approximate legacy-model corrections, not measured vehicle dimensions.
old_glass=[o for o in vehicle if o.name.startswith('bus-windscreen')]
glass_mat=next(m for m in bpy.data.materials if m.name.startswith('window-glass'))
for obj in old_glass:bpy.data.objects.remove(obj,do_unlink=True)
vehicle=list(bpy.context.scene.objects)
mesh=bpy.data.meshes.new('Review-windscreen-surface')
mesh.from_pydata([(3.48,.88,2.34),(3.48,-.88,2.34),(3.56,-.94,1.32),(3.56,.94,1.32)],[],[(0,1,2,3)])
mesh.update();window=bpy.data.objects.new('Review-windscreen-correction',mesh);parts['Glass'].objects.link(window);window.data.materials.append(glass_mat);vehicle.append(window)
# Recalculate normals in Edit mode on the explicitly selected body mesh.
body=next((obj for obj in vehicle if obj.type=='MESH' and obj.name.startswith('bus-body')),None)
if body:
 select_only([body]);bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT');bm=bmesh.from_edit_mesh(body.data);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bmesh.update_edit_mesh(body.data);bpy.ops.object.mode_set(mode='OBJECT')
reference=bpy.data.objects.new('User-reference-photo',None);bpy.context.scene.collection.objects.link(reference)
reference.empty_display_type='IMAGE';reference.data=bpy.data.images.load(str(REFERENCE));reference.data.pack();reference.hide_render=True;reference.hide_viewport=True
reference['role']='Appearance/color reference only; not a verified dimension or equipment source'
# Studio scene is kept separate from model export.
scene=bpy.context.scene;scene.unit_settings.system='METRIC';scene.unit_settings.scale_length=1
bpy.ops.mesh.primitive_plane_add(size=200,location=(0,0,0));floor=bpy.context.object;floor.name='Studio-floor'
mat=bpy.data.materials.new('Studio-ivory');mat.diffuse_color=rgba('#e9e7e0');mat.use_nodes=True
mat.node_tree.nodes.get('Principled BSDF').inputs['Base Color'].default_value=rgba('#e9e7e0');mat.node_tree.nodes.get('Principled BSDF').inputs['Roughness'].default_value=.8;floor.data.materials.append(mat)
world=bpy.data.worlds.new('Studio-world');scene.world=world;world.use_nodes=True;world.node_tree.nodes.get('Background').inputs['Color'].default_value=(.72,.76,.8,1);world.node_tree.nodes.get('Background').inputs['Strength'].default_value=.45
for name,location,power,size in [('Key',(2,5,7),2100,7),('Fill',(-4,-3,5),1600,6),('Rim',(-4,1,6),1700,5)]:
 data=bpy.data.lights.new(name,'AREA');data.energy=power;data.shape='DISK';data.size=size
 obj=bpy.data.objects.new(name,data);scene.collection.objects.link(obj);obj.location=location;obj.rotation_euler=(Vector((0,0,1.2))-obj.location).to_track_quat('-Z','Y').to_euler()
cam=bpy.data.cameras.new('Review-camera');camera=bpy.data.objects.new('Review-camera',cam);scene.collection.objects.link(camera);camera.location=(9,10,4.8);camera.rotation_euler=(Vector((0,0,1.32))-camera.location).to_track_quat('-Z','Y').to_euler();cam.type='ORTHO';cam.ortho_scale=8.6;scene.camera=camera
scene.render.engine='CYCLES';scene.cycles.device='CPU';scene.cycles.samples=16;scene.cycles.use_denoising=True
scene.render.resolution_x=1200;scene.render.resolution_y=780;scene.render.resolution_percentage=100
scene.view_settings.view_transform='AgX';scene.render.image_settings.file_format='PNG';scene.render.filepath=str(OUT/'coaster-material-review.png')
scene['geometryStatus']='Legacy blockout; not exact vehicle geometry. No seating configuration is represented.'
scene['colorReference']='User supplied photograph; light champagne brown'
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'coaster-material-review.blend'))
select_only([o for o in vehicle if o.name in scene.objects]);bpy.ops.export_scene.gltf(filepath=str(OUT/'coaster-material-review.glb'),export_format='GLB',use_selection=True)
report={'blenderVersion':bpy.app.version_string,'input':str(SOURCE),'inputSha256':hashlib.sha256(SOURCE.read_bytes()).hexdigest(),'modesUsed':['OBJECT','EDIT'],'editedMaterial':paint,'baseColorHex':'#bdad94','removedUnverifiedSeatObjects':removed_count,'meshCount':sum(o.type=='MESH' for o in vehicle),'geometryStatus':'unverified-legacy-blockout','localCorrections':['approximate windscreen surface visibility'],'lux3dTasksSubmitted':0,'outputs':['coaster-material-review.blend','coaster-material-review.glb','coaster-material-review.png']}
(OUT/'blender-execution.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
bpy.ops.render.render(write_still=True)
print('BLENDER_MATERIAL_REVISION_COMPLETE',flush=True)
