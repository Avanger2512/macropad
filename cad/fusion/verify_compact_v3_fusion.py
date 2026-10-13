"""Validate V3 mating geometry and export isolated fit-print artifacts."""
import json
import math
import struct
from pathlib import Path
import adsk.core
import adsk.fusion

FOLDER = Path('/Users/denisbabiichuk/3dPrint/macropad/cad/fusion/exports')


def run(context):
    app=adsk.core.Application.get()
    d=adsk.fusion.Design.cast(app.activeProduct)
    r=d.rootComponent
    body=r.bRepBodies.itemByName('SwitchFitCoupon_Compact_V3')
    lid=r.bRepBodies.itemByName('LidSupportCoupon_Compact_V3')
    if body is None or lid is None:
        raise RuntimeError('Missing V3 pair')
    errors=[t.name for t in d.timeline if t.healthState!=adsk.fusion.FeatureHealthStates.HealthyFeatureHealthState]
    unconstrained=[s.name for s in r.sketches if not s.isFullyConstrained]
    if errors or unconstrained or any(not b.isSolid or b.volume<=0 for b in (body,lid)):
        raise RuntimeError(str({'features':errors,'sketches':unconstrained}))
    inp=d.createInterferenceInput(adsk.core.ObjectCollection.createWithArray([body,lid]))
    inp.areCoincidentFacesIncluded=False
    if d.analyzeInterference(inp).count:
        raise RuntimeError('Receiver/lid interference')
    data=(FOLDER/'compact_reference_aligned_v3.stl').read_bytes()
    n=struct.unpack_from('<I',data,80)[0]
    vertices=set()
    centers=[]
    for i in range(n):
        tri=[struct.unpack_from('<3f',data,84+i*50+12+12*j) for j in range(3)]
        vertices.update(tri)
        centers.append(tuple(sum(p[a] for p in tri)/3 for a in range(3)))
    inside=adsk.fusion.PointContainment.PointInsidePointContainment
    def is_inside(solid,p):
        return solid.pointContainment(adsk.core.Point3D.create(*(v/10 for v in p)))==inside
    samples={}
    for solid in (body,lid):
        hits_vertices=sum(is_inside(solid,p) for p in vertices)
        hits_triangles=sum(is_inside(solid,p) for p in centers)
        if hits_vertices or hits_triangles:
            raise RuntimeError(f'Mesh overlap with {solid.name}: {hits_vertices}, {hits_triangles}')
        samples[solid.name]={'inside_vertices':hits_vertices,'inside_triangle_centroids':hits_triangles}
    ev=lambda expression:d.unitsManager.evaluateExpression(expression,'cm')*10
    angle=d.unitsManager.evaluateExpression('caseTilt','rad')
    c,s=math.cos(angle),math.sin(angle)
    cx,cy,front,bottom=(ev(x) for x in ('compactV3TrialX','keyRowOne','frontHeight','compactV3BottomDepth'))
    def point(x,y,z):
        return (cx+x,c*(cy+y)-s*(z-bottom),front+s*(cy+y)+c*(z-bottom))
    blocked=0
    for y,z in ((-2.500016,1.138835),(-5.099996,1.172852),(-3.011004,4.093049)):
        for x in (-9,-8,-7,-6,6,7,8,9):
            for deg in range(0,360,45):
                t=math.radians(deg)
                blocked+=is_inside(body,point(x,y+.55*math.cos(t),z+.55*math.sin(t)))
    for y in (-8,-7,-6,4,5,6,7,8):
        for deg in range(0,360,45):
            t=math.radians(deg)
            blocked+=is_inside(body,point(4.190238+.55*math.cos(t),y,4.093049+.55*math.sin(t)))
    if blocked:
        raise RuntimeError('Wire channel obstruction')
    for mesh in r.meshBodies:
        mesh.isLightBulbOn=False
    reference=next((m for m in r.meshBodies if m.name=='hotswap_mx__compact_REFERENCE_V3'),None)
    if reference is None:
        raise RuntimeError('Missing reference mesh')
    e=d.exportManager
    for solid,basename in ((body,'switch_fit_coupon_compact_v3'),(lid,'lid_support_coupon_compact_v3')):
        for b in r.bRepBodies:
            b.isVisible=b==solid
        if not e.execute(e.createSTEPExportOptions(str(FOLDER/(basename+'.step')))):
            raise RuntimeError('STEP failed')
        opt=e.createSTLExportOptions(solid,str(FOLDER/(basename+'_native.stl')))
        opt.unitType=adsk.fusion.DistanceUnits.MillimeterDistanceUnits
        opt.isBinaryFormat=True
        opt.meshRefinement=adsk.fusion.MeshRefinementSettings.MeshRefinementHigh
        if not e.execute(opt):
            raise RuntimeError('STL failed')
    def snapshot(solid,filename,from_below):
        for b in r.bRepBodies:
            b.isVisible=b==solid
        box=solid.boundingBox
        target=adsk.core.Point3D.create((box.minPoint.x+box.maxPoint.x)/2,(box.minPoint.y+box.maxPoint.y)/2,(box.minPoint.z+box.maxPoint.z)/2)
        camera=app.activeViewport.camera
        camera.target=target
        camera.eye=adsk.core.Point3D.create(target.x+3,target.y-4,target.z+(-4 if from_below else 4))
        camera.upVector=adsk.core.Vector3D.create(0,0,1)
        camera.isFitView=True
        app.activeViewport.camera=camera
        app.activeViewport.refresh()
        if not app.activeViewport.saveAsImageFile(str(FOLDER/filename),1400,1050):
            raise RuntimeError('Snapshot failed')
    snapshot(lid,'compact-v3-lid.png',False)
    snapshot(body,'compact-v3-receiver.png',True)
    reference.isLightBulbOn=True
    reference.opacity=.6
    app.activeViewport.refresh()
    if not app.activeViewport.saveAsImageFile(str(FOLDER/'compact-v3-assembled.png'),1400,1050):
        raise RuntimeError('Assembled snapshot failed')
    if not e.execute(e.createFusionArchiveExportOptions(str(FOLDER/'macropad_compact_trial_v3.f3d'))):
        raise RuntimeError('Archive failed')
    report={'revision':'V3','shift_toward_switch_mm':ev('compactV3Shift'),
            'holder_top_depth_mm':ev('compactV3TopDepth'),'holder_bottom_depth_mm':bottom,
            'pin_tip_local_z_mm_if_V2_measurement_is_4':bottom-(ev('holderBottomDepth')-4),
            'lid_normal_gap_mm':ev('holderLidGap'),'wire_diameter_mm':ev('compactV3WireDiameter'),
            'healthy_timeline':True,'unconstrained_sketches':unconstrained,
            'pair_interferences':0,'mesh_samples':samples,'vertices_checked':len(vertices),
            'triangle_centroids_checked':n,'wire_blocked_samples':blocked,'wire_samples_checked':256,
            'solid_volumes_mm3':{b.name:b.volume*1000 for b in (body,lid)},
            'main_holder_depths_mm':{x:ev(x) for x in ('holderTopDepth','holderBottomDepth')}}
    (FOLDER/'compact-v3-validation.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report))
