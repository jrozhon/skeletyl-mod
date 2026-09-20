#!/bin/sh
# Clone the reference sources next to this script (git-ignored).
set -e
cd "$(dirname "$0")"
[ -d splinktegrated ] || git clone --depth 1 https://github.com/Bastardkb/splinktegrated
[ -d Skeletyl ] || git clone --depth 1 https://github.com/Bastardkb/Skeletyl
echo "case STL: $(pwd)/Skeletyl/V4/case_v4_103.stl"
