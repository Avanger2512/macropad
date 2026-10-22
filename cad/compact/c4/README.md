# Compact C4 — corrections after the first C3 print

## CAD brief

User reported easy switch extraction, OLED glass interfering with the short
window edges, and incorrect ESP row slots. Keep the C3 layout and exterior
106×74×18.8. Units mm; origin rear-left bottom, +Xright,+Ytowarduser,+Zup.
Encoder is toward the rear, so the OLED's measured top margin faces −Y.
C1/C2/C3 remain historical versions; generator sources own parameters.

## Physical feedback and final changes

- **MX**: apertures14.1→14.0 square. Keep clip-bearing thickness1.5 and
  underside16.6square relief. Hole shrinking adds0.05material on each edge;
  actual retention must be checked with the same switch and print process.
- **OLED**: measured glass short side18.2; upper/rear margin6 and lower/front9.
  This implies glass center offset(6−9)/2=−1.5mm from PCB center, toward encoder.
  Old centered18.9window blocks that glass; BRep reproduces85.7325mm³ overlap.
  New throat34.9×19.0, centerX83/Y47.5, boundsX65.55..100.45/Y38..57.
  Short-edge clearance0.4/side; long edge unchanged from the successful print.
  Top entry bevel0.3. PCB/holes remain centeredX83/Y49.
- **OLED mounting**: four collars and downward pins are fused into the upper
  shell at measured31×28hole centers. CollarsØ4.4 contactPCBtopZ16.4; pinsØ2.2
  pass throughØ2.5holes and endZ14.4, with0.4leadcones narrowing toØ1.6.
  Insert the OLED from inside upward, then secure pins/PCB from underneath
  using adhesive per user assembly. Glass is not clamped. No separate frame.
- **ESP slots**: measured15.0 between row centers, occupied length20.5.
  Actual slots1.8×20.8 include0.15clearance at each end. CentersX12.5/27.5,
  centerY13.25, boundsY2.85..23.65; rear wall remains intact. MCU stays exposed
  on the roof with no added stand, rail or upper clamp. Adhesive from below.
- **Bottom**: OLED columns removed; a single flat2.4cover with the same fourM2
  clearance holes and exterior. No changes to the four upper insert bosses.
- **MX sample**:66×24×2.4, aperture choices13.9/14.0/14.1, identified by1/2/3
  edge notches. Same1.5seat and underside relief as case. STL already oriented
  with the flat outside face down and relief up. Case currently uses14.0.

## Exported files and print preparation

- `compact_model.step`: full assembly with simplified electronics references.
- `top_shell.step` / `top_shell.stl`: upper shell only; in assembly coordinates.
  Place the flat exterior roof against the print bed, interior/pins upward.
- `bottom_cover.step` / `bottom_cover.stl`: flat lower cover, flat underside down.
- `mx_coupon.step` / `mx_coupon.stl`: comparison sample, already onZ0 for print.
- `compact_c4_fit.f3d`: locally exported native Fusion STEP mirror.

First compare switch retention in the small MX sample before another upper
shell. The13.9option may be too tight; physical clip performance is not a BRep
property. No slicing or printer job has been run in this revision.

## Checks actually run

- Five BRep regression tests for switch throat/clip seat, integral roof mount,
  flat bottom, shifted glass edge and ESP slots. First three failed on the
  cloned C3, then passed after implementation; all five pass on finalC4.
- Three standalone single positive solids: shell, cover, MX sample.
- 81 printed-part/reference and printed-part pair tests: no positive overlaps.
- 12 OLED glass/PCB insertion samples along upward assembly path: no overlaps.
- Actual BRep face sections confirm slot1.8×20.8, spacing15, window34.9×19.0.
- Legacy C3 lower cover: no modeled intersections, but only0.2nominal gap
  between its old post keys and new downward pin tips. Prefer new flat cover,
  or trim old posts and dry-fit rather than relying on that print tolerance.
- Four exported STEP files inspected with facts/planes/positioning. Assembly,
  shell underside, bottom and MX sample snapshots reviewed.
- Three STL meshes: welded two-manifold edges, consistent winding, positive
  volume and expected dimensions. Volume agrees with BRep within0.1%.
- Native Fusion MCP results and source SHA256 in `fusion-validation.json`.

## Remaining assumptions

The6/9margins sum with18.2glass to33.2, whereas provisional PCB outline remains
36×34. These are rounded edge measurements, so use their **difference** to
correct glass offset while preserving the already established mounting-hole
coordinates. Actual PCB-to-hole offsets and glass Z thickness were not newly
measured. Nominal glass height2.4 leaves its surface flush atZ18.8; actual fit
still needs the next print. MCU outer envelope24×24 is provisional and only
its measured pin slots are fit targets. Encoder/keys positions unchanged.
Adhesive retention and print tolerances are not simulated. Catalog component
misses and provisional envelope provenance are inherited from C1/C3.

CAD Viewer is not installed; inspect snapshots and the Fusion document.
