# Skeletyl hardware

3D-printed parts and wiring for Bastardkb Skeletyls (V4 case) on an
RP2040-Zero: one hand-wired, one on the original flex PCBs.

- `rp2040zero_platform/` — platform holding a Waveshare RP2040-Zero and a
  USB-C serial breakout in place of the Splinktegrated PCB, plus the case
  modification for the USB-C link. See its README.
- `WIRING.md` — matrix and RP2040-Zero pinout, shared by the hand-wired and
  the flex-PCB builds.
- `docs/superpowers/` — design specs and implementation plans.
- `refs/fetch.sh` — clones the Bastardkb reference repos (case STL, PCBs) into
  the git-ignored `refs/` folder; needed only for `check_clearance.py`.

Requires FreeCAD ≥ 1.0 (`freecadcmd` on the PATH) and numpy.
