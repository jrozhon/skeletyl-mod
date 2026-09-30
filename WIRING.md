# Wiring manual: Skeletyl halves on an RP2040-Zero

Two Skeletyl builds share one pinout. They differ in one wire, the thumb
nearest the centre, so each has its own firmware target (§3):

- **Hand-wired:** switches, diodes and wire, no RGB.
- **Flex PCB:** the original Bastardkb flex PCBs (plate + thumb cluster)
  with an RP2040-Zero in place of the Splinktegrated.

Both use the RP2040-Zero platform (`rp2040zero_platform/`) and the USB-C
serial link between the halves.

## 1. Matrix (the flex PCB's, except one thumb)

4 rows × 5 columns per half, 18 keys. The names are the ones printed on
the flex PCB (every key has a label like `C3R2`, and the header pads are
labelled too), so both builds use the same names.

| | C2 pinky | C3 ring | C4 middle | C5 index | C6 inner index |
| --- | --- | --- | --- | --- | --- |
| **R1** top row | C2R1 | C3R1 | C4R1 | C5R1 | C6R1 |
| **R2** home row | C2R2 | C3R2 | C4R2 | C5R2 | C6R2 |
| **R3** bottom row | C2R3 | C3R3 | C4R3 | C5R3 | C6R3 |
| **R4** thumbs, flex | C2R4 | — | C4R4 | C5R4 | — |
| **R4** thumbs, hand-wired | — | — | C4R4 | C5R4 | C6R4 |

- On both halves, C2 is the pinky column and C6 the inner index column, so
  the right half is a mirror image of the left.
- **Flex thumbs:** C2, C4 and C5. From the key under the inner index
  column toward the centre of the keyboard, the thumbs are **C4R4, C5R4,
  C2R4**. That matches QMK's Skeletyl layout; go by the thumb PCB's
  silkscreen. The thumb nearest the centre (Space on the left, Enter on the
  right) shares the pinky column's wire.
- **Hand-wired thumbs:** C4, C5 and C6, in that order toward the centre:
  **C4R4, C5R4, C6R4**. The thumb nearest the centre moves from C2 to C6,
  so each thumb's column follows its position. The
  `skeletyl_zero_handwired_*` firmware maps C6R4 back to the key QMK expects
  on C2R4 (§3).
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

**Diode orientation is what counts, not which side the diode sits on.**
The firmware (`ROW2COL`, fixed by the flex PCB, which shares it) needs the
anode toward the row and the **band toward the column**:

- Diode on the column side (steps above): row → switch → diode → band →
  column.
- Diode on the row side also works, but flipped: row → diode → band →
  switch → column. The band faces the switch, away from the row wire.

The common hand-wiring habit of a diode on the row with its band on the
row wire is `COL2ROW`. With this firmware, no key wired that way works.
A single diode in backwards kills only its own key, so when one key is
dead, check its band first.

- **Rows:** R1, R2 and R3 each link the 5 keys of one row. R4 links the 3
  thumbs.
- **Columns:** C2 through C6 each link the diode bands of one column. The C4,
  C5 and C6 wires carry on to their thumb (C4 → C4R4, C5 → C5R4,
  C6 → C6R4). C2 has no thumb.
- In total you run 9 wires to the controller: R1–R4 and C2–C6.

### Schematic

One hand-wired half. Both halves are wired the same way.

```
                    C2          C3          C4          C5          C6
                    GP9        GP10        GP11        GP12        GP13
                   pinky       ring       middle       index    inner index
                     │           │           │           │           │
R1 GP14 ───┬─────────┼─┬─────────┼─┬─────────┼─┬─────────┼─┐         │
           └──SW──>|─┤ └──SW──>|─┤ └──SW──>|─┤ └──SW──>|─┤ └──SW──>|─┤
R2 GP15 ───┬─────────┼─┬─────────┼─┬─────────┼─┬─────────┼─┐         │
           └──SW──>|─┤ └──SW──>|─┤ └──SW──>|─┤ └──SW──>|─┤ └──SW──>|─┤
R3 GP26 ───┬─────────┼─┬─────────┼─┬─────────┼─┬─────────┼─┐         │
           └──SW──>|─┘ └──SW──>|─┘ └──SW──>|─┤ └──SW──>|─┤ └──SW──>|─┤
R4 GP27 ───────────────────────────┬─────────┼─┬─────────┼─┐         │
                                   └──SW──>|─┘ └──SW──>|─┘ └──SW──>|─┘
```

