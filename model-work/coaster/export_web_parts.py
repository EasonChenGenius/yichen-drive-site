"""Re-export existing Blender geometry with independent animation roots.
No vehicle geometry or equipment is invented by this export step.
"""
import bpy,json,hashlib
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[2];OUT=Path(__file__).resolve().parent
SOURCE=OUT/'coaster-material-review.blend';DEST=ROOT/'dist/models/coaster-scroll.glb'
bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
if bpy.context.object and bpy.context.object.mode!='OBJECT':bpy.ops.object.mode_set(mode='OBJECT')
parts={};assignments={};source_world={}
for group in ['Body','Glass','Wheels','Lights','Details']:
 for obj in list(bpy.data.collections[group].objects):
  if obj.type!='MESH':continue
  source_world[obj.name]=obj.matrix_world.copy()
  name=obj.name.lower();coords=[obj.matrix_world@Vector(corner) for corner in obj.bound_box];center=sum(coords,Vector())/len(coords)
  if group=='Wheels':part='Wheel_'+('Front_' if center.x>0 else 'Rear_')+('Left' if center.y>0 else 'Right')
  elif group=='Lights':part='Lights_Front' if center.x>0 else 'Lights_Rear'
  elif group=='Details':part='Exterior_Details'
  else:part=group
  parts.setdefault(part,[]).append(obj);assignments[obj.name]=part
assert sum(map(len,parts.values()))==87
assembly=bpy.data.objects.new('YICHEN_Coaster_Prototype',None);bpy.context.scene.collection.objects.link(assembly)
assembly['assetStatus']='structural-prototype-not-verified-production-vehicle'
assembly['configurationVerified']=False
roots=[];manifest=[]
for name,objects in parts.items():
 points=[obj.matrix_world@Vector(corner) for obj in objects for corner in obj.bound_box]
 low=Vector(tuple(min(p[i] for p in points) for i in range(3)));high=Vector(tuple(max(p[i] for p in points) for i in range(3)));center=(low+high)/2
 parent=bpy.data.objects.new('Part_'+name,None);bpy.context.scene.collection.objects.link(parent);parent.parent=assembly;parent.location=center
 parent['partId']=name;parent['meshCount']=len(objects);parent['motionRole']='independent-component-root';roots.append(parent)
 bpy.context.view_layer.update()
 for obj in objects:
  obj.parent=parent;obj.matrix_world=source_world[obj.name]
 bpy.context.view_layer.update()
 for obj in objects:
  error=max(abs(obj.matrix_world[i][j]-source_world[obj.name][i][j]) for i in range(4) for j in range(4))
  assert error<1e-5,('Reparent changed source geometry pose',obj.name,error)
 direction=[0,0,0]
 if name=='Body':direction=[0,.65,0]
 elif name=='Glass':direction=[0,1.7,0]
 elif name.startswith('Wheel_'):direction=[.24 if 'Front' in name else -.24,.04,-1.4 if 'Left' in name else 1.4]
 elif name=='Lights_Front':direction=[1.35,.2,0]
 elif name=='Lights_Rear':direction=[-1.35,.2,0]
 else:direction=[0,-.45,.2]
 manifest.append({'id':name,'node':'Part_'+name,'meshCount':len(objects),'initialPosition':[center.x,center.z,-center.y],'explosionDirection':direction,'meshNames':[obj.name for obj in objects]})
bpy.ops.object.select_all(action='DESELECT');assembly.select_set(True)
for parent in roots:parent.select_set(True)
for objects in parts.values():
 for obj in objects:obj.select_set(True)
bpy.context.view_layer.objects.active=assembly
bpy.ops.export_scene.gltf(filepath=str(DEST),export_format='GLB',use_selection=True,export_extras=True,export_cameras=False,export_lights=False)
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'coaster-web-assembly.blend'))
record={'source':str(SOURCE),'sourceSha256':hashlib.sha256(SOURCE.read_bytes()).hexdigest(),'output':'models/coaster-scroll.glb','outputSha256':hashlib.sha256(DEST.read_bytes()).hexdigest(),'blenderVersion':bpy.app.version_string,'mode':'OBJECT','meshCount':sum(map(len,parts.values())),'sourceWorldTransformsPreserved':True,'geometryRegenerated':False,'configurationVerified':False,'parts':manifest}
(ROOT/'dist/scroll-parts.json').write_text(json.dumps(record,indent=2));(OUT/'web-export.json').write_text(json.dumps(record,indent=2))
print('WEB_PARTS_EXPORT_COMPLETE',len(roots),'independent roots',sum(map(len,parts.values())),'meshes')
