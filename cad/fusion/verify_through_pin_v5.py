"""Verify actual V5 through-pin passage, contact separation and export parts."""
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
    spec=importlib.util.spec_from_file_location('v5_source',HERE/'macropad_through_pin_v5.py')
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    m,h=module.load_helpers();module.healthy(d)
    ev=lambda e:d.unitsManager.evaluateExpression(e,'cm')*10
    angle=d.unitsManager.evaluateExpression('caseTilt','rad');c,s=math.cos(angle),math.sin(angle)
    bottom,front=ev('carrierV4BottomDepth'),ev('frontHeight')
    py,pz=ev('throughPinV5Y'),ev('throughPinV5Z')
    inside=adsk.fusion.PointContainment.PointInsidePointContainment
    carrier=r.bRepBodies.itemByName('MiddleCarrier_Draft')
    coupon=r.bRepBodies.itemByName('SwitchFitCoupon_Compact_V4')
    holder=r.bRepBodies.itemByName('HotswapCompact_Pin_V4')
    pin=r.bRepBodies.itemByName('MechanicalPin_Through_V5_REFERENCE')
    if any(b is None for b in (carrier,coupon,holder,pin)):raise RuntimeError('Missing V5 geometry')
    baseline=json.loads((EXPORT/'through-pin-v5-baseline.json').read_text())
    changed={carrier.name,coupon.name,holder.name,'MechanicalPin_1mm_REFERENCE_SINGLE'}
    for name,volume in baseline.items():
        if name in changed:continue
        body=r.bRepBodies.itemByName(name)
        if body is None or abs(body.volume*1000-volume)>1e-5:raise RuntimeError('Unexpected change '+name)
    def point(cx,cy,x,y,z):
        return adsk.core.Point3D.create((cx+x)/10,(c*(cy+y)-s*(z-bottom))/10,(front+s*(cy+y)+c*(z-bottom))/10)
    manager=adsk.fusion.TemporaryBRepManager.get()
    def translated(body,x,y,z):
        out=manager.copy(body);matrix=adsk.core.Matrix3D.create();matrix.translation=adsk.core.Vector3D.create(x/10,y/10,z/10)
        if not manager.transform(out,matrix):raise RuntimeError('Transform failed')
        return out
    def overlap(a,b,label):
        out=manager.copy(a)
        if not manager.booleanOperation(out,manager.copy(b),adsk.fusion.BooleanTypes.IntersectionBooleanType):raise RuntimeError('Intersection failed '+label)
        if out.volume*1000>1e-5:raise RuntimeError('Interference '+label+' '+str(out.volume*1000))
    reference_x,reference_y=ev('compactV4TrialX'),ev('keyRowOne')
    # Require empty bore surrounded by real holder material, not an absent wall.
    for x in (-5,-4.3,-3,0,3,4.3,5):
        for y in (py-.7,py+.8):
            if holder.pointContainment(point(reference_x,reference_y,x,y,pz))!=inside:
                raise RuntimeError('Missing holder retaining land at '+str((x,y)))
    for side in (-1,1):
        for z in (.5,1.6,2.5):
            if coupon.pointContainment(point(reference_x,reference_y,side*4.8,0,z))!=inside:
                raise RuntimeError('Guide was damaged')
    clearances=[]
    for wy,wz in ((-2.500016,1.138835),(-5.099996,1.172852),(-3.011004,4.093049)):
        gap=math.hypot(py-wy,pz-wz)-.6-.75
        if gap<.5:raise RuntimeError('Pin / X wire web too thin')
        clearances.append(gap)
    y_wire_gap=abs(4.093049-pz)-.6-.75
    if y_wire_gap<.5:raise RuntimeError('Pin / Y wire web too thin')
    if py-.6-2<.15:raise RuntimeError('Central post clearance too small')
    results=[]
    all_positions=[('Compact','compactV4TrialX','keyRowOne',coupon,True)]
    all_positions += [(label,x,y,carrier,False) for label,x,y in m.locations()]
    main=[r.bRepBodies.itemByName(n) for n in ('UpperShell_Draft','MiddleCarrier_Draft','BottomCover_Draft','Diffuser_Draft')]
    inp=d.createInterferenceInput(adsk.core.ObjectCollection.createWithArray(main));inp.areCoincidentFacesIncluded=False
    if d.analyzeInterference(inp).count:raise RuntimeError('Static enclosure interference')
    for label,xexpr,yexpr,body,is_coupon in all_positions:
        cx,cy=ev(xexpr),ev(yexpr);samples=0
        participants=(body,holder) if is_coupon else (body,)
        for x in [i*.2 for i in range(-50,51)]:
            for radius in (0,.49,.58):
                for degree in range(0,360,45):
                    t=math.radians(degree);p=point(cx,cy,x,py+radius*math.cos(t),pz+radius*math.sin(t))
                    if any(b.pointContainment(p)==inside for b in participants):raise RuntimeError(label+' through path blocked')
                    samples+=1
        # Both opposite walls must support the pin with material around the bore.
        for x in (-8.5,8.5):
            for y in (py-1,py+1):
                if body.pointContainment(point(cx,cy,x,y,pz))!=inside:raise RuntimeError(label+' wall engagement missing')
        if not is_coupon:
            dx,dy=cx-reference_x,cy-reference_y
            placed_holder=translated(holder,dx,c*dy,s*dy);placed_pin=translated(pin,dx,c*dy,s*dy)
            for other in main:
                overlap(placed_holder,other,label+' holder / '+other.name)
                overlap(placed_pin,other,label+' pin / '+other.name)
        else:
            overlap(holder,coupon,'coupon holder');overlap(pin,coupon,'coupon pin');overlap(pin,holder,'holder pin')
        results.append({'position':label,'full_bore_samples':samples,'both_wall_engagement':True})
    unconstrained=[sk.name for sk in r.sketches if not sk.isFullyConstrained]
    if unconstrained:raise RuntimeError('Unconstrained '+str(unconstrained))
    exporter=d.exportManager
    for body,base in ((carrier,'middle_carrier_through_pin_v5'),(coupon,'switch_fit_coupon_through_pin_v5'),(holder,'hotswap_mx_through_pin_v5')):
        for b in r.bRepBodies:b.isVisible=b==body
        for mesh in r.meshBodies:mesh.isLightBulbOn=False
        if not exporter.execute(exporter.createSTEPExportOptions(str(EXPORT/(base+'.step')))):raise RuntimeError('STEP failed')
        opt=exporter.createSTLExportOptions(body,str(EXPORT/(base+'_native.stl')));opt.unitType=adsk.fusion.DistanceUnits.MillimeterDistanceUnits
        opt.isBinaryFormat=True;opt.meshRefinement=adsk.fusion.MeshRefinementSettings.MeshRefinementHigh
        if not exporter.execute(opt):raise RuntimeError('STL failed')
    for b in r.bRepBodies:b.isVisible=b in (coupon,holder,pin)
    # Opaque holder and smooth shading are preferable to transparent faceted edges.
    holder.opacity=1
    app.activeViewport.visualStyle=adsk.core.VisualStyles.ShadedVisualStyle
    box=coupon.boundingBox;target=adsk.core.Point3D.create((box.minPoint.x+box.maxPoint.x)/2,(box.minPoint.y+box.maxPoint.y)/2,(box.minPoint.z+box.maxPoint.z)/2)
    camera=app.activeViewport.camera;camera.target=target;camera.eye=adsk.core.Point3D.create(target.x-4,target.y+4,target.z-3)
    camera.upVector=adsk.core.Vector3D.create(0,0,1);camera.isFitView=True;app.activeViewport.camera=camera;app.activeViewport.refresh()
    if not app.activeViewport.saveAsImageFile(str(EXPORT/'through-pin-v5-assembled.png'),1400,1050):raise RuntimeError('PNG failed')
    coupon.isVisible=False
    app.activeViewport.fit();app.activeViewport.refresh()
    if not app.activeViewport.saveAsImageFile(str(EXPORT/'through-pin-v5-holder.png'),1400,1050):raise RuntimeError('Holder PNG failed')
    for b in r.bRepBodies:b.isVisible=b in main
    app.activeViewport.fit()
    if not exporter.execute(exporter.createFusionArchiveExportOptions(str(EXPORT/'macropad_through_pin_v5.f3d'))):raise RuntimeError('Archive failed')
    report={'revision':'V5 through pin','axis':'local X','axis_y_z_mm':[py,pz],'pin_diameter_mm':1,'bore_diameter_mm':1.2,
            'pin_straight_length_mm':20,'both_wall_span_mm':18.4,'external_length_each_side_mm':.8,'positions':results,
            'assumed_central_post_radius_mm':2,'assumed_central_post_bore_gap_mm':py-.6-2,'guide_bore_gap_mm':py-.6-.75,
            'electrical_x_wire_bore_gaps_mm':clearances,'electrical_y_wire_bore_gap_mm':y_wire_gap,
            'healthy_timeline':True,'unconstrained_sketches':unconstrained,
            'volumes_mm3':{b.name:b.volume*1000 for b in (carrier,coupon,holder)},
            'limits':'V5 requires new physical fit trial; full pin withdrawal and complete assembly removal remain unverified; lid supports unchanged; USB opening pending'}
    (EXPORT/'through-pin-v5-validation.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
