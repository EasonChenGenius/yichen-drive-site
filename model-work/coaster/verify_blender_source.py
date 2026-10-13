import bpy,json
from pathlib import Path
root=Path(__file__).resolve().parent
bpy.ops.wm.open_mainfile(filepath=str(root/'coaster-material-review.blend'))
assert bpy.context.object is None or bpy.context.object.mode=='OBJECT'
assert not any(obj.name.startswith('seat-') or obj.get('seat') for obj in bpy.data.objects)
assert all(name in bpy.data.collections for name in ['Body','Glass','Wheels','Lights','Details'])
assert any(image.packed_file for image in bpy.data.images),'Reference image not packed'
material=bpy.data.materials['body-paint'];shader=next(n for n in material.node_tree.nodes if n.type=='BSDF_PRINCIPLED')
report={'blenderVersion':bpy.app.version_string,'sourceReopened':True,'unverifiedSeatingRemoved':True,'referenceImagePacked':True,'collections':[name for name in ['Body','Glass','Wheels','Lights','Details']],'paintLinearRGBA':list(shader.inputs['Base Color'].default_value),'geometryStatus':'unverified-legacy-blockout','renderCamera':bpy.context.scene.camera.name}
(root/'source-verification.json').write_text(json.dumps(report,indent=2));print('SOURCE_VERIFICATION_PASSED')
