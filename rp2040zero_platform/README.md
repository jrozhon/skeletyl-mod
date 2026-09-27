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

- **Case:** `case_v4_103_usb_serial.stl` exactly like the original case.
  It is the **right** half; mirror it in the slicer for the left. The only
  change is the rear wall: the round jack hole is filled and a 9.82 × 3.62
  USB-C slot sits next to the RP2040's.
- **Platform:** underside (the face with the two screw countersinks) on the
  bed, no supports. 0.2 mm layers, 3 perimeters. As modelled it fits the
  right half; mirror it for the left.

## Assemble

The platform goes in from the bottom-plate side: the flat underside faces
the bottom plate, the ledges, corner stops and pedestal point up toward the switches.

1. **Serial breakout.** Solder four wires to U, D+, D−, G first. Set the
   shell on the pedestal, push it into the new slot until its face is
   ~0.8 mm inside the wall, and hot-glue the shell to the pedestal. The PCB
   tail drops between two L-shaped stops behind its end (0.2 mm off the
   end, touching its sides, the middle open for the wires); they take the
   push when you plug a cable in.
2. **Board.** Solder the wires to the RP2040-Zero's castellated pads first.
   Place it components down, USB-C toward the wall, long edges on the two
   ledges: it drops between the two L-shaped corner stops at its front
   end, which take the push when you plug a cable in. Push it left against
   the serial breakout's right stop, which rises to the board's height
   (0.1 mm off its left edge). Hot-glue the PCB to the ledges and along the stops' 0.5 mm lip.
3. Hold the plate against the ring faces and drive the two M4 × 8 screws
   from below.
4. BOOT/RESET face the bottom plate: remove it and press them through the
   window. Put `QK_BOOT` in the keymap as well.

## Fit checks before printing

| Parameter | Default | Why it matters |
| --- | --- | --- |
| `USB_H` | 3.2 | RP2040 USB-C shell height; sets the board height |
| `BOARD_Z_SHIFT` / `BOARD_X_SHIFT` | 0.0 | Nudge the board if its shell catches in the slot |
| `CORNER_T` / `CORNER_GAP` | 2.5 / 0.2 | Corner stops at the board's front: arm thickness and gap to the PCB edges (the board has 0.33 mm to the wall behind it) |
| `SER_H` / `SER_W` | 3.2 / 8.94 | Serial shell; sets the pedestal height. The slot has 0.21 mm each way vertically, 0.44 sideways |
| `SER_L` / `SER_PCB_W` | 14.6 / 8.9 | Breakout overall length (datasheet) and PCB width (caliper; the datasheet says 9.8); they place the stops behind the PCB (0.2 mm) and beside it, so check your part |
| `SER_SIDE_GAP` / `BOARD_SIDE_GAP` | 0.0 / 0.1 | Breakout PCB sides → its stops' side arms, line-to-line (0.2 and 0.1 printed loose); RP2040 left edge → the raised right serial stop |
| `SER_SHELL_L` | 9.0 | Shell length; the pedestal ends under the shell's rear |
| `SER_RECESS` / `USB_RECESS` | 0.8 / 1.0 | Shell faces behind the wall's outer face (wall is 2 mm); the serial shell sat too deep at 1.0 |
| `CSK_ANGLE` / `CSK_DEPTH` | 90 / 1.2 | Countersink for the conical heads: Ø6.9 at the underside down to the Ø4.5 hole. A full-depth seat does not fit the 2 mm plate, so the head hangs ≤ 1.3 mm below it (0.95 mm clear of the bottom plate) |

Both USB-C shells need rounded corners (≥ R0.8) to pass the slots'
full-radius ends.

## Clearance check

    python3 check_clearance.py            # against case_v4_103_usb_serial.stl

Reports any case surface sample inside the platform (only contact on the
rings' face plane is allowed) and writes `sec_*.png` cross-sections (case
blue, platform red, held parts green).
Last run: 2026-09-26 — 17315 points on the Z −3.75 contact plane; no collisions.
