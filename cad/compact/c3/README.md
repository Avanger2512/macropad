# Compact C3 — original layout with flush OLED

Historical first printed compact case. [C4](../c4/README.md) corrects its
physical fit issues and replaces the separate OLED frame with upper glue pins.

## CAD brief

User requested restoring C1 placement with C2 recessed display: six keys left,
OLED right alongside the keys, MCU above keys, encoder above OLED. No MCU seats,
rails, strap, clearance pocket or central aperture: only two pin slots. User
will secure the PCB from inside using adhesive after inserting its pins.

Units mm; rear-left bottom datum; X right, Y toward user, Z up.
Exterior 106 × 74 × 18.8, roof/walls/cover 2.4/2/2.4, corner R4,
outer roof chamfer 0.6. C1 and C2 artifacts remain unchanged.

- Keys: X14/33.05/52.1, Y39/58.05, pitch19.05; MX seat1.5.
- OLED PCB: X65/Y32, 36×34×1.6, undersideZ14.8. Glass34.5×18.5×2.4
  nominal topZ18.8 flush. Glass dimensions/offset are provisional.
- OLED measured hole pitch31×28, holesØ2.5; hidden frame pinsØ2.2 with
  0.4 lead cones. C2 lower-cover supports and 0.2 roof clearance retained.
- Encoder axis X83/Y14 shares OLED centerX83; PCB envelope26×19.
- MCU X8/Y1, provisional24×20; PCB underside rests directly atZ18.8.
  Two through slots1.8×16 centeredX9.3/30.7, Y3..19. No added MCU supports.
  Actual pin row spacing, underside protrusions and header insulation must be
  measured before releasing a full print. This assumes bare pins below PCB.
- Four M2 L4 OD3.5 insert pilotsØ3.2; screw headØ4×2 and feet2.8.
- No perfboard, hotswap holders or LED/diffuser.

## Validation and outputs

Source BRep validation: four checked single solids including MX coupon;
123 printed-part/reference and printed-part pair tests, no positive overlaps.
Primary assembly inspected with facts/planes/positioning; snapshot packet
reviewed. Native Fusion MCP checks passed 123 pairs with no intersections and confirmed
flush OLED, encoder/display X alignment and direct MCU roof contact. Native
results are recorded in fusion-validation.json; compact_c3_flush.f3d is saved.
Named component envelopes remain provisional; no full-case STL release yet.

Sources own parameters. STEP and local F3D are derived mirrors. CAD Viewer is
not installed; use the snapshots and Fusion document for visual review.

## Test print preparation

Print three plastic parts: top shell, bottom cover, and the separate OLED frame.
`oled_fit_coupon.stl` is the complete C3 OLED frame translated to Z0, not a
partial coupon. Print flat ring down, locating pins upward. Its STEP and mesh
inspection reports are adjacent. Upper/lower STL files exported by the user
have not been inspected here. Check pin slots on the real ESP and dry-fit all
electronics before installing inserts or applying adhesive. Current geometry
assumes flat MCU underside with bare pins.
