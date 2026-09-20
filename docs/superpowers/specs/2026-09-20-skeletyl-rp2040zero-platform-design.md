# Skeletyl RP2040-Zero + TRRS platform — design

Date: 2026-09-20

## Goal

A 3D-printed platform that replaces the Bastardkb Splinktegrated PCB in a
Skeletyl **V4** case (`case_v4_103.stl`) for a hand-wired build. It bolts to
the case's two existing M4 controller rings and holds:

- a **Waveshare RP2040-Zero** (18 × 23.5 × 1.0 mm, castellated, USB-C on a
  short edge) mounted **components down** so its USB-C lines up with the
  case's USB slot and BOOT/RESET are reachable from below;
- a **PJ-320A** TRRS jack (12 × 6 × 5 mm body, Ø5 × 2 mm nose, barrel axis
  2.5 mm above its mounting face, 4 legs along one long edge) lined up with
  the case's Ø5.7 jack hole.

Deliverable: a parametric FreeCAD Python script plus exported STEP/STL, in
`rp2040zero_platform/` in this repo (`~/skeletyl_hardware`, kept separate
from the QMK userspace).

## Reference measurements

Taken from `Bastardkb/splinktegrated` (`splinktegrated.kicad_pcb`) and
`Bastardkb/Skeletyl` (`V4/case_v4_103.stl`, `mods/pro micro mount plate`).

### Platform coordinate frame

- Origin: centre of case ring **A** (the ring nearer the jack).
- **X** to the right (toward ring B), **Y** toward the user (the rear wall is
  at negative Y), **Z** up. Z = 0 is the top face of the case rings.
- Case STL → platform: `X = x_case + 94.136`, `Y = z_case + 30.599`,
  `Z = y_case`.
- KiCad → platform: translate H1 `(131.60262, 109.99266)` to the origin, then
  rotate by `Δ = atan2(-28.267, 34.660) − atan2(-27.9, 34.587) ≈ −0.32°`
  (rigid, no scale). KiCad y maps to +Y without a flip.

### Case interface (V4)

| Feature | Value |
| --- | --- |
| Ring A centre | (0, 0) |
| Ring B centre | (34.660, −28.267) — pitch 44.73 mm (PCB holes: 44.44) |
| Rings | Ø10 outside, Ø5.5 insert bore, Z −3.75…0, nothing below them |
| Rear wall inner face | Y = −31.8 (wall 4.2 mm thick, outer face Y = −36.0) |
| Jack hole | Ø5.67, axis X = 5.0, Z = −1.22 |
| USB slot | X 15.64…26.47 (centre 21.05, 10.8 wide), Z −3.06…4.0 (7 tall) |
| Bottom plate top face | Z = −8 |

### Pro Micro mod stack-up (adopted)

Plate Z −4…−2 with Ø10 pockets that slip over the rings, pocket ceiling on the
ring tops, 2 mm cap above with Ø5.8 holes, M4 screws from above into the
existing heat-set inserts. Its board floor at Z = −2 puts a Pro Micro's
micro-USB at Z ≈ +0.9 — consistent with the slot centre, which validates the
frame above.

## Geometry

All numbers are defaults of named parameters in the script.

### 1. Base plate

- Outline: Splinktegrated head + neck from `Edge.Cuts`, i.e. everything with
  KiCad y < 137.79 (the snap-off line of the USB daughterboard). Arcs kept
  as arcs. The KiCad outline is closed across the snap line with a straight
  segment.
- Placed with the KiCad → platform transform, then the rear edge is trimmed
  to Y ≥ −31.3 (0.5 mm from the wall).
- Z −4.72…−2 (2.72 mm): the plate bottom is derived as the jack shelf bottom
  (`JACK_HOLE_Z − JACK_AXIS_H − JACK_FLOOR_T`) so the whole underside is one
  plane and the part prints flat without supports. 3.28 mm remain above the
  bottom plate (Z −8) for a zip tie.

### 2. Ring pockets (×2, at A and B)

