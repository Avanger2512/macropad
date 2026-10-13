# Native Fusion enclosure draft

The editable model is in the active Fusion Part Design document named `macropad`. Four enclosure bodies and two auxiliary trial bodies are in the same document:

- `UpperShell_Draft`: inclined exterior shell with six trim openings, OLED window, provisional encoder opening, diffuser opening, four carrier insert bosses, and four independent bottom-cover insert bosses.
- `MiddleCarrier_Draft`: switch plate, six contact-holder receivers with snaps and upper stops, PCB mounting rails and posts, opposed OLED retention, and an LED support tray.
- `BottomCover_Draft`: service cover with four M2 screw holes and six pairs of inclined holder support posts.
- `Diffuser_Draft`: open-back hollow flush insert with an internal retaining flange and wire exit.
- `SwitchFitCoupon_Trial` and `LidSupportCoupon_Trial`: separate one-button fit samples.

## Parameters and layout

The prototype has named user parameters and a native feature timeline. Current exterior footprint is 80 × 115 mm, tilt is 5°, and overall height is 29 mm at the front and approximately 39.061 mm at the rear. Heights remain provisional. Current STEP/F3D files are `exports/macropad_switch_retention_with_trials.step` and `.f3d`; they include the four enclosure bodies and two auxiliary samples. Earlier exports and the sections describing earlier iterations below are historical.

Confirmed 18 × 18 mm keycaps use 24.5 mm row and column spacing and 6.5 mm horizontal gaps. The layout is centered along the inclined face, with equal visible gaps between the key field, controls row, and LED opening. The display is on the left; the encoder is centered in the remaining right-hand area. Encoder knob diameter is a 20 mm placeholder, and its 7 mm hole still requires a threaded-bushing measurement.

Edit user parameters in Fusion's Parameters dialog. Parameter names, feature names, code, and documentation are English.

## Files

- [macropad_enclosure.py](macropad_enclosure.py): initial native Fusion generator. It refuses to run in a populated design to avoid overwriting existing work. Continue editing the existing Fusion document rather than rerunning the initial generator.
- [macropad_iteration2.py](macropad_iteration2.py): incremental native generator for fastening and reinforcement. It runs once on the initial draft.
- [STEP draft](exports/macropad_enclosure_draft.step): all four solids in assembled positions.
- [Native Fusion archive](exports/macropad_enclosure_draft.f3d): local backup of the editable model and timeline.
- [Fusion screenshot](exports/macropad-draft-iso.png).
- [Validation report](exports/validation.json).

The local archive export does not save a new cloud version of the open Fusion document. Save the open document in Fusion when ready.

## Verification

Native Fusion API checks confirmed four positive-volume solids, no volumetric interference between them, no timeline warnings or errors, and fully constrained sketches. On the initial draft, a parameter variation to 84 mm width and 10° tilt passed, followed by restoration to 80 mm and 8°. Iteration 2 at 80 mm width and 5° tilt passed the solid, interference, timeline, and sketch checks. Sixteen sampled downward carrier translations from 0 to 35 mm showed no volumetric intersection with the upper shell or diffuser; see [removal validation](exports/removal-validation.json) and [read-only verification source](verify_carrier_removal.py). This is a sampled geometric check, not a physical assembly test.

The local CAD inspection and STEP snapshot commands were attempted but could not run because the local Python runtime lacks cadpy/OCP dependencies. Visual review therefore uses the native Fusion screenshot. A separate CAD Viewer integration is not installed; Fusion is the active viewer.

These checks cover the draft enclosure bodies. They do not establish fit with the physical switches, perfboard, connectors, encoder, or display.

## Next mechanical work

The draft still needs hot-swap holder integration and verified contact depth, PCB mounting standoffs, component retention, direct rear USB-C access, and wiring clearance. Bottom screw-head recesses or feet remain to be designed. Corner rounding and print-fit tolerances will follow those decisions. Do not treat the exports as print-ready.

Measured components and design decisions are recorded in [the enclosure brief](../../docs/ENCLOSURE_DESIGN.md).

## Iteration 2 construction

The carrier can be assembled and wired outside the enclosure. Its four M2 screws are normal to the tilted face and accessible after removing the cover. Local pads retain 2.2 mm floors under the shell bosses; the switch clip seats remain 1.5 mm thick. Boss pockets include additional radial clearance for vertical carrier extraction. Four vertical bottom-cover screws are independent of the carrier screws. Front cover posts are at X20 and X60, Y4.8; rear cover posts are at X4.8 and X75.2, Y112 for the current footprint. Vertical reliefs let the carrier pass the lower posts.

