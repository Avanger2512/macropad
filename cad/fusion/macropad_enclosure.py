"""Build the first enclosure draft in the active, empty Fusion Part Design.

Run through Fusion MCP's script operation. The native Fusion document remains
the editable design. This script does not save or close the cloud document.
Mounting bosses, USB access and hot-swap contact depth are intentionally pending
physical measurements. All feature names and comments are English.
"""

import json
import adsk.core
import adsk.fusion


PARAMETERS = (
    ("caseWidth", "80 mm", "mm", "Exterior width"),
    ("caseLength", "115 mm", "mm", "Horizontal front-to-rear footprint"),
    ("caseTilt", "5 deg", "deg", "Rear-up face angle; provisional"),
    ("frontHeight", "22 mm", "mm", "Draft height, to be checked against electronics"),
    ("rearHeight", "frontHeight + caseLength * tan(caseTilt)", "mm", "Rear height"),
    ("shellWall", "2.4 mm", "mm", "Draft shell thickness"),
    ("bottomThickness", "2 mm", "mm", "Service cover thickness"),
    ("carrierThickness", "1.5 mm", "mm", "Local switch clip seating thickness"),
    ("carrierClearance", "0.4 mm", "mm", "Draft carrier clearance"),
    ("carrierRim", "4 mm", "mm", "Carrier frame width"),
    ("keycapSize", "18 mm", "mm", "Confirmed square keycap size"),
    ("layoutGap", "(caseWidth - 3 * keycapSize) / 4", "mm", "Equal visible horizontal gaps"),
    ("keyPitch", "keycapSize + layoutGap", "mm", "Equal row and column pitch"),
    ("switchOpening", "14.1 mm", "mm", "Draft opening; coupon verification required"),
    ("upperSwitchOpening", "16.2 mm", "mm", "Draft outer trim clearance"),
    ("displayWidth", "34.5 mm", "mm", "User-supplied window width"),
    ("displayHeight", "18.5 mm", "mm", "User-supplied window height"),
    ("encoderKnobDiameter", "20 mm", "mm", "Placeholder; actual knob diameter required"),
    ("encoderHole", "7 mm", "mm", "User-supplied provisional opening; verify bushing"),
    ("ledWidth", "67 mm", "mm", "User-supplied strip width"),
    ("ledHeight", "10 mm", "mm", "Initial diffuser opening height"),
    ("diffuserClearance", "0.2 mm", "mm", "Per-edge draft fit clearance"),
    ("diffuserFlange", "1.5 mm", "mm", "Retaining flange extension per side"),
    ("diffuserFlangeThickness", "1 mm", "mm", "Retaining flange thickness"),
    ("flangePocketClearance", "0.2 mm", "mm", "Carrier pocket clearance around diffuser flange"),
    ("carrierBayWidth", "min(caseWidth - 2 * (shellWall + carrierClearance + carrierRim); ledWidth - 2 * diffuserClearance + 2 * diffuserFlange - 2 mm)", "mm", "Electronics opening preserving diffuser support rails"),
    ("faceLength", "caseLength / cos(caseTilt)", "mm", "Length measured in the inclined face"),
    ("faceOriginV", "frontHeight * sin(caseTilt)", "mm", "Inclined sketch origin correction"),
    ("carrierFaceLength", "faceLength - 2 * (shellWall + carrierClearance) / cos(caseTilt) - carrierThickness * tan(caseTilt)", "mm", "Carrier length allowing normal extrusion clearance"),
    ("controlHeight", "max(displayHeight; encoderKnobDiameter)", "mm", "Visible controls row height"),
    ("contentLength", "2 * keycapSize + 3 * layoutGap + controlHeight + ledHeight", "mm", "Visible layout stack"),
    ("verticalMargin", "(faceLength - contentLength) / 2", "mm", "Balanced front and rear margins"),
    ("keyRowOne", "verticalMargin + keycapSize / 2", "mm", "Front key row center"),
    ("keyRowTwo", "keyRowOne + keyPitch", "mm", "Rear key row center"),
    ("controlCenter", "keyRowTwo + keycapSize / 2 + layoutGap + controlHeight / 2", "mm", "Display and encoder center"),
    ("ledCenter", "controlCenter + controlHeight / 2 + layoutGap + ledHeight / 2", "mm", "LED opening center"),
    ("encoderCenterX", "(layoutGap + displayWidth + caseWidth) / 2", "mm", "Centered in the area right of the display"),
)


