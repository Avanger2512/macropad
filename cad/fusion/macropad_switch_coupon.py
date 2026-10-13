"""Bolt-free contact-holder pockets, external snaps and inclined lid forks.

The original asymmetric holder mesh sets the pocket, hook and support lands.
A physical one-switch trial is required before printing the complete carrier.
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
    if plane.name in ("Exterior face datum", "Carrier seating datum", "Diffuser flange datum", "LED tray datum", "Diffuser rear skirt datum", "Diffuser inner skin datum", "OLED pressure datum", "Holder upper datum", "Holder hook datum", "Holder spring slit datum", "Holder lid support datum", "Holder frame datum", "Holder wire window datum"):
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




HOLDER_PARAMETERS = (
    ("holderStemX", "-0.08972306 mm", "Fitted central cylinder X in original holder mesh"),
    ("holderStemY", "1.49765268 mm", "Fitted central cylinder Y in original holder mesh"),
    ("holderWidth", "11.03147984 mm", "Exact 3MF X bounding width"),
    ("holderLength", "9.74910164 mm", "Exact 3MF Y bounding length"),
    ("holderHeight", "5.2 mm", "Exact 3MF bounding height"),
    ("holderTopDepth", "shellWall+carrierClearance+7 mm", "Measured flange underside to holder top"),
    ("holderBottomDepth", "holderTopDepth+holderHeight", "Holder lower bearing plane"),
    ("holderFit", "0.2 mm", "Provisional XY pocket clearance per side"),
    ("holderFrameX", "18.4 mm", "Receiver outer width"),
    ("holderFrameY", "17.6 mm", "Receiver outer length preserving OLED clearance"),
    ("holderSwitchVoid", "16 mm", "Provisional switch lower-body clearance"),
    ("holderHookOverlap", "0.3 mm", "Prototype retention overlap"),
    ("holderHookThickness", "0.8 mm", "Snap retaining lip thickness"),
    ("holderSpringWidth", "2 mm", "External spring width"),
    ("holderSpringY", "3.7 mm", "Mesh-verified plastic edge band clear of contact exits"),
    ("holderLidGap", "0.2 mm", "Normal clearance between holder underside and lid support"),
)


def holder_frames(d, r, body, cx, cy, label, planes):
    frame, upper, hook, slit = planes
    join = adsk.fusion.FeatureOperations.JoinFeatureOperation
    cut = adsk.fusion.FeatureOperations.CutFeatureOperation
    outer = rectangle(d, r, frame, label+" receiver profile", f"({cx})-holderFrameX/2", f"({cy})-holderFrameY/2", "holderFrameX", "holderFrameY")
    extrude(r, outer, label+" integrated receiver", "holderBottomDepth+holderHookThickness-shellWall-carrierClearance-carrierThickness", join, False, body)
    switch = rectangle(d, r, frame, label+" switch lower clearance profile", f"({cx})-holderSwitchVoid/2", f"({cy})-holderSwitchVoid/2", "holderSwitchVoid", "holderSwitchVoid")
    extrude(r, switch, label+" switch lower clearance", "holderTopDepth-shellWall-carrierClearance-carrierThickness", cut, False, body)
    # The central locating cylinder is offset from the bounding-box origin.
    cx=f"({cx})-holderStemX"; cy=f"({cy})-holderStemY"
    pocket = rectangle(d, r, upper, label+" holder pocket profile", f"({cx})-holderWidth/2-holderFit", f"({cy})-holderLength/2-holderFit", "holderWidth+2*holderFit", "holderLength+2*holderFit")
    extrude(r, pocket, label+" open-bottom holder pocket", "holderHeight+holderHookThickness+0.2 mm", cut, False, body)
    edges = adsk.core.ObjectCollection.create()
    for side in range(2):
        # The root is outside the switch's 16 mm clearance. Narrow slots
        # leave a long external cantilever, not a short brittle pocket tab.
        for end in range(2):
            xx = f"({cx})+holderWidth/2+holderFit" if side else f"({cx})-holderFrameX/2-0.1 mm"
            yy = f"(({cy})+holderSpringY)+holderSpringWidth/2" if end else f"(({cy})+holderSpringY)-holderSpringWidth/2-0.6 mm"
            slot = rectangle(d, r, slit, label+f" spring {side+1} release {end+1} profile", xx, yy,
                "holderFrameX/2-holderWidth/2-holderFit+0.1 mm", "0.6 mm")
            extrude(r, slot, label+f" spring {side+1} release {end+1}", "holderBottomDepth+holderHookThickness-shellWall-carrierClearance-carrierThickness-1 mm+0.2 mm", cut, False, body)
        xx = f"({cx})+holderWidth/2+holderFit" if side else f"({cx})-holderFrameX/2+0.8 mm"
        clear = rectangle(d, r, upper, label+f" spring {side+1} inner clearance profile", xx,
            f"(({cy})+holderSpringY)-holderSpringWidth/2", "holderFrameX/2-0.8 mm-holderWidth/2-holderFit", "holderSpringWidth")
        extrude(r, clear, label+f" spring {side+1} inner clearance", "holderHeight+holderHookThickness+0.2 mm", cut, False, body)
        inner = f"({cx})+holderWidth/2-holderHookOverlap" if side else f"({cx})-holderFrameX/2"
        width = "holderFrameX/2-holderWidth/2+holderHookOverlap"
        lip = rectangle(d, r, hook, label+f" spring {side+1} hook profile", inner, f"(({cy})+holderSpringY)-holderSpringWidth/2", width, "holderSpringWidth")
        extrude(r, lip, label+f" spring {side+1} retaining hook", "holderHookThickness", join, False, body)
        tipx = f"({cx})+holderWidth/2-holderHookOverlap" if side else f"({cx})-holderWidth/2+holderHookOverlap"
        target = lip.sketchToModelSpace(point(evaluate(d,tipx), evaluate(d,f"(({cy})+holderSpringY)+faceOriginV")))
        normal = hook.geometry.normal.copy(); normal.scaleBy(-evaluate(d,"holderHookThickness")); target.translateBy(normal)
        found = None
        for edge in body.edges:
            if edge.startVertex and edge.endVertex:
                a,b=edge.startVertex.geometry,edge.endVertex.geometry
                mid=point((a.x+b.x)/2,(a.y+b.y)/2,(a.z+b.z)/2)
                if mid.distanceTo(target)<1e-5:
                    found=edge;break
        if found is None:raise RuntimeError(label+" hook ramp edge not found")
        # Apply immediately: later cuts can invalidate stored BRep edge tokens.
        collection=adsk.core.ObjectCollection.create();collection.add(found)
        inp=r.features.chamferFeatures.createInput2()
        inp.chamferEdgeSets.addEqualDistanceChamferEdgeSet(collection,value("0.35 mm"),False)
        chamfer=r.features.chamferFeatures.add(inp);chamfer.name=label+f" spring {side+1} 45 degree lead-in"

    holder_upper_stops(d,r,body,cx,cy,label)
    holder_wire_windows(d,r,body,cx,cy,label)


def holder_upper_stops(d,r,body,cx,cy,label):
    upper=r.constructionPlanes.itemByName("Holder upper datum")
    for side in range(2):
        dx="-3 mm" if side==0 else "3 mm"
        s=rectangle(d,r,upper,label+f" upper stop {side+1} profile",f"({cx})+({dx})-0.5 mm",f"({cy})+4 mm","1 mm","holderFrameY/2-4 mm")
        extrude(r,s,label+f" upper stop {side+1}","0.8 mm",adsk.fusion.FeatureOperations.JoinFeatureOperation,True,body)

def holder_wire_windows(d,r,body,cx,cy,label):
    plane=r.constructionPlanes.itemByName("Holder wire window datum")
    if plane is None:
        plane=offset(r,r.constructionPlanes.itemByName("Holder upper datum"),"Holder wire window datum","-1.2 mm")
    for side in range(2):
        x=f"({cx})+holderWidth/2" if side else f"({cx})-holderFrameX/2-0.1 mm"
        s=rectangle(d,r,plane,label+f" wire exit {side+1} profile",x,f"({cy})-5.1 mm","holderFrameX/2-holderWidth/2+0.1 mm","7.8 mm")
        extrude(r,s,label+f" wire exit {side+1}","holderHeight+holderHookThickness-1.2 mm+0.2 mm",adsk.fusion.FeatureOperations.CutFeatureOperation,False,body)

def lid_support(d,r,body,cx,cy,label,cap_plane,bottom_plane):
    cx=f"({cx})-holderStemX";cy=f"({cy})-holderStemY"
    join=adsk.fusion.FeatureOperations.JoinFeatureOperation
    cut=adsk.fusion.FeatureOperations.CutFeatureOperation
    # These 1 x 3 mm lands were checked against the original mesh bottom.
    # Keep its asymmetric orientation; do not mirror individual holders.
    for side in range(2):
        offset_x = "-2.5 mm" if side==0 else "2.5 mm"
        x=f"({cx})+({offset_x})-0.5 mm"
        local_y=f"({cy})-1.2 mm"
        world_y=f"({local_y})*cos(caseTilt)+(holderBottomDepth+holderLidGap)*sin(caseTilt)"
        cap_z=f"frontHeight+({local_y})*sin(caseTilt)-(holderBottomDepth+holderLidGap)*cos(caseTilt)"
        stem=rectangle(d,r,bottom_plane,label+f" support {side+1} reinforced stem profile",f"({cx})+({offset_x})-1.2 mm",f"({world_y})-2.5 mm","2.4 mm","5 mm")
        extrude(r,stem,label+f" support {side+1} reinforced stem",f"({cap_z})-bottomThickness-2 mm",join,True,body)
        s=rectangle(d,r,bottom_plane,label+f" support {side+1} profile",x,f"({world_y})-1.5 mm","1 mm","3 mm")
        extrude(r,s,label+f" support {side+1}",f"({cap_z})-bottomThickness+0.5 mm",join,True,body)
        # A wider cutting profile trims the vertical post to the same 5-degree
        # plane as the contact holder. No cantilever ledge or solid wire block.
        trim=rectangle(d,r,cap_plane,label+f" support {side+1} cap profile",f"({x})-0.1 mm",f"({local_y})-2 mm","1.2 mm","4 mm")
        extrude(r,trim,label+f" support {side+1} inclined cap","rearHeight",cut,True,body)


def run(context):
 app=adsk.core.Application.get();d=adsk.fusion.Design.cast(app.activeProduct);r=d.rootComponent
 if r.bRepBodies.itemByName("SwitchFitCoupon_Trial"):raise RuntimeError("Coupon already exists")
 check_design(d,r)
 join=adsk.fusion.FeatureOperations.JoinFeatureOperation
 cut=adsk.fusion.FeatureOperations.CutFeatureOperation
 new=adsk.fusion.FeatureOperations.NewBodyFeatureOperation
 face=r.constructionPlanes.itemByName("Carrier seating datum")
 cx="115 mm";cy="keyRowOne"
 plate=rectangle(d,r,face,"Switch trial plate profile",f"({cx})-11 mm",f"({cy})-11 mm","22 mm","22 mm")
 coupon=extrude(r,plate,"Switch trial plate","carrierThickness",new,False).bodies.item(0);coupon.name="SwitchFitCoupon_Trial"
 seat=rectangle(d,r,face,"Switch trial clip seat profile",f"({cx})-switchOpening/2",f"({cy})-switchOpening/2","switchOpening","switchOpening")
 extrude(r,seat,"Switch trial clip seat","carrierThickness+0.1 mm",cut,False,coupon)
 planes=[r.constructionPlanes.itemByName(n) for n in ("Holder frame datum","Holder upper datum","Holder hook datum","Holder spring slit datum")]
 holder_frames(d,r,coupon,cx,cy,"Switch trial",planes)
 cap=r.constructionPlanes.itemByName("Holder lid support datum")
 bottom=r.constructionPlanes.itemByName("Holder lid inner datum")
 world_y=f"({cy})*cos(caseTilt)+(holderBottomDepth+holderLidGap)*sin(caseTilt)"
 lid_plate=rectangle(d,r,r.xYConstructionPlane,"Lid trial plate profile",f"({cx})-11 mm",f"({world_y})-11 mm","22 mm","22 mm")
 lid=extrude(r,lid_plate,"Lid trial plate","bottomThickness",new,True).bodies.item(0);lid.name="LidSupportCoupon_Trial"
 lid_support(d,r,lid,cx,cy,"Lid trial",cap,bottom)
 d.computeAll()
 issues=[t.name for t in d.timeline if t.healthState!=adsk.fusion.FeatureHealthStates.HealthyFeatureHealthState]
 if issues:raise RuntimeError(str(issues))
 if r.bRepBodies.count!=6 or any(not b.isSolid or b.volume<=0 for b in r.bRepBodies):raise RuntimeError("Expected four enclosure solids and two trial solids")
 if any(not sk.isFullyConstrained for sk in r.sketches):raise RuntimeError("Unconstrained trial sketch")
 inp=d.createInterferenceInput(adsk.core.ObjectCollection.createWithArray(list(r.bRepBodies)))
 inp.areCoincidentFacesIncluded=False
 collisions=d.analyzeInterference(inp)
 if collisions.count:raise RuntimeError(str([(c.entityOne.name,c.entityTwo.name,c.interferenceBody.volume) for c in collisions]))
 for b in r.bRepBodies:b.isVisible=b.name in ("SwitchFitCoupon_Trial","LidSupportCoupon_Trial")
 app.activeViewport.fit()
 print(json.dumps({"trial_solids":2,"plate_mm":22,"status":"One-switch snap and lid contact fit trial"}))
