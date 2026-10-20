"""Remove obsolete front triangular gussets beside the roof-connected pillars."""
import importlib.util
import json
from pathlib import Path

import adsk.core
import adsk.fusion

HERE = Path('/Users/denisbabiichuk/3dPrint/macropad/cad/fusion')
EXPORT = HERE / 'exports'


def load(name, filename):
    spec = importlib.util.spec_from_file_location(name, HERE / filename)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def run(context):
    m = load('v6_helpers', 'macropad_enclosure_finish_v6.py')
    _, d, r = m.context()
    m.healthy(d)
    names = [f'Front cover support {i} 45 degree gusset' for i in (1, 2)]
    features = [r.features.extrudeFeatures.itemByName(n) for n in names]
    if any(f is None or f.isSuppressed for f in features):
        raise RuntimeError('Expected two active original front gussets')
    if any(r.features.extrudeFeatures.itemByName(f'V7 front cover pillar {i}') is None for i in (1, 2)):
        raise RuntimeError('Roof-connected pillars must already exist')
    path = EXPORT / 'macropad_before_front_cleanup_v9.f3d'
    if path.exists():
        raise RuntimeError('Backup exists; inspect current state')
    if not d.exportManager.execute(d.exportManager.createFusionArchiveExportOptions(str(path))):
        raise RuntimeError('Backup failed')
    baseline = {b.name: b.volume * 1000 for b in r.bRepBodies}
    (EXPORT / 'front-cleanup-v9-baseline.json').write_text(json.dumps(baseline, indent=2) + '\n')
    for feature in reversed(features):
        feature.isSuppressed = True
    d.computeAll()
    m.healthy(d)
    for name, volume in baseline.items():
        if name != 'UpperShell_Draft' and abs(r.bRepBodies.itemByName(name).volume * 1000 - volume) > 1e-5:
            raise RuntimeError('Unexpected body change ' + name)
    print('Two obsolete front gussets removed; roof pillars, rear supports and printed carrier preserved')


def verify_export(context):
    m = load('v9_context', 'macropad_enclosure_finish_v6.py')
    _, _, r = m.context()
    shell = r.bRepBodies.itemByName('UpperShell_Draft')
    inside = adsk.fusion.PointContainment.PointInsidePointContainment
    for i, x in enumerate((20, 60), 1):
        pillar = r.features.extrudeFeatures.itemByName(f'V7 front cover pillar {i}')
        if pillar is None or pillar.isSuppressed:
            raise RuntimeError('Front roof pillar missing')
        for z in (8.2, 15, 24, 27, 28.5):
            if shell.pointContainment(adsk.core.Point3D.create(x / 10, .48, z / 10)) != inside:
                raise RuntimeError('Front pillar is not connected to the roof')
    verifier = load('v9_verifier', 'verify_service_clearance_v8.py')
    verifier.OUTPUT_TAG = 'v9'
    verifier.BASELINE_FILENAME = 'front-cleanup-v9-baseline.json'
    verifier.REVISION_LABEL = 'Front gusset cleanup V9'
    verifier.run(context)
    verifier.export(context)
