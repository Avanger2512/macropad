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


## Compact holder fit trial V2

The supplied `cad/hotswap_mx__compact.stl` is now the reference. A separate `SwitchFitCoupon_Compact_V2` body at X145 mm preserves the first trial and the six main carrier receivers. `hotswap_mx__compact_REFERENCE_V2` is an imported reference mesh, aligned by its X0/Y0 central hole and the existing holder bottom datum; use its Browser eye icon to compare or hide it. The source STL remains unchanged.

V2 has continuous receiver walls, no spring snaps or hooks, 1.8 mm upper stops, and 3 mm high rounded side-notch guides with provisional 0.2 mm radial clearance. Four 1.5 mm wire channels follow the exact side-entry bore axes of the supplied STL (native bore diameter 1.1 mm). Two lower X bores have Y/Z centers -2.500016/1.138835 and -5.099996/1.172852 mm; the upper X bore is -3.011004/4.093049 mm, and the upper Y bore has X/Z center 4.190238/4.093049 mm. Full projection through opposite walls creates several visible entry/exit holes.

Print `cad/print/SwitchFitCoupon_Compact_V2.stl` in millimeters, without rescaling. Its footprint is 22 x 22 mm and height is 12.2 mm; the flat switch plate is already on the bed. Start with the same material and settings as V1 for comparison. Check upper-stop bridging in the slicer. Test insertion without force, guide clearance, wire threading through the assembled holder and receiver, and alignment with the actual switch. Removing the snaps means the bottom cover/support remains responsible for axial support; this trial does not establish standalone retention without the lid.

Native Fusion validation found one positive-volume V2 solid, healthy timeline features and fully constrained sketches. None of 2,770 unique reference-mesh vertices or 5,568 triangle centroids were inside the receiver solid. This is a sampled interference check, not proof of all surface clearance or physical switch fit. The printable STL is closed with positive signed volume. Reports are `exports/compact-v2-validation.json` and `exports/compact-v2-print-validation.json`. Native snapshots are `exports/compact-v2-receiver.png` and `exports/compact-v2-assembled.png`; standalone STEP inspection/rendering could not run because cadpy/OCP is unavailable, and a separate CAD Viewer is not installed.

Files: `macropad_compact_trial_v2.py` adds V2 once; `verify_compact_v2_fusion.py` validates and exports from the active Fusion document. `exports/macropad_before_compact_v2.f3d` preserves the pre-change state. `exports/macropad_compact_trial_v2.f3d` preserves the new document with the reference mesh. `exports/switch_fit_coupon_compact_v2.step` is the isolated V2 solid. These local archives do not save a new cloud version of the open Fusion document.


## Compact holder fit trial V3

V3 follows the physical report that switch pin tips sit 4 mm above V2's open receiver rim. It moves the compact holder 3 mm toward the switch, using local parameters only: top depth 6.8 mm and bottom depth 12 mm. The main carrier depths remain 9.8/15 mm. On that measurement, pin tips reach STL-local Z1 mm, near the two lower wire bore center heights 1.138835/1.172852 mm; actual electrical contact and switch body fit remain physical-test questions.

`SwitchFitCoupon_Compact_V3` is at X175 mm. `LidSupportCoupon_Compact_V3` raises the bearing plane by the same normal shift, preserving the 0.2 mm nominal gap. Its vertical stems rise approximately 2.989 mm and shift Y by approximately -0.261 mm because of the 5-degree face. Four receiver channels move with the holder and retain 1.5 mm diameter. Guides, stops and pocket clearances otherwise match V2. Compact STL itself is unchanged; its original wire channels are segmented rather than full-width bores. The body channels provide access aligned to those existing entrances, not a new through-bore through the source holder.

Print BOTH `cad/print/SwitchFitCoupon_Compact_V3.stl` (22 x 22 x 9.2 mm) and `cad/print/LidSupportCoupon_Compact_V3.stl` (22 x 22 x 18.832 mm). Both are oriented flat-side down in millimeters. Do not combine V3 with the old lid coupon. Confirm full switch seating, full holder seating against stops, pin engagement without bending, wire-entry access and support contact before printing a complete enclosure. Upper stops remain horizontal bridges; V3 did not change their support requirements.

`macropad_compact_trial_v3.py` creates the separate pair; `verify_compact_v3_fusion.py` validates and exports it. Previous trial bodies and the main enclosure were preserved. Native validation passed healthy features, constrained sketches, two positive solids, no receiver/lid volumetric intersection, no sampled reference-mesh overlap with either solid (2,770 vertices and 5,568 triangle centroids each), and 256 unblocked wire-channel samples. Each isolated STEP contains one manifold solid; both printable STL meshes are closed with positive volume. See `exports/compact-v3-validation.json` and `exports/compact-v3-print-validation.json`. These sampled checks do not guarantee printed fit or electrical contact.

