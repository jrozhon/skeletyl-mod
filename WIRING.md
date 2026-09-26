# Wiring manual: Skeletyl halves on an RP2040-Zero

Two Skeletyl builds share one pinout, so one firmware runs both:

- **Hand-wired:** switches, diodes and wire, no RGB.
- **Flex PCB:** the original Bastardkb flex PCBs (plate + thumb cluster)
  with an RP2040-Zero in place of the Splinktegrated.

Both use the RP2040-Zero platform (`rp2040zero_platform/`) and the USB-C
serial link between the halves.

## 1. Matrix (same as the flex PCB)

4 rows × 5 columns per half, 18 keys. The names are the ones printed on
the flex PCB (every key has a label like `C3R2`, and the header pads are
labelled too), so both builds use the same names.

| | C2 pinky | C3 ring | C4 middle | C5 index | C6 inner index |
| --- | --- | --- | --- | --- | --- |
| **R1** top row | C2R1 | C3R1 | C4R1 | C5R1 | C6R1 |
| **R2** home row | C2R2 | C3R2 | C4R2 | C5R2 | C6R2 |
| **R3** bottom row | C2R3 | C3R3 | C4R3 | C5R3 | C6R3 |
| **R4** thumbs | C2R4 | — | C4R4 | C5R4 | — |

- On both halves, C2 is the pinky column and C6 the inner index column, so
  the right half is a mirror image of the left.
- The thumb row uses only C2, C4 and C5. From the key under the inner index
  column toward the centre of the keyboard, the thumbs are **C4R4, C5R4,
  C2R4**. That matches QMK's Skeletyl layout; on the flex build, go by the
  thumb PCB's silkscreen.
- **Thumb PCB:** it connects to the plate's 4-pad header with a straight
  4-wire ribbon, pad order C5, C4, R4, C2 on both boards. Its own KiCad net
  for the thumb row is `row1`, but it lands on the plate's `row5` net,
  which the silkscreen calls R4.
- **Diodes:** the flex PCB puts the diode's cathode (the band) toward the
  column. In QMK that direction is `ROW2COL`.

### Hand-wiring

For every key:

1. One switch pin goes to its **row** wire.
2. The other switch pin goes to the diode's anode (the end without the band).
3. The diode's cathode (**band**) goes to its **column** wire.

MX switch pins are interchangeable, so either pin can take the row.

- **Rows:** R1, R2 and R3 each link the 5 keys of one row. R4 links the 3
  thumbs.
- **Columns:** C2 through C6 each link the diode bands of one column. The C2,
  C4 and C5 wires carry on to their thumb (C2 → C2R4, C4 → C4R4,
  C5 → C5R4).
- In total you run 9 wires to the controller: R1–R4 and C2–C6.

## 2. RP2040-Zero pinout

### Pad map as mounted

Flat side up, USB-C toward the rear wall, seen from above. The left edge is
the one next to the serial breakout.

```
                     USB-C (rear wall)
                 ┌─────────[=====]─────────┐
 serial D+  GP0  ●                         ●  5V    ← breakout U
 serial D−  GP1  ●                         ●  GND   ← breakout G
 (RGB DIN)  GP2  ●                         ●  3V3
            GP3  ●                         ●  GP29
            GP4  ●                         ●  GP28
            GP5  ●                         ●  GP27  R4 thumbs
            GP6  ●                         ●  GP26  R3 bottom
            GP7  ●                         ●  GP15  R2 home
            GP8  ●                         ●  GP14  R1 top
                 └───●─────●─────●─────●─────●───┘
                   GP9  GP10  GP11  GP12  GP13
                    C2    C3    C4    C5    C6
                 pinky                    inner index
                   (front edge, toward the keys)
```

### Why these pins

1. **Wires leave toward the keys, on both halves.** The front edge faces
   the keys on either half, and all 9 matrix wires sit on the front edge
   and around the front-right corner of the map above. The case and
   platform are mirrored for the other half but the RP2040-Zero is not, so
   its edges swap walls:
   - **Right half** (the case as modelled): the board sits in the case's
     rear-left corner. The row pads face the keys, and the link wires to
     the breakout beside the left edge are short.
   - **Left half** (mirrored): the rows' edge faces the wall. The row wires
     leave around the front corner (a few mm longer), and the D+/D− wires
     cross the board to the breakout, which is now on the 5V/GND side.
2. **Grouped and in order.** Columns C2–C6 → GP9–GP13, rows R1–R4 →
   GP14, GP15, GP26, GP27: each group is contiguous and ascending, which
   makes the firmware pin lists easy to check against the board.
3. **Hardware UART on the link.** GP0/GP1 are UART0 TX/RX, so the link can
   switch from single-wire to two-wire serial later with no rewiring.
