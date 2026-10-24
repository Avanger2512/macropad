# Enclosure design brief

Latest: [FINAL print set](../cad/print/README_FINAL.md), C5 full OLED34.5×23 flush using measured2mm height, window34.9×23.4, insert pocketsØ3.2×5.5, and integral-foot lower cover.


Previous compact revision: [C4](../cad/compact/c4/README.md),106×74×18.8, retains
C3 placement after the first physical test print. MX apertures are14.0mm with
1.5clip seats. OLED glass short side18.2 and margins6towardencoder/9away imply
a1.5mm shift toward encoder: corrected34.9×19window centerX83/Y47.5. The PCB
mounting pattern31×28 stays centeredX83/Y49. Four integral upper collars and
downward glue pins replace the separate frame and lower columns. ESP slots
are1.8×20.8 with15center spacing; no added MCU supports. STL exports and a
three-size MX fit sample are in C4. Detailed checks/assumptions in its brief.
C1/C2/C3 and the prior printed enclosure remain historical models.

Optional [retrofit wedge feet](../cad/compact/accessories/rear_feet/README.md)
use measured Ø10 × 2 mm pads. Two raised rear and two low front glued bases
give a 6 mm differential rise (about 6.1°), clearing the existing screw heads
without changing or reprinting the C4 shells.

Current direction, 2026-10-22: the user rejected the printed enclosure's size and
approved a complete Iskra-inspired redesign, reprinting every plastic part and
rewiring without the 70 × 50 perfboard, hotswap holders, LEDs or diffuser. The
previous instruction to preserve the printed middle carrier does not constrain
the new concept. Retain the old model as a historical version. See
[compact C1 brief and validation](../cad/compact/README.md).

The approved concept places six MX switches at 19.05 mm pitch on the left,
OLED on the right, exposed ESP32 above the rear top with pins downward, and
encoder beside the MCU. OLED locating pins through its mounting holes are
preferred, with support pads and removable edge retention. Hole diameter and
center spacing were subsequently measured: 31 × 28 mm, Ø2.5 holes. The C1 OLED
frame now has four Ø2.2 locating pins with 0.5 mm tapered leads. Pattern centering
on the PCB and upward retention remain to be confirmed. Native Fusion MCP checks
on the separate imported compact STEP mirror passed; see `fusion-validation.json`
in `cad/compact`.

The sections below describe the previous printed V9 architecture.

Status: native Fusion prototype with revised PCB mounts and bolt-free holder retention, October 13, 2026. Four enclosure bodies and two auxiliary fit samples now exist in the user's `macropad` Fusion Part Design document; see [native Fusion draft details](../cad/fusion/README.md). Physical component fit is not validated. All dimensions are in millimeters.

## Confirmed requirements

The user reports that the breadboard assembly, buttons, LEDs, and display have been assembled and tested. This is a new user confirmation, separate from the historical October 7 verification report.

- Approximate enclosure footprint: 80 wide × 115 long; dimensions may change to accommodate the assembled electronics.
- Three main enclosure parts: upper exterior part, structural middle carrier, and removable bottom service cover.
- Middle carrier rigidly attached to the main exterior part with screws and M2 brass heat-set inserts.
- A separate diffuser installed from inside, flush with the exterior and retained by an internal flange.
- Rear-to-front arrangement: LED strip, OLED on the left and encoder on the right, then six individual switches in two rows of three.
- USB-C exit near the LED end. Direct rear access to the ESP32 USB-C port is confirmed; no panel extension or adapter.
- Enclosure material: PLA Matte. Diffuser material: Translucent Mellow Yellow PLA.
- A tilted face must be incorporated from the beginning.
- Keycaps are confirmed by the user as 18 × 18 mm. Spread the keys evenly across the enclosure width, with equal visible gaps rather than the conventional compact key pitch.

## Component measurements supplied by the user