The new local archive is `exports/macropad_compact_trial_v3.f3d`; the pre-change backup is `exports/macropad_before_compact_v3.f3d`. Isolated STEP files are `exports/switch_fit_coupon_compact_v3.step` and `exports/lid_support_coupon_compact_v3.step`. Native snapshots are `exports/compact-v3-receiver.png`, `exports/compact-v3-lid.png`, and `exports/compact-v3-assembled.png`. Standalone STEP rendering failed because OCP is unavailable; CAD Viewer is not installed. Visual review used the saved native Fusion snapshots. Local archive export does not save a new cloud version of the open document.


## Compact holder fit trial V4 — one removable pin

V4 removes the upper hotswap stops and the stepped compact pocket, leaving a 16 x 16 mm lower-switch clearance passage with the two lower notch guides. Holder depth remains 6.8/12 mm, matching V3; the V3 lid support coupon can be reused. Main enclosure and earlier trials are preserved. The original compact STL remains unchanged.

Print BOTH `cad/print/SwitchFitCoupon_Compact_V4.stl` and `cad/print/Hotswap_MX_Compact_Pin_V4.stl`. The latter is a modified copy of the supplied compact holder. One smooth 1 mm diameter, 10 mm long mechanical wire pin enters from the front receiver wall, crosses the compact holder land and ends in the right notch guide. The shared bore is 1.2 mm diameter, at compact-local X4.3/Z1.6 mm, with a blind end at Y-0.2 mm. About 1.1 mm of the pin remains exposed. The mechanical pin is separate from the electrical contact wires and is not a printed part.

Original contact channels remain segmented; four receiver channels follow their original axes. Test full switch flange seating, pin insertion/removal, holder retention and electrical wire access physically. Geometry checks do not establish actual switch fit or contact reliability. Native source: `macropad_compact_trial_v4.py`; validation/export: `verify_compact_v4_fusion.py`; print orientation: `prepare_compact_v4_meshes.py`. The live model suppresses the superseded two-pin features and restores their material.

Exports are `exports/switch_fit_coupon_compact_v4.step`, `exports/hotswap_mx_compact_pin_v4.step`, and `exports/macropad_compact_trial_v4.f3d`. Validation reports and native Fusion snapshots have the `compact-v4-` prefix. Local archive export does not save a cloud version. Visual review uses native Fusion screenshots because standalone STEP rendering requires the unavailable OCP dependency and CAD Viewer is not installed.


## Full middle carrier — compact V4

The user physically tested `SwitchFitCoupon_Compact_V4.stl` and `Hotswap_MX_Compact_Pin_V4.stl` and confirmed the fit. All six receivers in `MiddleCarrier_Draft` now use that V4 geometry: a smooth 16 x 16 mm lower cavity, rounded side guides, four aligned wire channels and one 1.2 mm retaining-pin bore. Superseded spring snaps, upper stops and stepped pockets are suppressed. Holder top/bottom normal depths are 6.8/12 mm. The original compact holder STL is preserved.

Use six copies of `cad/print/Hotswap_MX_Compact_Pin_V4.stl` and six smooth 1 mm metal retaining pins. Each pin needs a straight 10 mm working portion; allow extra external length if bending the exposed end. Bend only outside the receiver. The 3.6 mm partial withdrawal clearance passed geometric checks; unrestricted full-pin removal with every holder installed has not been established.

Native validation passed for all six positions: no hotswap/pin intersections with the enclosure, 294 switch-cavity samples, 120 pin-path samples, 256 wire-path samples and 1,092 coupon-comparison samples per receiver. The static enclosure has no volumetric intersections, the active timeline is healthy, and sketches are constrained. Other native bodies retain their baseline volumes. Reports: `exports/carrier-v4-validation.json` and `exports/carrier-v4-print-validation.json`.

The isolated `exports/middle_carrier_compact_v4.step` contains exactly one manifold solid named `MiddleCarrier_Draft`. `cad/print/MiddleCarrier_Compact_V4.stl` is oriented switch-face down on the bed, uses millimeters and has a 74.400 x 109.713 x 13.671 mm bounding box. Its edges are closed, signed volume is positive, and mesh volume differs from native CAD by approximately 0.012%. The local native archive is `exports/macropad_carrier_compact_v4.f3d`; exporting it does not save a cloud version.

Visual review used `exports/carrier-v4-underneath.png` and `exports/carrier-v4-top.png`. The standalone STEP snapshot command failed because OCP is unavailable; CAD Viewer is not installed. Native Fusion geometry checks and saved native screenshots provided the fallback.

### Remaining assembly work

The lower cover support posts remain at the old 15 mm holder-bottom datum; the V4 holder bottom is 12 mm. They have not been raised or approved for a complete lid print. The V3 lid support coupon matches the new nominal height, but physical testing remains necessary. The rear USB opening is pending, and actual encoder, connectors, PCB and cable fit require assembly checks.

Straight carrier extraction is obstructed: a vertical 3 mm drop overlaps the diffuser by approximately 0.239 mm3, while a 3 mm face-normal drop overlaps the upper shell by approximately 1.573 mm3. Do not assume either path is a valid service sequence. Resolve the assembly/removal order before final enclosure approval; PCB removal remains necessary for the previously identified rear-post obstruction. The current carrier STL is for a physical fit trial.
