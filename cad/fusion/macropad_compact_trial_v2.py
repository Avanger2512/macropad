"""Add a compact-STL reference and a separate rigid fit coupon; preserve V1."""
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
    cx = h.evaluate(d, 'compactTrialX')
    cy = h.evaluate(d, 'keyRowOne')
    angle = d.unitsManager.evaluateExpression('caseTilt', 'rad')
    c, s = math.cos(angle), math.sin(angle)
    front = h.evaluate(d, 'frontHeight')
    bottom = h.evaluate(d, 'holderBottomDepth')
    def center(x, y, z):
        return h.point(cx+x, c*(cy+y)-s*(z-bottom), front+s*(cy+y)+c*(z-bottom))
    plane_x = h.offset(r,r.yZConstructionPlane,'Compact V2 X wire entry datum','compactTrialX-10 mm')
    for index, (y,z) in enumerate(((-2.500016,1.138835),(-5.099996,1.172852),(-3.011004,4.093049)),1):
        sketch = r.sketches.add(plane_x)
        sketch.name = f'Compact V2 X wire {index} profile'
        p = sketch.modelToSketchSpace(center(-1,y/10,z/10))
        circle = sketch.sketchCurves.sketchCircles.addByCenterRadius(p,h.evaluate(d,'compactWireDiameter')/2)
        h.constrain_point(sketch,circle.centerSketchPoint,f'{p.x} cm',f'{p.y} cm')
        sketch.sketchDimensions.addDiameterDimension(circle,h.point(p.x+0.3,p.y+0.3)).parameter.expression='compactWireDiameter'
        h.extrude(r,sketch,f'Compact V2 X wire {index} through channel','20 mm',adsk.fusion.FeatureOperations.CutFeatureOperation,True,body)
    inp=r.constructionPlanes.createInput()
    inp.setByAngle(r.xConstructionAxis,h.value('caseTilt'),r.xZConstructionPlane)
    tilted=r.constructionPlanes.add(inp)
    tilted.name='Compact V2 Y wire angle datum'
    tilted.isLightBulbOn=False
    normal=tilted.geometry.normal
    sign=1 if normal.y>0 else -1
    if abs(normal.y-sign*c)>1e-6 or abs(normal.z-sign*s)>1e-6:
        inp=r.constructionPlanes.createInput()
        inp.setByAngle(r.xConstructionAxis,h.value('-caseTilt'),r.xZConstructionPlane)
        tilted=r.constructionPlanes.add(inp)
        tilted.name='Compact V2 Y wire corrected angle datum'
        tilted.isLightBulbOn=False
        normal=tilted.geometry.normal
        sign=1 if normal.y>0 else -1
    if abs(normal.y-sign*c)>1e-6 or abs(normal.z-sign*s)>1e-6:
        raise RuntimeError('Unexpected wire plane orientation '+str(normal.asArray()))
    plane_y=h.offset(r,tilted,'Compact V2 Y wire entry datum',f'{sign}*(keyRowOne+10 mm+frontHeight*sin(caseTilt))')
    sketch=r.sketches.add(plane_y)
    sketch.name='Compact V2 Y wire profile'
    p=sketch.modelToSketchSpace(center(4.190238/10,1,4.093049/10))
    circle=sketch.sketchCurves.sketchCircles.addByCenterRadius(p,h.evaluate(d,'compactWireDiameter')/2)
    h.constrain_point(sketch,circle.centerSketchPoint,f'{p.x} cm',f'{p.y} cm')
    sketch.sketchDimensions.addDiameterDimension(circle,h.point(p.x+0.3,p.y+0.3)).parameter.expression='compactWireDiameter'
    h.extrude(r,sketch,'Compact V2 Y wire through channel','20 mm',adsk.fusion.FeatureOperations.CutFeatureOperation,sign<0,body)


