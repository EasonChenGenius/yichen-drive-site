"""Prepare a real Blender workspace; this is NOT a completed vehicle model."""
from pathlib import Path
import bpy, math, json
from mathutils import Vector
OUT=Path(__file__).resolve().parent
bpy.ops.wm.read_factory_settings(use_empty=True)
scene=bpy.context.scene;scene.unit_settings.system='METRIC';scene.unit_settings.scale_length=1
scene['modelStatus']='reference-preparation-not-a-completed-vehicle'
scene['targetReference']='2022 Buick GL8 ES Lu Zun 653T'
scene['actualFleetTrimVerified']=False
scene['manufacturerPublishedDimensionSource']='https://auto.gasgoo.com/news/202109/13I70272527C107.shtml'
scene['officialVariantEvidence']='https://www.ciasi.org.cn/uploads/files/e6f45547c9d28d06d333719f56e5acd1.pdf'
collections={name:bpy.data.collections.new(name) for name in ['Reference','Body','Glass','Wheels','Lights','Grille_Trim','Studio']}
for col in collections.values():scene.collection.children.link(col)
# These line segments are measurement guides, not fabricated body geometry.
L,W,H,WB=5.219,1.878,1.799,3.088
points=[(-L/2,-W/2,0),(L/2,-W/2,0),(L/2,W/2,0),(-L/2,W/2,0),(-L/2,-W/2,H),(L/2,-W/2,H),(L/2,W/2,H),(-L/2,W/2,H)]
mesh=bpy.data.meshes.new('Published-dimension-guide-lines');mesh.from_pydata(points,[(0,1),(1,2),(2,3),(3,0),(4,5),(5,6),(6,7),(7,4),(0,4),(1,5),(2,6),(3,7)],[]);mesh.update()
obj=bpy.data.objects.new('REFERENCE_ONLY_5219x1878x1799mm',mesh);collections['Reference'].objects.link(obj);obj.display_type='WIRE';obj.hide_render=True;obj['role']='Published dimensional envelope only; not actual vehicle geometry'
wbmesh=bpy.data.meshes.new('Wheelbase-distance-guide');wbmesh.from_pydata([(-WB/2,0,-.15),(WB/2,0,-.15)],[(0,1)],[])
wb=bpy.data.objects.new('REFERENCE_ONLY_3088mm_distance',wbmesh);collections['Reference'].objects.link(wb);wb.hide_render=True;wb['role']='Distance reference only; actual axle placement requires full reference views'
for name,location,target in [('Front',(9,0,.95),(0,0,.95)),('Side',(0,-9,.95),(0,0,.95)),('Rear',(-9,0,.95),(0,0,.95)),('Threequarter',(8,-9,4),(0,0,.9))]:
 camera=bpy.data.cameras.new(name);ob=bpy.data.objects.new(name,camera);collections['Studio'].objects.link(ob);ob.location=location;ob.rotation_euler=(Vector(target)-ob.location).to_track_quat('-Z','Y').to_euler();camera.type='ORTHO';camera.ortho_scale=6.4
 if name=='Threequarter':scene.camera=ob
for name,location,power in [('Key',(3,-4,6),1700),('Fill',(-3,4,4),1200)]:
 light=bpy.data.lights.new(name,'AREA');light.energy=power;light.size=5;ob=bpy.data.objects.new(name,light);collections['Studio'].objects.link(ob);ob.location=location;ob.rotation_euler=(Vector((0,0,.9))-ob.location).to_track_quat('-Z','Y').to_euler()
world=bpy.data.worlds.new('Studio-world');world.use_nodes=True;world.node_tree.nodes.get('Background').inputs['Strength'].default_value=.45;scene.world=world
notes=bpy.data.texts.new('PRODUCTION_README');notes.write('Reference fixture only. No completed body, wheel, interior or seating geometry exists. Import approved Lux3D parts into named collections. Inspect actual geometry in Object mode; explicitly select the intended mesh before entering Edit mode. Do not label this fixture as a final model or export it as the finished vehicle.\n')
assert bpy.context.object is None or bpy.context.object.mode=='OBJECT'
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'production-workspace.blend'))
report={'blenderVersion':bpy.app.version_string,'mode':'OBJECT','collections':list(collections),'actualVehicleMeshCount':0,'referenceEnvelopeMetres':[L,W,H],'wheelbaseDistanceMetres':WB,'geometryStatus':'reference-guides-only','lux3dTasksSubmitted':0}
(OUT/'blender-preparation.json').write_text(json.dumps(report,indent=2));print('BLENDER_REFERENCE_WORKSPACE_SAVED')
