"""Migrate six integrated carrier receivers to the physically tested compact V4.

Preserve plate, OLED recut, main holder parameters and untested bottom supports.
The shared compact insert remains Hotswap_MX_Compact_Pin_V4.stl (six copies).
Channel centers are constrained at the current evaluated assembly pose. Regenerate
the channel sketches after changing key layout, tilt or holder depth.
"""
import importlib.util
import json
import math
import re
from pathlib import Path
import adsk.core
import adsk.fusion

HERE=Path('/Users/denisbabiichuk/3dPrint/macropad/cad/fusion')
EXPORT=HERE/'exports'


def helpers():
    spec=importlib.util.spec_from_file_location('carrier_coupon_helpers',HERE/'macropad_switch_coupon.py')
    h=importlib.util.module_from_spec(spec);spec.loader.exec_module(h)
    original_rectangle=h.rectangle
    def rectangle(d,r,plane,name,left,bottom,width,height):
        if not plane.name.startswith("Carrier V4"):
            return original_rectangle(d,r,plane,name,left,bottom,width,height)
        bottom=f'({bottom})+faceOriginV'
        sketch=r.sketches.add(plane);sketch.name=name
        sketch.isComputeDeferred=True
        try:
            coords=[h.point(h.evaluate(d,x),h.evaluate(d,y)) for x,y in
                    ((left,bottom),(f'({left})+({width})',bottom),
                     (f'({left})+({width})',f'({bottom})+({height})'),(left,f'({bottom})+({height})'))]
            lines=sketch.sketchCurves.sketchLines
            first=lines.addByTwoPoints(coords[0],coords[1]);last=first.endSketchPoint
            for coord in coords[2:]:last=lines.addByTwoPoints(last,coord).endSketchPoint
            lines.addByTwoPoints(last,first.startSketchPoint)
            edges=list(lines)
            for i,edge in enumerate(edges):
                if i%2:sketch.geometricConstraints.addVertical(edge)
                else:sketch.geometricConstraints.addHorizontal(edge)
            h.constrain_point(sketch,first.startSketchPoint,left,bottom)
            for edge,expr in zip(edges[:2],(width,height)):
                dim=sketch.sketchDimensions.addDistanceDimension(edge.startSketchPoint,edge.endSketchPoint,
                    adsk.fusion.DimensionOrientations.AlignedDimensionOrientation,h.point(coords[0].x+.4,coords[0].y+.4))
                dim.parameter.expression=expr
        finally:sketch.isComputeDeferred=False
        if sketch.profiles.count!=1:raise RuntimeError('Expected one rectangle profile')
        return sketch
    def xy_circle(d,r,plane,name,cx,cy,diameter):
        sketch=r.sketches.add(plane);sketch.name=name;sketch.isComputeDeferred=True
        try:
            x,y=h.evaluate(d,cx),h.evaluate(d,cy)
            circle=sketch.sketchCurves.sketchCircles.addByCenterRadius(h.point(x,y),h.evaluate(d,diameter)/2)
            h.constrain_point(sketch,circle.centerSketchPoint,cx,cy)
            sketch.sketchDimensions.addDiameterDimension(circle,h.point(x+.3,y+.3)).parameter.expression=diameter
        finally:sketch.isComputeDeferred=False
        return sketch
    h.rectangle=rectangle;h.xy_circle=xy_circle
    return h


def locations():
    return [(f'SW{row*3+col+1}',f'layoutGap+keycapSize/2+{col}*keyPitch',cy)
            for row,cy in enumerate(('keyRowOne','keyRowTwo')) for col in range(3)]


def tilted_y(h,d,r):
    angle=d.unitsManager.evaluateExpression('caseTilt','rad')
    c,s=math.cos(angle),math.sin(angle)
    for expression in ('caseTilt','-caseTilt'):
        inp=r.constructionPlanes.createInput()
        inp.setByAngle(r.xConstructionAxis,h.value(expression),r.xZConstructionPlane)
        plane=r.constructionPlanes.add(inp);plane.name='Carrier V4 Y channel angle datum'
        plane.isLightBulbOn=False
        normal=plane.geometry.normal;sign=1 if normal.y>0 else -1
        if abs(normal.y-sign*c)<1e-6 and abs(normal.z-sign*s)<1e-6:
            return plane,sign
    raise RuntimeError('Cannot establish inclined Y channel direction')