| Component | Supplied dimensions | Remaining fit information |
|---|---|---|
| Assembled perfboard | 50 × 70; mounting-hole center spacing 46 × 66; up to 5 below and approximately 17 above | Confirmed PCB thickness 1.6; header footprints, mating-plug overhang, wire bend space |
| LED strip | Four SK6812 LEDs, 67 × 10 | LED package height and RGB versus RGBW variant |
| KY-040 encoder | 26 × 19 × 29 including knob | Threaded bushing diameter and usable length, shaft diameter, knob diameter, wiring projection; the stated 7 mm opening needs to be matched to the bushing |
| SH1106 1.3-inch OLED | PCB 34 × 36 × 4; window 18.5 × 34.5 | Orientation of PCB dimensions, screen offset, glass versus visible display area, hole pattern and connector envelope |
| Cherry-style switch and keycap | Reported seat 14 × 15.5; 13.5 between retaining features; confirmed keycap 18 × 18 | Exact switch variant, clip geometry and seated position |
| Brass inserts | M2, several lengths and outer diameters shown in the supplied chart | M2 × L4 × OD3.5 is confirmed; printed pilot-hole size still requires a coupon |

The perfboard photograph shows an ESP32 near one edge, USB-C facing that edge, an LED connector on the right, an encoder connector at the lower right, and an OLED connector at the lower left. Board outlines alone do not include connector or cable envelopes.

## Existing hot-swap holder

Source: [whotswap-MX-v2.3mf](../cad/whotswap-MX-v2.3mf).

The millimeter-unit mesh in `3D/Objects/object_1.model` has a bounding box of approximately **11.0315 × 9.7491 × 5.2**. Its component transform is identity; the build transform translates it on the print bed. These are mesh bounds, not measured switch seating or electrical engagement dimensions.

The user tested solid copper 22 AWG wire in this holder. The wire is retained firmly and the switch inserts with a tight interference fit. No alternate contacts were available for comparison. This establishes an initial mechanical trial, not verified contact durability over repeated switch replacements.

Initially use supported, removable holder pockets in the middle carrier. Provide a positive mechanical seat so insertion loads pass through the carrier rather than relying on electrical pins as an end stop. Leave the holder replaceable until insertion force, pin alignment, electrical continuity, and repeated replacement have been checked. Integrating the proven geometry into a monolithic middle part remains an option after the coupon passes.

## Proposed construction

- **Upper exterior part:** visible shell and trim, OLED opening, supported encoder nut seat, and diffuser opening. Where switches are supported by the middle carrier, the upper trim must clear their housings and retaining clips; do not create a second conflicting seating plane.
- **Middle carrier:** structural switch seating plate, ribs, supported contact-holder pockets, cable paths, and PCB standoffs. It attaches rigidly to the exterior part. Pressing and inserting switches must load this structure.
- **Bottom cover:** separate service screws so the cover can be removed without loosening the switch carrier. Removing it exposes PCB fasteners, plugs, and wiring.
- **PCB mounting:** use the board's mounting holes and dedicated standoffs, with clearance under solder joints. Locate the board independently of the wiring. Make BOOT/RESET accessible for service and support the board against USB plug insertion forces.
- **Diffuser:** flush exterior tongue with an internal flange on a locating ledge, retained by the carrier or an internal mechanical feature. Reserve space for the full 67 × 10 strip, wire exit, and an adjustable LED-to-diffuser air gap.

## Initial layout and parameters

These values are proposals, not final manufacturing dimensions.

