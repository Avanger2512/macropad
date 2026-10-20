"""Validate V8 static geometry and sampled bare-carrier installation path."""
import importlib.util
import json
import math
from pathlib import Path

import adsk.core
import adsk.fusion

HERE = Path('/Users/denisbabiichuk/3dPrint/macropad/cad/fusion')
EXPORT = HERE / 'exports'
MAIN = ('UpperShell_Draft', 'MiddleCarrier_Draft', 'BottomCover_Draft', 'Diffuser_Draft')
OUTPUT_TAG = 'v8'
BASELINE_FILENAME = 'service-v8-baseline.json'
REVISION_LABEL = 'Service clearance V8'


def run(context):
    app = adsk.core.Application.get()
    d = adsk.fusion.Design.cast(app.activeProduct)
    if d is None or app.activeDocument.name != 'macropad':
        raise RuntimeError('Activate macropad')
    r = d.rootComponent
    baseline = json.loads((EXPORT / BASELINE_FILENAME).read_text())
    current = {b.name: b.volume * 1000 for b in r.bRepBodies}
    if baseline.keys() != current.keys():
        raise RuntimeError('Unexpected body list; clipping tools may remain')
    for name in baseline:
        if name not in ('UpperShell_Draft', 'Diffuser_Draft') and abs(current[name] - baseline[name]) > 1e-5:
            raise RuntimeError('Unexpected body change ' + name)
    errors = [t.name for t in d.timeline if not getattr(t.entity, 'isSuppressed', False)
              and t.healthState != adsk.fusion.FeatureHealthStates.HealthyFeatureHealthState]
    unconstrained = [s.name for s in r.sketches if not s.isFullyConstrained]
    if errors or unconstrained:
        raise RuntimeError(str({'features': errors, 'sketches': unconstrained}))
    bodies = [r.bRepBodies.itemByName(name) for name in MAIN]
    if any(not b.isSolid or b.lumps.count != 1 or b.volume <= 0 for b in bodies):
        raise RuntimeError('Expected four connected solids')
    manager = adsk.fusion.TemporaryBRepManager.get()
    def overlap(a, b):
        result = manager.copy(a)
        if not manager.booleanOperation(result, manager.copy(b), adsk.fusion.BooleanTypes.IntersectionBooleanType):
            raise RuntimeError('Boolean intersection failed')
        return result.volume * 1000
    for i, a in enumerate(bodies):
        for b in bodies[i + 1:]:
            if overlap(a, b) > 1e-5:
                raise RuntimeError('Static interference')
    shell, carrier, lid, diffuser = bodies
    encoder_cylinders = [adsk.core.Cylinder.cast(f.geometry) for f in shell.faces]
    if not any(c is not None and abs(c.radius * 20 - 7.4) < 1e-5 for c in encoder_cylinders):
        raise RuntimeError('Measured encoder clearance hole is missing')
    for index in range(161):
        moving = manager.copy(carrier)
        matrix = adsk.core.Matrix3D.create()
        matrix.translation = adsk.core.Vector3D.create(0, 0, -index * .025)
        if not manager.transform(moving, matrix):
            raise RuntimeError('Transform failed')
        for other in (shell, diffuser):
            if overlap(moving, other) > 1e-5:
                raise RuntimeError('Vertical path blocked at ' + str(index * .25) + ' mm / ' + other.name)
    inside = adsk.fusion.PointContainment.PointInsidePointContainment
    def p(x, y, z):
        return adsk.core.Point3D.create(x / 10, y / 10, z / 10)
    for x in (20, 60):
        for y in (4.8, 112):
            for z in (2.1, 3.5, 6.4):
                for degree in range(0, 360, 45):
                    t = math.radians(degree)
                    if shell.pointContainment(p(x + 1.5 * math.cos(t), y + 1.5 * math.sin(t), z)) == inside:
                        raise RuntimeError('Insert pilot blocked')
            for dx in (-2.2, 2.2):
                if shell.pointContainment(p(x + dx, y, 2.1)) != inside:
                    raise RuntimeError('Insert wall missing')
    report = {'revision': REVISION_LABEL, 'healthy_timeline': True,
              'fully_constrained_sketches': True, 'connected_main_solids': 4,
              'pairwise_intersections_mm3': 0, 'unchanged_carrier_cover_and_references': True,
              'vertical_bare_carrier_path': {'drop_mm': [0, 40], 'step_mm': .25,
                                            'poses': 161, 'against': ['shell', 'diffuser'], 'max_overlap_mm3': 0},
              'volumes_mm3': {b.name: b.volume * 1000 for b in bodies},
              'removed_mm3': {n: baseline[n] - current[n] for n in ('UpperShell_Draft', 'Diffuser_Draft')},
              'encoder': {'measured_bushing_diameter_mm': 7, 'measured_thread_length_mm': 7,
                          'shell_hole_diameter_mm': 7.4, 'shell_thickness_mm': 2.4,
                          'remaining_thread_before_nut_and_washer_mm': 4.6},
              'limits': ['Sampled BRep path, not continuous swept-volume proof',
                         'PCB, encoder, switches, keycaps and wires not included in carrier path',
                         'Keycaps must be fitted after carrier installation',
                         'Real component footprints and cable insertion still need physical fit checks']}
    (EXPORT / f'service-{OUTPUT_TAG}-validation.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report))


def export(context):
    app = adsk.core.Application.get()
    d = adsk.fusion.Design.cast(app.activeProduct)
    r = d.rootComponent
    e = d.exportManager
    for name, base in (('UpperShell_Draft', f'upper_shell_service_{OUTPUT_TAG}'), ('Diffuser_Draft', f'diffuser_service_{OUTPUT_TAG}')):
        body = r.bRepBodies.itemByName(name)
        for b in r.bRepBodies:
            b.isVisible = b.name == name
        for mesh in r.meshBodies:
            mesh.isLightBulbOn = False
        if not e.execute(e.createSTEPExportOptions(str(EXPORT / (base + '.step')))):
            raise RuntimeError('STEP failed')
        options = e.createSTLExportOptions(body, str(EXPORT / (base + '_native.stl')))
        options.unitType = adsk.fusion.DistanceUnits.MillimeterDistanceUnits
        options.isBinaryFormat = True
        options.meshRefinement = adsk.fusion.MeshRefinementSettings.MeshRefinementHigh
        if not e.execute(options):
            raise RuntimeError('STL failed')
    for b in r.bRepBodies:
        b.isVisible = b.name in MAIN
    for s in r.sketches:
        s.isVisible = False
    for plane in r.constructionPlanes:
        plane.isLightBulbOn = False
    if not e.execute(e.createSTEPExportOptions(str(EXPORT / f'macropad_service_{OUTPUT_TAG}.step'))):
        raise RuntimeError('Assembly STEP failed')
    if not e.execute(e.createFusionArchiveExportOptions(str(EXPORT / f'macropad_service_{OUTPUT_TAG}.f3d'))):
        raise RuntimeError('F3D failed')
    for b in r.bRepBodies:
        b.isVisible = b.name in ('UpperShell_Draft', 'Diffuser_Draft')
    camera = app.activeViewport.camera
    camera.target = adsk.core.Point3D.create(4, 5.75, 2)
    camera.eye = adsk.core.Point3D.create(16, 21, -19)
    camera.upVector = adsk.core.Vector3D.create(0, 0, 1)
    camera.isFitView = True
    app.activeViewport.camera = camera
    app.activeViewport.refresh()
    if not app.activeViewport.saveAsImageFile(str(EXPORT / f'service-{OUTPUT_TAG}-interior.png'), 1400, 1050):
        raise RuntimeError('Snapshot failed')
    for b in r.bRepBodies:
        b.isVisible = b.name in MAIN
    camera.eye = adsk.core.Point3D.create(18, 22, 16)
    camera.isFitView = True
    app.activeViewport.camera = camera
    app.activeViewport.refresh()
    print(OUTPUT_TAG.upper() + ' shell, diffuser and assembly exported')
