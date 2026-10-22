"""Native checks on the imported compact STEP mirror; run through Fusion MCP.

Validation does not modify the design. Export changes visibility/camera only and
writes local files; it never saves a cloud document.
"""

from pathlib import Path
import hashlib
import json

import adsk.core
import adsk.fusion

FOLDER = Path('/Users/denisbabiichuk/3dPrint/macropad/cad/compact')


def entries(design):
    return [(occ.component.name, body, occ)
            for occ in design.rootComponent.allOccurrences for body in occ.bRepBodies]


def active_design():
    design = adsk.fusion.Design.cast(adsk.core.Application.get().activeProduct)
    if design is None:
        raise RuntimeError('No active Fusion design')
    attribute = design.rootComponent.attributes.itemByName('macropad_compact', 'source_sha256')
    expected_hash = hashlib.sha256((FOLDER / 'compact_model.step').read_bytes()).hexdigest()
    if attribute is None or attribute.value != expected_hash:
        raise RuntimeError('Active document is not the current compact STEP mirror')
    return design, expected_hash


def cylinder_centers(body, diameter):
    found = []
    for face in body.faces:
        geometry = adsk.core.Cylinder.cast(face.geometry)
        if geometry is not None and abs(geometry.radius * 20 - diameter) < 1e-5:
            found.append([round(geometry.origin.x * 10, 6),
                          round(geometry.origin.y * 10, 6)])
    return sorted(found)


