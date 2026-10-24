"""Import and check a separate native Fusion mirror, preserving the C4 design."""
from pathlib import Path
import hashlib
import json
import adsk.core
import adsk.fusion

FOLDER = Path('/Users/denisbabiichuk/3dPrint/macropad/cad/compact/accessories/rear_feet')


def run(context):
    app = adsk.core.Application.get()
    source = FOLDER / 'fitted_case.step'
    document = app.importManager.importToNewDocument(app.importManager.createSTEPImportOptions(str(source)))
    if document is None:
        raise RuntimeError('Failed to create feet assembly document')
    design = adsk.fusion.Design.cast(app.activeProduct)
    if design is None:
        raise RuntimeError('Imported document is not a Fusion design')
    digest = hashlib.sha256(source.read_bytes()).hexdigest()
    design.rootComponent.attributes.add('macropad_feet', 'source_sha256', digest)
    entries = [(o.component.name, b) for o in design.rootComponent.allOccurrences for b in o.bRepBodies]
    if len(entries) != 14 or any(not b.isSolid or b.lumps.count != 1 or b.volume <= 0 for _, b in entries):
        raise RuntimeError('Expected 14 positive single-solid bodies')
    manager = adsk.fusion.TemporaryBRepManager.get()
    collisions, checks = [], 0
    for index, (name, body) in enumerate(entries):
        for other_name, other in entries[index + 1:]:
            checks += 1
            common = manager.copy(body)
            if not manager.booleanOperation(common, manager.copy(other),
                                            adsk.fusion.BooleanTypes.IntersectionBooleanType):
                raise RuntimeError('Native intersection failed')
            if abs(common.volume) * 1000 > 1e-5:
                collisions.append([name, other_name, common.volume * 1000])
    if collisions:
        raise RuntimeError(json.dumps(collisions))
    pads = [b for n, b in entries if n.startswith('REFERENCE rubber pad')]
    feet = [(n, b) for n, b in entries if 'wedge foot' in n]
    heads = [b for n, b in entries if n.startswith('REFERENCE existing screw head')]
    if len(pads) != 4 or len(feet) != 4 or len(heads) != 4:
        raise RuntimeError('Incorrect assembly grouping')
    pad_floor = [b.boundingBox.minPoint.z * 10 for b in pads]
    if any(abs(z) > 1e-4 for z in pad_floor):
        raise RuntimeError('Pads do not touch a common desk plane')
    if any(b.boundingBox.minPoint.z * 10 < -1e-4 for _, b in entries):
        raise RuntimeError('Body extends through the desk')
    source_report = json.loads((FOLDER / 'validation.json').read_text())
    pocket_counts = []
    for name, body in feet:
        expected = source_report['parts']['front_foot' if name.startswith('Front') else 'rear_foot']['volume_mm3']
        if abs(body.volume * 1000 - expected) > 0.01:
            raise RuntimeError('Native foot volume differs from source')
        cylinders = [adsk.core.Cylinder.cast(f.geometry) for f in body.faces]
        pockets = [c for c in cylinders if c is not None and abs(c.radius * 20 - 10.3) < 1e-5]
        if len(pockets) != 1 or abs(abs(pockets[0].axis.z) - 1) > 1e-5:
            raise RuntimeError('Pad seat diameter/orientation differs')
        pocket_counts.append(len(pockets))
    head_floor = min(b.boundingBox.minPoint.z * 10 for b in heads)
    if head_floor < 0.4:
        raise RuntimeError('Screw heads are too close to desk')
    report = {'fusion_mcp_validated': True, 'source_step_sha256': digest,
              'body_count': len(entries), 'intersection_checks': checks,
              'collisions': collisions, 'pad_floor_z_mm': pad_floor,
              'four_pad_seats_diameter_mm': 10.3,
              'screw_head_floor_min_clearance_mm': head_floor,
              'source_angle_deg': source_report['angle_deg']}
    (FOLDER / 'fusion-validation.json').write_text(json.dumps(report, indent=2) + '\n')
    camera = app.activeViewport.camera
    camera.target = adsk.core.Point3D.create(5.3, 3.7, 1.2)
    camera.eye = adsk.core.Point3D.create(19, 18, 10)
    camera.upVector = adsk.core.Vector3D.create(0, 0, 1)
    camera.isFitView = True
    app.activeViewport.camera = camera
    app.activeViewport.refresh()
    if not app.activeViewport.saveAsImageFile(str(FOLDER / 'previews' / 'fusion-feet-assembly.png'), 1600, 1100):
        raise RuntimeError('Native screenshot failed')
    archive = FOLDER / 'c4_with_rubber_feet.f3d'
    if not design.exportManager.execute(design.exportManager.createFusionArchiveExportOptions(str(archive))):
        raise RuntimeError('Local Fusion archive failed')
    print(json.dumps(report))