def value(expression):
    return adsk.core.ValueInput.createByString(expression)


def point(x, y, z=0):
    return adsk.core.Point3D.create(x, y, z)


def evaluate(design, expression):
    return design.unitsManager.evaluateExpression(expression, "cm")


def constrain_point(sketch, target, x_expr, y_expr):
    """Dimension a sketch point to the origin without zero-length dimensions."""
    origin = sketch.originPoint
    x, y = target.geometry.x, target.geometry.y
    gc = sketch.geometricConstraints
    dims = sketch.sketchDimensions
    if abs(x) < 1e-7 and abs(y) < 1e-7:
        gc.addCoincident(target, origin)
        return
    if abs(x) < 1e-7:
        gc.addVerticalPoints(origin, target)
    else:
        d = dims.addDistanceDimension(origin, target,
            adsk.fusion.DimensionOrientations.HorizontalDimensionOrientation,
            point(x / 2, y + 0.4))
        d.parameter.expression = x_expr if x > 0 else f"-({x_expr})"
    if abs(y) < 1e-7:
        gc.addHorizontalPoints(origin, target)
    else:
        d = dims.addDistanceDimension(origin, target,
            adsk.fusion.DimensionOrientations.VerticalDimensionOrientation,
            point(x + 0.4, y / 2))
        d.parameter.expression = y_expr if y > 0 else f"-({y_expr})"


def polygon(design, root, plane, name, expressions, world_yz=False):
    sketch = root.sketches.add(plane)
    sketch.name = name
    if world_yz:
        p0 = sketch.modelToSketchSpace(point(0, 0, 0))
        py = sketch.modelToSketchSpace(point(0, 1, 0))
        pz = sketch.modelToSketchSpace(point(0, 0, 1))
        transformed = []
        for ey, ez in expressions:
            ex = f"({py.x-p0.x:.0f}) * ({ey}) + ({pz.x-p0.x:.0f}) * ({ez})"
            sy = f"({py.y-p0.y:.0f}) * ({ey}) + ({pz.y-p0.y:.0f}) * ({ez})"
            transformed.append((ex, sy))
        expressions = transformed
    coords = [point(evaluate(design, x), evaluate(design, y)) for x, y in expressions]
    lines = sketch.sketchCurves.sketchLines
    first = lines.addByTwoPoints(coords[0], coords[1])
    vertices = [first.startSketchPoint, first.endSketchPoint]
    last = first.endSketchPoint
    for coord in coords[2:]:
        line = lines.addByTwoPoints(last, coord)
        last = line.endSketchPoint
        vertices.append(last)
    lines.addByTwoPoints(last, first.startSketchPoint)
    # Anchor one corner and dimension independent side lengths. Dimensioning
    # every vertex separately gives redundant constraints in Fusion's solver.
    edges = list(lines)
    for i, edge in enumerate(edges):
        a, b = coords[i], coords[(i+1) % len(coords)]
        if abs(a.x-b.x) < 1e-7:
            sketch.geometricConstraints.addVertical(edge)
        elif abs(a.y-b.y) < 1e-7:
            sketch.geometricConstraints.addHorizontal(edge)
    constrain_point(sketch, vertices[0], *expressions[0])
    for i in ((0, 1, 3) if world_yz else (0, 1)):
        j = (i+1) % len(coords)
        axis = 0 if abs(coords[j].x-coords[i].x) > 1e-7 else 1
        delta = (coords[j].x-coords[i].x) if axis == 0 else (coords[j].y-coords[i].y)
        expr = f"({expressions[j][axis]}) - ({expressions[i][axis]})"
        if delta < 0:
            expr = f"-({expr})"
        dim = sketch.sketchDimensions.addDistanceDimension(edges[i].startSketchPoint,
            edges[i].endSketchPoint, adsk.fusion.DimensionOrientations.AlignedDimensionOrientation,
            point(coords[i].x+0.4, coords[i].y+0.4))
        dim.parameter.expression = expr
    if sketch.profiles.count != 1:
        raise RuntimeError(f"Expected one closed profile: {name}")
    return sketch


