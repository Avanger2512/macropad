# Native trial exports

**Current enclosure print set: V9.** Use `UpperShell_Service_V9.stl`,
`BottomCover_Finish_V6.stl` and `Diffuser_Service_V8.stl`, or download
`Macropad_Print_Set_V9.zip`. Keep the already printed V5 middle carrier.
Older revisions below are retained as design history.

**Current retention revision: V5 through pin.** Use the V5 section below; V4 uses a superseded blind pin and is retained only as history.

`SwitchFitCoupon_Trial.stl` and `LidSupportCoupon_Trial.stl` preserve the Fusion assembly coordinates. The switch sample retains its 5-degree inclination; these files are not oriented on the printer bed.

Use the prepared millimeter files for the initial fit print:

- [Switch fit coupon](../fusion/exports/switch_fit_coupon.stl)
- [Lid support coupon](../fusion/exports/lid_support_coupon.stl)

See [trial instructions and validation](../fusion/README.md#trial-print-sequence). Physical fit and spring durability still require testing.


## Compact holder V2

`SwitchFitCoupon_Compact_V2.stl`: 22 x 22 x 12.2 mm rigid receiver fit test for `hotswap_mx__compact.stl`. Flat plate is already oriented onto the print bed. No spring snaps; widened stops, two rounded insertion guides and projected wire channels. Preserve millimeter scale and compare using the same material/settings as the first trial. Physical switch/wire fit and upper-stop bridges remain to be checked. Details and native Fusion archive are in `../fusion/README.md`.


## Compact holder V3 — use both new coupons

- `SwitchFitCoupon_Compact_V3.stl`: 22 x 22 x 9.2 mm. Holder is 3 mm closer to the switch; wire channels move with it.
- `LidSupportCoupon_Compact_V3.stl`: 22 x 22 x 18.832 mm. Supports raised to match, retaining nominal 0.2 mm gap.

Both files are oriented flat-side down and use millimeters. Print this pair together rather than reusing V1/V2 lid supports. Check pin engagement, holder/switch seating and wire routing physically. Original compact hotswap STL is unchanged and must be inserted in the orientation shown in Fusion. Horizontal upper stops still require slicer bridge/support inspection.


## Compact holder V4 — one mechanical pin

Print both `SwitchFitCoupon_Compact_V4.stl` and `Hotswap_MX_Compact_Pin_V4.stl`, in millimeters at 100% scale. Both are already oriented onto the bed. This trial removes upper stops and pocket steps. Use the modified V4 hotswap rather than the unchanged source STL. Add one smooth metal wire pin, diameter 1 mm and length 10 mm, through the front wall into the side guide; the shared bore is 1.2 mm. The V3 lid support coupon remains compatible in height. Test actual switch seating, wire routing and retention before updating the complete carrier. See `../fusion/README.md` for the assembly and validation details.


## Full middle carrier V4 — next fit print

Print `MiddleCarrier_Compact_V4.stl` at 100% millimeter scale. Its switch face is already oriented onto the bed; the bounding box is approximately 74.400 x 109.713 x 13.671 mm. Inspect bridges and wire bores in the slicer before printing. Start with the same PLA Matte settings used for the successful V4 coupon.

Prepare six `Hotswap_MX_Compact_Pin_V4.stl` holders and six smooth 1 mm metal pins with straight 10 mm working sections. Extra external length may be bent outside the receiver. Fit all six switches and holders, verify pin access and wire routing, and check the carrier against the upper shell.

Do not print the complete lower cover yet: its supports still use the earlier holder depth and need adaptation after testing. Straight carrier removal currently collides with the diffuser or shell, depending on the direction. The rear USB opening and full assembly/removal sequence are pending. See `../fusion/README.md#full-middle-carrier--compact-v4` for native files and validation details.


## Through pin V5 — print the small pair first

Print one `SwitchFitCoupon_Through_Pin_V5.stl` (22 x 22 x 9.2 mm) and one `Hotswap_MX_Through_Pin_V5.stl` (approximately 11.031 x 10.572 x 5.200 mm). Both are already oriented onto the bed. Use millimeters and 100% scale, inspect the horizontal 1.2 mm bore in the slicer, and check that it remains open after printing.

The pin enters from the left or right side, passes through both receiver walls and the entire hotswap width, and does not stop at a guide. Use a smooth 1 mm metal pin with approximately 20 mm straight length. Add extra external length for a bent end if needed. V4's front-entry 10 mm pin arrangement is obsolete for this revision. Verify full passage, switch seating, holder retention and electrical wire routing without soldering first. Central MX post clearance uses an assumed 2 mm radius until confirmed physically.

After the small trial passes, use `MiddleCarrier_Through_Pin_V5.stl` (approximately 74.400 x 109.713 x 13.671 mm) and six matching V5 holders. Do not mix V5 holders/carriers with V4 pin instructions. Full withdrawal among neighboring assembled holders has not been verified. The lower cover, USB opening and complete assembly/removal sequence still require work. See `../fusion/README.md#through-pin-correction-v5--current-retention-design` for source, STEP/F3D, snapshots and validation.

## Enclosure finish V6

`UpperShell_Finish_V6.stl` and `BottomCover_Finish_V6.stl` retain the 5-degree
layout and the physically fitted V5 middle carrier. Shell includes rear USB
14 x 10 mm access and exterior chamfers. Cover removes the old hotswap support
posts and includes two 3 mm BOOT/RESET tool bores, 9 mm apart. Use millimeters,
100% scale. Both files are already placed on the bed: shell roof down, cover
underside down. Review bridges/overhangs and screw heads in the slicer; physical
USB insertion and button reach still need an assembly check. Native geometry and
mesh checks are recorded in `../fusion/exports/enclosure-v6-validation.json` and
`../fusion/exports/enclosure-v6-print-validation.json`.

## Cover mount revision V7

Use `UpperShell_Cover_Mounts_V7.stl` instead of the V6 shell. Front lower-cover
bosses reach the roof; rear bosses have 55-degree wall gussets to avoid crossing
the PCB substrate. Reuse `BottomCover_Finish_V6.stl` and the printed V5 carrier.
The V7 shell is already roof-down on the bed in millimeters. Check the slicer's
remaining overhangs and actual components/wires near the rear supports before
printing; this revision addresses cover mounts rather than every shell feature.

## Print set V8 — superseded by V9

Use `UpperShell_Service_V8.stl`, `Diffuser_Service_V8.stl` and
`BottomCover_Finish_V6.stl`. Keep the existing printed V5 middle carrier.
V8 clears the vertical bare-carrier installation path and provides a 7.4 mm
upper-shell hole for the measured 7 mm encoder bushing. All three print files
use millimeters and are pre-oriented on the bed; use 100% scale. The shell USB
roof is a 14 mm bridge needing slicer review. Use light/translucent material for
the diffuser according to desired illumination. Current gray PLA Matte choice
is for the main enclosure. The lid has no screw-head pockets: use feet taller
than the measured 2 mm screw heads. Do not assume whole-shell support-free
printing or populated-assembly clearance from the bare CAD checks.

## Current shell V9

`UpperShell_Service_V9.stl` removes the two obsolete front triangular gussets
next to the roof-connected cover pillars. Use it with `BottomCover_Finish_V6.stl`
and `Diffuser_Service_V8.stl`. The printed middle carrier remains unchanged.
The rear clipped support gussets remain. The new shell is still roof-down,
in millimeters at 100% scale. All previous USB-bridge and physical-fit checks
still apply.