def channel_circle(h,d,r,plane,name,cx,cy,x,y,z,diameter):
    angle=d.unitsManager.evaluateExpression('caseTilt','rad');c,s=math.cos(angle),math.sin(angle)
    centerx=h.evaluate(d,cx)+x/10;centery=h.evaluate(d,cy)+y/10
    localz=z/10-h.evaluate(d,'carrierV4BottomDepth')
    world=h.point(centerx,c*centery-s*localz,h.evaluate(d,'frontHeight')+s*centery+c*localz)
    # Keep projection-based circles synchronous, matching the tested coupon.
    sketch=r.sketches.add(plane);sketch.name=name+' profile'
    p=sketch.modelToSketchSpace(world)
    circle=sketch.sketchCurves.sketchCircles.addByCenterRadius(p,h.evaluate(d,diameter)/2)
    h.constrain_point(sketch,circle.centerSketchPoint,f'{p.x} cm',f'{p.y} cm')
    sketch.sketchDimensions.addDiameterDimension(circle,h.point(p.x+.3,p.y+.3)).parameter.expression=diameter

    return sketch


def add_receiver_details(h,d,r,body,label,cx,cy,hook,yplane,sign):
    # Make the cut participant visible before creating the new features.
    body.isVisible=True
    join=adsk.fusion.FeatureOperations.JoinFeatureOperation;cut=adsk.fusion.FeatureOperations.CutFeatureOperation
    for side in (-1,1):
        x=f'({cx})-holderFrameX/2' if side==-1 else f'({cx})+4.8 mm'
        sketch=h.rectangle(d,r,hook,label+f' V4 guide web {side}',x,f'({cy})-0.35 mm','holderFrameX/2-4.8 mm','0.7 mm')
        h.extrude(r,sketch,label+f' V4 guide web {side}','carrierV4GuideHeight',join,True,body)
        sketch=h.inclined_circle(d,r,hook,label+f' V4 rounded guide {side}',f'({cx})+({side}*4.8 mm)',cy,'2*(0.95 mm-carrierV4GuideClearance)')
        h.extrude(r,sketch,label+f' V4 rounded guide {side}','carrierV4GuideHeight',join,True,body)
    plane=h.offset(r,r.yZConstructionPlane,label+' V4 X wire entry datum',f'({cx})-10 mm')
    for index,(y,z) in enumerate(((-2.500016,1.138835),(-5.099996,1.172852),(-3.011004,4.093049)),1):
        sketch=channel_circle(h,d,r,plane,label+f' V4 X wire {index}',cx,cy,-10,y,z,'carrierV4WireDiameter')
        h.extrude(r,sketch,label+f' V4 X wire {index}','20 mm',cut,True,body)
    plane=h.offset(r,yplane,label+' V4 Y wire entry datum',f'{sign}*(({cy})+10 mm+frontHeight*sin(caseTilt))')
    sketch=channel_circle(h,d,r,plane,label+' V4 Y wire',cx,cy,4.190238,10,4.093049,'carrierV4WireDiameter')
    h.extrude(r,sketch,label+' V4 Y wire','20 mm',cut,sign<0,body)
    sketch=channel_circle(h,d,r,plane,label+' V4 retaining pin',cx,cy,4.3,10,1.6,'carrierV4PinBore')
    h.extrude(r,sketch,label+' V4 single retaining pin','10 mm-carrierV4PinEnd',cut,sign<0,body)


