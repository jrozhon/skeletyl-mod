# RP2040-Zero + USB-C serial platform for the Skeletyl V4

Replaces the Splinktegrated PCB in a hand-wired Skeletyl. A flat plate that
screws from below against the case's two M4 controller rings and holds a
Waveshare RP2040-Zero **components down** (USB-C in the case slot,
BOOT/RESET reachable through a window with the bottom plate off) and a
small mid-mount **USB-C breakout** for the half-to-half serial link, in a
USB-C slot that replaces the case's TRRS hole. Both parts are positioned by
the plate and fixed with hot glue.

Design notes and measurements: `docs/superpowers/specs/2026-09-25-skeletyl-usb-serial-design.md`
(rev. 3) on top of `docs/superpowers/specs/2026-09-20-skeletyl-rp2040zero-platform-design.md`.

## Build

    ../refs/fetch.sh                             # the original case STL
    python3 case_usb_serial.py                   # -> case_v4_103_usb_serial.stl (~3 min)
    python3 rp2040zero_platform.py               # -> .FCStd / .step / .stl
    python3 -m unittest discover -s tests -t .. -v   # from this directory (~7 min)

`freecadcmd rp2040zero_platform.py` and opening it as a FreeCAD macro work
too.

## Print

- **Case:** `case_v4_103_usb_serial.stl` exactly like the original case
  (mirror it in the slicer for the other half). The only change is the rear
  wall: the round jack hole is filled and a 9.82 × 3.62 USB-C slot sits
  next to the RP2040's.
- **Platform:** underside (the face with the two screw countersinks) on the
  bed, no supports. 0.2 mm layers, 3 perimeters. Mirror for the other half.

## Assemble

The platform goes in from the bottom-plate side: the flat underside faces
the bottom plate, the ledges and pedestal point up toward the switches.

1. **Serial breakout.** Solder four wires to U, D+, D−, G first. Set the
   shell on the pedestal, push it into the new slot until its face is
   ~1 mm inside the wall, and hot-glue the shell to the pedestal. The PCB
   tail is free.
2. **Board.** Solder the wires to the RP2040-Zero's castellated pads first.
   Place it components down, USB-C toward the wall, long edges on the two
   ledges, push the connector into its slot, and hot-glue the PCB edges to
   the ledges.
3. Hold the plate against the ring faces and drive the two M4 × 8 screws
   from below.
4. BOOT/RESET face the bottom plate: remove it and press them through the
   window. Put `QK_BOOT` in the keymap as well.

## Fit checks before printing

| Parameter | Default | Why it matters |
| --- | --- | --- |
| `USB_H` | 3.2 | RP2040 USB-C shell height; sets the board height |
| `BOARD_Z_SHIFT` / `BOARD_X_SHIFT` | 0.0 | Nudge the board if its shell catches in the slot |
| `SER_H` / `SER_W` | 3.2 / 8.94 | Serial shell; sets the pedestal height. The slot has 0.21 mm each way vertically, 0.44 sideways |
| `SER_SHELL_L` | 9.0 | Shell length; the pedestal ends under the shell's rear |
| `SER_RECESS` / `USB_RECESS` | 1.0 | Shell faces behind the wall's outer face (wall is 2 mm) |
| `CSK_ANGLE` / `CSK_DEPTH` | 90 / 1.2 | Countersink for the conical heads: Ø6.9 at the underside down to the Ø4.5 hole. A full-depth seat does not fit the 2 mm plate, so the head hangs ≤ 1.3 mm below it (0.95 mm clear of the bottom plate) |

Both USB-C shells need rounded corners (≥ R0.8) to pass the slots'
full-radius ends.

## Clearance check

    python3 check_clearance.py            # against case_v4_103_usb_serial.stl

Reports any case surface sample inside the platform (only contact on the
rings' face plane is allowed) and writes `sec_*.png` cross-sections (case
blue, platform red, held parts green).
Last run: 2026-09-25 — 17315 points on the Z −3.75 contact plane; no collisions.
