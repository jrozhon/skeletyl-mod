# RP2040-Zero + USB-C serial platform for the Skeletyl V4

Replaces the Splinktegrated PCB in a hand-wired Skeletyl. A flat plate that
screws from below against the case's two M4 controller rings and holds a
Waveshare RP2040-Zero **components down** (USB-C in the case slot,
BOOT/RESET reachable through a window with the bottom plate off) and a
small mid-mount **USB-C breakout** for the half-to-half serial link, in a
USB-C slot that replaces the case's TRRS hole. The RP2040-Zero snaps in (a
rigid lip on its left edge, a snap hook on its right) with no glue; the
breakout's tail sits in a glue pocket that locks one blob of hot glue in
mechanically.

Design notes and measurements: `docs/superpowers/specs/2026-10-02-skeletyl-platform-rev4-glue-free-design.md`
(rev. 4) on top of `docs/superpowers/specs/2026-09-25-skeletyl-usb-serial-design.md` (rev. 3) and
`docs/superpowers/specs/2026-09-20-skeletyl-rp2040zero-platform-design.md`.

## Build

    ../refs/fetch.sh                             # the original case STL
    python3 case_usb_serial.py                   # -> case_v4_103_usb_serial.stl (~3 min)
    python3 rp2040zero_platform.py               # -> .FCStd / .step / .stl + hook_coupon.stl
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
- **PLA** is fine: the snap hook bends about 1.1 % (it stands in a relief
  groove so it bends over 6.7 mm).
- **Test coupon first:** `hook_coupon.stl` is the part of the platform
  with the RP2040 lip, the snap hook, the tail lip and the glue pocket.
  Print it the same way and check that the Zero clicks in and the
  breakout's tail sits under its lip before printing the whole platform.
  If the hook is too stiff or too loose, change `HOOK_T` / `HOOK_LIP`.

## Assemble

The platform goes in from the bottom-plate side: the flat underside faces
the bottom plate, the ledges, walls, lips and the hook point up toward the switches.

1. **Solder first.** Four wires to the breakout's pads (on its back, at
   the tail end) and all wires to the RP2040-Zero's pads.
2. **Breakout, back side up** (the side with the wire pads faces up, the
   leads and the small SMD part face the platform; USB-C works either way
   round). Set the shell on the pedestal with its right side against the
   middle wall, tilting it so the tail's right edge goes under the tail
   lip, then lower the left side. The bump behind the shell sits against
   the dam.
3. **Glue pocket.** Fill the pocket around the tail with hot glue, over
   the tail end, the solder joints and the first mm of wire, until glue
   shows in the two holes underneath. Trim anything that comes through
   flush with the underside. This one blob takes the pull when you unplug
   the link cable.
4. **Board.** Components down, USB-C toward the wall. Slide its left edge
   under the lip on the middle wall, then press the right edge down: it
   pushes the snap hook aside and clicks under it. No glue. To take it
   out, push the hook outward and lift the right edge.
5. **Into the case.** Tilt the platform in so both USB-C shells enter
   their slots, hold the plate against the ring faces and drive the two
   M4 × 8 screws from below.
6. BOOT/RESET face the bottom plate: remove it and press them through the
   window. Put `QK_BOOT` in the keymap as well.

## Fit checks before printing

| Parameter | Default | Why it matters |
| --- | --- | --- |
| `USB_H` | 3.2 | RP2040 USB-C shell height; sets the board height |
| `BOARD_Z_SHIFT` / `BOARD_X_SHIFT` | 0.0 | Nudge the board if its shell catches in the slot |
| `CORNER_T` / `CORNER_GAP` | 2.5 / 0.2 | Corner stops at the board's front: arm thickness and gap to the PCB edges (the board has 0.33 mm to the wall behind it) |
| `SER_H` / `SER_W` | 3.2 / 8.94 | Serial shell; sets the pedestal height. The slot has 0.21 mm each way vertically, 0.44 sideways |
| `SER_L` / `SER_SHELL_L` / `SER_PCB_W` | 14.0 / 8.5 / 8.9 | Breakout overall length, shell + bump length, PCB width (caliper); they place the dam, the tail lip and the pocket |
| `BOARD_SIDE_GAP` | 0.1 | RP2040 left edge → the middle wall |
| `LIP_OVER` / `LIP_GAP` | 0.5 / 0.1 | Rigid lips over the tail and the RP2040: reach over the edge, gap above the PCB |
| `HOOK_T` / `HOOK_LIP` / `HOOK_GAP` | 0.8 / 0.4 / 0.4 | Snap hook arm thickness, reach over the PCB (= its bend), gap to the ledge and groove width |
| `ZERO_PAD1_Y` | 2.38 | USB-end PCB edge → pad 1 centre (pad 4 ≈ 10 mm); places the left lip and the hook over unused pads |
| `POCKET_FLOOR_GAP` / `DAM_GAP` | 0.8 / 0.2 | Glue under the tail (clears the SMD part); bump → dam |
| `SER_RECESS` / `USB_RECESS` | 0.8 / 1.0 | Shell faces behind the wall's outer face (wall is 2 mm); the serial shell sat too deep at 1.0 |
| `CSK_ANGLE` / `CSK_DEPTH` | 90 / 1.2 | Countersink for the conical heads: Ø6.9 at the underside down to the Ø4.5 hole. A full-depth seat does not fit the 2 mm plate, so the head hangs ≤ 1.3 mm below it (0.95 mm clear of the bottom plate) |

Both USB-C shells need rounded corners (≥ R0.8) to pass the slots'
full-radius ends.

## Clearance check

    python3 check_clearance.py            # against case_v4_103_usb_serial.stl

Reports any case surface sample inside the platform (only contact on the
rings' face plane is allowed) and writes `sec_*.png` cross-sections (case
blue, platform red, held parts green).
Last run: 2026-10-03 — 17315 points on the Z −3.75 contact plane; no collisions.
