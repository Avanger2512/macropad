"""Incremental finishing of the V5 enclosure; preserve the printed carrier.

Millimeters, original assembly coordinates. USB throat is 14 x 10 mm at
X39/Z15.2. BOOT/RESET centers use the measured component-side board datums.
Run in the existing macropad Fusion document, never an empty design.
"""
import importlib.util
import json
import math
import re
from pathlib import Path

import adsk.core
import adsk.fusion

HERE = Path('/Users/denisbabiichuk/3dPrint/macropad/cad/fusion')
EXPORT = HERE / 'exports'
MAIN = ('UpperShell_Draft', 'MiddleCarrier_Draft', 'BottomCover_Draft', 'Diffuser_Draft')


def context():
    app = adsk.core.Application.get()
    design = adsk.fusion.Design.cast(app.activeProduct)
    if design is None or app.activeDocument.name != 'macropad':
        raise RuntimeError('Activate macropad')
    return app, design, design.rootComponent


def helpers():
    spec = importlib.util.spec_from_file_location('finish_helpers', HERE / 'macropad_switch_coupon.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def healthy(design):
    errors = [t.name for t in design.timeline
              if not getattr(t.entity, 'isSuppressed', False)
              and t.healthState != adsk.fusion.FeatureHealthStates.HealthyFeatureHealthState]
    if errors:
        raise RuntimeError('Unhealthy features: ' + str(errors))


def initialize(_context):
    _, d, r = context()
    if d.userParameters.itemByName('usbAccessWidthV6'):
        raise RuntimeError('V6 already initialized')
    healthy(d)
    backup = EXPORT / 'macropad_before_enclosure_finish_v6.f3d'
    baseline = {b.name: b.volume * 1000 for b in r.bRepBodies}
    baseline_path = EXPORT / 'enclosure-v6-baseline.json'
    if backup.exists():
        saved = json.loads(baseline_path.read_text())
        if saved.keys() != baseline.keys() or any(abs(saved[n] - v) > 1e-5 for n, v in baseline.items()):
            raise RuntimeError('Existing backup differs from current geometry')
    else:
        if not d.exportManager.execute(d.exportManager.createFusionArchiveExportOptions(str(backup))):
            raise RuntimeError('Backup failed')
        baseline_path.write_text(json.dumps(baseline, indent=2) + '\n')
    obsolete = [f for f in r.features.extrudeFeatures if re.fullmatch(
        r'SW[1-6] support [12]( reinforced stem| inclined cap)?', f.name)]
    if len(obsolete) != 36:
        raise RuntimeError('Expected 36 support features, found ' + str(len(obsolete)))
    for feature in reversed(obsolete):
        feature.isSuppressed = True
    d.computeAll()
    healthy(d)
    lid = r.bRepBodies.itemByName('BottomCover_Draft')
    if not lid.isSolid or abs(lid.boundingBox.maxPoint.z - .2) > 1e-6:
        raise RuntimeError('Expected a flat 2 mm cover after support removal')
    h = helpers()
    for name, expression in (('usbAccessWidthV6', '14 mm'), ('usbAccessHeightV6', '10 mm'),
                             ('exteriorChamferV6', '0.8 mm'), ('usbEntryChamferV6', '0.5 mm')):
        d.userParameters.add(name, h.value(expression), 'mm', 'V6 enclosure finishing')
    print(json.dumps({'suppressed_support_features': len(obsolete), 'lid_height_mm': 2}))


def usb(_context):
    _, d, r = context()
    if r.features.extrudeFeatures.itemByName('V6 rear USB access'):
        raise RuntimeError('USB opening already exists')
    h = helpers()
    shell = r.bRepBodies.itemByName('UpperShell_Draft')
    shell.isVisible = True
    # Query actual native orientation: this document's XZ normal points +Y.
    sign = 1 if r.xZConstructionPlane.geometry.normal.y > 0 else -1
    plane = h.offset(r, r.xZConstructionPlane, 'V6 rear USB datum', f'{sign}*(caseLength+1 mm)')
    probe = r.sketches.add(plane)
    origin = probe.modelToSketchSpace(adsk.core.Point3D.create(0, 0, 0))
    px = probe.modelToSketchSpace(adsk.core.Point3D.create(1, 0, 0))
    pz = probe.modelToSketchSpace(adsk.core.Point3D.create(0, 0, 1))
    sx, sz = round(px.x - origin.x), round(pz.y - origin.y)
    if abs(sx) != 1 or abs(sz) != 1:
        raise RuntimeError('Unexpected rear sketch axes')
    probe.deleteMe()
    sketch = h.rectangle(d, r, plane, 'V6 USB access profile',
                         f'{sx}*usbCenterX-usbAccessWidthV6/2', f'{sz}*usbCenterZ-usbAccessHeightV6/2',
                         'usbAccessWidthV6', 'usbAccessHeightV6')
    h.extrude(r, sketch, 'V6 rear USB access', 'shellWall+2 mm',
              adsk.fusion.FeatureOperations.CutFeatureOperation, sign < 0, shell)
    d.computeAll()
    healthy(d)
    print('USB opening created')


def chamfer(r, edges, name, expression, expected):
    if r.features.chamferFeatures.itemByName(name):
        raise RuntimeError(name + ' already exists')
    if len(edges) != expected:
        raise RuntimeError(name + ': expected ' + str(expected) + ' edges, found ' + str(len(edges)))
    inp = r.features.chamferFeatures.createInput2()
    inp.chamferEdgeSets.addEqualDistanceChamferEdgeSet(
        adsk.core.ObjectCollection.createWithArray(edges),
        adsk.core.ValueInput.createByString(expression), False)
    feature = r.features.chamferFeatures.add(inp)
    feature.name = name


def service_holes(_context):
    """Two tool holes using the user's component-side board measurements.

    Original board-left datum is mirrored in this assembly, just as USB X36
    from board-left becomes global X39. BOOT is 31 from that edge, RESET is
    30 from the opposite edge; both are 10 from the rear 70 mm board edge.
    """
    _, d, r = context()
    if d.userParameters.itemByName('serviceHoleDiameterV6'):
        raise RuntimeError('Service holes already initialized')
    h = helpers()
    values = (('serviceHoleDiameterV6', '3 mm'), ('serviceButtonRearInsetV6', '10 mm'),
              ('bootBoardLeftInsetV6', '31 mm'), ('resetBoardRightInsetV6', '30 mm'))
    for name, expression in values:
        d.userParameters.add(name, h.value(expression), 'mm', 'User measured BOOT/RESET access')
    lid = r.bRepBodies.itemByName('BottomCover_Draft')
    lid.isVisible = True
    for label, x in (('BOOT', 'pcbLeft+pcbWidth-bootBoardLeftInsetV6'),
                     ('RESET', 'pcbLeft+resetBoardRightInsetV6')):
        sketch = h.xy_circle(d, r, r.xYConstructionPlane, 'V6 ' + label + ' access profile',
                             x, 'pcbRear-serviceButtonRearInsetV6', 'serviceHoleDiameterV6')
        h.extrude(r, sketch, 'V6 ' + label + ' tool access', 'bottomThickness',
                  adsk.fusion.FeatureOperations.CutFeatureOperation, True, lid)
    d.computeAll()
    healthy(d)
    print(json.dumps({'BOOT_x_y_mm': [44, 102.2], 'RESET_x_y_mm': [35, 102.2], 'diameter_mm': 3}))


def finish_edges(_context):
    _, d, r = context()
    ev = lambda e: d.unitsManager.evaluateExpression(e, 'cm')
    width, length, front = ev('caseWidth'), ev('caseLength'), ev('frontHeight')
    slope = math.tan(d.unitsManager.evaluateExpression('caseTilt', 'rad'))
    near = lambda a, b: abs(a - b) < 1e-6
    shell = r.bRepBodies.itemByName('UpperShell_Draft')
    edges = []
    for edge in shell.edges:
        if not edge.startVertex or not edge.endVertex:
            continue
        a, b = edge.startVertex.geometry, edge.endVertex.geometry
        outer = any(near(getattr(a, axis), v) and near(getattr(b, axis), v)
                    for axis, v in (('x', 0), ('x', width), ('y', 0), ('y', length)))
        top = near(a.z, front + a.y * slope) and near(b.z, front + b.y * slope)
        corner = (near(a.x, b.x) and near(a.y, b.y)
                  and (near(a.x, 0) or near(a.x, width))
                  and (near(a.y, 0) or near(a.y, length)))
        if outer and (top or corner):
            edges.append(edge)
    chamfer(r, edges, 'V6 exterior top and corner chamfers', 'exteriorChamferV6', 8)
    d.computeAll()
    healthy(d)
    # Select only the four rectangular entry edges on the exterior rear wall.
    x, z = ev('usbCenterX'), ev('usbCenterZ')
    hw, hh = ev('usbAccessWidthV6') / 2, ev('usbAccessHeightV6') / 2
    edges = []
    for edge in shell.edges:
        if not edge.startVertex or not edge.endVertex:
            continue
        a, b = edge.startVertex.geometry, edge.endVertex.geometry
        if (near(a.y, length) and near(b.y, length)
                and all(x - hw - 1e-6 <= p.x <= x + hw + 1e-6
                        and z - hh - 1e-6 <= p.z <= z + hh + 1e-6 for p in (a, b))):
            edges.append(edge)
    chamfer(r, edges, 'V6 USB entry chamfer', 'usbEntryChamferV6', 4)
    lid = r.bRepBodies.itemByName('BottomCover_Draft')
    edges = [e for e in lid.edges if e.startVertex and e.endVertex
             and near(e.startVertex.geometry.z, 0) and near(e.endVertex.geometry.z, 0)
             and e.length > 7]
    chamfer(r, edges, 'V6 bottom exterior chamfer', 'exteriorChamferV6', 4)
    d.computeAll()
    healthy(d)
    print('Exterior 0.8 mm and USB entry 0.5 mm chamfers created')


def run(_context):
    initialize(_context)
    usb(_context)
    finish_edges(_context)
    service_holes(_context)
