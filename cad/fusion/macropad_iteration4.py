"""Prototype LED cavity, PCB fasteners and opposed OLED retention.

Native Fusion incremental generator. Switch holder height still requires
an actual switch/contact-holder coupon before the full enclosure is approved.
PCB post pilots are for trial M2 screws in plastic, not heat-set inserts.
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


TRIAL_PARAMETERS = (
    ("diffuserSkin", "0.8 mm", "mm", "Prototype optical front skin"),
    ("diffuserSideWall", "1 mm", "mm", "Prototype hollow plug walls"),
    ("diffuserRearDepth", "6 mm", "mm", "Rear rim presses strip edges"),
    ("ledTrayDepth", "6.2 mm", "mm", "LED strip seat below exterior face"),
    ("ledTrayThickness", "2.4 mm", "mm", "Structural LED tray"),
    ("ledWireWidth", "4 mm", "mm", "Right-hand prototype wiring relief"),
    ("oledBoardWidth", "36 mm", "mm", "Measured PCB orientation across case"),
    ("oledBoardLength", "34 mm", "mm", "Measured PCB orientation along face"),
    ("oledPcbThickness", "1.6 mm", "mm", "Confirmed OLED PCB thickness"),
    ("oledPcbFrontDepth", "2.8 mm", "mm", "Provisional OLED PCB front seating depth"),
    ("oledFitClearance", "0.2 mm", "mm", "Prototype PCB fit clearance"),
    ("oledBackDepth", "oledPcbFrontDepth + oledPcbThickness", "mm", "OLED PCB rear face"),
    ("pcbPostDiameter", "4.4 mm", "mm", "Trial PCB screw support diameter"),
    ("pcbPostHeight", "6 mm", "mm", "Short PCB posts below control hardware"),
    ("pcbPostPilot", "1.7 mm", "mm", "Trial M2 plastic thread pilot; coupon required"),
)


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


def run(_context: str):
    app = adsk.core.Application.get()
    d = adsk.fusion.Design.cast(app.activeProduct)
    if d is None or app.activeDocument.name != "macropad":
        raise RuntimeError("Activate macropad")
    r = d.rootComponent
    if d.userParameters.itemByName("diffuserSkin"):
        raise RuntimeError("Iteration 4 already exists")
    check_design(d, r)
    for name, expr, units, comment in TRIAL_PARAMETERS:
        d.userParameters.add(name, value(expr), units, comment)
    d.userParameters.itemByName("frontHeight").expression = "29 mm"
    # This moves the rear cover fasteners along the rear wall, away from
    # PCB screw heads. Their flush mounting orientation is preserved.
    d.userParameters.itemByName("bottomRearSideX").expression = "20 mm"
    upper = r.bRepBodies.itemByName("UpperShell_Draft")
    carrier = r.bRepBodies.itemByName("MiddleCarrier_Draft")
    diffuser = r.bRepBodies.itemByName("Diffuser_Draft")
    face = r.constructionPlanes.itemByName("Exterior face datum")
    carrier_plane = r.constructionPlanes.itemByName("Carrier seating datum")
    bottom_plane = r.constructionPlanes.itemByName("Bottom boss seat datum")
    join = adsk.fusion.FeatureOperations.JoinFeatureOperation
    cut = adsk.fusion.FeatureOperations.CutFeatureOperation
    # Extend the flange into an open-back skirt, then hollow the complete hood.
    skirt_plane = offset(r, face, "Diffuser rear skirt datum", "-(shellWall + diffuserFlangeThickness)")
    skirt = rectangle(d, r, skirt_plane, "Diffuser hollow skirt outside profile",
        "(caseWidth-ledWidth)/2 + diffuserClearance-diffuserFlange",
        "ledCenter-ledHeight/2+diffuserClearance-diffuserFlange",
        "ledWidth-2*diffuserClearance+2*diffuserFlange", "ledHeight-2*diffuserClearance+2*diffuserFlange")
    extrude(r, skirt, "Diffuser open rear skirt", "diffuserRearDepth-shellWall-diffuserFlangeThickness", join, False, diffuser)
    skin_plane = offset(r, face, "Diffuser inner skin datum", "-diffuserSkin")
    cavity = rectangle(d, r, skin_plane, "Diffuser optical cavity profile",
        "(caseWidth-ledWidth)/2+diffuserClearance+diffuserSideWall",
        "ledCenter-ledHeight/2+diffuserClearance+diffuserSideWall",
        "ledWidth-2*(diffuserClearance+diffuserSideWall)", "ledHeight-2*(diffuserClearance+diffuserSideWall)")
    extrude(r, cavity, "Hollow diffuser from inside", "diffuserRearDepth+1 mm", cut, False, diffuser)
    wire = rectangle(d, r, skirt_plane, "Diffuser right wire exit profile",
        "(caseWidth+ledWidth)/2-diffuserSideWall-1 mm", "ledCenter-ledWireWidth/2", "5 mm", "ledWireWidth")
    extrude(r, wire, "Diffuser right wire exit", "diffuserRearDepth", cut, False, diffuser)
    clearance = rectangle(d, r, carrier_plane, "Deep diffuser skirt clearance profile",
        "(caseWidth-ledWidth)/2+diffuserClearance-diffuserFlange-flangePocketClearance",
        "ledCenter-ledHeight/2+diffuserClearance-diffuserFlange-flangePocketClearance",
        "ledWidth-2*diffuserClearance+2*(diffuserFlange+flangePocketClearance)",
        "ledHeight-2*diffuserClearance+2*(diffuserFlange+flangePocketClearance)")
    extrude(r, clearance, "Clear carrier around hollow diffuser", "diffuserRearDepth-shellWall-carrierClearance+0.2 mm", cut, False, carrier)
    # A full-width rear web connects the tray to the carrier rear frame.
    tray_back = "faceLength-(shellWall+carrierClearance)/cos(caseTilt)-(ledTrayDepth+ledTrayThickness)*tan(caseTilt)"
    web_y = "faceLength-(shellWall+carrierClearance)/cos(caseTilt)-(shellWall+carrierClearance+carrierThickness)*tan(caseTilt)-carrierRim+0.4 mm"
    web = rectangle(d, r, carrier_plane, "LED rear support web profile", "(caseWidth-ledWidth)/2-0.2 mm", web_y, "ledWidth+0.4 mm", "4 mm")
    extrude(r, web, "LED rear support web", "ledTrayDepth+ledTrayThickness-shellWall-carrierClearance", join, False, carrier)
    tray_plane = offset(r, face, "LED tray datum", "-ledTrayDepth")
    tray = rectangle(d, r, tray_plane, "Continuous LED tray profile", "(caseWidth-ledWidth)/2-0.2 mm",
        "ledCenter-ledHeight/2-0.2 mm", "ledWidth+0.4 mm", f"({tray_back})-(ledCenter-ledHeight/2-0.2 mm)")
    extrude(r, tray, "Continuous LED mounting crossbar", "ledTrayThickness", join, False, carrier)
    wire = rectangle(d, r, tray_plane, "LED tray right wire relief profile", "(caseWidth+ledWidth)/2-2 mm",
        "ledCenter-ledWireWidth/2", "4 mm", "ledWireWidth")
    extrude(r, wire, "LED tray right wire relief", "ledTrayThickness+1 mm", cut, False, carrier)
    # Display support ledges act on the PCB edge bands, outside the glass.
    for row in range(2):
        sy = "controlCenter-oledBoardLength/2" if row == 0 else "controlCenter+oledBoardLength/2-5 mm"
        seat = rectangle(d, r, face, f"OLED seat {row+1} profile", "layoutGap+(displayWidth-oledBoardWidth)/2", sy, "oledBoardWidth", "3 mm")
        extrude(r, seat, f"OLED opposed locating ledge {row+1}", "oledPcbFrontDepth", join, False, upper)
    oled_left = "layoutGap+(displayWidth-oledBoardWidth)/2-oledFitClearance"
    oled_bottom = "controlCenter-oledBoardLength/2-oledFitClearance"
    def oled_clear():
        opening = rectangle(d, r, carrier_plane, "OLED PCB carrier clearance profile", oled_left, oled_bottom,
            "oledBoardWidth+2*oledFitClearance", "oledBoardLength+2*oledFitClearance")
        extrude(r, opening, "OLED PCB clearance in carrier", "oledBackDepth+oledFitClearance-shellWall-carrierClearance", cut, False, carrier)
    oled_clear()
    pressure_plane = offset(r, face, "OLED pressure datum", "-(oledBackDepth+oledFitClearance)")
    front_root = rectangle(d, r, carrier_plane, "OLED front clamp root profile", "18 mm", "controlCenter-18 mm", "14 mm", "1 mm")
    extrude(r, front_root, "OLED front clamp root", "oledBackDepth+oledFitClearance+2 mm-shellWall-carrierClearance", join, False, carrier)
    front = rectangle(d, r, pressure_plane, "OLED front opposed clamp profile", "18 mm", "controlCenter-18 mm", "14 mm", "4 mm")
    extrude(r, front, "OLED front opposed clamp", "2 mm", join, False, carrier)
    rear_root = rectangle(d, r, tray_plane, "OLED rear clamp connecting bridge profile", "18 mm", "controlCenter+12.8 mm", "14 mm", "3.8 mm")
    extrude(r, rear_root, "OLED rear clamp connecting bridge", "ledTrayThickness", join, False, carrier)
    rear = rectangle(d, r, pressure_plane, "OLED rear opposed clamp profile", "18 mm", "controlCenter+13 mm", "14 mm", "2 mm")
    extrude(r, rear, "OLED rear opposed clamp", "2 mm", join, False, carrier)
    oled_clear()
    # PCB short posts avoid running through the OLED/encoder footprints.
    post_plane = r.constructionPlanes.itemByName("PCB top layout datum")
    bridge_plane = offset(r, r.xYConstructionPlane, "PCB side bridge datum", "pcbTopHeight+4 mm")
    for row in range(2):
        y = f"pcbFront+(pcbLength-pcbHolePitchY)/2+{row}*pcbHolePitchY"
        for col in range(2):
            x = f"pcbLeft+(pcbWidth-pcbHolePitchX)/2+{col}*pcbHolePitchX"
            label = f"PCB{row*2+col+1}"
            web_x = "3.2 mm" if col == 0 else "caseWidth-4.8 mm"
            web = rectangle(d, r, bridge_plane, f"{label} perimeter support profile", web_x, f"({y})-2 mm", "1.6 mm", "4 mm")
            top = f"frontHeight+(({y})-2 mm)*tan(caseTilt)-(shellWall+carrierClearance+0.5 mm)/cos(caseTilt)"
            extrude(r, web, f"{label} perimeter support", f"({top})-pcbTopHeight-4 mm", join, True, carrier)
            bx = "3.2 mm" if col == 0 else "caseWidth-7 mm"
            bridge = rectangle(d, r, bridge_plane, f"{label} short post bridge profile", bx, f"({y})-2 mm", "3.8 mm", "4 mm")
            extrude(r, bridge, f"{label} short post bridge", "2 mm", join, True, carrier)
            circle = xy_circle(d, r, post_plane, f"{label} post profile", x, y, "pcbPostDiameter")
            extrude(r, circle, f"{label} screw mounting post", "pcbPostHeight", join, True, carrier)
            pilot = xy_circle(d, r, post_plane, f"{label} M2 pilot profile", x, y, "pcbPostPilot")
            extrude(r, pilot, f"{label} M2 pilot", "4.5 mm", cut, True, carrier)
    # Restore carrier fastener pockets and lower extraction routes after joins.
    pocket_plane = r.constructionPlanes.itemByName("Carrier boss clearance datum")
    entry_plane = r.constructionPlanes.itemByName("Carrier insert entry datum")
    extension_plane = offset(r, face, "Carrier hard stop datum", "-(carrierBossDepth+carrierClearance)")
    for row, cy in enumerate(("mountFrontV", "mountRearV")):
        for col, cx in enumerate(("mountSideX", "caseWidth-mountSideX")):
            label = f"M{row*2+col+1}"
            ring = inclined_circle(d, r, entry_plane, f"{label} carrier stop profile", cx, cy, "mountBossDiameter")
            extrude(r, ring, f"{label} rigid carrier stop", "carrierClearance", join, False, upper)
            pilot = inclined_circle(d, r, extension_plane, f"{label} stop insert entry profile", cx, cy, "insertPilotDiameter")
            extrude(r, pilot, f"{label} open stop insert entry", "carrierClearance+0.1 mm", cut, True, upper)
            if row == 1:
                pocket = inclined_circle(d, r, pocket_plane, f"{label} restored carrier pocket profile", cx, cy, "mountBossDiameter+2*mountPocketClearance")
                extrude(r, pocket, f"{label} restored carrier pocket", "carrierBossDepth+carrierClearance", cut, True, carrier)
                hole = inclined_circle(d, r, carrier_plane, f"{label} restored screw clearance profile", cx, cy, "m2Clearance")
                extrude(r, hole, f"{label} restored screw clearance", "carrierPadDepth", cut, False, carrier)
                bx = ("20 mm" if col == 0 else "caseWidth-20 mm")
                by = "4.8 mm" if row == 0 else "caseLength-3 mm"
                relief = xy_circle(d, r, bottom_plane, f"{label} restored cover boss relief profile", bx, by,
                    "bottomBossDiameter+2*bottomReliefClearance")
                extrude(r, relief, f"{label} restored cover boss relief", "rearHeight+1 mm", cut, True, carrier)
    check_design(d, r)
    app.activeViewport.fit()
    print(json.dumps({"iteration":4,"frontHeight_mm":evaluate(d,"frontHeight")*10,
        "rearHeight_mm":evaluate(d,"rearHeight")*10,"pcb_mounts":4,"oled_clamps":2,
        "diffuser":"Open-back hollow skin and wire exit","status":"Prototype; switch holder height and hardware clearances need fit testing"}))