- `┼` is a crossing with no connection. `┤` and `┘` are solder joints on
  the column wire.
- `>|` is the diode, with the band (`|`) toward the column (`ROW2COL`).
- C2 and C3 end at R3: they have no thumb.
- On the case the thumbs sit in the same order as their columns, from the
  key under the inner index column toward the centre:

```
                          left: Esc     Tab       Space
                         right: Del     Bksp      Enter
   inner index column ──>    [C4R4]  [C5R4]    [C6R4]   ──> centre of keyboard
```

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
                 └──●────●────●────●────●──┘
                   GP9 GP10 GP11 GP12 GP13
                   C2   C3   C4   C5   C6
                  pinky           inner index
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

### Connections (same on both builds, except the thumbs)

| Pad | Connects to | Notes |
| --- | --- | --- |
| GP9 | C2 (pinky column) | flex: also the thumb key C2R4 |
| GP10 | C3 (ring column) | |
| GP11 | C4 (middle column) | also the thumb key C4R4 |
| GP12 | C5 (index column) | also the thumb key C5R4 |
| GP13 | C6 (inner index column) | hand-wired: also the thumb key C6R4 |
| GP14 | R1 (top row) | |
| GP15 | R2 (home row) | |
| GP26 | R3 (bottom row) | |
| GP27 | R4 (thumbs) | |
| GP0 | serial breakout **D+** | the split link: a single half-duplex wire, like the original TRRS |
| GP1 | serial breakout **D−** | unused by the firmware; worth wiring now so two-wire serial is firmware-only (see §3) |
| 5V | serial breakout **U** | powers the other half through the link |
| GND | serial breakout **G** | |
| GP2 | *(flex build only, optional)* RGB **DIN** | hand-wired: leave free |
| 3V3 | *(flex build only, optional)* RGB **VCC** | each half powers its own LEDs |

- GP16 is the RP2040-Zero's on-board RGB LED. No wire is needed.
- GP3–GP8, GP28 and GP29 are free.
- **Plug USB into one half only.** On the Zero, the USB-C VBUS pins
  connect straight to the 5V pad with no diode (Waveshare schematic). The
  link joins both halves' 5V, so a second USB cable would connect two
  supplies directly.
- The link port carries 5 V. Only ever connect it half to half, never to a
  computer.
- **RGB runs on 3.3 V**, as it did on the Splinktegrated. Powered from 5 V,
  the LEDs would need a data signal of at least 3.5 V, and the Zero's
  3.3 V output falls short of that. Each half's LEDs load only that half's
  regulator: 18 LEDs at the firmware's brightness cap of 50/255 draw about
  180 mA.

### Flex build: header pads to the RP2040-Zero

The Splinktegrated's ribbons went to two headers on the plate PCB. Solder
the wires to the same pads instead, going by the silkscreen label printed
next to each pad.

| Plate header | Pads in order | Wire to |
| --- | --- | --- |
| 5-pad header | C3, X, C2, X, R1 | C3 → GP10, C2 → GP9, R1 → GP14; skip the two X pads (the second one is the unused 6th column) |
| 6-pad header | R3, R2, C4, C5, C6, R4 | GP26, GP15, GP11, GP12, GP13, GP27 |
| 4-pad header (C5, C4, R4, C2) | ribbon to the thumb PCB | leave as original |
| VCC / GND / DIN (3 pads) | RGB in | only if you want RGB: 3V3, GND, GP2 |

## 3. QMK

The firmware lives in the userspace repo (`~/qmk_userspace`, keymap
`jrozhon`), one target pair per build:

