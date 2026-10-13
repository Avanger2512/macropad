"""Verify holder-axis alignment and sampled retention lands in the source 3MF.

Uses only the Python standard library. Coordinates are mesh-local millimeters,
before any 3MF build-plate transform. Surface sampling establishes plastic
coverage, not physical wire clearance or the identity of the locating hole.
"""

import argparse
from collections import Counter
import hashlib
import json
import math
from pathlib import Path
import xml.etree.ElementTree as ET
import zipfile

NAMESPACE = {"m": "http://schemas.microsoft.com/3dmanufacturing/core/2015/02"}
MEMBER = "3D/Objects/object_1.model"
EXPECTED_SIZE = (11.03147984, 9.74910164, 5.1999998)
SURFACE_TOLERANCE = 1e-5
GRID_STEP = 0.025


def require(condition, message):
    if not condition:
        raise ValueError(message)


def read_mesh(path):
    with zipfile.ZipFile(path) as archive:
        info = archive.getinfo(MEMBER)
        require(info.file_size < 50_000_000, "Mesh XML exceeds the input limit")
        document = archive.read(MEMBER)
    require(b"<!DOCTYPE" not in document.upper(), "DTD declarations are unsupported")
    root = ET.fromstring(document)
    vertices = tuple(tuple(float(node.attrib[axis]) for axis in "xyz")
                     for node in root.findall(".//m:vertex", NAMESPACE))
    require(vertices and all(math.isfinite(c) for p in vertices for c in p),
            "Expected nonempty finite mesh vertices")
    indices = tuple(tuple(int(node.attrib[key]) for key in ("v1", "v2", "v3"))
                    for node in root.findall(".//m:triangle", NAMESPACE))
    require(indices and all(0 <= i < len(vertices) for face in indices for i in face),
            "Invalid triangle vertex index")
    triangles = tuple(tuple(vertices[i] for i in face) for face in indices)
    return vertices, triangles


def fit_axis(vertices):
    points = tuple(sorted(set((x, y) for x, y, z in vertices
                             if abs(z + 0.25) < 1e-6)))
    require(len(points) >= 3, "Missing locating-hole circle vertices")
    x0, y0 = points[0]
    rows = tuple((2 * (x - x0), 2 * (y - y0), x*x + y*y - x0*x0 - y0*y0)
                 for x, y in points[1:])
    aa = sum(a*a for a, _, _ in rows)
    ab = sum(a*b for a, b, _ in rows)
    bb = sum(b*b for _, b, _ in rows)
    ac = sum(a*c for a, _, c in rows)
    bc = sum(b*c for _, b, c in rows)
    determinant = aa*bb - ab*ab
    require(abs(determinant) > 1e-9, "Degenerate circle fit")
    cx = (ac*bb - bc*ab) / determinant
    cy = (bc*aa - ac*ab) / determinant
    radii = tuple(math.hypot(x - cx, y - cy) for x, y in points)
    diameter = 2 * sum(radii) / len(radii)
    require(abs(diameter - 4) < 0.001, "Locating-hole diameter changed")
    require(max(radii) - min(radii) < 1e-5, "Circle-fit residual exceeds tolerance")
    bottom = tuple((x, y) for x, y, z in vertices if abs(z + 2.6) < 1e-6
                   and abs(math.hypot(x - cx, y - cy) - diameter / 2) < 1e-5)
    require(len(bottom) >= 100, "Matching bottom cylindrical boundary is missing")
    return {"center_mm": [cx, cy], "diameter_mm": diameter,
            "radius_peak_to_peak_mm": max(radii) - min(radii),
            "fitted_vertices": len(points), "bottom_boundary_vertices": len(bottom),
            "holder_origin_offset_from_switch_axis_mm": [-cx, -cy],
            "hole_identity": "MX locating-post hole inferred from diameter and position"}


def contains(point, triangle):
    def cross(a, b):
        return ((b[0] - a[0]) * (point[1] - a[1])
                - (b[1] - a[1]) * (point[0] - a[0]))
    area = cross_at_vertex(triangle)
    if abs(area) < 1e-12:
        return False
    signs = tuple(cross(triangle[i], triangle[(i + 1) % 3]) for i in range(3))
    return min(signs) >= -1e-8 or max(signs) <= 1e-8


