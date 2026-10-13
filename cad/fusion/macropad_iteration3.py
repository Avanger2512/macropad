"""Move upper inserts away from walls and add printable front cover supports.

Run once after iteration 2. Lower fastener centers remain unchanged.
Carrier pads and extraction reliefs follow the revised geometry.
Solder-tool clearance is a local nominal envelope, not verified tool fit.
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
    side_indices = (0, 2) if world_yz and len(coords) == 3 else ((0, 1, 3) if world_yz else (0, 1))
    for i in side_indices:
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
    if design.userParameters.itemByName("bottomRearSideX"):
        raise RuntimeError("Iteration 3 already exists")
    check_design(design, root)
    design.userParameters.add("bottomRearSideX", value("4.8 mm"), "mm", "Preserved lower rear fastener position")
    design.userParameters.add("frontSupportWidth", value("bottomBossDiameter"), "mm", "Front cover support width")
    design.userParameters.add("frontSupportRun", value("4.8 mm + bottomBossDiameter / 2 - shellWall + 0.1 mm"), "mm", "45 degree support run and rise")
    # Lower rear fasteners previously shared the upper mount parameter.
    for col in range(2):
        label = f"M{3 + col}"
        cx = "bottomRearSideX" if col == 0 else "caseWidth - bottomRearSideX"
        for suffix in ("bottom shell boss profile", "bottom insert pilot profile",
                "bottom cover screw profile", "carrier vertical removal relief profile"):
            sketch = root.sketches.itemByName(f"{label} {suffix}")
            sketch.sketchDimensions.item(0).parameter.expression = cx
    design.userParameters.itemByName("mountSideX").expression = "12 mm"
    design.userParameters.itemByName("mountFrontV").expression = "10.5 mm"
    design.userParameters.itemByName("mountRearV").expression = "faceLength - 9.64 mm"
    design.userParameters.itemByName("mountPadWidth").expression = "12 mm"
    for i in range(4):
        cx = "mountSideX" if i % 2 == 0 else "caseWidth - mountSideX"
        sketch = root.sketches.itemByName(f"M{i + 1} carrier mounting pad profile")
        sketch.sketchDimensions.item(0).parameter.expression = f"({cx}) - mountPadWidth / 2"
    upper = root.bRepBodies.itemByName("UpperShell_Draft")
    carrier = root.bRepBodies.itemByName("MiddleCarrier_Draft")
    cut = adsk.fusion.FeatureOperations.CutFeatureOperation
    join = adsk.fusion.FeatureOperations.JoinFeatureOperation
    # Moved rear pads must preserve the existing diffuser-flange clearance.
    plane = root.constructionPlanes.itemByName("Carrier seating datum")
    pocket = rectangle(design, root, plane, "Iteration 3 diffuser flange clearance profile",
        "(caseWidth - ledWidth) / 2 + diffuserClearance - diffuserFlange - flangePocketClearance",
        "ledCenter - ledHeight / 2 + diffuserClearance - diffuserFlange - flangePocketClearance",
        "ledWidth - 2 * diffuserClearance + 2 * diffuserFlange + 2 * flangePocketClearance",
        "ledHeight - 2 * diffuserClearance + 2 * diffuserFlange + 2 * flangePocketClearance")
    extrude(root, pocket, "Restore diffuser clearance in moved rear pads",
        "diffuserFlangeThickness - carrierClearance + flangePocketClearance", cut, False, carrier)
    for col in range(2):
        cx = "20 mm" if col == 0 else "caseWidth - 20 mm"
        support_plane = offset(root, root.yZConstructionPlane, f"Front cover support {col + 1} datum",
            f"({cx}) - frontSupportWidth / 2")
        ramp = polygon(design, root, support_plane, f"Front cover support {col + 1} profile", (
            ("shellWall - 0.1 mm", "bottomThickness + bottomBossHeight"),
            ("shellWall - 0.1 mm + frontSupportRun", "bottomThickness + bottomBossHeight"),
            ("shellWall - 0.1 mm", "bottomThickness + bottomBossHeight + frontSupportRun")), world_yz=True)
        extrude(root, ramp, f"Front cover support {col + 1} 45 degree gusset", "frontSupportWidth", join,
            root.yZConstructionPlane.geometry.normal.x > 0, upper)
        bottom_plane = root.constructionPlanes.itemByName("Bottom boss seat datum")
        relief = rectangle(design, root, bottom_plane, f"Front support {col + 1} removal corridor profile",
            f"({cx}) - bottomBossDiameter / 2 - bottomReliefClearance", "0 mm",
            "bottomBossDiameter + 2 * bottomReliefClearance", "4.8 mm + bottomBossDiameter / 2 + bottomReliefClearance")
        extrude(root, relief, f"Front support {col + 1} vertical removal corridor", "rearHeight + 1 mm", cut, True, carrier)
    check_design(design, root)
    app.activeViewport.fit()
    print(json.dumps({"iteration": 3, "upper_mount_side_mm": evaluate(design, "mountSideX") * 10,
        "upper_front_face_y_mm": evaluate(design, "mountFrontV") * 10,
        "upper_rear_face_y_mm": evaluate(design, "mountRearV") * 10,
        "lower_fasteners": "Original centers preserved", "print_supports": "Two 45 degree front gussets",
        "status": "Solder-tool and print orientation revision; hardware fit remains pending"}))
