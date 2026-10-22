"""Import the generated compact STEP into a separate Fusion document via MCP.

The build123d sources remain authoritative; this is an imported native mirror.
The old enclosure document is never modified or closed.
"""

from pathlib import Path
import json
import hashlib

import adsk.core
import adsk.fusion

FOLDER = Path('/Users/denisbabiichuk/3dPrint/macropad/cad/compact/c4')


def run(context):
    app = adsk.core.Application.get()
    source = FOLDER / 'compact_model.step'
    manager = app.importManager
    document = manager.importToNewDocument(manager.createSTEPImportOptions(str(source)))
    if document is None:
        raise RuntimeError('STEP import did not create a document')
    design = adsk.fusion.Design.cast(app.activeProduct)
    if design is None:
        raise RuntimeError('Imported document is not a Fusion design')
    root = design.rootComponent
    root.attributes.add('macropad_compact', 'source_sha256', hashlib.sha256(source.read_bytes()).hexdigest())
    bodies = list(root.bRepBodies)
    for occurrence in root.allOccurrences:
        bodies.extend(list(occurrence.bRepBodies))
    print(json.dumps({'document': document.name, 'source': str(source),
                      'body_count': len(bodies),
                      'body_names': [body.name for body in bodies]}))
