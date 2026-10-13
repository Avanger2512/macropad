"""Add draft carrier reinforcement and independent fasteners to iteration 1.

Execute in the existing macropad Fusion document using Fusion MCP.
Insert pilots are provisional and require a printed coupon.
The source includes the initial generator helpers for standalone execution.
It adds 19 mount parameters and expands the existing carrier rim to 7 mm.
No PCB supports, USB cutout or hot-swap contact seat is finalized here.
"""

import json
import adsk.core
import adsk.fusion



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


MOUNT_PARAMETERS = (
    ("mountSideX", "4.8 mm", "mm", "Carrier fastener center from side"),
    ("mountFrontV", "8 mm", "mm", "Front fastener center in face coordinates"),
    ("mountRearV", "faceLength - 8.4 mm", "mm", "Rear fastener center in face coordinates"),
    ("mountBossDiameter", "7 mm", "mm", "Wall-connected M2 boss diameter"),
    ("insertLength", "4 mm", "mm", "Confirmed M2 insert length"),
    ("insertOuterDiameter", "3.5 mm", "mm", "Confirmed M2 insert outer diameter"),
    ("insertPilotDiameter", "3.2 mm", "mm", "Provisional PLA pilot; test coupon required"),
    ("insertPilotDepth", "insertLength + 0.5 mm", "mm", "Blind insert pocket depth"),
    ("carrierBossDepth", "7.4 mm", "mm", "Shell boss bottom below exterior face"),
    ("carrierPadDepth", "10 mm", "mm", "Carrier pad bottom below exterior face"),
    ("mountPocketClearance", "0.3 mm + (carrierBossDepth - shellWall - carrierClearance) * tan(caseTilt)", "mm", "Radial clearance allowing vertical removal past inclined bosses"),
    ("mountPadWidth", "7.8 mm", "mm", "Carrier mounting pad width"),
    ("mountPadLength", "9.4 mm", "mm", "Carrier mounting pad length"),
    ("m2Clearance", "2.3 mm", "mm", "Draft M2 screw clearance"),
    ("bottomBossHeight", "6 mm", "mm", "Independent cover boss height above lid"),
    ("bottomBossDiameter", "6 mm", "mm", "Cover boss diameter; corner insertion relief"),
    ("bottomReliefClearance", "0.2 mm", "mm", "Radial clearance for carrier removal past cover bosses"),
    ("carrierRibWidth", "2 mm", "mm", "Switch-field reinforcing rib width"),
    ("carrierRibDepth", "3 mm", "mm", "Reinforcement below switch plate"),
)


def circle_profile(design, root, plane, name, cx, cy, diameter):
    sketch = root.sketches.add(plane)
    sketch.name = name
    if plane.name != "Bottom boss seat datum":
        cy = f"({cy}) + faceOriginV"
    x, y = evaluate(design, cx), evaluate(design, cy)
    circle = sketch.sketchCurves.sketchCircles.addByCenterRadius(
        point(x, y), evaluate(design, diameter) / 2)
    constrain_point(sketch, circle.centerSketchPoint, cx, cy)
    sketch.sketchDimensions.addDiameterDimension(circle, point(x + 0.6, y + 0.6)).parameter.expression = diameter
    return sketch


def check_design(design, root):
    design.computeAll()
    issues = [t.name for t in design.timeline
        if t.healthState != adsk.fusion.FeatureHealthStates.HealthyFeatureHealthState]
    if issues:
        raise RuntimeError(f"Unhealthy features: {issues}")
    if root.bRepBodies.count != 4 or any(not b.isSolid or b.volume <= 0 for b in root.bRepBodies):
        raise RuntimeError("Expected four connected, positive-volume bodies")
    bodies = adsk.core.ObjectCollection.create()
    for body in root.bRepBodies:
        bodies.add(body)
    inp = design.createInterferenceInput(bodies)
    inp.areCoincidentFacesIncluded = False
    collisions = design.analyzeInterference(inp)
    if collisions.count:
        raise RuntimeError("Enclosure body interference")
    if any(not s.isFullyConstrained for s in root.sketches):
        raise RuntimeError("Unconstrained sketch")


