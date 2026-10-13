"""Revise native Fusion PCB mounts for components facing the bottom cover.

The horizontal solder-side seating face is supported by four short bosses
on continuous carrier perimeter rails. Trial M2 pilots use plastic threads.
Hardware clearance and carrier extraction still require physical checks.
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
    if plane.name in ("Exterior face datum", "Carrier seating datum", "Diffuser flange datum", "LED tray datum", "Diffuser rear skirt datum", "Diffuser inner skin datum", "OLED pressure datum"):
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
        raise RuntimeError("Enclosure body interference: " + str([(c.entityOne.name, c.entityTwo.name, c.interferenceBody.volume) for c in collisions]))
    if any(not s.isFullyConstrained for s in root.sketches):
        raise RuntimeError("Unconstrained sketch")


def xy_circle(design, root, plane, name, cx, cy, diameter):
    s = root.sketches.add(plane)
    s.name = name
    x, y = evaluate(design, cx), evaluate(design, cy)
    c = s.sketchCurves.sketchCircles.addByCenterRadius(point(x, y), evaluate(design, diameter) / 2)
    constrain_point(s, c.centerSketchPoint, cx, cy)
    s.sketchDimensions.addDiameterDimension(c, point(x + 0.5, y + 0.5)).parameter.expression = diameter
    return s


def inclined_circle(design, root, plane, name, cx, cy, diameter):
    return xy_circle(design, root, plane, name, cx, f"({cy}) + faceOriginV", diameter)


def run(context):
    app = adsk.core.Application.get()
    d = adsk.fusion.Design.cast(app.activeProduct)
    if d is None or app.activeDocument.name != "macropad":
        raise RuntimeError("Activate macropad")
    r = d.rootComponent
    if d.userParameters.itemByName("pcbMountHeight"):
        raise RuntimeError("PCB revision already exists")
    check_design(d, r)
    e = d.exportManager
    backup = "/Users/denisbabiichuk/3dPrint/macropad/cad/fusion/exports/macropad_enclosure_before_pcb_revision.f3d"
    if not e.execute(e.createFusionArchiveExportOptions(backup)):
        raise RuntimeError("Backup failed")
    obsolete = ("perimeter support", "short post bridge", "screw mounting post", "M2 pilot")
    remove = [f for f in r.features.extrudeFeatures if f.name.startswith(("PCB1 ", "PCB2 ", "PCB3 ", "PCB4 ")) and any(f.name.endswith(s) for s in obsolete)]
    if len(remove) != 16:
        raise RuntimeError("Expected sixteen old PCB mounting features")
    for f in reversed(remove):
        if not f.deleteMe():
            raise RuntimeError("Could not remove old PCB support")
    for s in list(r.sketches):
        if s.name.startswith(("PCB1 ", "PCB2 ", "PCB3 ", "PCB4 ")):
            s.isVisible = False
    d.userParameters.add("pcbMountHeight", value("22.3 mm"), "mm", "Upper solder-side PCB seating face; components face bottom cover")
    d.userParameters.add("pcbRailHeight", value("27.8 mm"), "mm", "Short screw bosses attach to continuous outer carrier rails")
    d.userParameters.add("pcbRailThickness", value("1.5 mm"), "mm", "Mounting ear thickness")
    d.userParameters.itemByName("pcbUndersideHeight").expression = "pcbMountHeight-pcbThickness"
    d.userParameters.itemByName("pcbTopHeight").expression = "pcbMountHeight"
    d.userParameters.itemByName("usbCenterX").expression = "pcbLeft+pcbWidth-36 mm"
    d.userParameters.itemByName("usbCenterZ").expression = "pcbUndersideHeight-5.5 mm"
    d.userParameters.itemByName("pcbPostHeight").expression = "pcbRailHeight+pcbRailThickness-pcbMountHeight"
    carrier = r.bRepBodies.itemByName("MiddleCarrier_Draft")
    join = adsk.fusion.FeatureOperations.JoinFeatureOperation
    cut = adsk.fusion.FeatureOperations.CutFeatureOperation
    # Two continuous perimeter rails stay outside the board and leave its
    # solder side open. Their upper edge follows the sloped carrier plate.
    for col in range(2):
        px = "3.2 mm" if col == 0 else "caseWidth-4.8 mm"
        side = offset(r, r.yZConstructionPlane, f"PCB direct rail {col+1} datum", px)
        front_top = "frontHeight+pcbFront*tan(caseTilt)-(shellWall+carrierClearance+carrierThickness-0.3 mm)/cos(caseTilt)"
        rear_top = "frontHeight+pcbRear*tan(caseTilt)-(shellWall+carrierClearance+carrierThickness-0.3 mm)/cos(caseTilt)"
        s = polygon(d, r, side, f"PCB direct rail {col+1} profile", (("pcbFront", "pcbRailHeight"), ("pcbRear", "pcbRailHeight"), ("pcbRear", rear_top), ("pcbFront", front_top)), True)
        extrude(r, s, f"PCB direct rail {col+1}", "1.6 mm", join, True, carrier)
    ear_plane = offset(r, r.xYConstructionPlane, "PCB direct mounting ear datum", "pcbRailHeight")
    seat_plane = r.constructionPlanes.itemByName("PCB top layout datum")
    for row in range(2):
        cy = f"pcbFront+(pcbLength-pcbHolePitchY)/2+{row}*pcbHolePitchY"
        for col in range(2):
            cx = f"pcbLeft+(pcbWidth-pcbHolePitchX)/2+{col}*pcbHolePitchX"
            label = f"PCB direct mount {row*2+col+1}"
            left = "3.2 mm" if col == 0 else "caseWidth-9.2 mm"
            s = rectangle(d, r, ear_plane, label+" ear profile", left, f"({cy})-2.2 mm", "6 mm", "4.4 mm")
            extrude(r, s, label+" ear", "pcbRailThickness", join, True, carrier)
            s = xy_circle(d, r, seat_plane, label+" boss profile", cx, cy, "pcbPostDiameter")
            extrude(r, s, label+" boss", "pcbPostHeight", join, True, carrier)
            s = xy_circle(d, r, seat_plane, label+" screw profile", cx, cy, "pcbPostPilot")
            extrude(r, s, label+" screw pilot", "4.5 mm", cut, True, carrier)
    check_design(d, r)
    app.activeViewport.fit()
    print(json.dumps({"revision":"PCB component side faces bottom cover", "pcb_solder_face_mm":evaluate(d,"pcbTopHeight")*10,"pcb_component_face_mm":evaluate(d,"pcbUndersideHeight")*10,"header_bottom_mm":evaluate(d,"pcbUndersideHeight-headerMaxHeight")*10,"usb_center_mm":[evaluate(d,"usbCenterX")*10,evaluate(d,"usbCenterZ")*10],"mounts":4,"central_solder_bay":"open"}))
