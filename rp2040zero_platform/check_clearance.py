"""Check the platform against the Skeletyl V4 case STL.

Usage: python3 check_clearance.py [path/to/case_v4_103.stl]

Samples the case surface inside the platform's bounding box and reports
sample points that fall inside the platform solid. Only points hugging a
case ring (the Ø10.4 bore around the Ø10 ring) are tolerated. Also writes
four cross-section PNGs (platform red, case blue) for eyeballing.
"""
import os
import struct
import sys
import zlib

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import freecad_path  # noqa: F401,E402
import rp2040zero_platform as rp  # noqa: E402

import MeshPart  # noqa: E402
from FreeCAD import Vector  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_CASE = os.path.join(HERE, "..", "refs", "Skeletyl", "V4", "case_v4_103.stl")
SAMPLE_STEP = 0.25     # mm between surface samples
RING_TOL = 0.35        # tolerated radial proximity to a case ring


def load_stl(path):
    d = open(path, 'rb').read()
    n = struct.unpack('<I', d[80:84])[0]
    rec = np.dtype([('n', '<f4', 3), ('v', '<f4', (3, 3)), ('a', '<u2')])
    return np.frombuffer(d[84:84 + n * 50], dtype=rec)['v'].astype(float)


def case_to_platform(tris):
    """(x, y, z)_case -> (x + 94.136, z + 30.599, y)."""
    out = np.empty_like(tris)
    out[..., 0] = tris[..., 0] + 94.136
    out[..., 1] = tris[..., 2] + 30.599
    out[..., 2] = tris[..., 1]
    return out


def sample_surface(tris, step):
    """Points on every triangle on a barycentric grid of spacing <= step."""
    out = []
    for a, b, c in tris:
        longest = max(np.linalg.norm(b - a), np.linalg.norm(c - a), np.linalg.norm(c - b))
        n = max(1, int(np.ceil(longest / step)))
        i, j = np.meshgrid(np.arange(n + 1), np.arange(n + 1), indexing='ij')
        m = (i + j) <= n
        u, v = i[m] / n, j[m] / n
        out.append(a + u[:, None] * (b - a) + v[:, None] * (c - a))
    return np.vstack(out)


def platform_mesh(shape):
    m = MeshPart.meshFromShape(Shape=shape, LinearDeflection=0.02, AngularDeflection=0.1)
    return np.array([[list(p) for p in f.Points] for f in m.Facets])


def section(tris, axis, val, u_axis, v_axis):
    """Polyline segments of the mesh cut by the plane axis=val, as (u, v) pairs."""
    segs = []
    for tri in tris:
        a = tri[:, axis]
        if a.min() > val or a.max() < val:
            continue
        pts = []
        for i in range(3):
            p, q = tri[i], tri[(i + 1) % 3]
            if (p[axis] - val) * (q[axis] - val) <= 0 and p[axis] != q[axis]:
                s = (val - p[axis]) / (q[axis] - p[axis])
                pts.append(p + s * (q - p))
        if len(pts) >= 2:
            segs.append(((pts[0][u_axis], pts[0][v_axis]), (pts[1][u_axis], pts[1][v_axis])))
    return segs