- For the current 80 mm exterior width and confirmed 18 mm keycaps, use **6.5 mm visible gaps**: `(80 - 3 × 18) / 4 = 6.5`. This makes the two gaps between columns equal to the two exterior edge margins. Column centers are **15.5, 40, and 64.5 mm** from the left exterior edge.
- Use **24.5 mm center spacing** in both directions, measured in the face plane: `18 + 6.5 = 24.5`. The six keycap envelopes occupy **67 × 42.5 mm**, excluding exterior margins. This intentionally replaces the previous 19.05 mm pitch proposal; conventional MX spacing remains a reference, not the selected layout.
- Use 6.5 mm as the initial shared visible gap for other components. Place the display toward the left with an edge margin. Encoder centering in the remaining right-hand area, with its center aligned vertically to the display window center, is the current interpretation and remains to be confirmed. Final vertical placement depends on the knob diameter, diffuser opening, and internal component envelopes; equal gaps do not establish collision-free packaging.
- Conventional MX reference geometry uses an approximately **14 × 14 mm** plate opening and a roughly **1.5 mm** clip-engagement thickness. The user's 14 × 15.5 measurement must be reconciled with the actual housing and clips before choosing the final opening.
- Reinforce the surrounding carrier with thicker material and ribs while retaining clearance for the switch clips. The whole printed carrier does not need to be only 1.5 mm thick.
- Provisional tilt: **5°**, rear higher. For a 115 mm horizontal footprint, rear-to-front height difference is about **10.1 mm**. The current prototype uses a 29 mm front height and approximately 39.1 mm rear height. At 10°, it is about 20.3 mm. Absolute enclosure heights remain undecided until the complete vertical stack is measured.
- Initial wall estimate: **2–2.4 mm**, with locally thicker insert bosses and structural supports.
- The confirmed insert is **M2 × L4 × OD3.5**. Boss and pilot-hole dimensions require the real insert and a PLA coupon. D1/D2 in the supplier drawing describe the insert, not a guaranteed printed hole size.
- Orient the OLED PCB with its 36 mm dimension across the enclosure if that matches the actual glass and connector orientation; this can accommodate a 34.5 mm window without treating the narrower 34 mm PCB dimension as the screen width.

## Main packaging decision

Direct rear USB access suggests placing the perfboard's 70 mm edge across the enclosure. In an 80 mm exterior width, 2–2.4 mm walls leave only 75.2–76 mm internal width. A centered 70 mm board therefore leaves about 2.6–3 mm per side before accounting for connector overhang, plugs, or wiring. The right-side LED connector can invalidate that arrangement.

A lateral USB exit requires rotating the board or adding a panel extension. Rotation puts 70 mm along the enclosure length and may overlap the switch-holder region; an extension introduces its own plug and cable envelope. The user selected direct rear access without an extension; retain the 70 mm-wide, 50 mm-long board orientation as a candidate until connector clearance is measured.

Keep the PCB below the rear controls as a candidate layout, with OLED and encoder mounted independently above it. Their complete vertical envelopes, wiring, and accessible fasteners must be checked before setting thickness or PCB orientation. Avoid locating the main PCB under the switch field unless the measured stack fits without contact or wire interference.

## Next validation

1. Measure board mounting holes, all assembled heights, and mating connector envelopes. USB orientation is confirmed as direct rear access; measure the actual port position.
2. Identify the switch clip geometry and encoder threaded bushing. Confirm OLED orientation and mounting features. Keycap size is already confirmed as 18 × 18 mm.
3. Print a one-switch coupon using the actual holder and copper wire: test nominal 14.0, 14.1, and 14.2 mm openings as candidates, clip engagement, key travel, pin alignment, continuity, and several insertion/removal cycles. Adjust sizes based on measurements rather than assuming the metal-plate tolerance transfers to FDM.
4. Print a small heat-set insert coupon and a diffuser sample in the selected materials. Compare diffuser thicknesses and LED spacing before fixing the optical cavity.
5. Build a rough component-envelope assembly and a section view; then finalize the three enclosure parts.

## Reference sources

