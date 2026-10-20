"""Validate revised cover mounts and export the V7 shell and assembly."""
import importlib.util
import json
import math
from pathlib import Path

import adsk.core
import adsk.fusion

HERE = Path('/Users/denisbabiichuk/3dPrint/macropad/cad/fusion')
EXPORT = HERE / 'exports'
MAIN = ('UpperShell_Draft', 'MiddleCarrier_Draft', 'BottomCover_Draft', 'Diffuser_Draft')


def run(context):
    app = adsk.core.Application.get()
    d = adsk.fusion.Design.cast(app.activeProduct)
    if d is None or app.activeDocument.name != 'macropad':
        raise RuntimeError('Activate macropad')
    r = d.rootComponent
    required = [f'V7 {kind} {i}' for kind in ('front cover pillar', 'rear cover gusset') for i in (1, 2)]
    if any(r.features.extrudeFeatures.itemByName(name) is None for name in required):
        raise RuntimeError('Missing V7 mounting features')
    errors = [t.name for t in d.timeline if not getattr(t.entity, 'isSuppressed', False)
              and t.healthState != adsk.fusion.FeatureHealthStates.HealthyFeatureHealthState]
    unconstrained = [s.name for s in r.sketches if not s.isFullyConstrained]
    if errors or unconstrained:
        raise RuntimeError(str({'features': errors, 'sketches': unconstrained}))
    baseline = json.loads((EXPORT / 'cover-mounts-v7-baseline.json').read_text())
    for b in r.bRepBodies:
        if b.name != 'UpperShell_Draft' and abs(b.volume * 1000 - baseline[b.name]) > 1e-5:
            raise RuntimeError('Unexpected body change ' + b.name)
    bodies = [r.bRepBodies.itemByName(n) for n in MAIN]
    if any(not b.isSolid or b.volume <= 0 or b.lumps.count != 1 for b in bodies):
        raise RuntimeError('Expected four connected positive-volume bodies')
    manager = adsk.fusion.TemporaryBRepManager.get()
    def overlap(a, b):
        result = manager.copy(a)
        if not manager.booleanOperation(result, manager.copy(b), adsk.fusion.BooleanTypes.IntersectionBooleanType):
            raise RuntimeError('Boolean failed')
        return result.volume * 1000
    for i, a in enumerate(bodies):
        for b in bodies[i + 1:]:
            if overlap(a, b) > 1e-5:
                raise RuntimeError('Interference ' + a.name + ' / ' + b.name)
    shell = bodies[0]
    inside = adsk.fusion.PointContainment.PointInsidePointContainment
    def point(x, y, z):
        return adsk.core.Point3D.create(x / 10, y / 10, z / 10)
    samples = 0
    for x, y in ((20, 4.8), (60, 4.8), (20, 112), (60, 112)):
        for z in (2.1, 3.5, 6.4):
            for radius in (0, 1.5):
                for degree in range(0, 360, 45):
                    angle = math.radians(degree)
                    if shell.pointContainment(point(x + radius * math.cos(angle), y + radius * math.sin(angle), z)) == inside:
                        raise RuntimeError('Insert pilot obstructed')
                    samples += 1
        for dx in (-2.2, 2.2):
            if shell.pointContainment(point(x + dx, y, 2.1)) != inside:
                raise RuntimeError('Insert seat wall missing')
    for x in (20, 60):
        for z in (8.2, 15, 24, 27, 28.5):
            if shell.pointContainment(point(x, 4.8, z)) != inside:
                raise RuntimeError('Front pillar roof connection missing')
    rear_samples = 0
    for x in (19, 20, 21, 59, 60, 61):
        for y, z in ((110.5, 8.5), (111.5, 10.5), (112.5, 12)):
            if shell.pointContainment(point(x, y, z)) != inside:
                raise RuntimeError('Rear gusset material missing')
            rear_samples += 1
    box = adsk.core.OrientedBoundingBox3D.create(point(40, 87.2, 21.5),
        adsk.core.Vector3D.create(1, 0, 0), adsk.core.Vector3D.create(0, 1, 0), 7, 5, .16)
    pcb = manager.createBox(box)
    pcb_overlap = overlap(shell, pcb)
    if pcb_overlap > 1e-5:
        raise RuntimeError('PCB substrate collision')
    ev = lambda e: d.unitsManager.evaluateExpression(e, 'cm') * 10
    report = {'revision': 'Cover mounts V7', 'healthy_timeline': True, 'fully_constrained_sketches': True,
              'connected_main_solids': 4, 'pairwise_intersections_mm3': 0,
              'other_bodies_unchanged': True, 'pcb_substrate_overlap_mm3': pcb_overlap,
              'insert_bore_clear_samples': samples, 'front_pillar_roof_connection': True,
              'rear_gusset_material_samples': rear_samples,
              'rear_gusset_run_mm': ev('rearBossRampRunV7'),
              'rear_gusset_top_z_mm': ev('bottomThickness+bottomBossHeight-0.1 mm+rearBossRampRunV7*tan(rearBossRampAngleV7)'),
              'rear_gusset_angle_above_print_bed_deg': 50,
              'shell_volume_mm3': shell.volume * 1000,
              'pending': ['Actual component and wire footprints near rear gussets',
                          'Slicer overhang review; no entire-shell supportless claim',
                          'Previously unresolved carrier extraction sequence']}
    (EXPORT / 'cover-mounts-v7-validation.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report))


def export(context):
    app = adsk.core.Application.get()
    d = adsk.fusion.Design.cast(app.activeProduct)
    r = d.rootComponent
    shell = r.bRepBodies.itemByName('UpperShell_Draft')
    for b in r.bRepBodies:
        b.isVisible = b == shell
    for mesh in r.meshBodies:
        mesh.isLightBulbOn = False
    for s in r.sketches:
        s.isVisible = False
    for p in r.constructionPlanes:
        p.isLightBulbOn = False
    e = d.exportManager
    if not e.execute(e.createSTEPExportOptions(str(EXPORT / 'upper_shell_cover_mounts_v7.step'))):
        raise RuntimeError('STEP failed')
    options = e.createSTLExportOptions(shell, str(EXPORT / 'upper_shell_cover_mounts_v7_native.stl'))
    options.unitType = adsk.fusion.DistanceUnits.MillimeterDistanceUnits
    options.isBinaryFormat = True
    options.meshRefinement = adsk.fusion.MeshRefinementSettings.MeshRefinementHigh
    if not e.execute(options):
        raise RuntimeError('STL failed')
    camera = app.activeViewport.camera
    camera.target = adsk.core.Point3D.create(4, 5.75, 2)
    camera.eye = adsk.core.Point3D.create(16, 21, -19)
    camera.upVector = adsk.core.Vector3D.create(0, 0, 1)
    camera.isFitView = True
    app.activeViewport.camera = camera
    app.activeViewport.refresh()
    if not app.activeViewport.saveAsImageFile(str(EXPORT / 'cover-mounts-v7-interior.png'), 1400, 1050):
        raise RuntimeError('Snapshot failed')
    for b in r.bRepBodies:
        b.isVisible = b.name in MAIN
    if not e.execute(e.createSTEPExportOptions(str(EXPORT / 'macropad_cover_mounts_v7.step'))):
        raise RuntimeError('Assembly STEP failed')
    if not e.execute(e.createFusionArchiveExportOptions(str(EXPORT / 'macropad_cover_mounts_v7.f3d'))):
        raise RuntimeError('F3D failed')
    camera.target = adsk.core.Point3D.create(4, 5.75, 2)
    camera.eye = adsk.core.Point3D.create(18, 22, 16)
    camera.upVector = adsk.core.Vector3D.create(0, 0, 1)
    camera.isFitView = True
    app.activeViewport.camera = camera
    app.activeViewport.refresh()
    print('V7 exports and interior snapshot saved')