def write_png(fn, layers, lo, hi, res=0.05):
    """layers: list of (segments, rgb). Grid every 1 mm, bold every 5 mm."""
    W = int((hi[0] - lo[0]) / res) + 1
    H = int((hi[1] - lo[1]) / res) + 1
    img = np.full((H, W, 3), 255, np.uint8)
    for g in np.arange(np.ceil(lo[0]), hi[0], 1.0):
        i = int((g - lo[0]) / res)
        img[:, i] = [140, 140, 140] if g % 5 == 0 else [225, 225, 225]
    for g in np.arange(np.ceil(lo[1]), hi[1], 1.0):
        j = int((g - lo[1]) / res)
        img[j, :] = [140, 140, 140] if g % 5 == 0 else [225, 225, 225]
    for segs, rgb in layers:
        for (u0, v0), (u1, v1) in segs:
            n = int(np.hypot(u1 - u0, v1 - v0) / res) + 2
            for k in np.linspace(0, 1, n):
                i = int((u0 + k * (u1 - u0) - lo[0]) / res)
                j = int((v0 + k * (v1 - v0) - lo[1]) / res)
                if 0 <= i < W and 0 <= j < H:
                    img[j, i] = rgb
    img = img[::-1]
    raw = b''.join(b'\x00' + img[i].tobytes() for i in range(H))

    def chunk(t, d):
        return struct.pack('>I', len(d)) + t + d + struct.pack('>I', zlib.crc32(t + d) & 0xffffffff)

    png = (b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('>IIBBBBB', W, H, 8, 2, 0, 0, 0))
           + chunk(b'IDAT', zlib.compress(raw)) + chunk(b'IEND', b''))
    open(fn, 'wb').write(png)


def main(case_path):
    shape = rp.build()
    bb = shape.BoundBox
    case = case_to_platform(load_stl(case_path))
    lo = np.array([bb.XMin, bb.YMin, bb.ZMin]) - 1.0
    hi = np.array([bb.XMax, bb.YMax, bb.ZMax]) + 1.0
    tmin, tmax = case.min(axis=1), case.max(axis=1)
    near = case[(tmax >= lo).all(1) & (tmin <= hi).all(1)]
    print("case triangles near the platform:", len(near))

    pts = sample_surface(near, SAMPLE_STEP)
    pts = pts[((pts >= lo) & (pts <= hi)).all(1)]
    print("sampled case surface points:", len(pts))
    bad = np.array([p for p in pts if shape.isInside(Vector(*p), 1e-6, True)])
    print("case points inside the platform:", len(bad))

    fatal = 0
    if len(bad):
        rings = np.array(rp.RING_CENTRES)
        d = np.min(np.linalg.norm(bad[:, None, :2] - rings[None, :, :], axis=2), axis=1)
        ring_ok = d <= rp.RING_OD / 2 + RING_TOL
        print("  within %.2f mm of a ring (expected, bore clearance): %d" % (rp.RING_OD / 2 + RING_TOL, ring_ok.sum()))
        others = bad[~ring_ok]
        fatal = len(others)
        for p in others[:40]:
            print("  COLLISION at X %.2f Y %.2f Z %.2f" % tuple(p))
        if fatal > 40:
            print("  ... and %d more" % (fatal - 40))

    plat = platform_mesh(shape)
    ax, ay = rp.RING_A
    bx, by = rp.RING_B
    # (file, axis, case plane, platform plane, u, v): Y-Z sections through the
    # rings, the jack axis and the USB centre; plus an X-Z "rear view" that
    # overlays the wall openings (cut inside the wall) with the platform's
    # rearmost features (cut just inside its rear edge).
    views = [
        ("sec_ringA.png", 0, ax, ax, 1, 2),
        ("sec_ringB.png", 0, bx, bx, 1, 2),
        ("sec_jack.png", 0, rp.JACK_AXIS_X, rp.JACK_AXIS_X, 1, 2),
        ("sec_usb.png", 0, rp.BOARD_CX, rp.BOARD_CX, 1, 2),
        ("sec_wall.png", 1, rp.WALL_INNER_Y - 0.5, rp.PLATE_REAR_Y + 0.5, 0, 2),
    ]
    for fn, axis, case_val, plat_val, u, v in views:
        layers = [(section(case, axis, case_val, u, v), (40, 90, 220)),
                  (section(plat, axis, plat_val, u, v), (220, 30, 30))]
        write_png(os.path.join(HERE, fn), layers, lo[[u, v]], hi[[u, v]])
        print("wrote", fn)
    return 1 if fatal else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else DEFAULT_CASE))
