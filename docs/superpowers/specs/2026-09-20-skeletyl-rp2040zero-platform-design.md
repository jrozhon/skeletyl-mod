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
- Thickness 2 mm, Z −4…−2.

### 2. Ring pockets (×2, at A and B)

- Bore Ø10.4 from Z −4 to 0 (open at the bottom).
- Outer Ø12.8 cylinder from Z −4 to +2, fused with the plate.
- Cap: Z 0…2, Ø4.5 through hole for M4.
- Screw: M4 × 6 or 8 button head into the case insert.

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
  X 11.65 and 30.45), from Y −31.3 to −6.1, Z −2…4.5. Front end-stop 1.5
  thick at Y −7.6…−6.1 between the rails, same height. Rails are interrupted
  where zip-tie slots pass.
- Floor window: the plate is cut away under the board, X 12.5…29.6,
  Y −29.5…−9.5, leaving the cradle and corner seats attached to the
  surrounding plate. Gives button access (BOOT/RESET end up at Z ≈ +0.9 next
  to the USB-C) and component clearance.
- Zip-tie slots: 2 (X) × 5 (Y) through the plate and the rails, directly
  outside the board edges (X 10.05…12.05 and 30.05…32.05), one pair at
  Y −26…−21 and one at Y −16…−11. A 2.5 mm tie loops under the plate and
  over the board.

### 4. PJ-320A pocket

- Jack axis X = 5.0. Body 6 wide → X 2.0…8.0; pocket X 1.8…8.2 (0.2 side
  clearance).
- Shelf top (jack mounting face) Z = −3.75 → barrel axis Z = −1.25. Shelf
  block extends down to Z = −5.25 (1.5 mm floor) and spans the pocket plus
  its walls.
- Body front face at Y = −31.6 (0.2 from the wall); nose enters the wall
  hole. Pocket length 12.3 → end-stop inner face at Y = −19.3.
- Walls 1.5 thick on the two long sides and the front end, Z −5.25…+1.25
  (full body height). Open toward the wall.
- Leg slot: 1.6 (X) × 10.0 (Y) through the shelf, centred on the pin edge
  (pins 0.8 mm inboard of the body face nearer X = 2.0 → slot X 2.1…3.7),
  Y −30.6…−20.6. Legs hang through; wires solder underneath (4 mm of space
  above the bottom plate).

### 5. Fusion order

plate − window − zip-tie slots − trim; + ring outers − ring bores − cap
holes; + rails + end-stop + cradle + seats; + jack block − jack pocket − leg
slot. Single solid, checked with `Shape.isValid()` and `len(Solids) == 1`.

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
4. Bounding-box sanity: platform Z within −5.25…4.5; nothing below Z −5.25
   (bottom plate at −8, zip-tie clearance).

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
  board and set `USB_C_HEIGHT` / `USB_OVERHANG` if they differ.
- Tightest tolerances: USB-C vs slot (≈0.9 mm each side) and jack barrel vs
  hole (≈0.3 mm). `BOARD_X_SHIFT` and `JACK_AXIS_X` are the knobs.
