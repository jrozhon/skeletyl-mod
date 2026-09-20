"""Import this before FreeCAD so the system python finds FreeCAD's modules.

Arch installs FreeCAD's python modules under /usr/lib/freecad/lib; when the
script runs inside freecadcmd/FreeCAD itself the import already works and
this is a no-op.
"""
import sys

FREECAD_LIB = "/usr/lib/freecad/lib"

if FREECAD_LIB not in sys.path:
    sys.path.append(FREECAD_LIB)