def run(context):
    h = helpers()
    app = adsk.core.Application.get()
    d = adsk.fusion.Design.cast(app.activeProduct)
    if d is None or app.activeDocument.name != 'macropad':
        raise RuntimeError('Activate the existing macropad document')
    r = d.rootComponent
    if r.bRepBodies.itemByName('SwitchFitCoupon_Compact_V2'):
        raise RuntimeError('Compact V2 already exists; do not rerun')
    EXPORT.mkdir(exist_ok=True)
    backup = EXPORT / 'macropad_before_compact_v2.f3d'
    if not backup.exists() and not d.exportManager.execute(d.exportManager.createFusionArchiveExportOptions(str(backup))):
        raise RuntimeError('Backup export failed')
    for name, expression, comment in (
        ('compactTrialX', '145 mm', 'Separate V2 coupon center'),
        ('compactGuideClearance', '0.2 mm', 'Radial clearance in STL 0.95 mm side notches'),
        ('compactGuideHeight', '3 mm', 'Guide within 3.2 mm notched region'),
        ('compactStopWidth', '1.8 mm', 'Wider upper stops for physical test'),
        ('compactWireDiameter', '1.5 mm', 'Provisional through-wall wire routing diameter'),
    ):
        d.userParameters.add(name, h.value(expression), 'mm', comment)
    cx, cy = 'compactTrialX', 'keyRowOne'
    join = adsk.fusion.FeatureOperations.JoinFeatureOperation
    cut = adsk.fusion.FeatureOperations.CutFeatureOperation
    new = adsk.fusion.FeatureOperations.NewBodyFeatureOperation
    face = r.constructionPlanes.itemByName('Carrier seating datum')
    frame = r.constructionPlanes.itemByName('Holder frame datum')
    upper = r.constructionPlanes.itemByName('Holder upper datum')
    hook = r.constructionPlanes.itemByName('Holder hook datum')
    sketch = h.rectangle(d,r,face,'Compact V2 plate profile',f'{cx}-11 mm',f'{cy}-11 mm','22 mm','22 mm')
    body = h.extrude(r,sketch,'Compact V2 plate','carrierThickness',new,False).bodies.item(0)
    body.name = 'SwitchFitCoupon_Compact_V2'
    sketch = h.rectangle(d,r,face,'Compact V2 switch seat profile',f'{cx}-switchOpening/2',f'{cy}-switchOpening/2','switchOpening','switchOpening')
    h.extrude(r,sketch,'Compact V2 switch seat','carrierThickness+0.1 mm',cut,False,body)
    sketch = h.rectangle(d,r,frame,'Compact V2 rigid receiver profile',f'{cx}-holderFrameX/2',f'{cy}-holderFrameY/2','holderFrameX','holderFrameY')
    h.extrude(r,sketch,'Compact V2 continuous receiver','holderBottomDepth-shellWall-carrierClearance-carrierThickness',join,False,body)
    sketch = h.rectangle(d,r,frame,'Compact V2 switch body profile',f'{cx}-holderSwitchVoid/2',f'{cy}-holderSwitchVoid/2','holderSwitchVoid','holderSwitchVoid')
    h.extrude(r,sketch,'Compact V2 switch clearance','holderTopDepth-shellWall-carrierClearance-carrierThickness',cut,False,body)
    sketch = h.rectangle(d,r,upper,'Compact V2 registered pocket profile',f'{cx}-5.42601681 mm-holderFit',f'{cy}-6.37220383 mm-holderFit','11.03147984 mm+2*holderFit','9.74910235 mm+2*holderFit')
    h.extrude(r,sketch,'Compact V2 open-bottom pocket','holderHeight+0.1 mm',cut,False,body)
    for side in (-1,1):
        x = f'{cx}+({side}*3 mm)-compactStopWidth/2'
        sketch = h.rectangle(d,r,upper,f'Compact V2 stop {side} profile',x,f'{cy}+2.6 mm','compactStopWidth','holderFrameY/2-2.6 mm')
        h.extrude(r,sketch,f'Compact V2 widened stop {side}','0.8 mm',join,True,body)
        x = f'{cx}-holderFrameX/2' if side == -1 else f'{cx}+4.8 mm'
        width = 'holderFrameX/2-4.8 mm'
        sketch = h.rectangle(d,r,hook,f'Compact V2 guide web {side} profile',x,f'{cy}-0.35 mm',width,'0.7 mm')
        h.extrude(r,sketch,f'Compact V2 guide web {side}','compactGuideHeight',join,True,body)
        sketch = h.inclined_circle(d,r,hook,f'Compact V2 rounded guide {side} profile',f'{cx}+({side}*4.8 mm)',cy,'2*(0.95 mm-compactGuideClearance)')
        h.extrude(r,sketch,f'Compact V2 rounded guide {side}','compactGuideHeight',join,True,body)
    wire_channels(h,d,r,body)
    d.computeAll()
    errors = [t.name for t in d.timeline if t.healthState != adsk.fusion.FeatureHealthStates.HealthyFeatureHealthState]
    if errors or not body.isSolid or body.volume <= 0:
        raise RuntimeError('Invalid V2 geometry: '+str(errors))
    angle = d.unitsManager.evaluateExpression('caseTilt','rad')
    mesh_path = EXPORT / 'compact_reference_aligned_v2.stl'
    aligned_mesh(mesh_path,h.evaluate(d,cx)*10,h.evaluate(d,cy)*10,
                 h.evaluate(d,'holderBottomDepth')*10,h.evaluate(d,'frontHeight')*10,angle)
    base = r.features.baseFeatures.add()
    base.name = 'Compact STL reference import V2'
    base.startEdit()
    try:
        imported = r.meshBodies.add(str(mesh_path),adsk.fusion.MeshUnits.MillimeterMeshUnit,base)
        if imported is None or imported.count != 1:
            raise RuntimeError('Compact reference import failed')
        imported.item(0).name = 'hotswap_mx__compact_REFERENCE_V2'
    finally:
        base.finishEdit()
    for b in r.bRepBodies:
        b.isVisible = b.name == body.name
    for sk in r.sketches:
        sk.isVisible = False
    for p in r.constructionPlanes:
        p.isLightBulbOn = False
    app.activeViewport.fit()
    print(json.dumps({'body':body.name,'volume_mm3':body.volume*1000,'reference_meshes':r.meshBodies.count,'backup':str(backup),'wire_channels':4}))
