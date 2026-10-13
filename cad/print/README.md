# Native trial exports

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
