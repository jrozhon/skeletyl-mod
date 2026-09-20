# Skeletyl hardware

3D-printed parts for a hand-wired Bastardkb Skeletyl (V4 case).

- `rp2040zero_platform/` — platform holding a Waveshare RP2040-Zero and a
  PJ-320A TRRS jack in place of the Splinktegrated PCB. See its README.
- `docs/superpowers/` — design specs and implementation plans.
- `refs/fetch.sh` — clones the Bastardkb reference repos (case STL, PCB) into
  the git-ignored `refs/` folder; needed only for `check_clearance.py`.

Requires FreeCAD ≥ 1.0 (`freecadcmd` on the PATH) and numpy.
