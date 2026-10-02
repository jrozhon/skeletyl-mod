# Skeletyl RP2040-Zero platform — glue-free seating (rev. 4)

Date: 2026-10-02. Builds on rev. 3
(`2026-09-25-skeletyl-usb-serial-design.md`); its coordinate frame, case
interface and serial slot still apply unless changed here.

## Why

The hand-wired build on rev. 3 worked, but the parts were hard to keep in
place:

- The RP2040-Zero and the USB-C breakout moved while the platform was
  tilted into the case. The parts are placed on the platform outside the
  case, then the whole platform is tilted in so both USB-C shells enter
  their wall slots, then screwed to the rings (confirmed with the user).
- Hot glue on smooth surfaces (shell → pedestal, PCB → ledges) did not
  hold them reliably.
- The breakout PCB (8.9 wide) is narrower than its slot (9.82), so when a
  cable is unplugged, only the glue resists the pull toward the wall.

Rejected along the way, with the user: male/female headers to make the
harness pluggable (the parts on offer did not suit), a different
connector or receptacle, and a lip in the case slot to stop the shell
(too sensitive to printer precision). The case, the serial breakout, the
cable and the pin map stay as they are.

## Goal

Only the platform changes:

- The **Zero** is held with no glue: a rigid lip on its left edge, a snap
  hook on its right edge, plus the existing ledges and corner stops.
- The **breakout** is held by a **glue pocket**: one blob of hot glue
  locked mechanically into the pocket around the tail end and the solder
  joints, plus a rigid lip over the tail. The glue no longer depends on
  sticking to a smooth surface.

## Measured parts (user, 2026-10-02)

| Part | Value | Was |
| --- | --- | --- |
| Breakout shell length, front face → where the bare PCB starts behind the leads | **8.5** | 9.0 (`SER_SHELL_L`) |
| Breakout overall length, front face → tail end | **14.0** | 14.6 (datasheet, `SER_L`) |
| Breakout tail (bare PCB) | 5.5 | 5.6 |
| Height at the leads/body bump behind the shell | 3.2 (= shell) | — |
| Breakout wire pads | on the **back** (the side without the leads) | — |
| Zero: USB-end PCB edge → pad 4 centre | ≈ 10 (pitch 2.54) | — |

The breakout's front side (leads, black body, "JRC-223" silkscreen and a
small SMD part near the tail end) was photographed. It has no hole, notch
or step that faces the wall, which is why its unplug pull needs the glue
pocket.

## Positions (platform frame)

Unchanged from rev. 3: Zero PCB X 12.0…30.0, Y −33.77 (USB edge)…−10.27,
Z 0.35…1.35 (components down); left ledge X 11.70…12.90 and right ledge
X 28.80…30.30, top Z 0.35; corner stops to Z 1.85; serial shell
X 2.13…11.07, Z −2.85…0.35, front face Y −35.27 (`SER_RECESS` 0.8); plate
top Z −3.75.

Zero pad centres along the long edges, from the USB edge: pad *k* at
≈ 10.0 + (k − 4) × 2.54, i.e. Y −33.77 + that. Before modelling, check this
against Waveshare's RP2040-Zero STEP/drawing (`ZERO_PAD1_Y`, `ZERO_PAD_PITCH`).

| Pad | Left edge | Right edge | Y (≈) |
| --- | --- | --- | --- |
| 4 | GP3 (free) | GP29 (free) | −23.77 |
| 5 | GP4 (free) | GP28 (free) | −21.23 |
| 6 | GP5 (free) | GP27 (R4) | −18.69 |

Breakout with the new lengths: shell + bump Y −35.27…−26.77, tail
Y −26.77…−21.27, PCB centred at Z −1.25 (0.8 thick: Z −1.65…−0.85).

## 1. Breakout: back side up, glue pocket

**Orientation.** The breakout is mounted **back side up**, upside down
compared with the user's photo: the wire pads face up and the wires leave
upward, into open space. USB-C is reversible, so the link works either way
round. The leads/body bump and the small SMD part face down. The bump is
no taller than the shell, so it rests on the pedestal like the shell.