Inserts are confirmed M2 × 4 × 3.5 mm. The 3.2 mm pilot diameter is provisional and must be tested in PLA Matte; pilot depth is 4.5 mm. Carrier bosses are 7 mm diameter, bottom bosses 6 mm diameter.

The 70 × 50 mm perfboard is intended for direct rear USB access without an adapter. Standoffs and the USB opening require header footprints and mated-plug envelopes. PCB thickness is confirmed as 1.6 mm and the USB lateral datum as 36 mm from the left board edge. The supplied hole pattern is 66 × 46 mm, and assembled projections are 5 mm below and approximately 17 mm above the board. These envelopes may require a taller enclosure. No electronics fit is claimed.

- [Interior view](exports/macropad-iteration2-interior.png): bottom cover hidden.
- [Carrier view](exports/macropad-iteration2-carrier.png): isolated middle part from below.
- [Iteration 1 STEP backup](exports/macropad_enclosure_iteration1.step).
- [Iteration 1 Fusion backup](exports/macropad_enclosure_iteration1.f3d).

## PCB layout guides

[macropad_pcb_layout.py](macropad_pcb_layout.py) adds 19 parameters and construction guides only. The historical candidate board bounds are X5–75, Y62.2–112.2, with underside Z8.8 and top Z10.4. Confirmed mounting centers are provisionally X7/73 and Y64.2/110.2, assuming equal 2 mm edge offsets. USB center is X41, Z15.9. See [layout measurements](exports/pcb-layout-validation.json).

The 17 mm headers reach Z27.4; the inner roof at the board front is Z25.033. Local header footprints must be checked before deciding enclosure height. Rear PCB mounting centers project over the rear lid posts, so separate PCB supports and screw access need a revised arrangement. No board fit or final USB cutout is approved by these guides.

Header measurements are recorded as 10/13/15 mm lengths for 3/4/5 circuits. The current measured height remains 17 mm including plugs and wires; a separate 14 mm routing target is conditional. Front headers are flush with the board edge, and the side header is reported 3 mm inboard. Exact housing widths and front lateral coordinates remain pending.

## Iteration 3 revision

[macropad_iteration3.py](macropad_iteration3.py) moves the upper insert axes away from the side walls, recenters and widens their carrier pads, preserves the diffuser clearance and adds two 45-degree front lower-boss supports with matching extraction corridors. Lower fastening coordinates stay unchanged. Upper centers are X12/68, with front face Y10.5 and rear face Y105.8. Nominal insert-entry wall clearances are 9.6 mm sideways, 8.7 mm forward and 6.6 mm rearward; full solder-tool access remains tool-dependent. Install inserts before the diffuser and electronics.

The upper shell should be oriented with its exterior face flat on the print bed; the carrier seating face goes toward the bed. Small pocket bridges and rear lower-boss overhangs still require slicer review. No support-free claim is made.

[Iteration 2 STEP](exports/macropad_enclosure_iteration2.step) and [Fusion archive](exports/macropad_enclosure_iteration2.f3d) preserve the previous state.

[Iteration 3 interior view](exports/macropad-iteration3-interior.png) shows relocated upper mounts and front cover supports.


## Iteration 4 prototype

The active Fusion model now has an open-back hollow diffuser, an LED support crossbar with a wire exit, four PCB mounting posts and opposed OLED PCB retaining strips. OLED PCB thickness is 1.6 mm; its provisional slot is 1.8 mm. The rear OLED support was shortened to clear the diffuser. Native validation passed: four connected solid bodies, healthy timeline features, constrained sketches and no body interference.

The 5-degree slope is retained. Front height is now 29 mm and rear height approximately 39.061 mm to accommodate the measured connector envelope. PCB pilots are provisional 1.7 mm holes for trial M2 screws in plastic. Rear lid fasteners move to X20/60 mm. Hardware clearance and the PCB removal sequence still need validation. The 7 mm switch-holder datum is recorded, but contact-holder seats and the rear USB opening are not yet implemented. This is a fit-test prototype, not an approved complete print.


## PCB orientation revision

The user confirmed that ESP32 and JST components face the removable bottom cover. [macropad_pcb_mount_revision.py](macropad_pcb_mount_revision.py) replaces the iteration 4 hanging supports with continuous carrier perimeter rails and four short downward screw bosses. The center remains open for solder-side projections. The solder-side seating face is Z22.3 mm and the component-side surface is Z20.7 mm. A 17 mm connector envelope reaches Z3.7 mm, giving a nominal 1.7 mm gap above the lid.

