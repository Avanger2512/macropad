"""Check pin-only retention V4 and export separate printable parts."""
import json
import math
import struct
from pathlib import Path
import adsk.core
import adsk.fusion

FOLDER=Path('/Users/denisbabiichuk/3dPrint/macropad/cad/fusion/exports')


def run(context):
    app=adsk.core.Application.get();d=adsk.fusion.Design.cast(app.activeProduct);r=d.rootComponent
    receiver=r.bRepBodies.itemByName('SwitchFitCoupon_Compact_V4')
    hotswap=r.bRepBodies.itemByName('HotswapCompact_Pin_V4')
    pins=[r.bRepBodies.itemByName('MechanicalPin_1mm_REFERENCE_SINGLE')]
    if any(b is None for b in (receiver,hotswap,*pins)):
        raise RuntimeError('Missing V4 bodies')
    errors=[t.name for t in d.timeline if not getattr(t.entity,"isSuppressed",False) and t.healthState!=adsk.fusion.FeatureHealthStates.HealthyFeatureHealthState]
    unconstrained=[s.name for s in r.sketches if not s.isFullyConstrained]
    if errors or unconstrained or any(not b.isSolid or b.volume<=0 for b in (receiver,hotswap,*pins)):
        raise RuntimeError(str({'features':errors,'sketches':unconstrained}))
    inp=d.createInterferenceInput(adsk.core.ObjectCollection.createWithArray([receiver,hotswap,*pins]))
    inp.areCoincidentFacesIncluded=False
    if d.analyzeInterference(inp).count:
        raise RuntimeError('V4 pin assembly interference')
    ev=lambda x:d.unitsManager.evaluateExpression(x,'cm')*10
    cx,cy,front,bottom=(ev(x) for x in ('compactV4TrialX','keyRowOne','frontHeight','compactV4BottomDepth'))
    angle=d.unitsManager.evaluateExpression('caseTilt','rad');c,s=math.cos(angle),math.sin(angle)
    def pt(x,y,z):
        return adsk.core.Point3D.create((cx+x)/10,(c*(cy+y)-s*(z-bottom))/10,(front+s*(cy+y)+c*(z-bottom))/10)
    inside=adsk.fusion.PointContainment.PointInsidePointContainment
    clear_samples=0
    # Lower-switch envelope in receiver only; not a claim about actual switch fit with hotswap.
    for depth in (4.4,5,6,7,8,8.8):
        for x in (-7.9,-6,-3,0,3,6,7.9):
            for y in (-7.9,-6,-3,0,3,6,7.9):
                if receiver.pointContainment(pt(x,y,bottom-depth))==inside:
                    raise RuntimeError('Receiver blocks lower switch clearance')
                clear_samples+=1
    blocked_pins=0
    for y in (-.08,0,.2,.6,1,1.8,2.7,3.3,4.5,6,8.4,8.8,9.5):
        for deg in range(0,360,45):
            t=math.radians(deg)
            p=pt(4.3+.49*math.cos(t),y,1.6+.49*math.sin(t))
            blocked_pins+=(receiver.pointContainment(p)==inside or hotswap.pointContainment(p)==inside)
    if blocked_pins:raise RuntimeError('Single pin path blocked')
    if receiver.pointContainment(pt(4.3,-.35,1.6))!=inside:
        raise RuntimeError('Guide blind-end wall missing')
    for x in (-5,5):
        if hotswap.pointContainment(pt(x,1.8,1.6))!=inside:
            raise RuntimeError('Obsolete side bore remains in compact')
    for x in (-8.5,8.5):
        if receiver.pointContainment(pt(x,1.8,1.6))!=inside:
            raise RuntimeError('Obsolete side bore remains in receiver')
    wire_hits=0
    for y,z in ((-2.500016,1.138835),(-5.099996,1.172852),(-3.011004,4.093049)):
        for x in (-9,-8,-7,-6,6,7,8,9):
            for deg in range(0,360,45):
                t=math.radians(deg)
                wire_hits+=receiver.pointContainment(pt(x,y+.55*math.cos(t),z+.55*math.sin(t)))==inside
    for y in (-8,-7,-6,4,5,6,7,8):
        for deg in range(0,360,45):
            t=math.radians(deg)
            wire_hits+=receiver.pointContainment(pt(4.190238+.55*math.cos(t),y,4.093049+.55*math.sin(t)))==inside
    if wire_hits:
        raise RuntimeError('Receiver obstructs original wire axes')
    for mesh in r.meshBodies:
        mesh.isLightBulbOn=False
    e=d.exportManager
    for body,base in ((receiver,'switch_fit_coupon_compact_v4'),(hotswap,'hotswap_mx_compact_pin_v4')):
        for b in r.bRepBodies:
            b.isVisible=b==body
        if not e.execute(e.createSTEPExportOptions(str(FOLDER/(base+'.step')))):
            raise RuntimeError('STEP failed')
        opt=e.createSTLExportOptions(body,str(FOLDER/(base+'_native.stl')))
        opt.unitType=adsk.fusion.DistanceUnits.MillimeterDistanceUnits;opt.isBinaryFormat=True
        opt.meshRefinement=adsk.fusion.MeshRefinementSettings.MeshRefinementHigh
        if not e.execute(opt):
            raise RuntimeError('STL failed')
    def snapshot(body,name,below):
        for b in r.bRepBodies:b.isVisible=b==body
        box=body.boundingBox
        target=adsk.core.Point3D.create((box.minPoint.x+box.maxPoint.x)/2,(box.minPoint.y+box.maxPoint.y)/2,(box.minPoint.z+box.maxPoint.z)/2)
        camera=app.activeViewport.camera;camera.target=target
        camera.eye=adsk.core.Point3D.create(target.x+3,target.y-4,target.z+(-4 if below else 4))
        camera.upVector=adsk.core.Vector3D.create(0,0,1);camera.isFitView=True
        app.activeViewport.camera=camera;app.activeViewport.refresh()
        if not app.activeViewport.saveAsImageFile(str(FOLDER/name),1400,1050):raise RuntimeError('Snapshot failed')
    snapshot(hotswap,'compact-v4-hotswap.png',False)
    snapshot(receiver,'compact-v4-receiver.png',True)
    for b in (hotswap,*pins):b.isVisible=True
    hotswap.opacity=.6
    app.activeViewport.refresh()
    if not app.activeViewport.saveAsImageFile(str(FOLDER/'compact-v4-assembled.png'),1400,1050):raise RuntimeError('Assembly snapshot failed')
    if not e.execute(e.createFusionArchiveExportOptions(str(FOLDER/'macropad_compact_trial_v4.f3d'))):raise RuntimeError('Archive failed')
    report={'revision':'V4','retention':'One front-entry transverse pin ending in side guide; no upper stops',
            'pin_diameter_mm':ev('compactV4PinDiameter'),'pin_bore_mm':ev('compactV4PinBore'),
            'pin_count':1,'pin_reference_length_mm':ev('compactV4PinLength'),'guide_blind_end_y_mm':ev('compactV4PinEnd'),
            'local_pin_x_z_mm':[4.3,1.6],'exposed_pin_length_mm':1.1,'holder_top_bottom_depth_mm':[ev('compactV4TopDepth'),bottom],
            'receiver_lower_switch_clearance_samples':clear_samples,'pin_obstruction_samples':blocked_pins,
            'wire_obstruction_samples':wire_hits,'pair_interferences':0,'healthy_timeline':True,
            'unconstrained_sketches':unconstrained,'volumes_mm3':{b.name:b.volume*1000 for b in (receiver,hotswap,*pins)},
            'main_holder_depths_mm':[ev('holderTopDepth'),ev('holderBottomDepth')],
            'limits':'Actual switch fit, pin insertion force and electrical contact require physical test'}
    (FOLDER/'compact-v4-validation.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report))
