"""Native checks on the imported compact STEP mirror; run through Fusion MCP.

Validation does not modify the design. Export changes visibility/camera only and
writes local files; it never saves a cloud document.
"""

from pathlib import Path
import hashlib
import json

import adsk.core
import adsk.fusion

FOLDER = Path('/Users/denisbabiichuk/3dPrint/macropad/cad/compact/c4')


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
    if len(all_entries) != 42:
        raise RuntimeError('Expected 42 imported bodies')
    if any(not b.isSolid or b.lumps.count != 1 or b.volume <= 0
           for _, b, _ in all_entries):
        raise RuntimeError('Expected valid connected positive solids')
    parts = [(n, b, o) for n, b, o in all_entries if n.startswith('C4 ')]
    references = [(n, b, o) for n, b, o in all_entries if n.startswith('REFERENCE ')]
    if len(parts) != 2 or len(references) != 40:
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
    shell = next(b for n, b, _ in parts if n.startswith('C4 top shell'))
    pcb = next(b for n, b, _ in references if n.startswith('REFERENCE OLED PCB'))
    pin_centers = cylinder_centers(shell, 2.2)
    hole_centers = cylinder_centers(pcb, 2.5)
    expected = [[67.5, 35.0], [67.5, 63.0], [98.5, 35.0], [98.5, 63.0]]
    if pin_centers != expected or hole_centers != expected:
        raise RuntimeError('Measured OLED pattern mismatch: ' + str((pin_centers, hole_centers)))
    cones = [face for face in shell.faces
             if adsk.core.Cone.cast(face.geometry) is not None
             and abs(face.boundingBox.minPoint.z * 10 - 14.4) < 1e-4]
    if len(cones) != 4:
        raise RuntimeError('Expected four pin lead-in cones')
    for face in cones:
        if abs((face.boundingBox.maxPoint.z - face.boundingBox.minPoint.z) * 10 - 0.4) > 1e-4:
            raise RuntimeError('Incorrect lead-in height')
    source_facts = json.loads((FOLDER / 'validation.json').read_text())['parts']
    aliases = [('C4 top shell', 'shell'), ('C4 removable lower', 'cover')]
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
    shell = next(b for n, b, _ in parts if n.startswith('C4 top shell'))
    cover = next(b for n, b, _ in parts if n.startswith('C4 removable lower'))
    glass = next(b for n, b, _ in references if n.startswith('REFERENCE OLED glass'))
    mcu = next(b for n, b, _ in references if n.startswith('REFERENCE ESP32-S3'))
    if abs(glass.boundingBox.maxPoint.z - shell.boundingBox.maxPoint.z) * 10 > 1e-5:
        raise RuntimeError('OLED glass is not flush with shell')
    if pcb.boundingBox.maxPoint.z >= shell.boundingBox.maxPoint.z:
        raise RuntimeError('OLED PCB must be hidden inside')
    encoder_centers = cylinder_centers(shell, 7.4)
    glass_center_x = (glass.boundingBox.minPoint.x + glass.boundingBox.maxPoint.x) * 5
    if encoder_centers != [[83.0, 14.0]] or abs(glass_center_x - 83) > 1e-5:
        raise RuntimeError('Encoder and display are not aligned')
    if abs(mcu.boundingBox.minPoint.z - shell.boundingBox.maxPoint.z) > 1e-6:
        raise RuntimeError('MCU must rest directly on shell roof')
    if any('MCU seat' in n or 'strap' in n for n, _, _ in parts):
        raise RuntimeError('Unwanted MCU support')
    inside = adsk.fusion.PointContainment.PointInsidePointContainment
    roof_samples = 0
    for x in (66.0, 100.0):
        for y in (33.0, 65.0):
            free = adsk.core.Point3D.create(x / 10, y / 10, 1.65)
            roof = adsk.core.Point3D.create(x / 10, y / 10, 1.67)
            if shell.pointContainment(free) == inside or shell.pointContainment(roof) != inside:
                raise RuntimeError('OLED PCB roof relief gap is incorrect')
            roof_samples += 2
    inside = adsk.fusion.PointContainment.PointInsidePointContainment
    def contains(x, y, z):
        return shell.pointContainment(adsk.core.Point3D.create(x / 10, y / 10, z / 10)) == inside

    def aperture(x, y, z, axis, span):
        values = []
        for face in shell.faces:
            bb = face.boundingBox
            lo, hi = ((bb.minPoint.x, bb.maxPoint.x) if axis == 'x'
                      else (bb.minPoint.y, bb.maxPoint.y))
            clo, chi = ((bb.minPoint.y, bb.maxPoint.y) if axis == 'x'
                        else (bb.minPoint.x, bb.maxPoint.x))
            cross, center = (y, x) if axis == 'x' else (x, y)
            if (abs(hi - lo) < 1e-6 and abs(lo * 10 - center) < span
                    and clo * 10 - 1e-5 <= cross <= chi * 10 + 1e-5
                    and bb.minPoint.z * 10 - 1e-5 <= z <= bb.maxPoint.z * 10 + 1e-5):
                values.append(round(lo * 10, 6))
        lower = [v for v in values if v < center]
        upper = [v for v in values if v > center]
        if not lower or not upper:
            raise RuntimeError('Cannot find aperture section')
        return [max(lower), min(upper)]

    slots = []
    for x in (12.5, 27.5):
        xs = aperture(x, 13.25, 17.8, 'x', 2)
        ys = aperture(x, 13.25, 17.8, 'y', 12)
        if abs(xs[1] - xs[0] - 1.8) > 1e-5 or abs(ys[1] - ys[0] - 20.8) > 1e-5:
            raise RuntimeError('Incorrect measured ESP slot')
        slots.append({'center_x_mm': sum(xs) / 2, 'x_bounds_mm': xs, 'y_bounds_mm': ys})
    if abs(slots[1]['center_x_mm'] - slots[0]['center_x_mm'] - 15) > 1e-5:
        raise RuntimeError('ESP rows are not 15 mm center-to-center')
    switch_measurements = []
    for y in (39.0, 58.05):
        for x in (14.0, 33.05, 52.1):
            xs = aperture(x, y, 18.3, 'x', 8)
            ys = aperture(x, y, 18.3, 'y', 8)
            if abs(xs[1] - xs[0] - 14) > 1e-5 or abs(ys[1] - ys[0] - 14) > 1e-5:
                raise RuntimeError('Switch throat is not 14x14')
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                if (not contains(x + 7.025 * dx, y + 7.025 * dy, 17.35)
                        or contains(x + 7.025 * dx, y + 7.025 * dy, 17.25)):
                    raise RuntimeError('Switch clip seat is not 1.5 mm')
            switch_measurements.append({'center_xy_mm': [x, y], 'x_bounds_mm': xs, 'y_bounds_mm': ys})
    for x, y in expected:
        if not contains(x, y, 14.6) or not contains(x + 1.5, y, 16.45) or contains(x + 1.5, y, 16.35):
            raise RuntimeError('OLED pin or PCB collar contact incorrect')
    if abs((cover.boundingBox.maxPoint.z - cover.boundingBox.minPoint.z) * 10 - 2.4) > 1e-5:
        raise RuntimeError('Lower cover still has unwanted columns')
    source_report = json.loads((FOLDER / 'validation.json').read_text())
    wx = sum(source_report['oled']['window_x_bounds_mm']) / 2
    wy = sum(source_report['oled']['window_y_bounds_mm']) / 2
    window_x = aperture(wx, wy, 18.3, 'x', 20)
    window_y = aperture(wx, wy, 18.3, 'y', 15)
    if window_x != source_report['oled']['window_x_bounds_mm'] or window_y != source_report['oled']['window_y_bounds_mm']:
        raise RuntimeError('Native OLED window differs from checked source')
    report = {'revision': 'C4 physical fit updates', 'fusion_mcp_validated': True,
              'source_step_sha256': source_hash, 'imported_body_count': len(all_entries),
              'native_pair_checks': checks, 'positive_volume_collisions': collisions,
              'parts': native_parts, 'switch_measurements': switch_measurements,
              'switch_clip_seat_mm': 1.5,
              'oled': {'centers_xy_mm': pin_centers, 'hole_diameter_mm': 2.5,
                       'pin_diameter_mm': 2.2, 'lead_height_mm': 0.4,
                       'glass_flush_with_shell': True, 'pcb_hidden_inside': True,
                       'window_x_bounds_mm': window_x, 'window_y_bounds_mm': window_y,
                       'mount': 'integral roof collars and downward pins; adhesive from below'},
              'mcu_slots': slots, 'mcu_row_spacing_mm': 15.0,
              'mcu_supports': False, 'separate_oled_frame': False,
              'limits': source_report['limits']}
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
    camera.target = adsk.core.Point3D.create(5.0, 4.1, 1.5)
    camera.eye = adsk.core.Point3D.create(18, 18, 16)
    camera.upVector = adsk.core.Vector3D.create(0, 0, 1)
    camera.isFitView = True
    viewport.camera = camera
    viewport.refresh()
    if not viewport.saveAsImageFile(str(FOLDER / 'previews' / 'c4-fusion-assembly.png'), 1600, 1100):
        raise RuntimeError('Native assembly snapshot failed')
    for name, _, occurrence in all_entries:
        occurrence.isLightBulbOn = name.startswith('C4 top shell')
    camera = viewport.camera
    camera.target = adsk.core.Point3D.create(7.5, 2.2, 1.5)
    camera.eye = adsk.core.Point3D.create(13, -4, -9)
    camera.upVector = adsk.core.Vector3D.create(0, 0, 1)
    camera.isFitView = True
    viewport.camera = camera
    viewport.refresh()
    if not viewport.saveAsImageFile(str(FOLDER / 'previews' / 'c4-fusion-oled-mounts.png'), 1600, 1100):
        raise RuntimeError('Native pin snapshot failed')
    for _, _, occurrence in all_entries:
        occurrence.isLightBulbOn = True
    camera = viewport.camera
    camera.target = adsk.core.Point3D.create(5.0, 4.1, 1.5)
    camera.eye = adsk.core.Point3D.create(18, 18, 16)
    camera.upVector = adsk.core.Vector3D.create(0, 0, 1)
    camera.isFitView = True
    viewport.camera = camera
    viewport.refresh()
    path = FOLDER / 'compact_c4_fit.f3d'
    if not design.exportManager.execute(design.exportManager.createFusionArchiveExportOptions(str(path))):
        raise RuntimeError('Native archive export failed')
    print('Native snapshots and local F3D exported: ' + str(path))
