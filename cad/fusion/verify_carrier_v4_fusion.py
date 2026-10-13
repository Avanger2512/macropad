"""Validate the six V4 receivers and export the isolated middle carrier."""
import importlib.util
import json
import math
from pathlib import Path
import adsk.core
import adsk.fusion

HERE=Path('/Users/denisbabiichuk/3dPrint/macropad/cad/fusion')
EXPORT=HERE/'exports'


def run(context):
    app=adsk.core.Application.get();d=adsk.fusion.Design.cast(app.activeProduct)
    if d is None or app.activeDocument.name!='macropad':raise RuntimeError('Activate macropad')
    r=d.rootComponent
    baseline=json.loads((EXPORT/'carrier-v4-baseline.json').read_text())['original_volumes_mm3']
    for name,volume in baseline.items():
        original=r.bRepBodies.itemByName(name)
        if original is None or abs(original.volume*1000-volume)>1e-5:raise RuntimeError('Unexpected change to '+name)
    spec=importlib.util.spec_from_file_location('carrier_v4_generator',HERE/'macropad_carrier_compact_v4.py')
    source=importlib.util.module_from_spec(spec);spec.loader.exec_module(source)
    ev=lambda expr:d.unitsManager.evaluateExpression(expr,'cm')*10
    angle=d.unitsManager.evaluateExpression('caseTilt','rad');c,s=math.cos(angle),math.sin(angle)
    bottom=ev('carrierV4BottomDepth');front=ev('frontHeight')
    carrier=r.bRepBodies.itemByName('MiddleCarrier_Draft')
    coupon=r.bRepBodies.itemByName('SwitchFitCoupon_Compact_V4')
    hotswap=r.bRepBodies.itemByName('HotswapCompact_Pin_V4')
    pin=r.bRepBodies.itemByName('MechanicalPin_1mm_REFERENCE_SINGLE')
    if any(b is None for b in (carrier,coupon,hotswap,pin)):raise RuntimeError('Missing V4 geometry')
    def point(cx,cy,x,y,z):
        return adsk.core.Point3D.create((cx+x)/10,(c*(cy+y)-s*(z-bottom))/10,(front+s*(cy+y)+c*(z-bottom))/10)
    inside=adsk.fusion.PointContainment.PointInsidePointContainment
    manager=adsk.fusion.TemporaryBRepManager.get()
    def translated(body,x,y,z=0):
        b=manager.copy(body);m=adsk.core.Matrix3D.create()
        m.translation=adsk.core.Vector3D.create(x/10,y/10,z/10)
        if not manager.transform(b,m):raise RuntimeError('Temporary transform failed')
        return b
    def overlap(a,b,label):
        result=manager.copy(a)
        if not manager.booleanOperation(result,manager.copy(b),adsk.fusion.BooleanTypes.IntersectionBooleanType):
            raise RuntimeError('Intersection failed: '+label)
        volume=result.volume*1000
        if volume>1e-5:raise RuntimeError('Interference '+label+': '+str(volume))
        return volume
    main=[r.bRepBodies.itemByName(n) for n in ('UpperShell_Draft','MiddleCarrier_Draft','BottomCover_Draft','Diffuser_Draft')]
    inp=d.createInterferenceInput(adsk.core.ObjectCollection.createWithArray(main));inp.areCoincidentFacesIncluded=False
    collisions=d.analyzeInterference(inp)
    if collisions.count:raise RuntimeError('Enclosure interference '+str([(x.entityOne.name,x.entityTwo.name) for x in collisions]))
    results=[];reference_x=ev('compactV4TrialX');reference_y=ev('keyRowOne')
    for label,xexpr,yexpr in source.locations():
        cx,cy=ev(xexpr),ev(yexpr);dx=cx-reference_x;dy=cy-reference_y
        shifted_hotswap=translated(hotswap,dx,c*dy,s*dy)
        shifted_pin=translated(pin,dx,c*dy,s*dy)
        for body in main:
            overlap(shifted_hotswap,body,label+' hotswap / '+body.name)
            overlap(shifted_pin,body,label+' pin / '+body.name)
        release=translated(shifted_pin,0,c*3.6,s*3.6)
        overlap(release,carrier,label+' partial pin withdrawal')
        clearance=0;pin_samples=0;wire_samples=0;match_samples=0
        for depth in (4.4,5,6,7,8,8.8):
            for x in (-7.9,-6,-3,0,3,6,7.9):
                for y in (-7.9,-6,-3,0,3,6,7.9):
                    if carrier.pointContainment(point(cx,cy,x,y,bottom-depth))==inside:raise RuntimeError(label+' switch cavity blocked')
                    clearance+=1
        for y in (-.08,0,.2,.6,1,1.8,2.7,3.3,4.5,6,8.4,8.8,9.5,11,13.4):
            for deg in range(0,360,45):
                t=math.radians(deg)
                if carrier.pointContainment(point(cx,cy,4.3+.49*math.cos(t),y,1.6+.49*math.sin(t)))==inside:
                    raise RuntimeError(label+' pin path blocked')
                pin_samples+=1
        if carrier.pointContainment(point(cx,cy,4.3,-.35,1.6))!=inside:raise RuntimeError(label+' pin blind end lost')
        for y,z in ((-2.500016,1.138835),(-5.099996,1.172852),(-3.011004,4.093049)):
            for x in (-9,-8,-7,-6,6,7,8,9):
                for deg in range(0,360,45):
                    t=math.radians(deg)
                    if carrier.pointContainment(point(cx,cy,x,y+.55*math.cos(t),z+.55*math.sin(t)))==inside:raise RuntimeError(label+' X wire blocked')
                    wire_samples+=1
        for y in (-8,-7,-6,4,5,6,7,8):
            for deg in range(0,360,45):
                t=math.radians(deg)
                if carrier.pointContainment(point(cx,cy,4.190238+.55*math.cos(t),y,4.093049+.55*math.sin(t)))==inside:raise RuntimeError(label+' Y wire blocked')
                wire_samples+=1
        # Near lower receiver region, exact geometry should match the coupon.
        for z in (.15,1.1,1.6,2.8,3.5,5.1):
            for x in (-9.1,-8.5,-7.7,-5,-4.8,-3,0,3,4.3,4.8,5,7.7,8.5,9.1):
                for y in (-8.7,-8.2,-7.7,-5.1,-3,-1,0,1,3,6,7.7,8.2,8.7):
                    a=carrier.pointContainment(point(cx,cy,x,y,z))==inside
                    b=coupon.pointContainment(point(reference_x,reference_y,x,y,z))==inside
                    if a!=b:raise RuntimeError(label+' differs from coupon at '+str((x,y,z)))
                    match_samples+=1
        results.append({'name':label,'center_face_mm':[cx,cy],'hotswap_and_pin_intersections':0,
                        'switch_clearance_samples':clearance,'pin_path_samples':pin_samples,'wire_path_samples':wire_samples,
                        'coupon_match_samples':match_samples,'pin_partial_withdrawal_mm':3.6})
    removal=[]
    # Record extraction obstructions independently of static fit checks.
    for path in ('vertical','face_normal'):
        obstruction=None
        for drop in (0,.25,.5,1,2,3,4,5,6,8,10,15,20,25,30,35):
            moving=translated(carrier,0,0 if path=='vertical' else s*drop,-drop if path=='vertical' else -c*drop)
            for name in ('UpperShell_Draft','Diffuser_Draft'):
                intersection=manager.copy(moving)
                if not manager.booleanOperation(intersection,manager.copy(r.bRepBodies.itemByName(name)),adsk.fusion.BooleanTypes.IntersectionBooleanType):
                    raise RuntimeError('Removal intersection computation failed')
                volume=intersection.volume*1000
                if volume>1e-5:
                    obstruction={'body':name,'drop_mm':drop,'intersection_mm3':volume}
                    break
            if obstruction:break
        removal.append({'path':path,'first_obstruction':obstruction})
    errors=[t.name for t in d.timeline if not getattr(t.entity,'isSuppressed',False) and t.healthState!=adsk.fusion.FeatureHealthStates.HealthyFeatureHealthState]
    unconstrained=[sk.name for sk in r.sketches if not sk.isFullyConstrained]
    if errors or unconstrained:raise RuntimeError(str({'features':errors,'sketches':unconstrained}))
    for body in r.bRepBodies:body.isVisible=body==carrier
    for mesh in r.meshBodies:mesh.isLightBulbOn=False
    exporter=d.exportManager
    if not exporter.execute(exporter.createSTEPExportOptions(str(EXPORT/'middle_carrier_compact_v4.step'))):raise RuntimeError('STEP failed')
    opt=exporter.createSTLExportOptions(carrier,str(EXPORT/'middle_carrier_compact_v4_native.stl'))
    opt.unitType=adsk.fusion.DistanceUnits.MillimeterDistanceUnits;opt.isBinaryFormat=True
    opt.meshRefinement=adsk.fusion.MeshRefinementSettings.MeshRefinementHigh
    if not exporter.execute(opt):raise RuntimeError('STL failed')
    box=carrier.boundingBox
    target=adsk.core.Point3D.create((box.minPoint.x+box.maxPoint.x)/2,(box.minPoint.y+box.maxPoint.y)/2,(box.minPoint.z+box.maxPoint.z)/2)
    for name,offset in (('carrier-v4-underneath.png',(8,-10,-12)),('carrier-v4-top.png',(-8,10,12))):
        camera=app.activeViewport.camera;camera.target=target
        camera.eye=adsk.core.Point3D.create(target.x+offset[0],target.y+offset[1],target.z+offset[2])
        camera.upVector=adsk.core.Vector3D.create(0,0,1);camera.isFitView=True
        app.activeViewport.camera=camera;app.activeViewport.refresh()
        if not app.activeViewport.saveAsImageFile(str(EXPORT/name),1400,1050):raise RuntimeError('Snapshot failed')
    for b in main:b.isVisible=True
    app.activeViewport.fit()
    if not exporter.execute(exporter.createFusionArchiveExportOptions(str(EXPORT/'macropad_carrier_compact_v4.f3d'))):raise RuntimeError('Archive failed')
    report={'revision':'Carrier compact V4','receivers':results,'enclosure_intersections':0,'healthy_timeline':True,'other_bodies_unchanged':True,
            'unconstrained_sketches':unconstrained,'removal_path_checks':removal,'volume_mm3':carrier.volume*1000,
            'limits':'Straight carrier extraction is obstructed and requires assembly-sequence validation; bottom supports unchanged and untested; encoder, connectors, real PCB and complete wired removal require physical validation; USB opening pending'}
    (EXPORT/'carrier-v4-validation.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