**Pedestal.** As rev. 3, Z −3.75 → −2.85, now Y −31.6 (plate edge)…−26.77
(the shell and bump together, 8.5 long). The shell front overhangs the
plate edge into the wall recess, as before.

**Shell side walls.**
- *Left:* X `SER_X0` − 1.2 … `SER_X0` (line-to-line with the shell, as
  rev. 3), Y −31.6…−26.77, up to the shell's mid-height (Z −1.25). It
  locates the shell sideways and is low enough to tilt the part in.
- *Right:* the shared middle wall (below).

**Shared middle wall** between the breakout and the Zero. There is only
0.93 mm between the serial shell (X 11.07) and the Zero's left edge
(X 12.0), so instead of two hooks one rigid wall serves both parts:
- X 11.07…11.90 (`BOARD_SIDE_GAP` 0.1 to the Zero), Y −31.6…−17.69. It
  replaces rev. 3's raised right serial stop and merges with the left
  ledge where they overlap. Beside the shell (Y −31.6…−26.77) it only
  rises to Z 0.35, the ledge height, so the GP0/GP1 wires cross freely
  to the breakout. From Y −26.77 forward it rises to Z 2.15.
- It is the right side wall of the shell and the tail, line-to-line.
- **Tail lip** to the left: 0.5 over the tail's right edge
  (X 10.57…11.07), underside Z −0.75 (0.1 above the tail's top face),
  0.6 thick, Y −26.77…−24.77 (the first 2 mm of the tail behind the bump).
  This assumes the back-side pads sit near the tail end, clear of the
  lip; the user confirms before modelling (`SER_LIP_L` shortens it if
  not).
- **Zero lip** to the right (section 2).

**Glue pocket** around the tail end:
- *Rear wall:* rev. 3's stop behind the tail, moved for the 14.0 length:
  Y −21.07…−18.57 (0.2 off the tail end), X from the left pocket wall to
  the middle wall, up to Z −0.35 (0.5 above the tail top). The middle
  stays closed: the wires leave upward, not backward.
- *Left wall:* X 1.15…1.95 (0.2 off the tail's left edge, so glue runs
  down the edge), Y −24.27…−18.57, same height.
- *Right wall:* the middle wall.
- *Floor:* Z −2.45, 0.8 under the tail's underside. That clears the small
  SMD part near the tail end, and glue gets under the tail.
- *Dam:* the pocket's wall-side end at Y −24.27: a rib from the floor up to
  0.1 under the tail (Z −1.75), across the pocket. It takes the unplug pull
  through the glue blob.
- *Keys:* two Ø1.5 holes through the floor and the plate. Glue runs into
  them and anchors the blob.
- *Open top:* hot glue fills the pocket from above, over the tail end, the
  solder joints and the first mm of wire.

The unplug pull goes: shell → PCB → glue wrapped around the tail and the
joints → the dam and the keys. Plug-in push: the tail end against the rear
wall, as now. To remove the breakout, peel the glue out.

**Removed:** rev. 3's serial L stops (replaced by the pocket walls) and
their side arms.

## 2. Zero: left lip, right snap hook, no glue

**Left lip** (rigid, on the middle wall): it overhangs the Zero's left edge
by 0.5 (X 11.90…12.50, 0.1 off the edge with `BOARD_SIDE_GAP`), underside
Z 1.45 (0.1 above the flat top), top Z 2.15. Y over pads 4–6 (GP3–GP5,
all free) ± 1: Y −24.77…−17.69. The underside has a 45° chamfer toward the
wall so it prints without support.

**Right snap hook:**
- Vertical cantilever outside the right ledge: X 30.40…31.20 (0.8 thick,
  `HOOK_T`), from the plate top (Z −3.75) up to Z 2.15. It flexes outward
  in X.
- Lip 0.5 over the PCB's right edge (X 29.50…30.00 over the board, which
  ends at X 30.0), underside Z 1.45, with a 45° ramp on top so the PCB
  pushes the hook aside as it goes down.
- Y centred on GP28 (pad 5), 2 wide: Y −22.23…−20.23. The neighbours'
  joints are ≥ 0.75 away: GP29 is free, GP27 (R4) is at −18.69.