def rectangle(design, root, plane, name, left, bottom, width, height):
    if plane.name in ("Exterior face datum", "Carrier seating datum", "Diffuser flange datum"):
        bottom = f"({bottom}) + faceOriginV"
    return polygon(design, root, plane, name, (
        (left, bottom), (f"({left}) + ({width})", bottom),
        (f"({left}) + ({width})", f"({bottom}) + ({height})"),
        (left, f"({bottom}) + ({height})")))


def extrude(root, sketch, name, distance, operation, positive=True, body=None):
    features = root.features.extrudeFeatures
    inp = features.createInput(sketch.profiles.item(0), operation)
    extent = adsk.fusion.DistanceExtentDefinition.create(value(distance))
    direction = (adsk.fusion.ExtentDirections.PositiveExtentDirection if positive
        else adsk.fusion.ExtentDirections.NegativeExtentDirection)
    inp.setOneSideExtent(extent, direction)
    if body is not None:
        inp.participantBodies = [body]
    feature = features.add(inp)
    feature.name = name
    sketch.isVisible = False
    return feature


def offset(root, reference, name, distance):
    inp = root.constructionPlanes.createInput()
    inp.setByOffset(reference, value(distance))
    plane = root.constructionPlanes.add(inp)
    plane.name = name
    plane.isLightBulbOn = False
    return plane


