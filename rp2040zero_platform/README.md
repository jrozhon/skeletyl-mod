# RP2040-Zero + TRRS platform for the Skeletyl V4

Replaces the Splinktegrated PCB in a hand-wired Skeletyl. Holds a Waveshare
RP2040-Zero **components down** (USB-C in the case's USB slot, BOOT/RESET
reachable from below) and a PJ-320A TRRS jack in the case's jack hole. Bolts
to the two existing M4 heat-set rings with M4 × 6–8 mm screws. Use a head
no wider than Ø7 mm (DIN 912 socket head) — at ring B the rear wall is only
3.5 mm from the screw axis.

Design notes and measurements: `docs/superpowers/specs/2026-09-20-skeletyl-rp2040zero-platform-design.md`.

## Build

    freecadcmd rp2040zero_platform.py        # writes .FCStd / .step / .stl here
    python3 -m unittest discover -s tests -t .. -v   # from this directory

Or open `rp2040zero_platform.py` in FreeCAD as a macro; a `Platform` object is
added to the active document.

## Print

Flat, pockets up, no supports. 0.2 mm layers, 3+ perimeters. Mirror the STL in
the slicer for the other half, exactly like the case.

## Assemble

1. Drop the PJ-320A into its pocket, nose toward the wall; legs hang through
   the slots (either orientation). Solder its wires from underneath.
2. Place the RP2040-Zero upside down: USB-C toward the wall resting on the
   cradle, far corners on the two seats. Wire it on the flat (label) side,
   which faces up. Zip-tie through the slots (under the plate, over the board).
3. Slip the ring pockets over the case rings, screw down.
4. BOOT/RESET face the bottom plate: remove the plate and press through the
   floor window with a toothpick. Put `QK_BOOT` in the keymap; the Splinky
   `RP2040_BOOTLOADER_DOUBLE_TAP_RESET*` settings do not apply.

## Before printing, check on your parts

| Parameter | Default | Why it matters |
| --- | --- | --- |
| `USB_H` | 3.2 | Sets the board height; USB-C must land in the 7 mm slot |
| `USB_OVERHANG` | 1.3 | How far the shell sticks past the PCB edge |
| `BOARD_X_SHIFT` | 0.0 | Sideways nudge if the USB-C is off-centre in the slot |
| `JACK_AXIS_H` | 2.5 | Barrel axis height above the jack's mounting face |
| `JACK_AXIS_X` | 5.0 | Sideways nudge for the jack |

All other dimensions are in the parameter block at the top of the script.

## Clearance check

    ./refs/fetch.sh
    python3 rp2040zero_platform/check_clearance.py

Samples the case surface and reports any sample inside the platform (only
bore/ring proximity is allowed) and writes `sec_*.png` cross-sections.
Last run: 2026-09-20 — 13486 points inside, all within the ring bores; no collisions.
