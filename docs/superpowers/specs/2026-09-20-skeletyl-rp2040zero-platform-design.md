# Skeletyl RP2040-Zero + TRRS platform — design

Date: 2026-09-20, revised 2026-09-21 (rev. 2: mounts from below; see
"Revision history").

## Goal

A 3D-printed platform that replaces the Bastardkb Splinktegrated PCB in a
Skeletyl **V4** case (`case_v4_103.stl`) for a hand-wired build. It bolts to
the case's two existing M4 controller rings and holds:

- a **Waveshare RP2040-Zero** (18 × 23.5 × 1.0 mm, castellated, USB-C on a
  short edge) mounted **components down** so its USB-C lines up with the
  case's USB slot and BOOT/RESET can be pressed from below;
- a **PJ-320A** TRRS jack (12 × 6 × 5 mm body, Ø5 × 2 mm nose, barrel axis
  2.5 mm above its mounting face, 4 legs along one long edge) lined up with
  the case's jack hole.

Both are positioned by the platform and fixed with hot glue. Keep the part as
simple as possible.

Deliverable: a parametric FreeCAD Python script plus exported STEP/STL, in
`rp2040zero_platform/` in this repo.

## Reference measurements (Skeletyl V4 STL)

### Platform coordinate frame

- Origin: centre of case ring **A** (the ring nearer the jack).
- **X** to the right (toward ring B), **Y** toward the user (the rear wall is
  at negative Y), **Z** up (toward the switches). Z = 0 is the top face of
  the case rings.
- Case STL → platform: `X = x_case + 94.136`, `Y = z_case + 30.599`,
  `Z = y_case`.

### Case interface

| Feature | Value |
| --- | --- |
| Ring A centre | (0, 0) |
| Ring B centre | (34.660, −28.267) |
| Rings | Z −3.75…0; free face (heat-set insert side) at **Z −3.75**, a flat annulus Ø5.5…Ø10.6, nothing below it |
| Above the rings | closed: the keywell underside is 12–20 mm up. The part can only be installed from the bottom-plate side |
| Bottom plate top face | Z −8 → 4.25 mm between the ring faces and the plate |
| Rear wall | outer face Y −36.07; inner face Y −32.0, **recessed to Y −34.1 between Z −5.5 and 3.0** (2 mm wall around the connectors; at the jack the recess spans Z −6.25…2.4) |
| USB slot | X 16.09…25.91 (9.82 wide), Z −3.06…0.56 (3.62 tall), centre (21.0, −1.25); straight through the 2 mm wall, full-radius ends |
| Jack hole | Ø5.2 through the wall, axis X 5.10, Z −1.60 (the mouth is chamfered to ≈Ø6.4, which is what earlier measurements caught) |
| Left wall | slanted inner face: X −5.1 at Y ≥ 0, −3.87 at Y −10, −1.71 at Y −28, then a fillet into the rear wall |
| Ring B surroundings | flat face at X 30.93 for Y ≤ −24, Z ≤ 1; case material at X ≥ 33 for Y ≤ −23 above the ring faces; free to X 38 in front of Y −22.5 |
| Below Z −3.75 | free everywhere between the left wall, the rear wall and X 45 |

## Geometry

All numbers are defaults of named parameters in the script.

### 1. Plate

- 2.0 mm thick, Z −5.75…−3.75: the top face is pressed against the ring
  faces, the underside faces the bottom plate (print bed).