- [CHERRY MX Series manufacturer drawing, hosted by SparkFun](https://cdn.sparkfun.com/datasheets/Components/Switches/MX%20Series.pdf): switch dimensions and metal-frame cutout reference.
- [CHERRY Keymodule MX manufacturer document](https://deskthority.net/wiki/images/d/de/Keymodule_MX.pdf): standard MX key spacing.
- [KiCad official MX 1U plate footprint](https://raw.githubusercontent.com/KiCad/kicad-footprints/master/Button_Switch_Keyboard.pretty/SW_Cherry_MX_1.00u_Plate.kicad_mod): 1U envelope and pin layout reference.

This brief preserves user measurements and current design proposals; it does not certify clearances or manufacture readiness.

## Iteration 2: fasteners and carrier reinforcement

The user intends to assemble and solder the switch wiring on the removable middle carrier before final enclosure assembly. Keep the carrier accessible from below and provide replaceable contact holders after their seated depth is verified.

Four face-normal M2 carrier fasteners use wall-connected 7 mm shell bosses and locally thickened carrier pads. The bosses end 7.4 mm below the exterior face; the pad bottoms are 10 mm below that face. Clearance pockets leave a 0.4 mm axial gap and 2.2 mm pad floors. Four independent vertical M2 bottom-cover fasteners use 6 mm-diameter, 6 mm-tall bosses above the 2 mm lid. Front posts are moved inward; rear posts are near the back corners. Vertical reliefs in the carrier clear these posts during removal. The carrier rim is 7 mm wide to preserve connectivity around the reliefs. Both systems use the confirmed M2 × 4 × 3.5 mm inserts, with provisional 3.2 mm pilot holes and 4.5 mm pilot depth. Verify the pilot with PLA coupons before printing the complete enclosure.

Two longitudinal ribs and one transverse rib reinforce the switch field from below. They stay away from the switch openings and preserve the local 1.5 mm clip-seating thickness. The lid currently has through holes; screw-head recesses or feet remain to be designed after selecting the screws.

PCB supports, direct rear USB opening, hot-swap holder supports, display retention and LED strip retention remain pending. In particular, the rear upper/lower bosses reserve space near the board corners; no electronic component fit is claimed.

## Additional board measurements

The user supplied a 66 × 46 mm mounting-hole pattern on the 70 × 50 mm board. Centering that pattern gives provisional 2 mm edge offsets; equal offsets should be confirmed on the actual board. The assembled board projects at most 5 mm below and approximately 17 mm above the PCB surfaces. PCB thickness is confirmed as 1.6 mm. The tallest components are the three headers; their footprints remain to be measured.

The USB-C connector does not extend beyond the perfboard edge. Its lower and upper edges are respectively 4 mm and 7 mm above the PCB, giving a 5.5 mm center height above the PCB. The 36 mm lateral center coordinate is confirmed from the left edge of the 70 mm board side. Direct rear access is required without adapters. The opening must accommodate the plug body when the receptacle is recessed behind the rear wall.

These new envelope measurements may require increased enclosure height or a revised local component arrangement. At that earlier stage, the 22 mm front height was provisional. The later prototype uses 29 mm and revised PCB mounts; do not approve electronics fit solely from enclosure-body geometry. Rear board holes must remain accessible and must be checked against both fastening systems.

## Confirmed PCB datum and connector height distribution

PCB thickness is confirmed as 1.6 mm. The USB-C center is 36 mm from the left edge of the 70 mm side. For a centered board in the current 80 mm enclosure, its provisional enclosure X coordinate is 41 mm. The receptacle center is 5.5 mm above the PCB top surface, based on its measured 4–7 mm height range.

The approximately 17 mm upper envelope occurs at three connection headers: two along the front edge of the board and one along the right side. It is not a uniform height across the ESP32. Header footprints and mated cable projections are still required for local collision checks against the OLED, encoder, carrier, and rear mounting systems. The bottom solder/wire envelope remains 5 mm below the PCB underside.

## JST-XH connection envelopes

The user identifies the headers as JST-XH, with measured housing lengths of 15 mm for 5 pins, 13 mm for 4 pins, and 10 mm for 3 pins. The two front headers are flush with the board edge. The right-side header is 3 mm inboard of the edge; confirm whether this measures the housing edge or its centerline before placing a final envelope. Housing widths and lateral offsets of the two front headers are still unspecified.

The approximately 17 mm height includes mated plugs and outgoing wires. The user expects wire routing may reduce this to 13–14 mm. Keep 17 mm as the measured current envelope and 14 mm as a conditional routing target until physically verified. At the current provisional PCB top Z10.4, a 14 mm header envelope reaches Z24.4, leaving only approximately 0.633 mm beneath the bare inner roof at the board front. This does not establish clearance to the OLED, encoder, carrier or individual wires.

Manufacturer reference: [JST XH datasheet](https://www.jst-mfg.com/product/pdf/eng/eXH.pdf) lists a 9.8 mm assembled height for standard top-entry XH and a 5.7 mm housing depth. Wire bends add to that height. Use the user's measured complete envelope for packaging; nominal catalog geometry does not establish the exact installed variant or cable clearance.

## Iteration 3: heat-insert access and print support

The user rejected upper insert placement near the side walls because the soldering iron can damage the shell. Upper carrier fasteners now use X12/68 mm; front centers are at face Y10.5, and rear centers at approximately Y105.8. At the insert-entry plane, nominal center-to-inner-wall clearance is 9.6 mm to the sides, approximately 8.7 mm at the front and 6.6 mm at the rear. These values describe the entry plane; they do not certify access for an arbitrary iron barrel along its complete approach. Install upper inserts before the diffuser, carrier or electronics.

Carrier pads are now 12 mm wide and centered on the relocated fasteners. The diffuser-flange recess is restored wherever a moved pad crosses it. Lower fastener coordinates remain unchanged: front X20/60,Y4.8; rear X4.8/75.2,Y112. The lower rear X coordinates have been decoupled from the upper mount parameter.

Two 45-degree triangular gussets connect the front lower bosses to the front wall. Rectangular vertical removal corridors clear these gussets when extracting the middle carrier. Rear lower boss reinforcement is deferred because it could intrude into the PCB envelope.

Print the upper shell with the inclined exterior face flat on the bed, and the middle carrier with its switch seating face toward the bed, ribs and pads upward. The gussets reduce the abrupt front-boss overhang. Local pocket roofs, rear lower bosses and component openings still need slicer review; no support-free print is claimed. Retain the selected 5-degree operating tilt and existing top component layout.

## Planned switch and display mounting

The switch clip seats belong to the structural middle carrier. The copper-contact holder geometry will be incorporated below each switch after a single-switch seating/contact coupon establishes its depth and pin alignment. The complete middle switch assembly should be wireable outside the shell.

Mount the OLED on an internal locating frame attached to the upper shell. Removable screw-fastened clamp tabs should retain the PCB against the frame without loading the glass. Verify screen-to-PCB offsets, edge clearances, cable access and the encoder envelope before modeling the final frame.

## Confirmed switch holder datum

The user measured 7 mm from the underside of the switch seating flange to the top of the assembled printed contact holder. Use that datum for the trial contact-holder seat. It does not independently confirm XY pin registration, FDM clip fit or repeated insertion force; verify those on a single-switch coupon before the six-button carrier is approved.


### Confirmed PCB flip and revised attachment

The ESP32 and JST side faces the bottom cover; the solder side faces the middle carrier. Continuous perimeter rails with four short mounting bosses replace the iteration 4 hanging supports. Mounting holes retain their 66 × 46 mm pattern. The horizontal solder face is Z22.3 mm, with the component face Z20.7 mm. The provisional 17 mm downward envelope leaves 1.7 mm above the lid. Maintain an open center for the measured 5 mm upward solder projection.

The flip preserves the rear USB direction but mirrors the measured transverse offset: USB center becomes X39 mm and Z15.2 mm. The side JST moves to the left. Native enclosure-body validation passed; hardware envelopes, the USB cutout and assembled carrier extraction remain pending. The PCB must be removed before the carrier while rear lid posts obstruct the assembled downward path.


### Bolt-free hot-swap holder retention

Receivers are integral to the middle carrier. External snap hooks retain the existing separate printed holders; upper stops prevent upward withdrawal with the switch. Side windows route contact wires. The bottom cover adds reinforced fork supports with inclined bearing faces and a 0.2 mm normal clearance. No switch-holder mounting bolts are required.

Do not center the holder bounding box on the switch: the supplied mesh central cylinder is at X−0.08972306/Y+1.49765268 mm. Place holder-local origin at switch center plus X+0.08972306/Y−1.49765268 mm. The cylinder is interpreted as the switch center-post reference and must be checked in the one-button coupon. Preserve the holder orientation across all six pockets.

Verified mesh plastic bearing lands: bottom X±2.5/Y−1.2 mm, 1 × 3 mm per lid contact; top X±3/Y+4.3 mm, 1 × 0.6 mm per upper contact; snap contact bands X±5.215..5.515, Y2.7..4.7 mm at the bottom face. Contact holes elsewhere make generic edge supports unsuitable. The measured 7 mm flange offset sets holder top normal depth 9.8 mm and bottom 15 mm. Physical PLA flex, actual pin alignment, wire clearance and print support choices remain trial checks.

## Physical assembly feedback and enclosure finishing — 2026-10-20

The user printed the current middle carrier, installed the switches in the
hotswap holders, and confirmed that the PCB mounting fits. Preserve that printed
carrier and its mounting geometry in subsequent enclosure revisions.

Requested next changes:

- Remove the twelve obsolete bottom-cover holder contact posts, including their
  reinforced stems and inclined cap cuts. Preserve the four bottom-cover screw
  fastenings. The transverse retaining pins now retain the holders.
- Add direct rear USB access. Current documented connector center is X39/Z15.2 mm;
  the rear board edge is Y112.2 mm against exterior Y115 mm. The opening must pass
  the cable plug moulding through at least 2.8 mm of recess. Actual plug width,
  height and shoulder/insertion reach remain to be measured before final sizing.
- Add exterior chamfers, initially targeting 0.8 mm on safe outer edges and
  0.3–0.5 mm on the USB entry. Preserve functional seats and mating faces; validate
  remaining wall thickness and native feature health after selecting edges.
- Evaluate a smaller operating tilt while preserving the printed carrier. Do not
  simply change `caseTilt`: the carrier has horizontal PCB mounts and channel
  sketches constrained at the original evaluated pose. Consider rigid rotation
  of the installed assembly and adaptation of the lower shell/cover instead.

At 115 mm depth, reducing 5 degrees to 3 degrees changes the nominal exterior
height difference from 10.061 to 6.027 mm. Existing documented component clearance
above the lid is only 1.7 mm (component envelope bottom Z3.7, lid top Z2). Thus a
roughly 4 mm rear lowering cannot be assumed to fit. Retaining rear height and
raising the front is a candidate; exact minimum clearance requires a transformed
hardware-envelope check in Fusion.

Other open items: encoder bushing and knob dimensions, OLED/diffuser physical fit,
wire bends, screw-head recesses or feet, and the service removal sequence. Earlier
sampled carrier extraction checks found obstructions; physical carrier/PCB fit
confirmation does not establish the complete extraction path.

Execution status: no enclosure geometry has been changed in this session. The
configured Fusion MCP server exposed its script API, but the active-model
inspection request timed out. No new STEP/STL/F3D or geometry validation results
were produced. The above dimensions are from existing project records, not a live
measurement of the currently open Fusion document.

### V6 implementation and native validation

Fusion MCP connectivity was restored through the configured localhost endpoint.
V6 now removes all twelve lid support posts and their stems, adds the rear
14 x 10 mm USB throat with 0.5 mm entry chamfer, and applies 0.8 mm exterior
chamfers to the shell top/corners and the underside perimeter of the cover.
The printed V5 carrier and PCB mounting geometry remain unchanged.

User button measurements define BOOT X44/Y102.2 and RESET X35/Y102.2 in enclosure
coordinates, both with 3 mm through holes in the bottom cover. This follows the
same mirrored component-side board datum as USB: 31 mm to BOOT from original
board-left, 30 mm to RESET from the opposite edge, 9 mm between centers, and
10 mm from the rear 70 mm board edge. Physical reach through the bores remains
an assembly check.

Native Fusion validation passed healthy active features, constrained sketches,
four connected solids, no pairwise solid overlaps, 125 unobstructed USB-throat
samples and 96 unobstructed service-bore samples. Carrier, diffuser and reference
body volumes match the pre-change baseline. Report:
`cad/fusion/exports/enclosure-v6-validation.json`.

For a rigidly repositioned assembly at 3 degrees, retaining rear roof height
raises the front roof to 33.020 mm and gives a conservative component/lid gap of
1.819 mm. Retaining front height instead produces a negative gap of -2.200 mm.
These are feasibility estimates, requiring lower-shell/cover and footprint
adaptation before a smaller-angle variant can be approved. V6 retains 5 degrees.

### V7 lower-cover mounting supports

Two front cover bosses now extend to the internal roof while preserving the
6 mm diameter, existing axes, lower seating faces and insert pilots. The printed
carrier is unchanged. Rear full-height posts would intersect the PCB substrate;
rear wall-connected 55-degree gussets replace that idea at the existing rear
bosses. Their slope is approximately 50 degrees above the bed with the shell
roof-down and their maximum Z is 13.184 mm.

Native validation confirms no enclosure-body intersections or intersection with
the nominal PCB substrate. Actual downward-facing components/wires still need
checking near X17..23/57..63,Y109..112.7. This revision targets support beneath the
cover mounts, not every overhang in the shell. The V6 lower cover remains valid.

### Pre-print audit and V8 corrections

The V5 printed middle carrier must not be changed or reprinted. V8 retains that
body exactly through targeted shell/diffuser operations and confirms its original
native volume; the lower cover remains V6. V7 gusset corner interference during
installation was resolved by clipping gussets inside the existing 6 mm cylindrical
boss envelope. A 0.355 mm maximum trim of the hidden rear diffuser flange/skirt
clears the other installation obstruction. The removed diffuser material lies
at normal depths 2.4–6 mm, leaving the optical skin and visible plug unchanged.
The bare carrier now passes 161 sampled vertical placements through 40 mm.
Fully populated hardware and wiring are outside this path check.

The encoder bushing is measured as diameter 7 mm, threaded length 7 mm. Only the
upper hole changes to 7.4 mm for diametral print clearance. The printed middle
and its mounting do not change.

Remaining checks before the large print: physical insert seating, OLED/glass
registration, encoder push/knob envelope, actual rear component/wire clearance,
USB plug insertion reach and BOOT/RESET tool access. Inspect the 14 mm USB roof
bridge in the printer's slicer. The chosen insert is M2 x L4 x OD3.5 mm; eight
are used. A nominal M2 x 6 mm screw leaves 4 mm engagement through the 2 mm lid.
User screw heads are diameter 4 x height 2 mm, so add feet with more than 2 mm
installed clearance if keeping the unrecessed lid.

Low-risk visual improvements: gray matte shell with a light/translucent diffuser,
a matching dark encoder knob, four hidden rubber feet and small underside
BOOT/RESET marks after verifying button identity. A locating lip for a more
consistent cover seam is a future option, requiring its own fit check. Large
corner changes and new electronics seats are deferred until physical assembly.