4. **Analog pins kept free.** GP28 and GP29 are two of the RP2040's four
   ADC inputs. They stay free for anything analog you may add later.

The platform's stops don't limit the choice: the pads are soldered from
the flat (top) side and the wires bend away from the board.

### Connections (same on both builds)

| Pad | Connects to | Notes |
| --- | --- | --- |
| GP9 | C2 (pinky column) | also the thumb key C2R4 |
| GP10 | C3 (ring column) | |
| GP11 | C4 (middle column) | also the thumb key C4R4 |
| GP12 | C5 (index column) | also the thumb key C5R4 |
| GP13 | C6 (inner index column) | |
| GP14 | R1 (top row) | |
| GP15 | R2 (home row) | |
| GP26 | R3 (bottom row) | |
| GP27 | R4 (thumbs) | |
| GP0 | serial breakout **D+** | the split link: a single half-duplex wire, like the original TRRS |
| GP1 | serial breakout **D−** | optional; only for two-wire serial later |
| 5V | serial breakout **U** | powers the other half through the link |
| GND | serial breakout **G** | |
| GP2 | *(flex build only, optional)* RGB **DIN** | hand-wired: leave free |

- GP16 is the RP2040-Zero's on-board RGB LED. No wire is needed.
- GP3–GP8, GP28 and GP29 are free.
- The link port carries 5 V. Only ever connect it half to half, never to a
  computer.

### Flex build: header pads to the RP2040-Zero

The Splinktegrated's ribbons went to two headers on the plate PCB. Solder
the wires to the same pads instead, going by the silkscreen label printed
next to each pad.

| Plate header | Pads in order | Wire to |
| --- | --- | --- |
| 5-pad header | C3, X, C2, X, R1 | C3 → GP10, C2 → GP9, R1 → GP14; skip the two X pads (the second one is the unused 6th column) |
| 6-pad header | R3, R2, C4, C5, C6, R4 | GP26, GP15, GP11, GP12, GP13, GP27 |
| 4-pad header (C5, C4, R4, C2) | ribbon to the thumb PCB | leave as original |
| VCC / GND / DIN (3 pads) | RGB in | only if you want RGB: 5V, GND, GP2 |

## 3. QMK

The matrix is the same as QMK's `bastardkb/skeletyl`, whose
`LAYOUT_split_3x5_3` works unchanged: matrix row 0–3 = R1–R4 and matrix
column 0–4 = C2–C6. Starting point for `keyboard.json`:

```json
{
    "processor": "RP2040",
    "bootloader": "rp2040",
    "diode_direction": "ROW2COL",
    "matrix_pins": {
        "cols": ["GP9", "GP10", "GP11", "GP12", "GP13"],
        "rows": ["GP14", "GP15", "GP26", "GP27"]
    },
    "split": {
        "enabled": true,
        "serial": {"driver": "vendor", "pin": "GP0"}
    }
}
```

Both halves are wired identically, so the firmware can't tell left from
right by a pin. Add `#define EE_HANDS` to `config.h` and flash each half
once with `qmk flash -bl uf2-split-left` and `-bl uf2-split-right`.

On the flex build with RGB, add `"ws2812": {"pin": "GP2", "driver": "vendor"}`
and reuse `bastardkb/skeletyl`'s `rgb_matrix` layout.

## Flex PCB check (2026-09-26)

Read from the KiCad sources: the plate is rev. 1.3; the thumb cluster is
release 2.1, the only release, identical to `main`.

- Every matrix net's switch, diode and header pads connect through copper
  traces on both boards, including both pad positions of the reversible
  switch footprints (so the same PCB works on either half).
- On both boards, each diode's cathode goes to its column and its anode to
  the switch; the other switch pin goes to the row.
- Thumb cluster: 3 keys on C2, C4 and C5, one row. From the outer end,
  they are C4R4, C5R4, C2R4. This follows QMK's layout and also the thumb
  PCB's LEFT/RIGHT silkscreen, read the same way as on the plate.
- RGB (not used by the hand-wired build): DIN goes through a series
  resistor to the first LED. The thumb PCB's chain has 3 LEDs and is fed
  from the plate's DOUT pads.

## Sources

- Matrix, diode direction and silkscreen labels: `refs/Skeletyl-PCB-plate`
  (flex rev. 1.3) and `refs/TBK-Mini-PCB-thumb-cluster` (rev. 2.1), both
  KiCad sources from `refs/fetch.sh`.
- QMK layout: `keyboards/bastardkb/skeletyl/info.json` in qmk_firmware.
- RP2040-Zero pad order and positions (side pads start 1.59 mm from the USB
  edge, 2.54 mm pitch): github.com/CountParadox/RP2040-Zero-Kicad.
