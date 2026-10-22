# Compact Iskra-inspired concept — C1

Historical first compact layout. The current [C4 revision](c4/README.md) keeps
this layout with measured OLED glass offset, integral upper OLED glue pins,
tighter MX apertures and corrected ESP pin slots. [C3](c3/README.md) records
the first printed compact version; [C2](c2/README.md) is an alternative layout.

The user approved a full rebuild and direct soldering on 2026-10-22. This branch
of the mechanical design supersedes the requirement to preserve the printed V5
carrier **only for this new concept**. The existing Fusion V9 project and exports
remain the historical, printed design.

## CAD brief

- New two-piece enclosure and illustrative electronics assembly, independently
  designed from the approved layout; Iskra is a visual/packaging reference.
- Units mm. Origin rear-left at the bottom of the cover. X right, Y toward the
  user, Z up. Flat top for the first prototype.
- Exterior 106 × 74 × 18.8, corner radius 4; roof 2.4, walls 2, bottom 2.4.
- Six existing MX switches and 18 mm caps on a 19.05 mm pitch; direct wiring.
- OLED PCB 36 × 34 × 1.6 on the right, external face up. Support the PCB edges;
  use removable edge retainers. Do not press on the glass.
- ESP32-S3 SuperMini exposed above the rear top, pins/wires downward, direct rear
  USB access. Its 24 × 20 envelope is provisional; lower components, pads,
  connector and antenna keep-out must be measured before mounting is finalized.
- Encoder at X47/Y14, measured bushing Ø7, thread length 7, hole Ø7.4. Board
  26 × 19 and total board-to-knob height 29 are documented; axis centering,
  body depth, knob diameter 20, and electrical lead projection are provisional.
- No perfboard, hotswap holders, LED strip or diffuser.
- MCU outline is shifted 3 mm right from the initial sketch to clear the rear
  left cover boss. A provisional removable front-edge strap with integral legs
  and a stop opposes USB forces. Both electronics have separate flat-print cradles
  in 0.4 mm locating pockets; no external mounts project above the shell roof.
- Six M2 × L4 × OD3.5 inserts: four cover mounts and two MCU strap mounts, all
  on internal bosses. Pilot Ø3.2 × 4.5;
  heat-set fit remains a coupon check. M2 screw heads Ø4 × 2, clearance Ø2.4.
  M2 × 6 is a cover candidate (3.6 mm engagement); M2 × 8 is a strap candidate
  (3.75 mm engagement after the 4.25 mm strap/leg thickness). Verify real screws.
- Four illustrative rubber feet have 2.8 mm effective height; they are needed
  with the unrecessed screw heads. They are purchased parts, not printed solids.
- Primary outputs are STEP and source; any full-case mesh is a concept preview,
  not an approved print. MX coupon STL is a separate low-cost fitting test.
- Validate positive closed solids, dimensions, solid count, hardware-envelope
  collisions, mounting alignment, minimum assumed solder clearance and snapshots.

## Fit gates

The user measured the OLED hole pattern on 2026-10-22: **31 mm along the wide
side, 28 mm along the short side, holes Ø2.5**. Four Ø2.2 locating pins are now
enabled, giving 0.3 mm diametral clearance, with 0.5 mm conical leads ending at
Ø1.6. Their pattern is assumed centered on the 36 × 34 PCB; this center offset
still needs physical verification. Pins extend 0.7 mm beyond the 1.6 mm PCB.
They locate the board, but do not hold it against upward removal. Edge retention
remains pending safe PCB edge areas and glass-offset confirmation.

Switch openings 14.1/14.2 mm must be tested with the actual switches; old records
also mention 14 × 15.5, so no assumption of a proven standard fit is made. The
coupon has a 1.5 mm seat. Electronics are simplified explicit envelopes, not
manufacturer models. A step.parts query for ESP32 S3 SuperMini, SuperMini,
Cherry MX, SH1106 and KY-040 returned no matching records on 2026-10-22.

At 106 × 74 the footprint area is 14.7% smaller than 80 × 115. The more compact
appearance comes primarily from the shorter body, denser key spacing, and reduced
shell height. Height excludes caps, exposed MCU and encoder knob.

Fusion MCP was restored after the user enabled it. The updated STEP assembly was
imported into a **separate** Fusion document; the old enclosure was untouched.
The native mirror is static imported geometry; Python sources own its parameters.
`fusion-validation.json` records native Fusion checks independently of the
standalone OpenCASCADE `validation.json` report.

## C1 outputs and checks

- `compact_model.step`: assembled concept with explicitly labelled simplified
  electronics. `top_shell.step` and `bottom_cover.step`: independent parts.
- `oled_cradle.step`, `mcu_cradle.step`, `mcu_strap.step`: separate small parts;
  the large shell's exterior print face stays flat.
- `oled_fit_coupon.step` / `.stl`: the updated OLED frame translated to Z0 for
  printing with all four pins upward. Footprint 36 × 34, total height 3.5. Print
  flat in PLA, 0.15 mm layers, without supports; check insertion without force.
- `mx_coupon.stl` / `.step`: 44 × 25 × 1.5 fitting sample. In its original top
  orientation, X12 hole is 14.1 square, X32 hole is 14.2 square. Print flat, without
  supports; the small edge notch marks the 14.1 mm hole. Use
  0.15 mm layers including the first layer for the nominal 1.5 mm
  seating thickness. The successful opening must be tested with the actual switch.
- `validation.json`: six valid single solids; 210 enclosure-part-to-reference
  and enclosure-part intersection checks, zero positive-volume collisions. The
  assumed switch solder-tip clearance to the cover is 4.9 mm, excluding wire bends.
- `inspection.json`: STEP topology facts, major planes and positioning checks.
- `fusion-validation.json`: 45 connected imported solid bodies, five enclosure
  parts and 40 reference bodies; 210 native BRep intersection checks without
  collisions; native/source part bounds and volumes agree. Pin/hole cylinders
  have the same four centers at [67.5,35], [67.5,63], [98.5,35], [98.5,63] mm.
  Native pin diameters, hole diameters and four 0.5 mm leads were checked.
- `compact_c1_oled_31x28.f3d`: local native archive of that checked imported mirror.
  No cloud document was saved. `fusion_import.py` / `fusion_validate.py` reproduce
  the import, validation and local exports through the Fusion MCP script API.
- `previews/`: reviewed assembly isometric, opposed underside, top and front;
  shell interior, cover and coupon snapshots from the primary STEP artifacts.

The 18.8 mm dimension is the nominal shell top above the cover bottom. The separate
MCU strap reaches Z23.05; assumed keycaps reach Z31;
encoder knob reaches Z35.9; feet extend to Z−2.8. These are **not** an 18.8 mm
fully assembled device. Electronics sit at their explicit reference datums.

No full-case STL is released. Finalize hardware dimensions and OLED retention,
then inspect the shell roof-down in the slicer. Cradles print flat, and the strap
prints outer broad face down with its legs upward. The shell exterior is planar;
its shallow pockets and local switch-seat reliefs still require slicer/print QA.

The standalone generation environment used build123d 0.10.0, cadquery-ocp
7.8.1.1.post1 and ocp_gordon 0.1.17 with the installed CAD skill's `scripts/step`,
`scripts/inspect` and `scripts/snapshot`. CAD Viewer is not installed; snapshots
and deterministic B-rep/STEP checks plus the Fusion mirror are the available handoff.
