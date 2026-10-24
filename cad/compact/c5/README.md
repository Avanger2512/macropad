# C5 — full OLED flush installation

## CAD brief and measured datums

Modify C4 upper shell; retain exterior106×74×18.8 mm, all MX/MCU/encoder
locations, lower cover interface and screws. Origin rear-left bottom, mm,
+Y toward user. C4 files remain unchanged.

User confirmed full OLED34.5×23, rear margin6 (toward encoder), front4.6.
PCB35.5×33.6 is centered atX83/Y49; full OLED boundsX65.75..100.25,
Y38.2..61.2. Its2mm measured height above PCB places PCBtopZ16.8 and
OLEDfaceZ18.8, flush with housing. PCB thickness1.6 remains a prior assumption.

Window throat34.9×23.4 atX65.55/Y38 provides0.2/side nominal clearance.
Drawing OLED tolerance±0.2 reduces this to0.1/side at maximum part size,
prior to printer tolerance. Upper edge bevel0.3 retained.

PCB relief clearance0.2 above board. Four roof-mounted collars and locating
pins remain; inner collar lips are trimmed clear of the full OLED insertion
path. Existing measured31×28 hole pattern and2.5diameter are retained despite
drawing30.5/Ø3.1 conflict. Pin diameter2.2. Install from inside and glue PCB
at pins; do not press/clamp glass. No separate display cradle.

## Files and printing

- `top_shell.step` primary CAD; `top_shell.stl` replacement upper shell.
- `top_shell.f3d` local native Fusion mirror, checked through Fusion MCP.
- `compact_model.py`, `layout.py`, `top_shell.py` own geometry.

STL uses assembly coordinates. Orient the flat exterior roof onto bed,
interior and pins up. Use existing matte PLA profile; inspect slicing around
pins and window bevel. The integral-foot lower cover from the prior task fits
without changes. No slicing or physical fit test performed for C5.

## Validation

Five B-rep tests pass: single valid connected shell, measured full envelope
and margins, flush face, glass and PCB collision-free, full glass insertion
sweep and nominal throat clear. Mesh manifold/winding/volume/bounds checks
and C4 lower-cover mating check recorded in `validation.json`. Fusion MCP
independently confirms one positive solid, four pin shafts and external size.
Snapshots of outer and inner faces were reviewed; CAD Viewer unavailable.

## 5 mm heat-set inserts

Four existing bores retain Ø3.2 and now have effective blind depth5.5 mm
from lower shell mating faceZ2.4: 5 mm insert plus0.5 allowance. Closed bore
endZ7.9 leaves10.9 mm to outer roofZ18.8; boss wall thickness1.4 mm radial.
Lower cover holes and all screw axes unchanged. Six geometric tests pass.
STEP/STL/F3D and inspection reports regenerated after this change.