def run(context):
    app=adsk.core.Application.get();d=adsk.fusion.Design.cast(app.activeProduct)
    if d is None or app.activeDocument.name!='macropad':raise RuntimeError('Activate macropad')
    r=d.rootComponent;h=helpers()
    if d.userParameters.itemByName('carrierV4BottomDepth'):raise RuntimeError('Carrier V4 already applied')
    body=r.bRepBodies.itemByName('MiddleCarrier_Draft')
    if body is None:raise RuntimeError('Missing carrier')
    original={b.name:b.volume*1000 for b in r.bRepBodies if b.name!='MiddleCarrier_Draft'}
    backup=EXPORT/'macropad_before_carrier_v4.f3d'
    if not backup.exists() and not d.exportManager.execute(d.exportManager.createFusionArchiveExportOptions(str(backup))):
        raise RuntimeError('Backup failed')
    params=(('carrierV4TopDepth','compactV4TopDepth'),('carrierV4BottomDepth','carrierV4TopDepth+holderHeight'),
            ('carrierV4GuideHeight','compactV4GuideHeight'),('carrierV4GuideClearance','compactV4GuideClearance'),
            ('carrierV4PinBore','compactV4PinBore'),('carrierV4PinEnd','compactV4PinEnd'),
            ('carrierV4WireDiameter','compactV4WireDiameter'))
    for name,expr in params:d.userParameters.add(name,h.value(expr),'mm','Main carrier uses physically tested V4 geometry')
    obsolete=[t.entity for t in d.timeline if re.match(r'^SW[1-6] (open-bottom holder pocket|spring |upper stop |wire exit )',t.name)
              and t.entity.objectType in ('adsk::fusion::ExtrudeFeature','adsk::fusion::ChamferFeature')]
    if len(obsolete)!=90:raise RuntimeError('Expected 90 old receiver features, got '+str(len(obsolete)))
    for feature in reversed(obsolete):feature.isSuppressed=True
    for label,cx,cy in locations():
        outer=r.features.extrudeFeatures.itemByName(label+' integrated receiver')
        inner=r.features.extrudeFeatures.itemByName(label+' switch lower clearance')
        if outer is None or inner is None:raise RuntimeError('Missing '+label)
        outer.extentOne.distance.expression='-(carrierV4BottomDepth-shellWall-carrierClearance-carrierThickness)'
        inner.extentOne.distance.expression='-(carrierV4BottomDepth-shellWall-carrierClearance-carrierThickness+0.1 mm)'
    d.computeAll()
    hook=h.offset(r,r.constructionPlanes.itemByName('Exterior face datum'),'Carrier V4 hook datum','-carrierV4BottomDepth')
    plane,sign=tilted_y(h,d,r)
    for label,cx,cy in locations():add_receiver_details(h,d,r,body,label,cx,cy,hook,plane,sign)
    d.computeAll()
    errors=[t.name for t in d.timeline if not getattr(t.entity,'isSuppressed',False)
            and t.healthState!=adsk.fusion.FeatureHealthStates.HealthyFeatureHealthState]
    unconstrained=[s.name for s in r.sketches if not s.isFullyConstrained]
    if errors or unconstrained or not body.isSolid or body.volume<=0:raise RuntimeError(str({'features':errors,'sketches':unconstrained}))
    for name,volume in original.items():
        current=r.bRepBodies.itemByName(name)
        if current is None or abs(current.volume*1000-volume)>1e-5:raise RuntimeError('Unexpected change to '+name)
    for b in r.bRepBodies:b.isVisible=b==body
    for sk in r.sketches:sk.isVisible=False
    for p in r.constructionPlanes:p.isLightBulbOn=False
    for mesh in r.meshBodies:mesh.isLightBulbOn=False
    app.activeViewport.fit()
    report={'revision':'Main carrier compact V4','receivers':6,'pins_per_holder':1,'suppressed_legacy_features':len(obsolete),
            'holder_depths_mm':[h.evaluate(d,'carrierV4TopDepth')*10,h.evaluate(d,'carrierV4BottomDepth')*10],
            'carrier_volume_mm3':body.volume*1000,'other_bodies_unchanged':True,'healthy_timeline':True,
            'bottom_supports':'Unchanged, still need height update and physical test','backup':str(backup)}
    (EXPORT/'carrier-v4-migration.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report))
