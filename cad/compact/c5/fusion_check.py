"""Native Fusion import, seat verification and local archive of integral cover."""
import json
from pathlib import Path
import adsk.core
import adsk.fusion


def run(context):
    folder = Path('/Users/denisbabiichuk/3dPrint/macropad/cad/compact/c5')
    app = adsk.core.Application.get()
    app.importManager.importToNewDocument(app.importManager.createSTEPImportOptions(str(folder / 'top_shell.step')))
    design = adsk.fusion.Design.cast(app.activeProduct)
    root = design.rootComponent
    bodies = list(root.bRepBodies)
    bodies += [b for o in root.allOccurrences for b in o.bRepBodies]
    assert len(bodies) == 1 and bodies[0].isSolid and bodies[0].lumps.count == 1
    body = bodies[0]
    pockets = []
    for face in body.faces:
        cyl = adsk.core.Cylinder.cast(face.geometry)
        if cyl and abs(cyl.radius * 20 - 2.2) < 1e-5:
            pockets.append(cyl)
    assert len(pockets) == 4
    bbox = body.boundingBox
    dimensions = [(getattr(bbox.maxPoint, a)-getattr(bbox.minPoint,a))*10 for a in ('x','y','z')]
    assert abs(dimensions[0]-106) < 1e-4 and abs(dimensions[1]-74) < 1e-4
    assert abs(bbox.minPoint.z*10 - 2.4) < 1e-5
    report = {'fusion_mcp_validated':True, 'solid_count':1,'oled_pin_shafts':4,'shaft_diameter_mm':2.2,'dimensions_mm':dimensions,'volume_mm3':body.volume*1000}
    (folder/'fusion-validation.json').write_text(json.dumps(report,indent=2)+'\n')
    app.activeViewport.fit()
    assert design.exportManager.execute(design.exportManager.createFusionArchiveExportOptions(str(folder/'top_shell.f3d')))
    print(json.dumps(report))