The case rings are not free-standing cylinders (measured from the V4 STL):
ring A hangs off a slanted wall at X ≈ −4.2…−5.1 with fillets filling the
whole X < 0 side below Z = 0; ring B is a blob with a flat face at X = 30.9
(from the rear wall up to Y = −24.5), a top face at Z = +0.25, and flares
into the rear/right walls, leaving free space only in the 15°…195° sector.

- Bore Ø10.4 from Z −4 up to the ring's top (A: 0, B: 0.25), open at the
  bottom; for ring B the bore also follows the flat face (X ≥ 30.6,
  Y ≤ −24.2 (0.3 mm clearance, `RING_B_FLAT_CLEAR`)).
- Seat: a full Ø9.2 disc from the ring top to Z = 2 under the screw head.
- Boss: Ø12.8 cylinder from Z −4 to +2, kept only where the case is free —
  ring A: X ≥ 0.5 (the wall and its fillets occupy the X < 0 side; the seat
  disc alone carries the head there); ring B: the half-space 0.5 mm past the
  centre toward 105°.
- Ø4.5 through hole for M4.
- Screw: M4 × 6 or 8 with a head ≤ Ø7 (DIN 912 socket head): at ring B the
  rear wall is 3.5 mm from the screw axis, so a Ø7.6 button head would
  touch it. The right rail stops 1 mm in front of ring B's flat face
  (Y ≥ −23.5) so a Ø7 head has a clear footprint; a test sweeps a
  Ø7.4 × 2.4 mm volume above each cap.
- Ring B is only 3.5 mm from the rear wall and the case ring itself merges
  into the wall, so its pocket is cut off by the same rear trim as the plate
  (Y ≥ −31.3): the boss and bore are open toward the wall on that side.

### 3. RP2040-Zero pocket (components down)

- Board 18 × 23.5, PCB 1.0 thick. USB-C: 8.94 wide, 3.2 tall, 7.35 long,
  overhangs the PCB edge by `USB_OVERHANG = 1.3`.
- Position: centre X = 21.05 + `BOARD_X_SHIFT` (default 0). USB-C front
  face at Y = −31.8 − `USB_INTO_WALL` (1.0) = −32.8, so the PCB rear edge is
  at Y = −31.5 and the front edge at Y = −8.0.
- Heights: USB-C underside Z = −1.1, so the connector centre is at Z = +0.5.
  PCB Z 2.1…3.1, flat solder side up.
- Support (touches only bare PCB / metal shell):
  - USB cradle: 6 (X) × 4 (Y) block centred on the connector, X 18.05…24.05,
    Y −31.3…−27.3, top at Z = −1.1.
  - Corner seats at the far (front) corners: 3 (X) × 1 (Y), top at Z = 2.1,
    at Y −9.0…−8.0, X 12.05…15.05 and 27.05…30.05. (Pad rows on the board
    stop ~1.6 mm short of the long-edge ends and ~3.9 mm short of the far
    corners, so the seats rest on bare PCB.)
- Guides: side rails 1.5 thick, 0.4 clearance to the board (inner faces at
  X 11.65 and 30.45); left rail from Y −31.3, right rail from Y −23.5
  (`RING_B_FLAT_Y_TOP + RAIL_R_GAP`), both to −6.1, Z −4.72…4.5. Front
  end-stop 1.5 thick at Y −7.6…−6.1 between the rails, same height. Rails
  are interrupted where zip-tie slots pass.
- Floor window: the plate is cut away under the board, X 13.55…28.55,
  Y −29.5…−9.5 (1.5 mm strips remain beside the zip-tie slots), leaving the
  cradle and corner seats attached to the surrounding plate. Gives button
  access (BOOT/RESET end up at Z ≈ +0.9 next to the USB-C) and component
  clearance.
- Zip-tie slots: 2 (X) × 5 (Y) through the plate and the rails, directly
  outside the board edges (X 10.05…12.05 and 30.05…32.05), one pair at
  Y −21…−16 and one at Y −14…−9 (both clear of ring B's pocket, whose
  outer wall reaches Y ≈ −22 at those X). A 2.5 mm tie loops under the
  plate and over the board.
- Ring-cap relief: within the board pocket footprint (between the rail
  inner faces) the ring caps are lowered to Z = PCB underside − 0.6 ≈ 1.47,
  so ring B's cap cannot touch the board edge; the M4 head (Ø7.5) sits
  entirely outside that footprint.