def run(_context: str):
    app = adsk.core.Application.get()
    design = adsk.fusion.Design.cast(app.activeProduct)
    if design is None or app.activeDocument.name != "macropad":
        raise RuntimeError("Activate the intended macropad design")
    root = design.rootComponent
    if design.userParameters.itemByName("carrierBossDepth"):
        raise RuntimeError("Iteration 2 already exists; edit its parameters instead")
    check_design(design, root)
    for name, expression, units, comment in MOUNT_PARAMETERS:
        design.userParameters.add(name, value(expression), units, comment)
    design.userParameters.itemByName("carrierRim").expression = "7 mm"
    upper = root.bRepBodies.itemByName("UpperShell_Draft")
    carrier = root.bRepBodies.itemByName("MiddleCarrier_Draft")
    lid = root.bRepBodies.itemByName("BottomCover_Draft")
    if upper is None or carrier is None or lid is None:
        raise RuntimeError("Draft body names do not match")
    face = root.constructionPlanes.itemByName("Exterior face datum")
    carrier_plane = root.constructionPlanes.itemByName("Carrier seating datum")
    boss_bottom = offset(root, face, "Carrier insert entry datum", "-carrierBossDepth")
    pocket_bottom = offset(root, face, "Carrier boss clearance datum", "-(carrierBossDepth + carrierClearance)")
    bottom_seat = offset(root, root.xYConstructionPlane, "Bottom boss seat datum", "bottomThickness")
    join = adsk.fusion.FeatureOperations.JoinFeatureOperation
    cut = adsk.fusion.FeatureOperations.CutFeatureOperation
    for row, cy in enumerate(("mountFrontV", "mountRearV")):
        for col, cx in enumerate(("mountSideX", "caseWidth - mountSideX")):
            label = f"M{row * 2 + col + 1}"
            boss = circle_profile(design, root, face, f"{label} carrier shell boss profile", cx, cy, "mountBossDiameter")
            extrude(root, boss, f"{label} carrier shell boss", "carrierBossDepth", join, False, upper)
            pilot = circle_profile(design, root, boss_bottom, f"{label} carrier insert pilot profile", cx, cy, "insertPilotDiameter")
            extrude(root, pilot, f"{label} carrier insert pilot", "insertPilotDepth", cut, True, upper)
            left = "shellWall + carrierClearance" if col == 0 else "caseWidth - shellWall - carrierClearance - mountPadWidth"
            pad = rectangle(design, root, carrier_plane, f"{label} carrier mounting pad profile", left,
                f"({cy}) - mountPadLength / 2", "mountPadWidth", "mountPadLength")
            extrude(root, pad, f"{label} reinforced carrier pad", "carrierPadDepth - shellWall - carrierClearance", join, False, carrier)
            pocket = circle_profile(design, root, pocket_bottom, f"{label} carrier boss clearance profile", cx, cy,
                "mountBossDiameter + 2 * mountPocketClearance")
            extrude(root, pocket, f"{label} carrier boss clearance", "carrierBossDepth + carrierClearance", cut, True, carrier)
            hole = circle_profile(design, root, carrier_plane, f"{label} carrier screw profile", cx, cy, "m2Clearance")
            extrude(root, hole, f"{label} carrier screw clearance", "carrierPadDepth", cut, False, carrier)
            # Cover screws run vertically; the carrier screws are normal to the face.
            bx = "20 mm" if col == 0 else "caseWidth - 20 mm"
            if row == 1:
                bx = cx
            by = "4.8 mm" if row == 0 else "caseLength - 3 mm"
            lower_boss = circle_profile(design, root, bottom_seat, f"{label} bottom shell boss profile", bx, by, "bottomBossDiameter")
            extrude(root, lower_boss, f"{label} independent bottom boss", "bottomBossHeight", join, True, upper)
            lower_pilot = circle_profile(design, root, bottom_seat, f"{label} bottom insert pilot profile", bx, by, "insertPilotDiameter")
            extrude(root, lower_pilot, f"{label} bottom insert pilot", "insertPilotDepth", cut, True, upper)
            lid_hole = circle_profile(design, root, bottom_seat, f"{label} bottom cover screw profile", bx, by, "m2Clearance")
            extrude(root, lid_hole, f"{label} bottom cover screw clearance", "bottomThickness + 0.5 mm", cut, False, lid)
            relief = circle_profile(design, root, bottom_seat, f"{label} carrier vertical removal relief profile", bx, by,
                "bottomBossDiameter + 2 * bottomReliefClearance")
            extrude(root, relief, f"{label} carrier vertical removal relief", "rearHeight + 1 mm", cut, True, carrier)
    for col in range(2):
        center = f"layoutGap + keycapSize / 2 + ({col} + 0.5) * keyPitch"
        rib = rectangle(design, root, carrier_plane, f"Switch column rib {col + 1} profile",
            f"({center}) - carrierRibWidth / 2", "mountFrontV + mountPadLength / 2",
            "carrierRibWidth", "keyRowTwo + keycapSize / 2 + 1 mm - mountFrontV - mountPadLength / 2")
        extrude(root, rib, f"Switch column reinforcement {col + 1}", "carrierThickness + carrierRibDepth", join, False, carrier)
    rib = rectangle(design, root, carrier_plane, "Switch row rib profile", "10 mm",
        "(keyRowOne + keyRowTwo) / 2 - carrierRibWidth / 2", "caseWidth - 20 mm", "carrierRibWidth")
    extrude(root, rib, "Switch row reinforcement", "carrierThickness + carrierRibDepth", join, False, carrier)
    check_design(design, root)
    app.activeViewport.fit()
    print(json.dumps({"iteration": 2, "bodies": [b.name for b in root.bRepBodies],
        "carrier_mounts": 4, "independent_cover_mounts": 4,
        "insert": "M2 x 4 x 3.5 mm", "pilot": "3.2 mm provisional",
        "status": "Draft fasteners and ribs; hardware fit and hot-swap seats pending"}))