def run(context):
    design, source_hash = active_design()
    all_entries = entries(design)
    if len(all_entries) != 45:
        raise RuntimeError('Expected 45 imported bodies')
    if any(not b.isSolid or b.lumps.count != 1 or b.volume <= 0
           for _, b, _ in all_entries):
        raise RuntimeError('Expected valid connected positive solids')
    parts = [(n, b, o) for n, b, o in all_entries if n.startswith('C1 ')]
    references = [(n, b, o) for n, b, o in all_entries if n.startswith('REFERENCE ')]
    if len(parts) != 5 or len(references) != 40:
        raise RuntimeError('Unexpected printed/reference body grouping')
    manager = adsk.fusion.TemporaryBRepManager.get()
    checks = 0
    collisions = []

    def check(a, b):
        nonlocal checks
        checks += 1
        result = manager.copy(a[1])
        if not manager.booleanOperation(result, manager.copy(b[1]),
                                        adsk.fusion.BooleanTypes.IntersectionBooleanType):
            raise RuntimeError('Native intersection failed: ' + a[0] + '/' + b[0])
        volume = abs(result.volume) * 1000
        if volume > 1e-5:
            collisions.append({'a': a[0], 'b': b[0], 'volume_mm3': volume})

    for index, part in enumerate(parts):
        for reference in references:
            check(part, reference)
        for other in parts[index + 1:]:
            check(part, other)
    if collisions:
        raise RuntimeError(json.dumps(collisions))
    cradle = next(b for n, b, _ in parts if n.startswith('C1 OLED cradle'))
    pcb = next(b for n, b, _ in references if n.startswith('REFERENCE OLED PCB'))
    pin_centers = cylinder_centers(cradle, 2.2)
    hole_centers = cylinder_centers(pcb, 2.5)
    expected = [[67.5, 35.0], [67.5, 63.0], [98.5, 35.0], [98.5, 63.0]]
    if pin_centers != expected or hole_centers != expected:
        raise RuntimeError('Measured OLED pattern mismatch: ' + str((pin_centers, hole_centers)))
    cones = [face for face in cradle.faces if adsk.core.Cone.cast(face.geometry) is not None]
    if len(cones) != 4:
        raise RuntimeError('Expected four pin lead-in cones')
    for face in cones:
        if abs((face.boundingBox.maxPoint.z - face.boundingBox.minPoint.z) * 10 - 0.5) > 1e-4:
            raise RuntimeError('Incorrect lead-in height')
    source_facts = json.loads((FOLDER / 'validation.json').read_text())['parts']
    aliases = [('C1 top shell', 'shell'), ('C1 removable lower', 'cover'),
               ('C1 removable MCU strap', 'mcu_strap'), ('C1 OLED cradle', 'oled_cradle'),
               ('C1 replaceable MCU cradle', 'mcu_cradle')]
    native_parts = {}
    for prefix, key in aliases:
        body = next(b for n, b, _ in parts if n.startswith(prefix))
        bb = body.boundingBox
        sizes = [(bb.maxPoint.x - bb.minPoint.x) * 10,
                 (bb.maxPoint.y - bb.minPoint.y) * 10,
                 (bb.maxPoint.z - bb.minPoint.z) * 10]
        if any(abs(a - b) > 1e-3 for a, b in zip(sizes, source_facts[key]['bbox_mm'])):
            raise RuntimeError('Native/source dimensions differ: ' + key)
        volume = body.volume * 1000
        if abs(volume - source_facts[key]['volume_mm3']) > max(0.05, volume * 1e-5):
            raise RuntimeError('Native/source volumes differ: ' + key)
        native_parts[key] = {'bbox_mm': sizes, 'volume_mm3': volume,
                              'solid': body.isSolid, 'lumps': body.lumps.count}
    report = {'revision': 'C1 OLED 31x28', 'fusion_mcp_validated': True,
              'validation_kind': 'native Fusion BRep checks of imported STEP mirror',
              'source_step_sha256': source_hash, 'imported_body_count': len(all_entries),
              'native_pair_checks': checks, 'positive_volume_collisions': collisions,
              'parts': native_parts,
              'oled': {'centers_xy_mm': pin_centers, 'pitch_mm': [31, 28],
                       'hole_diameter_mm': 2.5, 'pin_diameter_mm': 2.2,
                       'diametral_clearance_mm': 0.3, 'lead_height_mm': 0.5,
                       'centered_on_pcb_assumed': True},
              'limits': ['Hardware envelopes except measured dimensions remain provisional',
                         'OLED pins locate only; upward retention still pending',
                         'Physical fit and slicing of the full shell not yet verified',
                         'Native document is a STEP mirror; Python source owns parameters']}
    (FOLDER / 'fusion-validation.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report))


def export(context):
    app = adsk.core.Application.get()
    design, source_hash = active_design()
    report = json.loads((FOLDER / 'fusion-validation.json').read_text())
    if report['source_step_sha256'] != source_hash:
        raise RuntimeError('Current STEP has not passed native checks')
    all_entries = entries(design)
    for _, _, occurrence in all_entries:
        occurrence.isLightBulbOn = True
    viewport = app.activeViewport
    camera = viewport.camera
    camera.target = adsk.core.Point3D.create(5.3, 3.7, 1.5)
    camera.eye = adsk.core.Point3D.create(18, -12, 16)
    camera.upVector = adsk.core.Vector3D.create(0, 0, 1)
    camera.isFitView = True
    viewport.camera = camera
    viewport.refresh()
    if not viewport.saveAsImageFile(str(FOLDER / 'previews' / 'c1-oled-fusion-assembly.png'), 1600, 1100):
        raise RuntimeError('Native assembly snapshot failed')
    for name, _, occurrence in all_entries:
        occurrence.isLightBulbOn = name.startswith('C1 OLED cradle')
    camera = viewport.camera
    camera.target = adsk.core.Point3D.create(8.3, 4.9, 2.0)
    camera.eye = adsk.core.Point3D.create(13, -2, 9)
    camera.upVector = adsk.core.Vector3D.create(0, 0, 1)
    camera.isFitView = True
    viewport.camera = camera
    viewport.refresh()
    if not viewport.saveAsImageFile(str(FOLDER / 'previews' / 'c1-oled-fusion-pins.png'), 1600, 1100):
        raise RuntimeError('Native pin snapshot failed')
    for _, _, occurrence in all_entries:
        occurrence.isLightBulbOn = True
    camera = viewport.camera
    camera.target = adsk.core.Point3D.create(5.3, 3.7, 1.5)
    camera.eye = adsk.core.Point3D.create(18, -12, 16)
    camera.upVector = adsk.core.Vector3D.create(0, 0, 1)
    camera.isFitView = True
    viewport.camera = camera
    viewport.refresh()
    path = FOLDER / 'compact_c1_oled_31x28.f3d'
    if not design.exportManager.execute(design.exportManager.createFusionArchiveExportOptions(str(path))):
        raise RuntimeError('Native archive export failed')
    print('Native snapshots and local F3D exported: ' + str(path))