Flipping the board about its longitudinal axis retains rear USB access and mirrors its lateral position: USB center is X39 mm, Z15.2 mm; the side JST is now on the left. These values replace the previous X41/Z15.9 guide coordinates. The USB wall opening is still pending. Native checks passed for four solid bodies, healthy features, constrained sketches and no enclosure-body intersections. Encoder and cable clearance remain unverified. Remove the PCB before withdrawing the carrier until a complete assembled extraction path is validated; the rear lid posts obstruct a straight downward path with the PCB installed.

Historical PCB-revision exports: `exports/macropad_enclosure_pcb_revision.step` and `.f3d`.


## Bolt-free switch-holder trial

The carrier now uses six open-bottom receivers with two external cantilever snaps per holder, upper travel stops and side wire exits. The bottom cover has two reinforced support posts per holder with 5-degree bearing faces and a 0.2 mm normal gap. Holders are retained independently of their wires when the cover is removed. These features require a physical trial before the full carrier is approved.

The exact supplied 3MF bounding box is 11.03147984 × 9.74910164 × 5.2 mm. Its central cylindrical locating hole is offset from that bounding-box origin: X−0.08972306, Y+1.49765268 mm, with fitted diameter 3.99999888 mm. Holder pockets and retention features are translated X+0.08972306, Y−1.49765268 relative to each switch axis. The switch opening and outer frame stay centered on the switch. The large cylinder is interpreted as the MX center-post datum; confirm this interpretation on the physical coupon. Preserve the original mesh orientation; do not rotate individual holders by 180 degrees.

The measured 7 mm flange-to-holder-top distance gives holder normal depths 9.8 and 15.0 mm from the exterior face. Pocket clearance is 0.2 mm per side; retaining-hook overlap is 0.3 mm. Frame dimensions are 18.4 × 17.6 mm. Registered spring walls are approximately 0.71/0.89 mm thick, so insertion force and fatigue must be checked in the intended PLA Matte. Upper stops bear on mesh-local top lands around X±3/Y+4.3 mm. Hooks capture verified bottom edge bands Y2.7–4.7 mm. Lid contacts bear on mesh-local X±2.5/Y−1.2 mm lands, each 1 × 3 mm. Their top gap is 4 mm; the reinforced stems leave a 2.6 mm central passage. Check actual wire bends as well as the bare printed holder.

The new joins require the OLED PCB clearance to be cut again. Encoder clearance, the rear USB opening and the complete assembled removal path remain pending.

### Trial print sequence

Print the 22 × 22 mm `switch_fit_coupon.stl` and `lid_support_coupon.stl`, then use the existing `cad/whotswap-MX-v2.3mf` holder and the actual switch with 22 AWG contacts. The receiver STL is oriented with its flat switch plate on the bed; the lid sample is bottom-face down. Use millimeters and preserve scale. Start with 0.16 mm layers and a 0.4 mm nozzle. Inspect the two-wall spring sections and release slots in the slicer. Small local supports may be needed under the long snap lips and upper stops; do not fill spring-release slots with support. These are initial print settings, not a verified slicer profile.

Insert the holder from below until both snaps engage and its top reaches the stops. Confirm that the switch central post and contact pins align without forcing. Insert the switch from above and check plate-clip engagement. Confirm the holder stays captured when the switch is removed and the lid sample is absent. Gently deflect the exposed tabs outward for removal. Repeat several insertions and inspect for cracks. Check that the lid lands support plastic rather than wires, leaving the nominal 0.2 mm gap. Only then print the complete carrier and cover.

`macropad_switch_retention_with_trials.step` and `.f3d` contain the four enclosure bodies plus two auxiliary trial bodies outside the enclosure.


Final native validation passed for four enclosure bodies and two trial bodies: positive solid volumes, healthy timeline, fully constrained sketches and zero body intersections. `exports/switch-retention-validation.json` records the results. Both trial STL files have 22 × 22 mm bed footprints; their signed volumes and closed edge counts passed the checks in `prepare_switch_trial_meshes.py`. `exports/switch-trial-mesh-validation.json` records export scale and print poses. These checks do not verify spring fatigue or actual hardware fit.

The standalone STEP snapshot renderer is unavailable because its OCP dependency is missing; CAD Viewer is not installed. Native Fusion screenshots provide the visual check: `exports/macropad-switch-retention-carrier.png` and `exports/macropad-switch-retention-lid.png`. The F3D archive opens with the enclosure visible; auxiliary trial bodies are hidden.

STEP exports include only visible bodies in this Fusion setup. Make all four enclosure bodies and both trial bodies visible before exporting the complete STEP, then restore the desired view. The current complete STEP was checked for all six named manifold solids.