- The case is clear: no case surface at X < 38.8 for Y −22.5…−18 between
  the plate and Z 3.35 (probed 2026-10-02 on
  `case_v4_103_usb_serial.stl`). Ring B's flat face (X 30.93) only starts
  at Y ≤ −24.
- The plate outline reaches X 31.8 (`PLATE_RIGHT_X`), so the hook stands
  on the plate. The 0.1 gap between the arm and the right ledge (X 30.30)
  lets it flex.
- Strain: deflection 0.6 (lip 0.5 + gap 0.1) over a 5.2 arm (Z −3.75 →
  the lip at 1.45), 0.8 thick: 1.5·t·δ/L² ≈ 2.7 %. Fine in PETG, marginal
  in PLA. Hence the test coupon (below) and the `HOOK_T` / `HOOK_LIP`
  parameters.

**Insertion:** components down, USB end toward the wall. Slide the left
edge under the left lip, lower the right edge: it snaps under the hook.
The ledges carry it, the corner stops hold it front to back, the lips
stop it lifting.

**Removal:** push the hook outward and lift the right edge.

**Unchanged:** ledges, corner stops (front L stops, to Z 1.85), window,
screw seats and countersinks, plate outline.

## 3. Assembly (README)

1. Solder the four wires to the breakout's back-side pads and the Zero's
   pads first, as before.
2. Breakout: back side up, shell on the pedestal, tail under the middle
   wall's lip, tail end against the rear wall. Fill the glue pocket with
   hot glue and let it set.
3. Zero: components down, left edge under its lip, press the right edge
   down until the hook clicks.
4. Tilt the platform into the case so both shells enter their slots, and
   screw it to the rings with the two M4 × 8.

## 4. Parameters

New or changed in `rp2040zero_platform.py`:

| Parameter | Default | Meaning |
| --- | --- | --- |
| `SER_SHELL_L` | 8.5 | shell + bump length (measured) |
| `SER_L` | 14.0 | overall length (measured) |
| `MID_WALL_TOP_Z` | 2.15 | middle wall top |
| `LIP_OVER` | 0.5 | how far each lip and the hook reach over a PCB edge |
| `LIP_GAP` | 0.1 | lip underside above the PCB top |
| `SER_LIP_L` | 2.0 | tail lip length behind the bump |
| `ZERO_PAD1_Y` / `ZERO_PAD_PITCH` | 2.38 / 2.54 | USB edge → pad 1 centre (so pad 4 ≈ 10.0), pitch |
| `HOOK_T` | 0.8 | snap-hook arm thickness |
| `HOOK_W` | 2.0 | snap-hook width along Y |
| `HOOK_GAP` | 0.1 | hook arm → right ledge |
| `POCKET_FLOOR_GAP` | 0.8 | tail underside → pocket floor |
| `POCKET_L` | 3.0 | pocket length in front of the tail end |
| `POCKET_KEY_D` | 1.5 | key hole diameter |

## 5. Verification

1. `tests/test_platform.py`, updated:
   - single valid solid, flat underside, extents;
   - the held parts (Zero PCB + shell; breakout shell, bump and tail with
     the new lengths) don't intersect the part;
   - each lip's underside is `LIP_GAP` above its PCB and reaches `LIP_OVER`
     over the PCB edge; the left lip and the hook sit at the pad positions
     above and stay ≥ 0.7 clear of the used pads (GP0, GP1, GP27);
   - hook arm free of the ledge by `HOOK_GAP`;
   - glue pocket: floor, dam, key holes through the plate, rear wall 0.2
     behind the tail end;
   - rev. 3's serial L stops and the raised right serial stop are gone
     (replaced by the middle wall);
   - everything else unchanged (screw seats, window, ledges, corner stops).
2. `check_clearance.py` against `case_v4_103_usb_serial.stl`: no case
   samples inside the part except on the Z −3.75 contact plane. New section
   PNGs: an XZ cut through the hook and the left lip (Y −21.2), and one
   through the glue pocket (Y −22).
3. **Test coupon** `hook_coupon.stl`: a cut-out of the plate, X 10…32 ×
   Y −26…−16, so the Zero's lip and hook and the breakout's tail lip can be
   tried with the real parts before printing the full platform. Same
   script, same parameters.

## Not in scope

The case, the pin map, the firmware, the serial breakout and the cable.
