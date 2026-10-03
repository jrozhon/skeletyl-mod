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
  rev. 3), Y −30.4…−26.77 (behind −30.4 the case corner clips it to a
  sliver), up to the shell's mid-height (Z −1.25). It
  locates the shell sideways and is low enough to tilt the part in.
- *Right:* the shared middle wall (below).

**Shared middle wall** between the breakout and the Zero. There is only
0.93 mm between the serial shell (X 11.07) and the Zero's left edge
(X 12.0), so instead of two hooks one rigid wall serves both parts:
- X 11.07…11.90 (`BOARD_SIDE_GAP` 0.1 to the Zero), Y −31.6…−20.23. It
  replaces rev. 3's raised right serial stop and merges with the left
  ledge where they overlap. Beside the shell (Y −31.6…−26.77) it only
  rises to Z 0.35, the ledge height, so the GP0/GP1 wires cross freely
  to the breakout. From Y −26.77 forward it rises to Z 2.15.
- It is the right side wall of the shell and the tail, line-to-line.
- **Tail lip** to the left: 0.5 over the tail's right edge
  (X 10.57…11.07), underside Z −0.75 (0.1 above the tail's top face),
  Y −26.77…−24.77 (the first 2 mm of the tail behind the bump). It rises
  to the wall's top, which thickens the middle wall to 1.33 there; the
  0.83 left beside the RP2040 lip is backed by the pocket's glue below
  Z ≈ −0.35.

**Minimum thickness check (2026-10-03, after review):** slicing the STL
at 22 heights showed nothing thinner than 1.2 except the hook arm (0.8,
meant to bend), the middle wall beside the RP2040 lip (0.83, limited by
the 0.93 gap) and the ring B countersink breaking the plate's rear edge
(since rev. 3).
  The back-side pads sit at the tail end (user, 2026-10-02), clear of the
  lip.
- **Zero lip** to the right (section 2).

**Glue pocket** around the tail end:
- *Rear wall:* rev. 3's stop behind the tail, moved for the 14.0 length:
  Y −21.07…−18.57 (0.2 off the tail end), X from the left pocket wall to
  the middle wall, up to Z −0.35 (0.5 above the tail top). The middle
  stays closed: the wires leave upward, not backward.
- *Left wall:* X 0.75…1.95 (1.2 thick) (0.2 off the tail's left edge, so glue runs
  down the edge), Y −26.77…−18.57 (the whole tail), same height.
- *Right wall:* the middle wall.
- *Floor:* Z −2.45, 0.8 under the tail's underside, from the dam to the
  rear wall. That clears the small SMD part on the tail's underside, and
  glue gets under the tail.
- *Dam:* right behind the bump, Y −26.57…−25.37 (0.2 off the bump, 1.2
  thick), a rib across the pocket from the plate up to 0.1 under the tail
  (Z −1.75). The SMD part sits about 2–4 mm behind the bump (estimated
  from the photo), so the dam stays in front of it, where the tail has
  only vias. Its rear face takes the unplug pull through the glue blob;
  its front face also stops the bump on a plug-in push.
- *Keys:* two Ø1.5 holes through the floor and the plate, at X 4.1 and
  9.1, Y −23.22. Glue runs into them and anchors the blob. Glue that
  pushes through to the underside is trimmed flush (2.25 mm to the bottom
  plate).
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
Z 1.45 (0.1 above the flat top), top Z 2.15. Y over pads 4–5 ± 1:
Y −24.77…−20.23. Pads 4–5 are unwired on **both** halves: GP3/GP4 on the
right half, and GP29/GP28 on the left half, where the platform is
mirrored but the Zero is not (WIRING.md §2). Pad 6 would be GP27 (R4,
wired) on the left half, so the lip and the high middle wall end 0.79
before its pad (final review, 2026-10-03). No chamfer under it: one would reach
down into the PCB edge. The 0.6 overhang (0.7 thick) prints in PLA
without support; so does the tail lip's 0.5.

**Sideways play:** the board sits between the middle wall (X 11.90) and
the front-right corner stop's side arm (X 30.20), so it can shift 0.3.
At worst the left lip still overlaps it by 0.3 and the hook by 0.3.

**Right snap hook** (printed in **PLA**, so the strain is kept ≤ 1.5 %):
- Vertical cantilever outside the right ledge: X 30.70…31.50 (0.8 thick,
  `HOOK_T`; 0.4 off the ledge's outer face at X 30.30, `HOOK_GAP`). It
  flexes outward in X and rises to Z 2.55.
- **Relief groove:** the arm stands in a rectangular groove in the plate,
  X 30.30…31.90 × Y −22.63…−19.83 (0.4 around the arm), 1.5 deep. Its
  0.5 floor (Z −5.25) is the arm's root, so the arm bends over 6.7 mm
  (Z −5.25 → the lip at 1.45) instead of 5.2.
- The plate widens locally to X 33.5, 1.6 around the groove on its three
  free sides, to carry the groove's outer side. Below the ring faces the case is free to X 45.
- Lip 0.4 over the PCB's right edge (`HOOK_LIP`; X 29.60…30.00, the board
  ends at X 30.0), underside Z 1.45. Its tip has a 0.4 vertical land
  (`HOOK_LAND`, two 0.2 layers) up to Z 1.85, and a 45° ramp from there
  to the arm at Z 2.55 so the PCB pushes the hook aside as it goes down.
  Without the land the catch was a knife edge that only the first,
  drooping layer would hold (final review). Under the part outside the PCB
  (X 30.30…30.70) a 45° chamfer meets the arm, so only 0.7 overhangs.
- Y centred on GP28 (pad 5), 2 wide: Y −22.23…−20.23. The neighbours'
  joints are ≥ 0.75 away: GP29 is free, GP27 (R4) is at −18.69.
- The case is clear: no case surface at X < 38.8 for Y −22.5…−18 between
  the plate and Z 3.35 (probed 2026-10-02 on
  `case_v4_103_usb_serial.stl`). Ring B's flat face (X 30.93) only starts
  at Y ≤ −24.
- Strain: deflection 0.4 (the lip) over a 6.7 arm, 0.8 thick:
  1.5·t·δ/L² ≈ 1.1 %, within PLA's ≈ 1.5 % for a snap fit that is opened
  a few times. The test coupon (below) checks it on the user's printer.

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
| `LIP_OVER` | 0.5 | how far each rigid lip reaches over a PCB edge |
| `LIP_GAP` | 0.1 | lip underside above the PCB top |
| `SER_LIP_L` | 2.0 | tail lip length behind the bump |
| `ZERO_PAD1_Y` / `ZERO_PAD_PITCH` | 2.38 / 2.54 | USB edge → pad 1 centre (so pad 4 ≈ 10.0), pitch |
| `HOOK_T` | 0.8 | snap-hook arm thickness |
| `HOOK_W` | 2.0 | snap-hook width along Y |
| `HOOK_LIP` | 0.4 | how far the snap hook reaches over the PCB edge (= its deflection) |
| `HOOK_GAP` | 0.4 | hook arm → right ledge (also the groove width) |
| `HOOK_GROOVE_DEPTH` | 1.5 | relief groove depth into the 2 mm plate |
| `POCKET_FLOOR_GAP` | 0.8 | tail underside → pocket floor |
| `DAM_GAP` / `DAM_T` | 0.2 / 1.2 | bump → dam, dam thickness |
| `POCKET_KEY_D` | 1.5 | key hole diameter |

## 5. Verification

1. `tests/test_platform.py`, updated:
   - single valid solid, flat underside, extents;
   - the held parts (Zero PCB + shell; breakout shell, bump and tail with
     the new lengths) don't intersect the part;
   - each lip's underside is `LIP_GAP` above its PCB and reaches `LIP_OVER`
     over the PCB edge (the hook `HOOK_LIP`); the hook's groove floor is
     0.5 thick and its arm touches nothing but the floor; the left lip and the hook sit at the pad positions
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
3. **Test coupon** `hook_coupon.stl`: a cut-out of the platform,
   X 0.5…32.5 × Y −31.6…−11 (the whole pedestal, and past the board window, which would otherwise split it), with the Zero's lip and hook, the tail lip
   and the glue pocket, to try with the real parts before printing the
   full platform. Same script, same parameters.

## Not in scope

The case, the pin map, the firmware, the serial breakout and the cable.

## Revision after the first coupon print (2026-10-03)

Feedback from the user on the printed coupon, and what changed. This
replaces the parts of sections 1 and 2 above that it contradicts.

**Zero: lip and hook too thin.**
- Left lip top raised from Z 2.15 to **3.0** (`MID_WALL_TOP_Z`), so the lip
  is 1.55 thick instead of 0.7. The case is clear to Z 12 above the board.
  The middle wall is still 0.83 between the shell and the Zero (limited by
  the 0.93 gap), but only from the ledge top (Z 0.35) up: below that it is
  fused with the left ledge (1.83).
- Snap hook **3.5 wide** (`HOOK_W`, was 2.0), Y −23.73…−20.23, ending with
  the left lip. GP27 (pad 6) limits it in front. Behind it, ring B's curved
  side was probed on the case STL: in front of Y −24.0 it is beyond
  X 32.08, ≥ 0.18 off the arm bent outward (`RING_B_HOOK_Y`). The extra
  width doesn't change the hook's strain, only how hard it grips.

**Plate "fork" spreading/squeezing:** a 4 mm **band** (`BAND_W`) closes the
window's rear end, under the Zero's USB-C shell (0.9 below it). The user
confirmed BOOT/RESET sit further from the USB end, so they stay reachable.

**Breakout seesawed on the dam.** The dam (0.1 under the modelled tail)
lifted the shell off the pedestal, so the real PCB sits lower in the shell
than modelled. The breakout was also hard to insert: tilting the tail's
edge under the tail lip makes the shell's upper corner dig into the middle
wall and its lower corner hit the left wall.
- Removed: the dam, the raised pocket floor, the key holes (no glue under
  the tail or through the plate, per the user), and the **tail lip** (the
  user chose dropping it over sliding the part 5.5 mm in under it).
- Nothing is under or over the tail: the shell on the pedestal alone sets
  the level, and the breakout drops straight in. The left shell wall is now
  0.15 off the shell (`SHELL_WALL_GAP`); the middle wall stays
  line-to-line on the right.
- **Glue from the top only:** behind the tail end (0.2 off) a 1.2 **rib**
  up to Z −0.35 (the plug-in push), then a 2.0 **trough** (floor Z −1.65)
  and a 1.2 back wall. The left pocket wall runs along the whole length,
  and the middle wall continues low (Z −0.35, below the Zero's PCB) as the
  trough's right side. The glue goes over the tail end, the joints and the
  rib into the trough, so on unplugging, the glue hooked behind the rib
  takes the pull.

### Second coupon (2026-10-03)

The breakout fits. Two changes:
- **Left lip broke on first use.** It now covers pads **3–5** (Y −27.31…−20.23,
  7.1 long, was 4.5) and rises to Z **4.0** (2.55 thick, was 1.55). Pad 3 is
  GP2 (right half) / 3V3 (left half), both free in the hand-wired build; in
  the flex build they carry RGB, so set `ZERO_LIP_PADS` to (4, 5) there. It
  still stays ≥ 0.7 off GP1 (pad 2) and GP27 (pad 6). The tall wall now
  starts 0.54 beside the shell's rear, still clear of the shell.
- **Wires at the tail end:** the rib is now level with the tail top
  (Z −0.85, `RIB_TOP_Z`) instead of 0.5 above it, so the wires lie flat
  over it. The trough floor dropped to Z −2.45, keeping a 1.6 deep hook for
  the glue. The left wall, the trough's back wall and its low right side
  stay at Z −0.35 to keep the glue in.
- **Correction:** the part that broke was the **snap hook**, not the left
  lip. It snapped off along a layer: the upright arm bent across the layer
  lines, PLA's weakest direction, despite the nominal 1.1 % strain. The
  lip changes above stay (they cost nothing).
- **New snap hook, a horizontal leaf spring:** a 1.2 thick leaf (X 30.70…31.90)
  stands on the bed in a slot through the plate (0.4 around it). It runs
  from its root in the front-right corner stop (Y −13.27) back to the
  catch (Y −23.43…−20.23, `HOOK_W` 3.2) and is only as tall as the ledges
  (Z 0.35), so it stays below the PCB and away from the right-edge wires.
  The catch's lip, land, ramp and chamfer are unchanged. It flexes outward
  in X, which bends the leaf along its printed lines: 0.4 at the catch over
  8.7 mm ≈ 0.95 % strain. The plate is widened to X 34.0 along the slot,
  so a 1.7 strip closes a frame around it. The catch was narrowed from
  3.5 to 3.2 so the bent leaf stays in front of Y −23.5, where ring B's
  curved side is beyond X 33.19 (probed). The bent end reaches X 32.4,
  0.8 clear.
- The coupon now runs to the plate's front edge (it holds the leaf's root)
  and up to Z 5.0 (it had clipped the 4.0 lip at 3.55).
- **Catch reach 0.7** (`HOOK_LIP`, was 0.4), at the user's request: with
  the board's 0.3 sideways play it still overlaps the PCB by ≥ 0.6. The
  leaf bends 0.7: ≈ 1.7 % strain along the extrusions. The bent end
  reaches X 32.8, 0.4 clear of ring B. The ramp now tops out at Z 2.85, and
  the catch's flat underside overhangs 1.0 (X 29.3…30.3) before the
  chamfer.

### Third coupon (2026-10-03): the hook's catch broke again

The part above the leaf snapped with little pressure. **Root cause (my
error):** the slot left 0.4 outside the catch's column, but the catch must
move 0.7 aside since `HOOK_LIP` went to 0.7. Below the plate top, the
column hit the slot's edge after 0.4, and the board bent the thin
(1.2) column above it across the layers. No test checked the travel.

New hook:
- **Head:** a solid block from the bed to the catch, X 30.70…34.70 (4.0)
  × Y −22.67…−20.23 (`HOOK_W` 2.4). It starts 0.3 in front of ring B's
  front-most point (Y −22.97 = ring centre + Ø10.6/2). In front of that
  the case is clear right of the board to X 38.9 at every height (probed).
  A first try at Y −22.98 touched the ring: the 0.2 sample grid had
  missed the circle's last sliver. Same lip, land, ramp and chamfer.
- **Leaf:** 1.6 thick (`HOOK_T`), X 33.10…34.70, outside the front-right
  corner stop's side arm (0.4 gap). It runs from the head forward to its
  root in the plate at Y −9.27, 11.0 free, up to Z 0.35 (below the PCB).
  Strain 1.5·1.6·0.7/11.0² ≈ 1.4 % along the extrusions.
- **Slot:** through the plate around the head and the leaf, reaching
  `HOOK_LIP` + 0.4 = 1.1 past their outer face (X 35.8). The plate is widened to
  X 37.5 around it (`HOOK_SLOT_M` 1.7). New tests check the full travel and the
  solid head.
- The coupon now reaches Y −4.57 to include the leaf's root.

### Fourth coupon (2026-10-03)

- **Head lengthened toward the front** (`HEAD_FRONT_L` 2.0): the head body
  now runs Y −22.63…−18.23 (4.4) beside the board, 0.7 off its edge and
  so past pad 6 (GP27's joint). The catch over the PCB still ends at
  Y −20.23. The leaf's root moved forward to Y −7.27 (`CORNER_Y1` + 0.3)
  to keep 11.0 free: strain stays ≈ 1.4 %. The plate frame around the slot
  now reaches Y −5.57, still clear of the case.
- **Rib a layer lower:** top at Z −1.05, 0.2 under the tail top
  (`RIB_TOP_Z`). The trough floor follows it to Z −2.65 (1.6 deep).
- **Catch over pads 4 and 5** (user): the catch now runs Y −24.77…−20.23
  (`CATCH_Y0` = pad 4 − 1.0), like the original left lip. Behind the
  head, ring B rises only to Z 0.25 (probed), and the catch's underside
  is at Z ≥ 1.05, so it reaches back over ring B. Only the head's body
  (from the bed up) has to stay in front of the ring (Y ≥ −22.67). A 0.4
  wide 45° wedge under the catch's outer edge (X 30.7…31.1) carries it
  back from the head. It stops 0.5 short of the catch's rear end
  (`CATCH_WEDGE_SHORT`; 0.5 overhang): at full length its lower corner came
  0.13 from ring B with the hook pushed aside. A new test shifts the hook
  outward by its full travel and measures ≥ 0.2 to the case STL's
  triangles.
- **Reverted to one straight head** (user: the stepped head, with its body
  run forward and its catch run back over a wedge, was too complex and
  likely to fail in print). The head and its catch are one block with the
  same profile end to end, Y −22.63…−20.23 (2.4): ring B is behind it,
  GP27 in front. The user chose this over a 4.4 head over pads 5–6, which
  would need R4 moved off GP27. The leaf keeps its root at Y −7.27, so it
  is 13.0 free: ≈ 1.0 % strain. The pushed-aside clearance test against
  the case STL stays.