def cross_at_vertex(triangle):
    a, b, c = triangle
    return (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])


def segment_distance(point, edge):
    a, b = edge
    dx, dy = b[0] - a[0], b[1] - a[1]
    denominator = dx*dx + dy*dy
    if denominator == 0:
        return math.hypot(point[0] - a[0], point[1] - a[1])
    factor = max(0, min(1, ((point[0] - a[0])*dx + (point[1] - a[1])*dy)
                           / denominator))
    return math.hypot(point[0] - a[0] - factor*dx, point[1] - a[1] - factor*dy)


def sample_land(triangles, label, z, bounds):
    surface = tuple(t for t in triangles
                    if all(abs(p[2] - z) < SURFACE_TOLERANCE for p in t)
                    and abs(cross_at_vertex(t)) > 1e-12)
    require(surface, f"Missing flat surface for {label}")
    left, right, front, rear = bounds
    nx = max(1, math.ceil((right - left) / GRID_STEP))
    ny = max(1, math.ceil((rear - front) / GRID_STEP))
    points = tuple((left + (right-left)*i/nx, front + (rear-front)*j/ny)
                   for i in range(nx + 1) for j in range(ny + 1))
    missing = tuple(p for p in points if not any(contains(p, t) for t in surface))
    require(not missing, f"{label} intersects a void: {missing[:3]}")
    edge_counts = Counter(tuple(sorted((t[i][:2], t[(i+1) % 3][:2])))
                          for t in surface for i in range(3))
    edges = tuple(edge for edge, count in edge_counts.items() if count == 1)
    perimeter = tuple(p for p in points if p[0] in (left, right) or p[1] in (front, rear))
    clearance = min(segment_distance(p, edge) for p in perimeter for edge in edges)
    return {"name": label, "surface_z_mm": z, "bounds_xy_mm": list(bounds),
            "samples": len(points), "covered_samples": len(points), "missing_samples": 0,
            "flat_triangles": len(surface),
            "sampled_perimeter_boundary_clearance_mm": clearance}


def validate(path):
    vertices, triangles = read_mesh(path)
    bounds = tuple((min(p[i] for p in vertices), max(p[i] for p in vertices))
                   for i in range(3))
    size = tuple(high - low for low, high in bounds)
    require(all(abs(actual - expected) < 1e-5
                for actual, expected in zip(size, EXPECTED_SIZE)), "Holder dimensions changed")
    lands = (
        ("Bottom support left", -2.6, (-3.0, -2.0, -2.7, 0.3)),
        ("Bottom support right", -2.6, (2.0, 3.0, -2.7, 0.3)),
        ("Snap edge left", -2.6, (-5.515, -5.215, 2.7, 4.7)),
        ("Snap edge right", -2.6, (5.215, 5.515, 2.7, 4.7)),
        ("Upper stop left", 2.6, (-3.5, -2.5, 4.0, 4.6)),
        ("Upper stop right", 2.6, (2.5, 3.5, 4.0, 4.6)),
    )
    return {"status": "passed", "source_file": path.name,
            "source_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            "mesh_member": MEMBER, "coordinate_system": "Untransformed mesh-local millimeters",
            "bounds_mm": bounds, "size_mm": size, "axis": fit_axis(vertices),
            "maximum_sampling_step_mm": GRID_STEP,
            "lands": [sample_land(triangles, *land) for land in lands],
            "limitations": "Discrete surface coverage; does not validate wire routing, switch fit or snap durability"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    try:
        report = validate(args.source)
        args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    except (OSError, ValueError, KeyError, ET.ParseError, zipfile.BadZipFile) as error:
        parser.exit(1, f"Holder mesh verification failed: {error}\n")
    print(json.dumps({"status": report["status"], "axis": report["axis"],
                      "verified_lands": len(report["lands"])}))


if __name__ == "__main__":
    main()
