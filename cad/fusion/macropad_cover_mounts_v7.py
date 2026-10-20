"""Roof-connected front cover pillars and printable rear boss gussets.

Preserve the V5 printed carrier, V6 lid and USB access. Rear full cylinders
would cross the horizontal PCB; rear gussets stay below its substrate instead.
Component/wire footprints near rear gussets still require physical checking.
"""
import importlib.util
import json
from pathlib import Path

import adsk.core
import adsk.fusion

HERE = Path('/Users/denisbabiichuk/3dPrint/macropad/cad/fusion')
EXPORT = HERE / 'exports'


def module():
    spec = importlib.util.spec_from_file_location('finish_v6', HERE / 'macropad_enclosure_finish_v6.py')
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


def initialize(context):
    m = module()
    _, d, r = m.context()
    m.healthy(d)
    if d.userParameters.itemByName('rearBossRampAngleV7'):
        raise RuntimeError('V7 already initialized')
    if not r.features.chamferFeatures.itemByName('V6 USB entry chamfer'):
        raise RuntimeError('Expected finished V6 enclosure')
    backup = EXPORT / 'macropad_before_cover_mounts_v7.f3d'
    if backup.exists():
        raise RuntimeError('V7 backup exists; inspect recovery state')
    if not d.exportManager.execute(d.exportManager.createFusionArchiveExportOptions(str(backup))):
        raise RuntimeError('Backup failed')
    baseline = {b.name: b.volume * 1000 for b in r.bRepBodies}
    (EXPORT / 'cover-mounts-v7-baseline.json').write_text(json.dumps(baseline, indent=2) + '\n')
    h = m.helpers()
    d.userParameters.add('rearBossRampAngleV7', h.value('55 deg'), 'deg',
                         '50 degrees above print bed when the 5 degree roof faces down')
    d.userParameters.add('rearBossRampRunV7', h.value('3 mm-shellWall+0.1 mm+bottomBossDiameter/2'),
                         'mm', 'Reach from rear wall overlap to inward boss tangent')
    print('V7 backup and parameters created')


def front(context):
    m = module()
    _, d, r = m.context()
    h = m.helpers()
    if r.features.extrudeFeatures.itemByName('V7 front cover pillar 1'):
        raise RuntimeError('Front pillars already exist')
    shell = r.bRepBodies.itemByName('UpperShell_Draft')
    shell.isVisible = True
    plane = h.offset(r, r.xYConstructionPlane, 'V7 front pillar start datum',
                     'bottomThickness+bottomBossHeight-0.1 mm')
    for i, x in enumerate(('20 mm', 'caseWidth-20 mm'), 1):
        sketch = h.xy_circle(d, r, plane, f'V7 front cover pillar {i} profile',
                             x, '4.8 mm', 'bottomBossDiameter')
        height = ('frontHeight+4.8 mm*tan(caseTilt)-shellWall/cos(caseTilt)+0.5 mm'
                  '-(bottomThickness+bottomBossHeight-0.1 mm)')
        h.extrude(r, sketch, f'V7 front cover pillar {i}', height,
                  adsk.fusion.FeatureOperations.JoinFeatureOperation, True, shell)
    d.computeAll()
    m.healthy(d)
    print('Front pillars reach the inner roof; bottom insert pilots retained')


def rear(context):
    m = module()
    _, d, r = m.context()
    h = m.helpers()
    if r.features.extrudeFeatures.itemByName('V7 rear cover gusset 1'):
        raise RuntimeError('Rear gussets already exist')
    shell = r.bRepBodies.itemByName('UpperShell_Draft')
    shell.isVisible = True
    wall = 'caseLength-shellWall+0.1 mm'
    base = 'bottomThickness+bottomBossHeight-0.1 mm'
    for i, x in enumerate(('20 mm', 'caseWidth-20 mm'), 1):
        plane = h.offset(r, r.yZConstructionPlane, f'V7 rear gusset {i} datum',
                         f'({x})-bottomBossDiameter/2')
        sketch = h.polygon(d, r, plane, f'V7 rear gusset {i} profile', (
            (wall, base), (f'({wall})-rearBossRampRunV7', base),
            (wall, f'({base})+rearBossRampRunV7*tan(rearBossRampAngleV7)')), world_yz=True)
        h.extrude(r, sketch, f'V7 rear cover gusset {i}', 'bottomBossDiameter',
                  adsk.fusion.FeatureOperations.JoinFeatureOperation,
                  r.yZConstructionPlane.geometry.normal.x > 0, shell)
    d.computeAll()
    m.healthy(d)
    print('Rear 55 degree gussets added; substrate and physical component clearance must be verified')


def run(context):
    initialize(context)
    front(context)
    rear(context)
