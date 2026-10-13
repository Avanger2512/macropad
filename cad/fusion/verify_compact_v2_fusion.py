import adsk.core,adsk.fusion,json,math,struct
from pathlib import Path

def run(context):
 app=adsk.core.Application.get();d=adsk.fusion.Design.cast(app.activeProduct);r=d.rootComponent
 b=r.bRepBodies.itemByName('SwitchFitCoupon_Compact_V2')
 if b is None:raise RuntimeError('Missing V2 body')
 folder=Path('/Users/denisbabiichuk/3dPrint/macropad/cad/fusion/exports')
 errs=[t.name for t in d.timeline if t.healthState!=adsk.fusion.FeatureHealthStates.HealthyFeatureHealthState]
 if errs:raise RuntimeError('Unhealthy features '+str(errs))
 if not b.isSolid or b.volume<=0:raise RuntimeError('V2 not a solid')
 verts=[];centers=[]
 data=(folder/'compact_reference_aligned_v2.stl').read_bytes();n=struct.unpack_from('<I',data,80)[0]
 for i in range(n):
  tri=[struct.unpack_from('<3f',data,84+i*50+12+12*j) for j in range(3)]
  verts.extend(tri);centers.append(tuple(sum(p[a] for p in tri)/3 for a in range(3)))
 inside=adsk.fusion.PointContainment.PointInsidePointContainment
 count=sum(b.pointContainment(adsk.core.Point3D.create(*(x/10 for x in v)))==inside for v in set(verts))
 triangles=sum(b.pointContainment(adsk.core.Point3D.create(*(x/10 for x in v)))==inside for v in centers)
 if count or triangles:raise RuntimeError(f'Compact mesh interference samples: vertices={count}, triangles={triangles}')
 for body in r.bRepBodies:body.isVisible=body==b
 # Meshes are references, not exported printable solids.
 e=d.exportManager
 mesh=next((m for m in r.meshBodies if m.name=='hotswap_mx__compact_REFERENCE_V2'),None)
 if mesh is None:raise RuntimeError('Missing compact reference')
 mesh.isLightBulbOn=False
 if not e.execute(e.createSTEPExportOptions(str(folder/'switch_fit_coupon_compact_v2.step'))):raise RuntimeError('STEP failed')
 opt=e.createSTLExportOptions(b,str(folder/'switch_fit_coupon_compact_v2_native.stl'))
 opt.unitType=adsk.fusion.DistanceUnits.MillimeterDistanceUnits;opt.isBinaryFormat=True
 opt.meshRefinement=adsk.fusion.MeshRefinementSettings.MeshRefinementHigh
 if not e.execute(opt):raise RuntimeError('STL failed')
 if not e.execute(e.createFusionArchiveExportOptions(str(folder/'macropad_compact_trial_v2.f3d'))):raise RuntimeError('F3D failed')
 mesh=next((m for m in r.meshBodies if m.name=='hotswap_mx__compact_REFERENCE_V2'),None)
 if mesh is None:raise RuntimeError('Missing imported compact reference')
 mesh.isLightBulbOn=False
 app.activeViewport.fit()
 camera=app.activeViewport.camera
 box=b.boundingBox
 target=adsk.core.Point3D.create((box.minPoint.x+box.maxPoint.x)/2,(box.minPoint.y+box.maxPoint.y)/2,(box.minPoint.z+box.maxPoint.z)/2)
 camera.target=target
 camera.eye=adsk.core.Point3D.create(target.x+3,target.y-4,target.z-4)
 camera.upVector=adsk.core.Vector3D.create(0,0,1)
 camera.isFitView=True
 app.activeViewport.camera=camera
 app.activeViewport.refresh()
 if not app.activeViewport.saveAsImageFile(str(folder/'compact-v2-receiver.png'),1400,1050):raise RuntimeError('Receiver snapshot failed')
 mesh.isLightBulbOn=True
 mesh.opacity=0.6
 app.activeViewport.refresh()
 if not app.activeViewport.saveAsImageFile(str(folder/'compact-v2-assembled.png'),1400,1050):raise RuntimeError('Assembly snapshot failed')
 if not e.execute(e.createFusionArchiveExportOptions(str(folder/'macropad_compact_trial_v2.f3d'))):raise RuntimeError('Final F3D failed')
 report={'body':b.name,'volume_mm3':b.volume*1000,'healthy_timeline':True,'mesh_inside_vertex_samples':count,'mesh_inside_triangle_samples':triangles,'mesh_vertices_checked':len(set(verts)),'mesh_triangles_checked':n,'body_count':r.bRepBodies.count,'reference_mesh_count':r.meshBodies.count,'unconstrained_sketches':[s.name for s in r.sketches if not s.isFullyConstrained]}
 (folder/'compact-v2-validation.json').write_text(json.dumps(report,indent=2))
 print(json.dumps(report))
