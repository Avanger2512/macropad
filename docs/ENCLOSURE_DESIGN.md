# Enclosure design brief

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
