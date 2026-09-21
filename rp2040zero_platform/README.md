# RP2040-Zero + TRRS platform for the Skeletyl V4

Replaces the Splinktegrated PCB in a hand-wired Skeletyl. A flat plate that
screws from below against the case's two M4 controller rings and holds a
Waveshare RP2040-Zero **components down** (USB-C in the case slot,
BOOT/RESET reachable through a window with the bottom plate off) and a
PJ-320A TRRS jack in the case's jack hole. Both parts are positioned by the
plate and fixed with hot glue.

Design notes and measurements: `docs/superpowers/specs/2026-09-20-skeletyl-rp2040zero-platform-design.md`.

## Build

    freecadcmd rp2040zero_platform.py          # writes .FCStd / .step / .stl next to the script
    python3 rp2040zero_platform.py             # same, using the system python + FreeCAD's modules
    python3 -m unittest discover -s tests -t .. -v   # from this directory

Or open `rp2040zero_platform.py` in FreeCAD as a macro; a `Platform` object is
added to the active document.

## Print

Underside (the face with the two screw counterbores) on the bed, everything
grows upward; no bridges, no supports. 0.2 mm layers, 3 perimeters. Mirror
the STL in the slicer for the other half, exactly like the case.

## Assemble

The part goes in from the bottom-plate side: the flat underside faces the
bottom plate, the rails and ribs point up toward the switches.

1. **Jack.** Solder the wires on first. Drop the PJ-320A into its shallow
   pocket, nose toward the wall, legs through whichever leg slot they land
   in (there is one along each side; wires go down through the slot). Push
   the nose into the case hole — that is what positions it — and hot-glue
   the body to the ribs.
2. **Board.** Solder the wires to the RP2040-Zero's castellated pads first.
   Place it components down, USB-C toward the wall, long edges on the two
   ledges, and push the connector into the case slot until the PCB edge is
   ~0.3 mm from the wall. Hot-glue the PCB edges to the rails (they stand
   1 mm above the PCB) on both sides and at the front.
3. Hold the plate against the ring faces and drive the two M4 × 8 screws
   from below. Screw heads up to Ø8 × 2.5 mm fit the counterbores with
   0.55 mm to spare above the bottom plate.
4. BOOT/RESET face the bottom plate: remove the plate and press them through
   the window. Put `QK_BOOT` in the keymap as well.

## Fit checks before printing

The case openings are tight and the connectors are positioned by the plate
alone, so check these on your parts:

| Parameter | Default | Why it matters |
| --- | --- | --- |
| `USB_H` | 3.2 | USB-C shell height; the slot is 3.62 mm tall, so the shell has 0.21 mm each way |
| `BOARD_Z_SHIFT` | 0.0 | Raise/lower the board if the shell catches on the slot's top or bottom edge |
| `BOARD_X_SHIFT` | 0.0 | Sideways nudge; the shell has 0.44 mm each way in the 9.82 mm slot |
| `USB_RECESS` | 1.0 | Shell face behind the wall's outer face (the wall is 2 mm thick there) |
| `JACK_AXIS_H` | 2.5 | Barrel axis above the jack's mounting face; the Ø5 nose has 0.1 mm in the Ø5.2 hole |
| `JACK_LEG_IN` / `JACK_LEG_OUT` | 1.4 / 0.6 | How far the leg slots reach inside/outside each body side face |
| `HEAD_D` / `HEAD_H` | 8.0 / 2.5 | Screw head; sets the counterbore |

The USB-C shell's corners must be rounded (≥ R0.8) to pass the slot's
rounded ends; every 16-pin receptacle I know of is.

## Clearance check

    ./refs/fetch.sh
    python3 rp2040zero_platform/check_clearance.py

Samples the case surface and reports any sample inside the platform (only
contact on the rings' face plane is allowed) and writes `sec_*.png`
cross-sections (case blue, platform red, board/jack green).
Last run: 2026-09-21 — 17315 points on the Z −3.75 contact plane; no collisions.
