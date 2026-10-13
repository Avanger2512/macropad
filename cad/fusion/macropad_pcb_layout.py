"""Add 19 PCB layout parameters and fully constrained construction guides.

Run once in the existing macropad Fusion design. No hardware bodies,
PCB standoffs or USB cutout are created. Placement is provisional.
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


PCB_PARAMETERS=(
 ("pcbWidth","70 mm","mm","Confirmed board width"),
 ("pcbLength","50 mm","mm","Confirmed board length"),
 ("pcbThickness","1.6 mm","mm","Confirmed board thickness"),
 ("pcbHolePitchX","66 mm","mm","Confirmed hole center spacing across board"),
 ("pcbHolePitchY","46 mm","mm","Confirmed hole center spacing along board"),
 ("pcbRearGap","0.4 mm","mm","Provisional board-to-rear-wall clearance"),
 ("pcbUndersideHeight","bottomThickness + bottomBossHeight + 0.8 mm","mm","Provisional PCB underside, clearing lower bosses"),
 ("pcbTopHeight","pcbUndersideHeight + pcbThickness","mm","PCB top reference"),
 ("pcbLeft","(caseWidth - pcbWidth) / 2","mm","Centered board left edge"),
 ("pcbRear","caseLength - shellWall - pcbRearGap","mm","Board rear edge"),
 ("pcbFront","pcbRear - pcbLength","mm","Board front edge"),
 ("usbCenterX","pcbLeft + 36 mm","mm","Confirmed USB center from board left edge"),
 ("usbCenterZ","pcbTopHeight + 5.5 mm","mm","USB center above PCB top"),
 ("headerMaxHeight","17 mm","mm","Local header envelope; footprints pending"),
 ("headerRoutingTarget","14 mm","mm","Conditional mated header and wire envelope; physical verification required"),
 ("xh3Length","10 mm","mm","Measured 3-pin connector length"),
 ("xh4Length","13 mm","mm","Measured 4-pin connector length"),
 ("xh5Length","15 mm","mm","Measured 5-pin connector length"),
 ("sideHeaderInset","3 mm","mm","User-supplied side header inset; reference edge to verify"),
)

def run(_context: str):
 app=adsk.core.Application.get();d=adsk.fusion.Design.cast(app.activeProduct);r=d.rootComponent
 if app.activeDocument.name!="macropad" or r.bRepBodies.count!=4:raise RuntimeError("Unexpected design")
 if d.userParameters.itemByName("pcbWidth"):raise RuntimeError("PCB guides already exist")
 for name,expr,units,comment in PCB_PARAMETERS:d.userParameters.add(name,value(expr),units,comment)
 lower=offset(r,r.xYConstructionPlane,"PCB underside layout datum","pcbUndersideHeight")
 upper=offset(r,r.xYConstructionPlane,"PCB top layout datum","pcbTopHeight")
 for plane,label in ((lower,"PCB underside outline - provisional position"),(upper,"PCB top outline - provisional position")):
  s=rectangle(d,r,plane,label,"pcbLeft","pcbFront","pcbWidth","pcbLength")
  for line in s.sketchCurves.sketchLines:line.isConstruction=True
  s.isVisible=True
 for row in range(2):
  for col in range(2):
   s=r.sketches.add(lower);s.name=f"PCB mounting center {row*2+col+1} - hole size pending"
   x=f"pcbLeft + (pcbWidth - pcbHolePitchX)/2 + {col}*pcbHolePitchX"
   y=f"pcbFront + (pcbLength - pcbHolePitchY)/2 + {row}*pcbHolePitchY"
   p=s.sketchPoints.add(point(evaluate(d,x),evaluate(d,y)));constrain_point(s,p,x,y);s.isVisible=True
 d.computeAll()
 if any(t.healthState!=adsk.fusion.FeatureHealthStates.HealthyFeatureHealthState for t in d.timeline):raise RuntimeError("Unhealthy PCB layout")
 if any(not s.isFullyConstrained for s in r.sketches):raise RuntimeError("Unconstrained layout")
 report={"pcb_left_mm":evaluate(d,"pcbLeft")*10,"pcb_front_mm":evaluate(d,"pcbFront")*10,
 "pcb_rear_mm":evaluate(d,"pcbRear")*10,"pcb_underside_mm":evaluate(d,"pcbUndersideHeight")*10,
 "pcb_top_mm":evaluate(d,"pcbTopHeight")*10,"usb_center_x_mm":evaluate(d,"usbCenterX")*10,
 "usb_center_z_mm":evaluate(d,"usbCenterZ")*10,
 "header_top_mm":evaluate(d,"pcbTopHeight + headerMaxHeight")*10,
 "roof_inner_at_board_front_mm":evaluate(d,"frontHeight + pcbFront*tan(caseTilt)-shellWall/cos(caseTilt)")*10,
 "status":"Construction guides only; connector footprints and final board mounting pending"}
 app.activeViewport.fit();print(json.dumps(report))
