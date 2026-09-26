#!/bin/sh
# Clone the reference sources next to this script (git-ignored).
set -e
cd "$(dirname "$0")"
[ -d splinktegrated ] || git clone --depth 1 https://github.com/Bastardkb/splinktegrated
[ -d Skeletyl ] || git clone --depth 1 https://github.com/Bastardkb/Skeletyl
[ -d Skeletyl-PCB-plate ] || git clone --depth 1 https://github.com/Bastardkb/Skeletyl-PCB-plate
[ -d TBK-Mini-PCB-thumb-cluster ] || git clone --depth 1 https://github.com/Bastardkb/TBK-Mini-PCB-thumb-cluster
echo "case STL: $(pwd)/Skeletyl/V4/case_v4_103.stl"