def run(_context: str):
    app = adsk.core.Application.get()
    design = adsk.fusion.Design.cast(app.activeProduct)
    if design is None or app.activeDocument.name != "macropad":
        raise RuntimeError("Activate the intended macropad Fusion design")
    root = design.rootComponent
    if root.bRepBodies.count or root.sketches.count or root.occurrences.count:
        raise RuntimeError("Initial generator only runs in an empty design; no existing work was changed")
    for name, expression, units, comment in PARAMETERS:
        if design.userParameters.itemByName(name) is None:
            design.userParameters.add(name, value(expression), units, comment)
    if evaluate(design, "verticalMargin") <= 0:
        raise RuntimeError("Visible controls do not fit the selected face length")
    new = adsk.fusion.FeatureOperations.NewBodyFeatureOperation
    cut = adsk.fusion.FeatureOperations.CutFeatureOperation
    join = adsk.fusion.FeatureOperations.JoinFeatureOperation

    side = polygon(design, root, root.yZConstructionPlane, "Upper shell side profile", (
        ("0 mm", "bottomThickness"), ("caseLength", "bottomThickness"),
        ("caseLength", "rearHeight"), ("0 mm", "frontHeight")), world_yz=True)
    yz_positive = root.yZConstructionPlane.geometry.normal.x > 0
    upper = extrude(root, side, "Upper shell wedge", "caseWidth", new, yz_positive).bodies.item(0)
    upper.name = "UpperShell_Draft"
    bottom_faces = [f for f in upper.faces
        if abs(f.boundingBox.maxPoint.z - evaluate(design, "bottomThickness")) < 1e-6
        and abs(f.boundingBox.minPoint.z - evaluate(design, "bottomThickness")) < 1e-6]
    if len(bottom_faces) != 1:
        raise RuntimeError("Could not identify the wedge bottom for shelling")
    faces = adsk.core.ObjectCollection.create()
    faces.add(bottom_faces[0])
    shell_input = root.features.shellFeatures.createInput(faces, False)
    shell_input.insideThickness = value("shellWall")
    root.features.shellFeatures.add(shell_input).name = "Open-bottom exterior shell"

    angle_input = root.constructionPlanes.createInput()
    angle_input.setByAngle(root.xConstructionAxis, value("caseTilt"), root.xYConstructionPlane)
    angle_plane = root.constructionPlanes.add(angle_input)
    angle_plane.name = "Face angle datum"
    angle_plane.isLightBulbOn = False
    face_plane = offset(root, angle_plane, "Exterior face datum", "frontHeight * cos(caseTilt)")
    carrier_plane = offset(root, face_plane, "Carrier seating datum", "-(shellWall + carrierClearance)")

    board = rectangle(design, root, carrier_plane, "Middle carrier outline",
        "shellWall + carrierClearance", "(shellWall + carrierClearance) / cos(caseTilt) - (shellWall + carrierClearance) * tan(caseTilt)",
        "caseWidth - 2 * (shellWall + carrierClearance)",
        "carrierFaceLength")
    carrier = extrude(root, board, "Middle carrier plate", "carrierThickness", new, False).bodies.item(0)
    carrier.name = "MiddleCarrier_Draft"
    rear_opening = rectangle(design, root, carrier_plane, "Carrier rear access opening",
        "(caseWidth - carrierBayWidth) / 2", "keyRowTwo + keycapSize / 2 + layoutGap / 2",
        "carrierBayWidth",
        "faceLength - (shellWall + carrierClearance) / cos(caseTilt) - (shellWall + carrierClearance + carrierThickness) * tan(caseTilt) - carrierRim - (keyRowTwo + keycapSize / 2 + layoutGap / 2)")
    extrude(root, rear_opening, "Open carrier electronics bay", "carrierThickness + 1 mm", cut, False, carrier)

    for row, cy in enumerate(("keyRowOne", "keyRowTwo")):
        for col in range(3):
            cx = f"layoutGap + keycapSize / 2 + {col} * keyPitch"
            label = f"SW{row*3+col+1}"
            for plane, size, target, prefix, depth in (
                (carrier_plane, "switchOpening", carrier, "Seat", "carrierThickness + 1 mm"),
                (face_plane, "upperSwitchOpening", upper, "Trim", "shellWall + 1 mm")):
                opening = rectangle(design, root, plane, f"{label} {prefix} profile",
                    f"({cx}) - {size} / 2", f"({cy}) - {size} / 2", size, size)
                extrude(root, opening, f"{label} {prefix} opening", depth, cut, False, target)

    led = rectangle(design, root, face_plane, "LED diffuser opening profile",
        "(caseWidth - ledWidth) / 2", "ledCenter - ledHeight / 2", "ledWidth", "ledHeight")
    extrude(root, led, "LED diffuser opening", "shellWall + 1 mm", cut, False, upper)
    display = rectangle(design, root, face_plane, "OLED window profile", "layoutGap",
        "controlCenter - displayHeight / 2", "displayWidth", "displayHeight")
    extrude(root, display, "OLED window", "shellWall + 1 mm", cut, False, upper)
    encoder = root.sketches.add(face_plane)
    encoder.name = "Encoder provisional bushing profile"
    circle = encoder.sketchCurves.sketchCircles.addByCenterRadius(
        point(evaluate(design, "encoderCenterX"), evaluate(design, "controlCenter + faceOriginV")),
        evaluate(design, "encoderHole") / 2)
    constrain_point(encoder, circle.centerSketchPoint, "encoderCenterX", "controlCenter + faceOriginV")
    encoder.sketchDimensions.addDiameterDimension(circle,
        point(evaluate(design, "encoderCenterX") + 1, evaluate(design, "controlCenter + faceOriginV"))).parameter.expression = "encoderHole"
    extrude(root, encoder, "Encoder provisional opening", "shellWall + 1 mm", cut, False, upper)

    lid_sketch = rectangle(design, root, root.xYConstructionPlane, "Bottom cover outline",
        "0 mm", "0 mm", "caseWidth", "caseLength")
    lid = extrude(root, lid_sketch, "Bottom service cover", "bottomThickness", new).bodies.item(0)
    lid.name = "BottomCover_Draft"

    plug_sketch = rectangle(design, root, face_plane, "Diffuser flush plug profile",
        "(caseWidth - ledWidth) / 2 + diffuserClearance",
        "ledCenter - ledHeight / 2 + diffuserClearance",
        "ledWidth - 2 * diffuserClearance", "ledHeight - 2 * diffuserClearance")
    diffuser = extrude(root, plug_sketch, "Diffuser flush plug", "shellWall", new, False).bodies.item(0)
    diffuser.name = "Diffuser_Draft"
    flange_plane = offset(root, face_plane, "Diffuser flange datum", "-shellWall")
    flange = rectangle(design, root, flange_plane, "Diffuser retaining flange profile",
        "(caseWidth - ledWidth) / 2 + diffuserClearance - diffuserFlange",
        "ledCenter - ledHeight / 2 + diffuserClearance - diffuserFlange",
        "ledWidth - 2 * diffuserClearance + 2 * diffuserFlange",
        "ledHeight - 2 * diffuserClearance + 2 * diffuserFlange")
    extrude(root, flange, "Diffuser retaining flange", "diffuserFlangeThickness", join, False, diffuser)
    pocket = rectangle(design, root, carrier_plane, "Diffuser flange carrier pocket profile",
        "(caseWidth - ledWidth) / 2 + diffuserClearance - diffuserFlange - flangePocketClearance",
        "ledCenter - ledHeight / 2 + diffuserClearance - diffuserFlange - flangePocketClearance",
        "ledWidth - 2 * diffuserClearance + 2 * diffuserFlange + 2 * flangePocketClearance",
        "ledHeight - 2 * diffuserClearance + 2 * diffuserFlange + 2 * flangePocketClearance")
    extrude(root, pocket, "Diffuser flange carrier recess",
        "diffuserFlangeThickness - carrierClearance + flangePocketClearance", cut, False, carrier)

    for row, row_y in enumerate(("keyRowOne", "keyRowTwo")):
        for col in range(3):
            guide = rectangle(design, root, face_plane, f"SW{row*3+col+1} keycap envelope",
                f"layoutGap + {col} * keyPitch", f"{row_y} - keycapSize / 2", "keycapSize", "keycapSize")
            for line in guide.sketchCurves.sketchLines:
                line.isConstruction = True
            guide.isVisible = True
    guides = root.sketches.add(face_plane)
    guides.name = "Encoder knob envelope - provisional diameter"
    knob = guides.sketchCurves.sketchCircles.addByCenterRadius(
        point(evaluate(design, "encoderCenterX"), evaluate(design, "controlCenter + faceOriginV")),
        evaluate(design, "encoderKnobDiameter") / 2)
    constrain_point(guides, knob.centerSketchPoint, "encoderCenterX", "controlCenter + faceOriginV")
    guides.sketchDimensions.addDiameterDimension(knob,
        point(evaluate(design, "encoderCenterX") + 1, evaluate(design, "controlCenter + faceOriginV"))).parameter.expression = "encoderKnobDiameter"
    knob.isConstruction = True
    guides.isVisible = True
    design.computeAll()
    if root.bRepBodies.count != 4 or any(not b.isSolid or b.volume <= 0 for b in root.bRepBodies):
        raise RuntimeError("Expected four positive-volume draft solids")
    app.activeViewport.fit()
    print(json.dumps({"document":app.activeDocument.name,"bodies":[b.name for b in root.bRepBodies],
        "parameters":design.userParameters.count,"keyPitch_mm":evaluate(design,"keyPitch")*10,
        "gap_mm":evaluate(design,"layoutGap")*10,"frontHeight_mm":evaluate(design,"frontHeight")*10,
        "rearHeight_mm":evaluate(design,"rearHeight")*10,"status":"Draft: mounting, USB and contact depth pending"}))
