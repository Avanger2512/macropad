"""Preserve printed V5 carrier while clearing its vertical installation path.

Clip rear V7 gussets to the original 6 mm boss envelope and trim only the
hidden rear diffuser flange. Candidate geometry was tested at 161 poses.
"""
import importlib.util
import json
import math
from pathlib import Path

import adsk.core
import adsk.fusion

HERE = Path('/Users/denisbabiichuk/3dPrint/macropad/cad/fusion')
EXPORT = HERE / 'exports'


def helpers():
    spec = importlib.util.spec_from_file_location('v6', HERE / 'macropad_enclosure_finish_v6.py')
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m, m.helpers()


def initialize(context):
    m, h = helpers()
    _, d, r = m.context()
    m.healthy(d)
    if d.userParameters.itemByName('serviceDiffuserRearLimitV8'):
        raise RuntimeError('V8 already initialized')
    path = EXPORT / 'macropad_before_service_clearance_v8.f3d'
    if path.exists():
        raise RuntimeError('Backup exists; inspect recovery state')
    if not d.exportManager.execute(d.exportManager.createFusionArchiveExportOptions(str(path))):
        raise RuntimeError('Backup failed')
    (EXPORT / 'service-v8-baseline.json').write_text(json.dumps(
        {b.name: b.volume * 1000 for b in r.bRepBodies}, indent=2) + '\n')
    d.userParameters.add('serviceDiffuserRearLimitV8', h.value('101.55 mm'), 'mm',
                         'Vertical rear flange limit for original 5 degree enclosure layout')
    print('V8 baseline saved')


def combine(root, target, tools, operation, name):
    inp = root.features.combineFeatures.createInput(
        target, adsk.core.ObjectCollection.createWithArray(tools))
    inp.operation = operation
    inp.isKeepToolBodies = False
    feature = root.features.combineFeatures.add(inp)
    feature.name = name
    return feature


def rear(context):
    m, h = helpers()
    _, d, r = m.context()
    if r.features.combineFeatures.itemByName('V8 rear gusset 1 service clearance'):
        raise RuntimeError('Rear service relief already exists')
    shell = r.bRepBodies.itemByName('UpperShell_Draft')
    shell.isVisible = True
    plane = h.offset(r, r.xYConstructionPlane, 'V8 gusset clipping datum',
                     'bottomThickness+bottomBossHeight-0.11 mm')
    height = 'rearBossRampRunV7*tan(rearBossRampAngleV7)+0.2 mm'
    new = adsk.fusion.FeatureOperations.NewBodyFeatureOperation
    cut = adsk.fusion.FeatureOperations.CutFeatureOperation
    for i, x in enumerate(('20 mm', 'caseWidth-20 mm'), 1):
        sketch = h.rectangle(d, r, plane, f'V8 rear clip box {i} profile',
                             f'({x})-bottomBossDiameter/2-0.01 mm', 'caseLength-6.1 mm',
                             'bottomBossDiameter+0.02 mm', '6.1 mm-shellWall')
        tool = h.extrude(r, sketch, f'V8 rear clip box {i}', height, new, True).bodies.item(0)
        tool.name = f'V8 rear clipping tool {i}'
        sketch = h.xy_circle(d, r, plane, f'V8 rear cylindrical preserve {i} profile',
                             x, 'caseLength-3 mm', 'bottomBossDiameter')
        cylinder = h.extrude(r, sketch, f'V8 rear cylindrical preserve {i}', height, new, True).bodies.item(0)
        cylinder.name = f'V8 rear preservation tool {i}'
        difference = combine(r, tool, [cylinder], cut, f'V8 rear gusset {i} clipping mask')
        if difference.bodies.count != 1:
            raise RuntimeError('Expected one connected clipping tool')
        combine(r, shell, [difference.bodies.item(0)], cut, f'V8 rear gusset {i} service clearance')
    d.computeAll()
    m.healthy(d)
    print('Rear gussets clipped to existing boss diameter; carrier unchanged')


def diffuser(context):
    m, h = helpers()
    _, d, r = m.context()
    if r.features.extrudeFeatures.itemByName('V8 diffuser rear service clearance'):
        raise RuntimeError('Diffuser already updated')
    body = r.bRepBodies.itemByName('Diffuser_Draft')
    body.isVisible = True
    manager = adsk.fusion.TemporaryBRepManager.get()
    original = manager.copy(body)
    sketch = h.rectangle(d, r, r.xYConstructionPlane, 'V8 diffuser rear service profile',
                         '0 mm', 'serviceDiffuserRearLimitV8', 'caseWidth', '3 mm')
    h.extrude(r, sketch, 'V8 diffuser rear service clearance', 'rearHeight+1 mm',
              adsk.fusion.FeatureOperations.CutFeatureOperation, True, body)
    d.computeAll()
    m.healthy(d)
    if not manager.booleanOperation(original, manager.copy(body), adsk.fusion.BooleanTypes.DifferenceBooleanType):
        raise RuntimeError('Diffuser trim comparison failed')
    angle = d.unitsManager.evaluateExpression('caseTilt', 'rad')
    front = d.unitsManager.evaluateExpression('frontHeight', 'cm')
    depths = [(v.geometry.y * math.sin(angle) - (v.geometry.z - front) * math.cos(angle)) * 10
              for v in original.vertices]
    wall = d.unitsManager.evaluateExpression('shellWall', 'cm') * 10
    if min(depths) < wall - .001:
        raise RuntimeError('Trim reaches visible diffuser plug')
    report = {'removed_mm3': original.volume * 1000, 'removed_normal_depth_mm': [min(depths), max(depths)],
              'visible_plug_depth_mm': [0, wall], 'visible_plug_and_08mm_skin_unchanged': True}
    (EXPORT / 'service-v8-diffuser-trim.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report))
    print('Hidden rear diffuser flange cleared for vertical carrier installation')


def encoder_fit(context):
    m, _ = helpers()
    _, d, r = m.context()
    before = {b.name: b.volume * 1000 for b in r.bRepBodies if b.name != 'UpperShell_Draft'}
    d.userParameters.itemByName('encoderHole').expression = '7.4 mm'
    d.userParameters.itemByName('encoderHole').comment = 'Measured 7 mm threaded bushing; 0.4 mm diametral print clearance'
    d.computeAll()
    m.healthy(d)
    for name, volume in before.items():
        if abs(r.bRepBodies.itemByName(name).volume * 1000 - volume) > 1e-5:
            raise RuntimeError('Encoder change affected ' + name)
    print('Upper shell encoder opening 7.4 mm; printed carrier unchanged')


def run(context):
    initialize(context)
    rear(context)
    diffuser(context)
    encoder_fit(context)
