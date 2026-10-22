# C2 — flush OLED, left encoder, no upper ESP32 clamp

User-approved revision of C1. C1 source/files and the old printed Fusion V9 are
preserved in their existing directories. Units mm; rear-left XY datum, +Z up.

## Layout and brief

- 100 × 82 footprint, nominal shell top Z18.8. The previous side-by-side key/OLED
  arrangement was changed to a rear control row and centered keys below it.
- Encoder axis X17/Y22; OLED center X75/Y22. Both controls share the same Y datum.
- Six 18 mm caps at 19.05 pitch, centered on X50, first row Y48, second Y67.05.
- ESP32 at X31/Y1, 24 × 20 provisional outline, exposed above the USB edge.
  The upper bridge/strap and its two insert bosses are removed. Only a lower
  seat with a front PCB-edge stop remains, below the component-side PCB surface.
- OLED PCB 36 × 34 × 1.6, positioned inside at X57/Y5/Z14.8. Assumed glass
  34.5 × 18.5 × 2.4 has top at Z18.8: nominally flush with the shell.
- Glass opening 34.9 × 18.9 with a 0.3 entrance bevel. This is a **glass window**,
  not a verified mask matching the active pixel area; glass size/offset are still
  the existing provisional envelope. No green OLED PCB or locating pins show above.
- Underside PCB relief leaves 0.2 clearance above its edges. The frame supports
  the PCB; nothing presses on the glass surface.
- Measured hole pattern 31 × 28, holes Ø2.5; locating pins Ø2.2. Pins now end
  flush with PCB top, with a 0.4 lead, so they do not hit the enclosure roof.
- Hidden frame base Z13.6, thickness 1.2. Four Ø4.4 OLED-only support columns
  rise from the lower cover and end at the frame underside. Their Ø2 dowels
  enter Ø2.3 × 0.7 blind pockets in the frame, providing lateral registration.
  Nominal shoulder contact carries the frame; no designed compression preload.
  With the cover installed, the roof stops the PCB lifting off its pins.
- Four M2 × L4 × OD3.5 cover inserts, pilots Ø3.2 × 4.5. Cover M2 × 6 is a
  candidate; four rubber feet must clear the 2 mm screw heads.

## Verification and remaining fit gates

Source BRep checks and native Fusion MCP checks must use this directory's STEP,
not the C1 mirror. Geometry is source-parametric Python; Fusion imports a static
mirror into a new document, preserving older open designs.

Check positive single-solid parts, all enclosure/reference intersections, flush
glass plane, hidden PCB/pins, matching control-row centers, seated frame dowels,
PCB/roof gap, and absence of the upper MCU strap. Review STEP snapshots and a
native Fusion screenshot. Physical tests still need actual MCU outline/components,
encoder board axis/contacts, OLED glass offset/height and short-pin insertion.
MCU upward retention is intentionally not provided by an upper clamp. The lower
stop opposes USB insertion, but its physical registration is not verified.

No full-case print release is implied by envelope checks. The hidden OLED frame
is a separate low-cost fitting sample. Do not use the old C1 raised-frame STL
for the flush C2 arrangement.

## Results

- `validation.json`: four assembled plastic parts plus the existing MX coupon
  checked as positive single solids; 166 enclosure/reference pair checks, zero
  positive-volume collisions. Calculated glass top and roof are both Z18.8.
- `fusion-validation.json`: 44 imported connected solids; native Fusion confirms
  the same 166 pairs, part dimensions/volumes, encoder/display Y22 alignment,
  flush glass, hidden PCB, four aligned lower-cover registration keys, and eight
  PCB-roof relief samples. No upper MCU clamp occurs in the imported assembly.
- `compact_c2_flush.f3d`: checked local native mirror; no cloud save. Parameter
  edits are made in the Python source, then regenerated/reimported.
- `oled_fit_coupon.step` / `.stl`: short-pin hidden C2 frame grounded for printing,
  36 × 34 × 2.8. Print pins upward, PLA, 0.15 mm layers, no supports. This checks
  the hole pattern and pin fit; it does not establish the glass Z datum by itself.
- `previews/`: STEP assembly isometric/top/front/opposed underside, shell inside,
  lower cover posts, hidden OLED frame and lower MCU seat. Native Fusion views
  are also saved. CAD Viewer is unavailable; snapshots and Fusion provide review.