| Build | Left half | Right half |
| --- | --- | --- |
| Flex PCB | `skeletyl_zero_jrozhon_lefthalf` | `skeletyl_zero_jrozhon_righthalf` |
| Hand-wired | `skeletyl_zero_handwired_lefthalf` | `skeletyl_zero_handwired_righthalf` |

See that repo's README for building and flashing.

- **Hand-wired thumbs:** `SKELETYL_HANDWIRED=yes` adds `handwired.c` to the
  keymap, which swaps C2 and C6 on the thumb row before QMK looks up a
  keycode or a key's hand (Chordal Hold). The key on C6R4 then acts as the
  stock C2R4 (Space / Enter), and the keymap stays unchanged.

- **Keymap:** unchanged. The matrix is the same as QMK's
  `bastardkb/skeletyl` (matrix rows 0–3 = R1–R4, columns 0–4 = C2–C6), so
  its `LAYOUT_split_3x5_3` and the shared `users/jrozhon/jrozhon.c` layers
  work as they are (the hand-wired thumb on C6 goes through `handwired.c`,
  above). Diode direction is `ROW2COL`.
- **Pins:** set in the keymap's `config.h` when `SKELETYL_RP2040_ZERO=yes`,
  on top of `bastardkb/skeletyl/promicro` with `CONVERT_TO=rp2040_ce`.
- **Master detection:** the converter senses USB power on GP19, which is
  wired on the Splinktegrated but not on the Zero. The Zero build detects
  the USB connection in software instead (`SPLIT_USB_DETECT`): a half
  that the host enumerates within 2 s becomes master. Plugged in while the
  computer is off (USB powered, host not running), no half enumerates and
  both settle as slaves; `SPLIT_WATCHDOG_ENABLE` (shared `config.h`) then
  reboots them every ~2 s until the host comes up, so no replugging is
  needed.
  - **No VBUS divider on the Zero.** On the Splinktegrated, GP19 senses the
    USB connector's side of a Schottky diode, which the link's 5V cannot
    reach. The Zero has no such diode: its USB VBUS *is* the 5V pad, and
    the link joins both halves' 5V. A divider from 5V to a GPIO would read
    high on both halves and make both master. Hardware sensing would need
    the Zero's VBUS trace cut and bridged with a Schottky, the divider on
    the connector side; that diode would also make a second USB cable
    safe. Not done: the watchdog covers the use case.
- **Handedness:** both halves are wired identically, so it lives in
  EEPROM (`EE_HANDS`). It is seeded on first boot by the left or right
  file (`INIT_EE_HANDS_LEFT` / `_RIGHT`). Plain `-bl uf2-split-left`
  cannot write it on the RP2040.

### Split link: one wire, or two

The link is **half-duplex on one wire**: data on D+ (GP0), plus 5V and
GND, the same three conductors as the stock Skeletyl's TRRS link. The half
with USB sends a request, then listens, and the other half answers on the
same wire. That is plenty for key presses, layer state and the RGB sync.

**Two wires (full-duplex)** only pays off when much more data crosses the
link, such as a trackball or displays on the other half. If D− is already
soldered to GP1 on both halves, switching needs no rewiring. Add to the
Zero block of the keymap's `config.h`:

```c
#    define SERIAL_USART_FULL_DUPLEX
#    define SERIAL_USART_RX_PIN 1U // GP1, D−
#    define SERIAL_USART_PIN_SWAP
```

Transmit stays on GP0 (D+): QMK takes it from `SOFT_SERIAL_PIN`, which the
block already sets. Defining `SERIAL_USART_TX_PIN` as well fails the build
with a redefinition error.

`SERIAL_USART_PIN_SWAP` is what keeps both halves wired identically. A
straight USB-C cable joins D+ to D+ and D− to D−, so one half's transmit
pin meets the other half's transmit pin. With this option set, the half
with USB swaps its TX and RX when it starts (QMK's RP2040 serial driver,
`serial_transport_driver_master_init`). Either half can still be the one
with USB. The snippet compiles (checked 2026-09-26) but is untested on
hardware.

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
