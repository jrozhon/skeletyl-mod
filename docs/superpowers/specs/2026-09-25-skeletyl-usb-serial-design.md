# Skeletyl RP2040-Zero platform — USB-C serial link (rev. 3)

Date: 2026-09-25. Branch `usb-serial`. Builds on rev. 2
(`2026-09-20-skeletyl-rp2040zero-platform-design.md`); its coordinate frame
and "Case interface" table still apply unless changed here.

## Goal

Replace the PJ-320A TRRS jack with a small **mid-mount USB-C receptacle on a
breakout PCB** for the half-to-half serial link, and strip the platform down
to the fewest features that still position both parts for hot glue.

The breakout: shell 8.94 × 3.2 mm, PCB ≈ 9 wide, ≤ 0.8 thick, passing
through the shell at mid-height; 14 mm overall, of which ≈ 9 mm is shell
and ≈ 5 mm bare PCB tail behind it with pads U (VBUS), D+, D−, G.

The case's Ø5.2 jack hole cannot pass a USB-C shell, so the case is modified
too and reprinted.

Deliverables:

1. `rp2040zero_platform/case_usb_serial.py` → `case_v4_103_usb_serial.stl`
   (the V4 case with the jack hole replaced by a USB-C slot).
2. The simplified platform (`rp2040zero_platform.py`, STEP/STL as before).

## New measurements (case_v4_103.stl, platform frame)

| Feature | Value |
| --- | --- |
| Rear-left corner lump (behind the wall) | case material up to **X 1.60** for Y −34…−32 at Z ≥ −1.5; up to X −0.40 below Z −1.5; X 0.05 at Y −31.5 |
| Wall inner (recessed) face | Y −34.10 for X ≥ 2 (except the jack hole X 2.5…7.7) |
| RP2040 frame, nearest part | left ledge X 11.70…12.90 (top Z 0.35); left rail X 10.20…11.70 (removed in rev. 3) |

## 1. Case modification

- **Fill** the old jack hole: a Ø6.6 cylinder on the hole axis (X 5.10,
  Z −1.60) spanning the wall, Y −35.92…−34.10. Ø6.6 covers the ≈Ø6.4
  chamfered mouth; the outer end stays 0.15 mm inside the outer face so the
  fill never stands proud: the face curves into the corner and is at Y −35.95
  at the plug's left edge, X 1.8 (measured by ray-casting; checked by a test).
- **Cut** the new slot, same shape as the RP2040 slot: 9.82 × 3.62,
  full-radius ends, straight along Y through the wall (cutter Y −37.5…−33.5).
  Centre **X 6.60, Z −1.25** → X 1.69…11.51, Z −3.06…0.56. It clears the
  corner lump (1.60) and leaves a 4.58 mm web to the RP2040 slot (16.09).
  The fill is needed because a Ø5.2 hole does not fit inside a 3.62 tall
  slot — crescents would stay open above and below.
- **Method:** STL → FreeCAD mesh → `Part` shape (sewn, solid) → fuse fill,
  cut slot → mesh → STL, written in the case's own coordinates (the inverse
  of the platform transform) so it prints and mirrors exactly like the
  original. Fallback if the boolean on the 55k-facet mesh is unusably slow or
  invalid: `case_v4_v99.step`, only after checking it matches the STL in the
  rear-wall region.

## 2. Platform (simplified)

Removed: jack pocket, leg slots, jack ribs and end stop; the RP2040 rails
and front stop (the left rail would collide with the new shell).

Kept unchanged: plate outline (same numbers: X −4.6…31.8, Y −31.6…−8.47,
ring pads, left-wall clip), window, the two ledges.

Changed: the screw seats. The kit screws have conical (countersunk) heads, so
the flat counterbores did nothing; each seat is now a 90° countersink 1.2 mm
deep (Ø6.9 at the underside → the Ø4.5 hole, 0.8 mm straight above). A
full-depth seat (2.05 mm) does not fit the 2 mm plate; the head hangs at most
1.3 mm below the plate, 0.95 mm clear of the bottom plate.

New: **pedestal** under the USB-C shell.

- Shell centred in the new slot: X 2.13…11.07, Z −2.85…0.35 (0.21 mm each
  way vertically, 0.44 sideways), front face Y −35.07 (1 mm behind the outer
  face), rear Y −26.07; PCB tail to Y −21.07.
- Pedestal X 2.13…11.07 × Y −31.6 (plate rear edge)…−26.07, Z −3.75 → −2.85
  (0.9 mm), clipped by the plate's left-wall outline. The shell front
  2.5 mm overhangs the plate edge into the wall recess.
- Clearances: shell → corner lump 0.53 mm, shell → left ledge 0.63 mm.
- Fixing: the slot holds the front, the pedestal sets the height at the
  back, hot glue shell → pedestal. The PCB tail is free (any thickness ≤ 0.8
  works) so wires can be soldered to the pads before or after.

**Serial stops** (added with the user): the datasheet gives 14.6 mm overall
and a 9.8 mm wide PCB (tail 5.6 mm, PCB X 1.70…11.50, end at Y −20.47). Stops
0.2 mm behind the PCB end, 2.5 mm thick, up to 0.5 mm above the PCB top
(Z −0.35, below the RP2040): an L at the left corner (side arm 3 mm) and a
straight arm on the right that runs into the RP2040's left ledge, which is
the right side guide (0.2 mm off the PCB). The middle stays open for wires.

After the first print (2026-09-26) both parts moved sideways too easily:
the breakout's side guides are now 0.1 mm off each PCB side
(`SER_SIDE_GAP`; the right stop became an L too, its side arm fused to the
ledge), and the right stop rises to the corner stops' height (Z 1.85) and
reaches to 0.1 mm off the RP2040's left edge (`BOARD_SIDE_GAP`), at
Y −20.27…−17.77 (13.5…16 mm from the board's USB edge).

Parameters: `SER_W`, `SER_H`, `SER_SHELL_L`, `SER_L`, `SER_PCB_W`,
`SER_PCB_T`, `SER_CENTER_X`, `SER_RECESS`; the new slot position lives in
one place shared by both scripts.

Board: unchanged position (components down, USB-C in the original slot,
long edges on the ledges); glued along the ledges.

**Corner stops** (added after review with the user): an L at each front
corner of the board, 2.5 mm thick, 0.2 mm off the PCB edges, from the bed to
0.5 mm above the PCB top (Z 1.85). The front arm reaches 2.5 mm in from the
side edge and takes the push of a cable being plugged in; the side arm runs
3 mm back and locates the board sideways. Each L stands on its own footing,
so the outline grows by up to 0.9 mm at those corners (below the rings the
case is free to X 45).

## Print

Platform: underside on the bed, no supports; tallest feature now the ledges
(Z 0.35 → 6.1 mm above the bed). Case: as the original.

## Verification

1. `tests/test_platform.py`: single valid solid; flat underside; extents;
   held components (RP2040 PCB + shell, breakout shell + PCB) do not
   intersect the part; no jack/rail/stop features left; pedestal top at the
   shell underside; shell centred in the new slot; clearances to the corner
   lump and the left ledge; screw seats, window, ledges unchanged.
2. `tests/test_case_usb_serial.py`: output is one valid closed solid; points
   in the old hole outside the slot are now solid; the slot interior is
   empty through the whole wall; points away from the rear wall and the case
   bounding box are unchanged.
3. `check_clearance.py` runs against the modified case: no samples inside
   the platform except on the Z −3.75 contact plane; section PNGs through
   both slots, including an XZ rear view showing both shells in their slots.