- Outline = union of a body X −4.6…31.8 × Y −31.6…−8.47, a Ø14 pad around
  each ring (ring A's joined to the body by a strip X −4.6…7 × Y −10…0),
  clipped to the right of the left-wall polyline `LEFT_EDGE` (0.5 mm off the
  wall) and in front of Y −31.6. No Splinktegrated outline, no tail.
- **Window** X 13.5…28.5 × Y −31.6 (open at the rear)…−12.27 under the
  board: BOOT/RESET and the LED are reachable with the bottom plate off.
- **Screw seats**: Ø4.5 through hole; from below a Ø8.6 counterbore 0.8 mm
  deep (1.2 mm floor) for the kit's M4 × 8 Torx screws (head Ø8 × 2.5,
  measured). Head bottom at Z −7.45, 0.55 mm above the bottom plate. No
  ring bores: the plate top simply meets the flat ring faces (and the flat
  Z −3.75 underside of ring A's wall fillet).

### 2. Board frame (components down)

- USB-C centre on the slot centre Z −1.25 ⇒ shell Z −2.85…0.35, PCB
  Z 0.35…1.35 (flat side up, solder there). Board X 12…30 (centre 21.0 =
  slot centre), rear PCB edge Y −33.77 with the shell face 1 mm behind the
  wall's outer face so a plug seats fully.
- Two **ledge walls** 1.2 thick, plate → Z 0.35, the full length under both
  long PCB edges (0.9 mm under the edge — castellation pads only). Right
  ledge 0.63 mm off ring B's flat face.
- Two **rails** 1.5 thick outside the ledges, plate → Z 2.35 (1 mm above the
  PCB top: glue bridges PCB edge → rail). Left rail full length; right rail
  from Y −22.5 forward (ring B's blob is behind that).
- **Front stop** 1.5 thick at Y −9.97…−8.47, same height. The rear stop is
  the USB-C in its slot.
- 0.9 mm between the USB-C shell and the plate top; all other components are
  shorter.
- Margins: shell 8.94 × 3.2 in a 9.82 × 3.62 slot → 0.44 / 0.21 mm each
  way. `USB_H`, `BOARD_X_SHIFT`, `BOARD_Z_SHIFT` are the knobs.

### 3. Jack pocket

- Body X 2.1…8.1 × Y −33.9…−21.9, lying in a **0.35 mm pocket** (floor
  Z −4.10 = hole axis − 2.5) with 0.2 mm side/rear clearance, so the axis is
  on the hole axis and the Ø5 nose (0.1 mm radial clearance) reaches to
  0.17 mm behind the wall's outer face.
- **Leg slots** through the plate along both body sides, from 1.4 mm inside
  to 0.6 mm outside each side face (X 1.5…3.5 and 6.7…8.7), Y −31.6 (open at
  the rear)…−22.9: legs may be under or beside the body, either way round.
  The body rests on the 3.2 mm strip between the slots and on the front
  1 mm.
- **Ribs** 1.5 thick, 2.5 tall outside the slots (left from Y −29.6 forward,
  where the left wall allows; right merged into the board's left rail) and
  an **end stop** 0.3 mm behind the body. Position really comes from the
  nose in the hole plus glue; ribs are a glue dam and rough guide.

### 4. Assembly order in the script

plate (body ∪ pads ∩ keep − window) ∪ frame ∪ ribs − jack pocket − leg
slots − screw holes/counterbores → `removeSplitter()`. Single valid solid.
`make_components()` returns the PCB, shell, jack body and nose at their
design positions for the tests and the section drawings.

## Print

Underside on the bed; everything grows upward; no bridges or supports.
Tallest feature 8.1 mm.

## Verification

1. `tests/test_platform.py`: single valid solid; flat underside; extents;
   held components do not intersect the part; plate meets the ring faces;
   counterbore geometry and head clearance to the bottom plate; clearances
   to the rear wall, ring B and the left wall; USB-C centred in the slot;
   ledges, rails, stop, window; jack axis on the hole axis, pocket, slots,
   ribs; export writes three files.
2. `check_clearance.py`: sample the case STL surface and report samples
   inside the part; only samples on the Z −3.75 contact plane are allowed.
   Writes YZ sections through both rings, the jack axis and the USB centre,
   and an XZ rear view cut inside the 2 mm wall showing the nose in the hole
   and the shell in the slot.

## Revision history

- **Rev. 1 (2026-09-20)** put the plate *over* the rings with screw caps on
  top and rails 9 mm tall, based on a mis-read of the case: it assumed the
  rings were reachable from above and a 7 mm tall USB slot. Printed and
  test-fitted: it could only be mounted upside down, was too tall for the
  4.25 mm under the rings, and both connectors sat 1–3 mm too low. It also
  carried the Splinktegrated neck for no reason and held the board on
  3 × 1 mm pillars.
- **Rev. 2 (2026-09-21)** re-measured the case: closed above the rings,
  insert faces at Z −3.75, USB slot 3.62 mm tall, wall recess, jack hole
  Ø5.2 at Z −1.60. Redesigned as this document describes.
