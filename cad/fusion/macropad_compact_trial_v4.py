"""Add a compact-STL reference and a separate rigid fit coupon; preserve earlier trials and the main carrier."""
import importlib.util
import json
import math
import struct
from pathlib import Path
import adsk.core
import adsk.fusion

HERE = Path('/Users/denisbabiichuk/3dPrint/macropad/cad/fusion')
SOURCE = HERE.parent / 'hotswap_mx__compact.stl'
EXPORT = HERE / 'exports'


def helpers():
    spec = importlib.util.spec_from_file_location('coupon_helpers', HERE / 'macropad_switch_coupon.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    rectangle_original = module.rectangle
    extrude_original = module.extrude
    def resolve(expression):
        return expression.replace('holderBottomDepth','compactV4BottomDepth').replace('holderTopDepth','compactV4TopDepth')
    def rectangle(design,root,plane,name,left,bottom,width,height):
        if plane.name.startswith('Compact V4') and any(word in plane.name for word in ('upper datum','hook datum','lid support datum')):
            bottom=f'({bottom})+faceOriginV'
        return rectangle_original(design,root,plane,name,resolve(left),resolve(bottom),resolve(width),resolve(height))
    def extrude(root,sketch,name,distance,operation,positive=True,body=None):
        return extrude_original(root,sketch,name,resolve(distance),operation,positive,body)
    module.rectangle=rectangle
    module.extrude=extrude
    return module


def aligned_mesh(path, cx, cy, bottom_depth, front_height, tilt):
    data = SOURCE.read_bytes()
    count = struct.unpack_from('<I', data, 80)[0]
    if len(data) != 84 + count * 50:
        raise ValueError('Invalid binary STL')
    c, s = math.cos(tilt), math.sin(tilt)
    out = bytearray(data[:84])
    for i in range(count):
        values = struct.unpack_from('<12fH', data, 84 + i * 50)
        nx, ny, nz = values[:3]
        result = [nx, c * ny - s * nz, s * ny + c * nz]
        for j in (3, 6, 9):
            x, y, z = values[j:j + 3]
            result.extend((cx + x, c * (cy + y) - s * (z - bottom_depth),
                           front_height + s * (cy + y) + c * (z - bottom_depth)))
        out.extend(struct.pack('<12fH', *result, values[-1]))
    path.write_bytes(out)


def wire_channels(h, d, r, body):
    cx = h.evaluate(d, 'compactV4TrialX')
    cy = h.evaluate(d, 'keyRowOne')
    angle = d.unitsManager.evaluateExpression('caseTilt', 'rad')
    c, s = math.cos(angle), math.sin(angle)
    front = h.evaluate(d, 'frontHeight')
    bottom = h.evaluate(d, 'compactV4BottomDepth')
    def center(x, y, z):
        return h.point(cx+x, c*(cy+y)-s*(z-bottom), front+s*(cy+y)+c*(z-bottom))
    plane_x = h.offset(r,r.yZConstructionPlane,'Compact V4 X wire entry datum','compactV4TrialX-10 mm')
    for index, (y,z) in enumerate(((-2.500016,1.138835),(-5.099996,1.172852),(-3.011004,4.093049)),1):
        sketch = r.sketches.add(plane_x)
        sketch.name = f'Compact V4 X wire {index} profile'
        p = sketch.modelToSketchSpace(center(-1,y/10,z/10))
        circle = sketch.sketchCurves.sketchCircles.addByCenterRadius(p,h.evaluate(d,'compactV4WireDiameter')/2)
        h.constrain_point(sketch,circle.centerSketchPoint,f'{p.x} cm',f'{p.y} cm')
        sketch.sketchDimensions.addDiameterDimension(circle,h.point(p.x+0.3,p.y+0.3)).parameter.expression='compactV4WireDiameter'
        h.extrude(r,sketch,f'Compact V4 X wire {index} through channel','20 mm',adsk.fusion.FeatureOperations.CutFeatureOperation,True,body)
    inp=r.constructionPlanes.createInput()
    inp.setByAngle(r.xConstructionAxis,h.value('caseTilt'),r.xZConstructionPlane)
    tilted=r.constructionPlanes.add(inp)
    tilted.name='Compact V4 Y wire angle datum'
    tilted.isLightBulbOn=False
    normal=tilted.geometry.normal
    sign=1 if normal.y>0 else -1
    if abs(normal.y-sign*c)>1e-6 or abs(normal.z-sign*s)>1e-6:
        inp=r.constructionPlanes.createInput()
        inp.setByAngle(r.xConstructionAxis,h.value('-caseTilt'),r.xZConstructionPlane)
        tilted=r.constructionPlanes.add(inp)
        tilted.name='Compact V4 Y wire corrected angle datum'
        tilted.isLightBulbOn=False
        normal=tilted.geometry.normal
        sign=1 if normal.y>0 else -1
    if abs(normal.y-sign*c)>1e-6 or abs(normal.z-sign*s)>1e-6:
        raise RuntimeError('Unexpected wire plane orientation '+str(normal.asArray()))
    plane_y=h.offset(r,tilted,'Compact V4 Y wire entry datum',f'{sign}*(keyRowOne+10 mm+frontHeight*sin(caseTilt))')
    sketch=r.sketches.add(plane_y)
    sketch.name='Compact V4 Y wire profile'
    p=sketch.modelToSketchSpace(center(4.190238/10,1,4.093049/10))
    circle=sketch.sketchCurves.sketchCircles.addByCenterRadius(p,h.evaluate(d,'compactV4WireDiameter')/2)
    h.constrain_point(sketch,circle.centerSketchPoint,f'{p.x} cm',f'{p.y} cm')
    sketch.sketchDimensions.addDiameterDimension(circle,h.point(p.x+0.3,p.y+0.3)).parameter.expression='compactV4WireDiameter'
    h.extrude(r,sketch,'Compact V4 Y wire through channel','20 mm',adsk.fusion.FeatureOperations.CutFeatureOperation,sign<0,body)


def retaining_pins(h,d,r,receiver,hotswap):
    cy=h.evaluate(d,'keyRowOne');cx=h.evaluate(d,'compactV4TrialX')
    bottom=h.evaluate(d,'compactV4BottomDepth');front=h.evaluate(d,'frontHeight')
    angle=d.unitsManager.evaluateExpression('caseTilt','rad');c,s=math.cos(angle),math.sin(angle)
    tilted=r.constructionPlanes.itemByName('Compact V4 Y wire corrected angle datum') or r.constructionPlanes.itemByName('Compact V4 Y wire angle datum')
    if tilted is None:raise RuntimeError('Missing inclined Y datum')
    normal=tilted.geometry.normal;sign=1 if normal.y>0 else -1
    if abs(normal.y-sign*c)>1e-6 or abs(normal.z-sign*s)>1e-6:raise RuntimeError('Incorrect Y datum')
    def circle(plane,name,diameter,local_y):
        sketch=r.sketches.add(plane);sketch.name=name+' profile'
        z=1.6/10-bottom
        world=h.point(cx+4.3/10,c*(cy+local_y)-s*z,front+s*(cy+local_y)+c*z)
        p=sketch.modelToSketchSpace(world)
        curve=sketch.sketchCurves.sketchCircles.addByCenterRadius(p,h.evaluate(d,diameter)/2)
        h.constrain_point(sketch,curve.centerSketchPoint,f'{p.x} cm',f'{p.y} cm')
        sketch.sketchDimensions.addDiameterDimension(curve,h.point(p.x+.3,p.y+.3)).parameter.expression=diameter
        return sketch
    plane=h.offset(r,tilted,'Compact V4 single pin entry datum',f'{sign}*(keyRowOne+10 mm+frontHeight*sin(caseTilt))')
    sketch=circle(plane,'Compact V4 single retaining pin','compactV4PinBore',1)
    for solid,label in ((receiver,'receiver'),(hotswap,'hotswap')):
        h.extrude(r,sketch,'Compact V4 single pin '+label+' bore','10 mm-compactV4PinEnd',adsk.fusion.FeatureOperations.CutFeatureOperation,sign<0,solid)
    tip=h.evaluate(d,'compactV4PinEnd+0.1 mm')
    plane=h.offset(r,tilted,'Compact V4 single pin reference datum',f'{sign}*(keyRowOne+compactV4PinEnd+0.1 mm+frontHeight*sin(caseTilt))')
    sketch=circle(plane,'Compact V4 single pin reference','compactV4PinDiameter',tip)
    pin=h.extrude(r,sketch,'Compact V4 single pin reference','compactV4PinLength',adsk.fusion.FeatureOperations.NewBodyFeatureOperation,sign>0).bodies.item(0)
    pin.name='MechanicalPin_1mm_REFERENCE_SINGLE'
    return [pin]


def run(context):
    h = helpers()
    app = adsk.core.Application.get()
    d = adsk.fusion.Design.cast(app.activeProduct)
    if d is None or app.activeDocument.name != 'macropad':
        raise RuntimeError('Activate the existing macropad document')
    r = d.rootComponent
    if r.bRepBodies.itemByName('SwitchFitCoupon_Compact_V4'):
        raise RuntimeError('Compact V4 already exists; do not rerun')
    EXPORT.mkdir(exist_ok=True)
    backup = EXPORT / 'macropad_before_compact_v4.f3d'
    if not backup.exists() and not d.exportManager.execute(d.exportManager.createFusionArchiveExportOptions(str(backup))):
        raise RuntimeError('Backup export failed')
    for name, expression, comment in (
        ('compactV4TrialX', '205 mm', 'Separate V4 coupon center'),
        ('compactV4Shift', '3 mm', 'Move holder toward switch based on pin-tip measurement'),
        ('compactV4TopDepth', '6.8 mm', 'Local trial depth; preserve main carrier'),
        ('compactV4BottomDepth', 'compactV4TopDepth+holderHeight', 'New holder bottom datum'),
        ('compactV4GuideClearance', '0.2 mm', 'Radial clearance in STL 0.95 mm side notches'),
        ('compactV4GuideHeight', '3 mm', 'Guide within 3.2 mm notched region'),
        ('compactV4PinBore', '1.2 mm', 'Mechanical pin clearance diameter'),
        ('compactV4PinDiameter', '1 mm', 'Smooth removable mechanical pin'),
        ('compactV4PinEnd', '-0.2 mm', 'Single pin bore blind end in side guide'),
        ('compactV4PinLength', '10 mm', 'Smooth removable single retaining pin length'),
        ('compactV4WireDiameter', '1.5 mm', 'Provisional through-wall wire routing diameter'),
    ):
        d.userParameters.add(name, h.value(expression), 'mm', comment)
    cx, cy = 'compactV4TrialX', 'keyRowOne'
    join = adsk.fusion.FeatureOperations.JoinFeatureOperation
    cut = adsk.fusion.FeatureOperations.CutFeatureOperation
    new = adsk.fusion.FeatureOperations.NewBodyFeatureOperation
    face = r.constructionPlanes.itemByName('Carrier seating datum')
    frame = r.constructionPlanes.itemByName('Holder frame datum')
    exterior=r.constructionPlanes.itemByName('Exterior face datum')
    upper=h.offset(r,exterior,'Compact V4 upper datum','-compactV4TopDepth')
    hook=h.offset(r,exterior,'Compact V4 hook datum','-compactV4BottomDepth')
    sketch = h.rectangle(d,r,face,'Compact V4 plate profile',f'{cx}-11 mm',f'{cy}-11 mm','22 mm','22 mm')
    body = h.extrude(r,sketch,'Compact V4 plate','carrierThickness',new,False).bodies.item(0)
    body.name = 'SwitchFitCoupon_Compact_V4'
    sketch = h.rectangle(d,r,face,'Compact V4 switch seat profile',f'{cx}-switchOpening/2',f'{cy}-switchOpening/2','switchOpening','switchOpening')
    h.extrude(r,sketch,'Compact V4 switch seat','carrierThickness+0.1 mm',cut,False,body)
    sketch = h.rectangle(d,r,frame,'Compact V4 rigid receiver profile',f'{cx}-holderFrameX/2',f'{cy}-holderFrameY/2','holderFrameX','holderFrameY')
    h.extrude(r,sketch,'Compact V4 continuous receiver','compactV4BottomDepth-shellWall-carrierClearance-carrierThickness',join,False,body)
    sketch = h.rectangle(d,r,frame,'Compact V4 switch body profile',f'{cx}-holderSwitchVoid/2',f'{cy}-holderSwitchVoid/2','holderSwitchVoid','holderSwitchVoid')
    h.extrude(r,sketch,'Compact V4 switch clearance','compactV4BottomDepth-shellWall-carrierClearance-carrierThickness+0.1 mm',cut,False,body)
    for side in (-1,1):
        x = f'{cx}-holderFrameX/2' if side == -1 else f'{cx}+4.8 mm'
        width = 'holderFrameX/2-4.8 mm'
        sketch = h.rectangle(d,r,hook,f'Compact V4 guide web {side} profile',x,f'{cy}-0.35 mm',width,'0.7 mm')
        h.extrude(r,sketch,f'Compact V4 guide web {side}','compactV4GuideHeight',join,True,body)
        sketch = h.inclined_circle(d,r,hook,f'Compact V4 rounded guide {side} profile',f'{cx}+({side}*4.8 mm)',cy,'2*(0.95 mm-compactV4GuideClearance)')
        h.extrude(r,sketch,f'Compact V4 rounded guide {side}','compactV4GuideHeight',join,True,body)
    wire_channels(h,d,r,body)
    d.computeAll()
    errors = [t.name for t in d.timeline if t.healthState != adsk.fusion.FeatureHealthStates.HealthyFeatureHealthState]
    if errors or not body.isSolid or body.volume<=0:
        raise RuntimeError('Invalid V4 geometry: '+str(errors))
    angle = d.unitsManager.evaluateExpression('caseTilt','rad')
    mesh_path = EXPORT / 'compact_reference_aligned_v4.stl'
    aligned_mesh(mesh_path,h.evaluate(d,cx)*10,h.evaluate(d,cy)*10,
                 h.evaluate(d,'compactV4BottomDepth')*10,h.evaluate(d,'frontHeight')*10,angle)
    base = r.features.baseFeatures.add()
    base.name = 'Compact STL reference import V4'
    base.startEdit()
    try:
        imported = r.meshBodies.add(str(mesh_path),adsk.fusion.MeshUnits.MillimeterMeshUnit,base)
        if imported is None or imported.count != 1:
            raise RuntimeError('Compact reference import failed')
        imported.item(0).name = 'hotswap_mx__compact_REFERENCE_V4'
    finally:
        base.finishEdit()
    convert=r.features.meshConvertFeatures
    convert_input=convert.createInput([imported.item(0)])
    if convert_input is None:
        raise RuntimeError('This Fusion build cannot convert the compact mesh')
    convert_input.meshConvertMethodType=adsk.fusion.MeshConvertMethodTypes.FacetedMeshConvertMethodType
    converted=convert.add(convert_input)
    if converted is None or converted.bodies.count!=1:
        raise RuntimeError('Faceted compact conversion failed')
    converted.name='Compact V4 source STL to exact faceted solid'
    hotswap=converted.bodies.item(0)
    hotswap.name='HotswapCompact_Pin_V4'
    pins=retaining_pins(h,d,r,body,hotswap)
    d.computeAll()
    errors=[t.name for t in d.timeline if t.healthState!=adsk.fusion.FeatureHealthStates.HealthyFeatureHealthState]
    if errors or any(not b.isSolid or b.volume<=0 for b in (body,hotswap,*pins)):
        raise RuntimeError('Invalid V4 pin assembly '+str(errors))
    inp=d.createInterferenceInput(adsk.core.ObjectCollection.createWithArray([body,hotswap,*pins]))
    inp.areCoincidentFacesIncluded=False
    if d.analyzeInterference(inp).count:
        raise RuntimeError('V4 assembly solids interfere')
    for b in r.bRepBodies:
        b.isVisible = b.name in (body.name,hotswap.name,*[pin.name for pin in pins])
    for sk in r.sketches:
        sk.isVisible = False
    for p in r.constructionPlanes:
        p.isLightBulbOn = False
    for mesh in r.meshBodies:
        mesh.isLightBulbOn=mesh.name=='hotswap_mx__compact_REFERENCE_V4'
    app.activeViewport.fit()
    print(json.dumps({'body':body.name,'volume_mm3':body.volume*1000,'reference_meshes':r.meshBodies.count,'backup':str(backup),'wire_channels':4,'hotswap_body':hotswap.name,'pin_bore_mm':1.2,'pin_count':1,'shift_mm':3}))