### 4. PJ-320A pocket

- Jack axis X = 5.0. Body 6 wide → X 2.0…8.0; pocket X 1.8…8.2 (0.2 side
  clearance).
- Shelf top at Z = JACK_HOLE_Z − 2.5 = −3.72; 1.0 mm floor below it
  (Z = −4.72), which is also the plate bottom, and spans the pocket plus its
  walls.
- Body front face at Y = −31.6 (0.2 from the wall); nose enters the wall
  hole. Pocket length 12.3 → end-stop inner face at Y = −19.3.
- Walls 1.5 thick on the two long sides and the front end, Z −4.72…+1.28
  (full body height). Open toward the wall.
- Leg slots: 1.6 (X) × 10.0 (Y) through the shelf on *both* sides, centred
  0.8 mm inboard of each body side face (X 2.0…3.6 and 6.4…8.0), Y
  −30.6…−20.6, so the jack can go in either way round. Legs hang through;
  wires solder underneath (4 mm of space above the bottom plate).

### 5. Fusion order

plate − window; + ring outers (each minus the cap relief); + rails +
end-stop + cradle + seats; + jack block − jack pocket − leg slots; − zip-tie
slots; − ring bores − cap holes; finally ∩ (Y ≥ −31.3) so nothing — ring B's
boss included — lies behind the rear trim. Single solid, checked with
`Shape.isValid()` and `len(Solids) == 1`.

## Script

`rp2040zero_platform/rp2040zero_platform.py`

- Runs headless: `freecadcmd rp2040zero_platform.py` (exports
  `rp2040zero_platform.FCStd`, `.step`, `.stl` next to the script) and as a
  GUI macro (builds the part into the active document; no export).
- Parameter block at the top: every number above, grouped by section, with
  a one-line comment each.
- Outline: the KiCad `Edge.Cuts` segments/arcs for the head + neck are
  embedded as a Python list (start/end/mid points in KiCad coordinates)
  extracted once from the PCB file, so the script has no external
  dependency. The transform is applied at build time.
- Pure `Part` workbench (`Part.makePolygon`/`Part.ArcOfCircle`, `Face`,
  `extrude`, `makeCylinder`, `makeBox`, `fuse`, `cut`).

## Verification

1. Headless build succeeds; solid valid, one solid, volume printed.
2. Collision check against `case_v4_103.stl`: rasterise both meshes into a
   0.25 mm voxel grid over the platform's bounding box (case transformed
   into the platform frame) and report voxels containing both surfaces.
   Expected: none except the intentional ring/pocket contact (ring bore vs
   ring outer surface) — reported by region so it is obviously benign.
3. Section overlays (platform over case) through: ring A, ring B, the jack
   axis, the USB slot centre. Saved as PNGs for eyeballing clearances.
4. Bounding-box sanity: platform Z within −4.72…4.5; the underside is one
   plane (ZMin == PLATE_Z0).

## Assembly notes (go in the README)

- Print flat, pockets up, no supports. Mirror the STL in the slicer for the
  other half, exactly like the case.
- Solder wires on the RP2040-Zero's flat (label) side; it faces up.
- BOOT/RESET face the bottom plate: remove the plate (or find a voronoi hole)
  and press with a toothpick. Put `QK_BOOT` in the keymap; the
  `RP2040_BOOTLOADER_DOUBLE_TAP_RESET*` settings in the firmware's
  `keyboards/bastardkb/skeletyl/keymaps/jrozhon/config.h` (qmk_userspace)
  are Splinky-only.
- Before printing, measure the actual USB-C height and overhang on your
  board and set `USB_H` / `USB_OVERHANG` if they differ.
- Tightest tolerances: USB-C vs slot (≈0.9 mm each side) and jack barrel vs
  hole (≈0.3 mm). `BOARD_X_SHIFT` and `JACK_AXIS_X` are the knobs.
- USB-C reach: the receptacle face is ~3 mm behind the case's outer face;
  use a cable whose overmold fits the 10.8 × 7 mm slot.
- Screw heads ≤ Ø7 (DIN 912).
