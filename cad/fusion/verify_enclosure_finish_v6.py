"""Native V6 checks, tilt clearance study, exports and review snapshots."""
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
    errors = [t.name for t in d.timeline if not getattr(t.entity, 'isSuppressed', False)
              and t.healthState != adsk.fusion.FeatureHealthStates.HealthyFeatureHealthState]
    unconstrained = [s.name for s in r.sketches if not s.isFullyConstrained]
    if errors or unconstrained:
        raise RuntimeError(str({'features': errors, 'sketches': unconstrained}))
    bodies = [r.bRepBodies.itemByName(name) for name in MAIN]
    if any(b is None or not b.isSolid or b.volume <= 0 or b.lumps.count != 1 for b in bodies):
        raise RuntimeError('Expected four connected positive solids')
    baseline = json.loads((EXPORT / 'enclosure-v6-baseline.json').read_text())
    for b in r.bRepBodies:
        if b.name not in ('UpperShell_Draft', 'BottomCover_Draft'):
            if abs(b.volume * 1000 - baseline[b.name]) > 1e-5:
                raise RuntimeError('Unexpected body change ' + b.name)
    manager = adsk.fusion.TemporaryBRepManager.get()
    for i, a in enumerate(bodies):
        for b in bodies[i + 1:]:
            result = manager.copy(a)
            if not manager.booleanOperation(result, manager.copy(b), adsk.fusion.BooleanTypes.IntersectionBooleanType):
                raise RuntimeError('Boolean operation failed')
            if result.volume * 1000 > 1e-5:
                raise RuntimeError('Interference ' + a.name + ' / ' + b.name)
    shell, carrier, lid, diffuser = bodies
    inside = adsk.fusion.PointContainment.PointInsidePointContainment
    service_samples = 0
    for x in (35, 44):
        for z in (.1, 1, 1.9):
            for radius in (0, 1.4):
                for degree in range(0, 360, 45):
                    angle = math.radians(degree)
                    p = adsk.core.Point3D.create((x + radius * math.cos(angle)) / 10,
                                                (102.2 + radius * math.sin(angle)) / 10, z / 10)
                    if lid.pointContainment(p) == inside:
                        raise RuntimeError('BOOT/RESET access obstructed')
                    service_samples += 1
    samples = 0
    for x in (32.1, 35, 39, 43, 45.9):
        for z in (10.3, 12, 15.2, 18, 20.1):
            for y in (112.2, 112.7, 113.8, 114.9, 115.1):
                p = adsk.core.Point3D.create(x / 10, y / 10, z / 10)
                if shell.pointContainment(p) == inside:
                    raise RuntimeError('USB throat blocked ' + str((x, y, z)))
                samples += 1
    ev = lambda e: d.unitsManager.evaluateExpression(e, 'cm') * 10
    # Rigidly transform the conservative component envelope, never regenerate
    # the printed carrier by changing its original design parameters.
    studies = []
    for tilt in (5, 4, 3, 2, 0):
        delta = math.radians(tilt - 5)
        pivot_y, pivot_z = ev('caseLength'), ev('rearHeight')
        def transformed_z(y, z):
            return pivot_z + math.sin(delta) * (y - pivot_y) + math.cos(delta) * (z - pivot_z)
        component_bottom = ev('pcbUndersideHeight-headerMaxHeight')
        min_z = min(transformed_z(y, component_bottom) for y in (ev('pcbFront'), ev('pcbRear')))
        front_pivot_z = ev('frontHeight')
        lowered_min_z = min(front_pivot_z + math.sin(delta) * y
                            + math.cos(delta) * (component_bottom - front_pivot_z)
                            for y in (ev('pcbFront'), ev('pcbRear')))
        studies.append({'face_tilt_deg': tilt, 'front_roof_z_mm': transformed_z(0, ev('frontHeight')),
                        'rear_roof_z_mm': pivot_z, 'component_envelope_lid_gap_mm': min_z - ev('bottomThickness'),
                        'front_fixed_component_lid_gap_mm': lowered_min_z - ev('bottomThickness'),
                        'method': 'Rigid rotation about rear roof X axis; flat lid top remains Z2 for study only'})
    report = {'revision': 'Enclosure finishing V6', 'healthy_timeline': True, 'fully_constrained_sketches': True,
              'connected_main_solids': 4, 'pairwise_intersections_mm3': 0,
              'carrier_and_other_reference_volumes_unchanged': True, 'usb_throat_samples': samples,
              'usb_throat_mm': [14, 10], 'usb_center_x_z_mm': [39, 15.2],
              'service_holes': {'BOOT_center_mm': [44, 102.2], 'RESET_center_mm': [35, 102.2],
                                'diameter_mm': 3, 'bore_samples': service_samples,
                                'datum': 'User component-side measurements; board-left mirrored like USB'},
              'volumes_mm3': {b.name: b.volume * 1000 for b in bodies},
              'tilt_study': studies, 'current_face_tilt_deg': 5,
              'pending': ['Physical BOOT/RESET tool access test', 'Final cable insertion test',
                          'Carrier service extraction sequence', 'Lower shell adaptation if tilt changes']}
    (EXPORT / 'enclosure-v6-validation.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report))


def export(context):
    app = adsk.core.Application.get()
    d = adsk.fusion.Design.cast(app.activeProduct)
    r = d.rootComponent
    for body_name, basename in (('UpperShell_Draft', 'upper_shell_finish_v6'),
                                ('BottomCover_Draft', 'bottom_cover_finish_v6')):
        body = r.bRepBodies.itemByName(body_name)
        for b in r.bRepBodies:
            b.isVisible = b.name == body_name
        for mesh in r.meshBodies:
            mesh.isLightBulbOn = False
        if not d.exportManager.execute(d.exportManager.createSTEPExportOptions(str(EXPORT / (basename + '.step')))):
            raise RuntimeError('STEP export failed')
        options = d.exportManager.createSTLExportOptions(body, str(EXPORT / (basename + '_native.stl')))
        options.unitType = adsk.fusion.DistanceUnits.MillimeterDistanceUnits
        options.isBinaryFormat = True
        options.meshRefinement = adsk.fusion.MeshRefinementSettings.MeshRefinementHigh
        if not d.exportManager.execute(options):
            raise RuntimeError('STL export failed')
    for b in r.bRepBodies:
        b.isVisible = b.name in MAIN
    for s in r.sketches:
        s.isVisible = False
    for p in r.constructionPlanes:
        p.isLightBulbOn = False
    if not d.exportManager.execute(d.exportManager.createSTEPExportOptions(str(EXPORT / 'macropad_enclosure_finish_v6.step'))):
        raise RuntimeError('Assembly STEP failed')
    if not d.exportManager.execute(d.exportManager.createFusionArchiveExportOptions(str(EXPORT / 'macropad_enclosure_finish_v6.f3d'))):
        raise RuntimeError('F3D export failed')
    camera = app.activeViewport.camera
    camera.target = adsk.core.Point3D.create(4, 5.75, 1.95)
    camera.eye = adsk.core.Point3D.create(18, 22, 16)
    camera.upVector = adsk.core.Vector3D.create(0, 0, 1)
    camera.isFitView = True
    app.activeViewport.camera = camera
    app.activeViewport.visualStyle = adsk.core.VisualStyles.ShadedWithVisibleEdgesOnlyVisualStyle
    app.activeViewport.refresh()
    if not app.activeViewport.saveAsImageFile(str(EXPORT / 'enclosure-v6-rear.png'), 1400, 1050):
        raise RuntimeError('Snapshot failed')
    for b in r.bRepBodies:
        b.isVisible = b.name == 'BottomCover_Draft'
    camera = app.activeViewport.camera
    camera.target = adsk.core.Point3D.create(4, 5.75, .1)
    camera.eye = adsk.core.Point3D.create(11, 16, -12)
    camera.upVector = adsk.core.Vector3D.create(0, 1, 0)
    camera.isFitView = True
    app.activeViewport.camera = camera
    app.activeViewport.refresh()
    if not app.activeViewport.saveAsImageFile(str(EXPORT / 'enclosure-v6-bottom.png'), 1400, 1050):
        raise RuntimeError('Bottom snapshot failed')
    for b in r.bRepBodies:
        b.isVisible = b.name in MAIN
    camera.target = adsk.core.Point3D.create(4, 5.75, 1.95)
    camera.eye = adsk.core.Point3D.create(18, 22, 16)
    camera.upVector = adsk.core.Vector3D.create(0, 0, 1)
    camera.isFitView = True
    app.activeViewport.camera = camera
    app.activeViewport.refresh()
    print('STEP, native STL, F3D and rear view exported')
