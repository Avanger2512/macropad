# Retrofit wedge feet for compact C4

## CAD brief

2026-10-23: raise the USB/encoder edge of the existing printed case without
reprinting either shell. The user measured round rubber pads Ø10 × 2 mm.
C4 assembly datum: rear-left underside of lower cover, X right, Y front, Z up.

The kit contains two raised rear feet and two low front feet. All have Ø14 mm
bodies and Ø10.3 mm pad pockets, 0.4 mm deep normal to their sloped faces.
The low front bases are necessary because bare 2 mm pads would leave almost no
clearance for the existing Ø4 × 2 mm screw heads when tilted.

All four feet attach with adhesive to the existing flat lower cover. The screw
holes are unchanged and remain accessible. This is an intentional compact
alternative to large offset brackets attached at the near-corner screw holes.
No new screws or inserts are required. The pads are reference cylinders from
user measurements, not catalog component geometry.

## Geometry and placement

- Rear pad/foot centers: X12/Y10 and X94/Y10.
- Front centers: X12/Y66 and X94/Y66.
- Coordinates are mm on the cover underside before tilting the case.
- Equivalently: centers are 12 mm from each side, rear centers 10 mm from the
  USB edge, front centers 8 mm from the opposite edge.
- Effective support depths including pads are 9.2 mm rear and 3.2 mm front,
  measured where their desk planes cross the pad-center Y datum.
- Difference 6 mm over a 56 mm support span gives 6.1155° inclination.
- Wedge faces and pad bottoms all become horizontal after assembly rotation.
  No rubber deformation is needed in the nominal geometry.
- Rear printed part envelope: Ø14, maximum height 8.34084 mm.
- Front printed part: Ø14, maximum height 2.34084 mm.
- Each foot is thicker toward the USB edge. The rear pair is taller overall;
  the low front pair has the same slope orientation.

## Printing and assembly

Print `feet_set.stl` once for the complete four-part kit. For separate plates,
print two copies each of `rear_foot.stl` and `front_foot.stl`.
All STL files already lie on Z0, flat glue face down, pad pocket up. There is
4 mm spacing between objects in the full set. No supports are geometrically
required. A 0.2 mm layer is compatible with the nominal 0.4 mm pocket depth.

Remove existing rubber pads from these mounting locations. Dry-fit the parts,
then attach their flat faces to the lower cover with suitable adhesive. All
thicker edges point toward USB. Stick the user's rubber pads into the pockets.
Adhesive thickness is excluded from the model; keep it similar at all four feet.
The model does not establish a particular adhesive's strength on the user's PLA.

## Sources and artifacts

- `rear_foot.py`: shared parameters, geometry, explicit support datums and pose.
- `front_foot.py`: individual front part in print pose.
- `feet_set.py`: two rear and two front feet in print pose, 32 × 32 mm envelope.
- `fitted_case.py`: unchanged C4 shell/cover references, feet, rubber pads and
  screw-head envelopes, positioned through the source tilt transform.
- Corresponding STEP files are primary; STL files are secondary print exports.
- `validation.json` records actual B-rep and mesh checks.
- `fusion_check.py` prepares a separate Fusion mirror without editing C4.
- `previews/` contains mandatory reviewed snapshots.

## Validation

Four regression tests pass: single solid and radial fitting clearance, pocket
opening/seat contact, true normal pocket depth and installed contacts/clearances.
Actual B-reps for all 14 assembly bodies are valid single positive solids.
All 91 body-pair intersection tests pass with no positive-volume intersections.
All four pad minima lie on the desk plane and no body penetrates it.
Minimum foot-to-screw-head distance: 0.61769 mm. Minimum screw-head height
above desk: 0.50071 mm. Minimum front pocket floor material: 0.63991 mm.

Rear/front/set STL meshes have closed two-manifold edges, consistent winding,
positive volume and Z0 print contact. Mesh bbox differs from B-rep by at most
0.00237 mm due to circular tessellation (allowed 0.005 mm); mesh volume agrees
within 0.3%. Four STEP artifacts were inspected with facts, planes and positioning.
Print-set and tilted-case snapshots were reviewed.

Fusion MCP reconnected after starting Fusion. Native checks of the separate
14-body mirror passed all 91 pairs, confirmed all four Ø10.3 seats parallel
to the desk and all four pad minima exactly on Z0. Native minimum screw-head
floor clearance is 0.50071 mm. Results and source SHA-256 are recorded in
`fusion-validation.json`. Local archive: `c4_with_rubber_feet.f3d`.
CAD Viewer is not installed; use the Fusion document, STEP and saved snapshots.
No slicing, print job, physical bond test or rubber compression test was run.

## Integral replacement lower cover

`bottom_cover_with_feet.stl` is the complete C4 replacement cover with all four
feet fused into one solid. `bottom_cover_with_feet.step` is its primary CAD
artifact and `bottom_cover_with_feet.f3d` the checked Fusion import. Generator:
`bottom_cover_with_feet.py`. Uses the existing C4 cover interior and screw
pattern, identical four pad positions, Ø10.3 ×0.4 seats for user pads Ø10×2,
6 mm differential rear rise and 6.1155° slope. Overall print size
106×74×10.74084 mm. Requires four rubber pads, no adhesive foot-to-cover joints.

Print in exported orientation: flat interior face on bed, feet and pad pockets
up. No supports required by geometry; use 0.2 mm layers, 3 walls and 15–20%
infill with the printer's established matte PLA profile. Replace old cover and
retain existing screws. Glue only the four rubber pads into their seats.

Four B-rep tests pass: original cover preserved, one valid connected solid,
original M2 holes and Ø4×2 head envelopes clear, correct print pose and inherited
support plane. Native Fusion MCP independently confirms one positive solid,
four Ø10.3 seats, bounds and bed pose. Mesh validation is recorded separately.
CLI inspection and saved snapshots supplement Fusion; CAD Viewer unavailable.
Physical printing and pad compression remain untested.

### Integral foot base update

Integral feet now widen into the cover with 45° base chamfers instead of the
retrofit glue-edge neck. Rear base Ø16.4 (1.2 mm chamfer), front base Ø14.8
(0.4 mm chamfer to retain screw-head clearance); foot trunks stay Ø14.
Pad seats, overall height and support angle unchanged. Five B-rep tests pass.
STEP/STL/F3D, Fusion validation and snapshots regenerated for this revision.
