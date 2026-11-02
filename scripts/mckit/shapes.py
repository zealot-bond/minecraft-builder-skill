"""Geometric primitives, seeded 2D/3D smooth noise, and spline tubes."""

import math
from .palette import rand01


def _smooth(t):
    return t * t * (3.0 - 2.0 * t)


def _lerp(a, b, t):
    return a + (b - a) * t


def noise2d(x, z, scale=12.0, seed=0):
    """Smooth value noise in `[-1.0, 1.0]`."""
    sx = float(x) / max(1e-6, scale)
    sz = float(z) / max(1e-6, scale)
    ix = math.floor(sx)
    iz = math.floor(sz)
    fx = _smooth(sx - ix)
    fz = _smooth(sz - iz)
    v00 = rand01(ix, 0, iz, seed)
    v10 = rand01(ix + 1, 0, iz, seed)
    v01 = rand01(ix, 0, iz + 1, seed)
    v11 = rand01(ix + 1, 0, iz + 1, seed)
    a = _lerp(v00, v10, fx)
    b = _lerp(v01, v11, fx)
    return _lerp(a, b, fz) * 2.0 - 1.0


def fbm2d(x, z, scale=16.0, octaves=3, seed=0):
    """Multi-octave fractal noise in roughly `[-1.0, 1.0]`."""
    val = 0.0
    amp = 1.0
    norm = 0.0
    sc = float(scale)
    for o in range(octaves):
        val += amp * noise2d(x, z, scale=sc, seed=seed + o * 101)
        norm += amp
        amp *= 0.5
        sc = max(1.5, sc * 0.5)
    return val / max(1e-6, norm)


def noise3d(x, y, z, scale=6.0, seed=0):
    """Smooth 3D value noise in `[-1.0, 1.0]`."""
    sx = float(x) / max(1e-6, scale)
    sy = float(y) / max(1e-6, scale)
    sz = float(z) / max(1e-6, scale)
    ix, iy, iz = math.floor(sx), math.floor(sy), math.floor(sz)
    fx, fy, fz = _smooth(sx - ix), _smooth(sy - iy), _smooth(sz - iz)

    def c(dx, dy, dz):
        return rand01(ix + dx, iy + dy, iz + dz, seed)

    c00 = _lerp(c(0, 0, 0), c(1, 0, 0), fx)
    c10 = _lerp(c(0, 1, 0), c(1, 1, 0), fx)
    c01 = _lerp(c(0, 0, 1), c(1, 0, 1), fx)
    c11 = _lerp(c(0, 1, 1), c(1, 1, 1), fx)
    c0 = _lerp(c00, c10, fy)
    c1 = _lerp(c01, c11, fy)
    return _lerp(c0, c1, fz) * 2.0 - 1.0


def _resolve(block_or_fn, x, y, z):
    return block_or_fn(x, y, z) if callable(block_or_fn) else block_or_fn


def box(canvas, x0, y0, z0, x1, y1, z1, block):
    ax, bx = sorted((int(round(x0)), int(round(x1))))
    ay, by = sorted((int(round(y0)), int(round(y1))))
    az, bz = sorted((int(round(z0)), int(round(z1))))
    for y in range(ay, by + 1):
        for z in range(az, bz + 1):
            for x in range(ax, bx + 1):
                canvas.set(x, y, z, _resolve(block, x, y, z))


def shell(canvas, x0, y0, z0, x1, y1, z1, block):
    ax, bx = sorted((int(round(x0)), int(round(x1))))
    ay, by = sorted((int(round(y0)), int(round(y1))))
    az, bz = sorted((int(round(z0)), int(round(z1))))
    for y in range(ay, by + 1):
        for z in range(az, bz + 1):
            for x in range(ax, bx + 1):
                if x in (ax, bx) or y in (ay, by) or z in (az, bz):
                    canvas.set(x, y, z, _resolve(block, x, y, z))


def disc(canvas, cx, y, cz, r, block, ragged=0.0, seed=0, only_air=False):
    ir = int(math.ceil(r))
    r2 = r * r
    inner2 = max(0.0, r - 1.1) ** 2
    y = int(round(y))
    for dz in range(-ir, ir + 1):
        for dx in range(-ir, ir + 1):
            d2 = dx * dx + dz * dz
            if d2 > r2:
                continue
            x, z = int(round(cx)) + dx, int(round(cz)) + dz
            if ragged and d2 > inner2 and rand01(x, y, z, seed) < ragged:
                continue
            if only_air and canvas.get(x, y, z) != 'air':
                continue
            canvas.set(x, y, z, _resolve(block, x, y, z))


def ring(canvas, cx, y, cz, r_outer, r_inner, block):
    ir = int(math.ceil(r_outer))
    ro2 = r_outer * r_outer
    ri2 = r_inner * r_inner
    y = int(round(y))
    for dz in range(-ir, ir + 1):
        for dx in range(-ir, ir + 1):
            d2 = dx * dx + dz * dz
            if ri2 <= d2 <= ro2:
                x, z = int(round(cx)) + dx, int(round(cz)) + dz
                canvas.set(x, y, z, _resolve(block, x, y, z))


def cylinder(canvas, cx, y0, cz, r, height, block, hollow=False):
    for dy in range(int(round(height))):
        y = int(round(y0)) + dy
        if hollow:
            ring(canvas, cx, y, cz, r, max(0.0, r - 1.05), block)
        else:
            disc(canvas, cx, y, cz, r, block)


def ellipsoid(canvas, cx, cy, cz, rx, ry, rz, block, only_air=False):
    ix, iy, iz = int(math.ceil(rx)), int(math.ceil(ry)), int(math.ceil(rz))
    for dy in range(-iy, iy + 1):
        for dz in range(-iz, iz + 1):
            for dx in range(-ix, ix + 1):
                d = (dx / max(0.5, rx)) ** 2 + (dy / max(0.5, ry)) ** 2 + (dz / max(0.5, rz)) ** 2
                if d <= 1.0:
                    x, y, z = int(round(cx + dx)), int(round(cy + dy)), int(round(cz + dz))
                    if only_air and canvas.get(x, y, z) != 'air':
                        continue
                    canvas.set(x, y, z, _resolve(block, x, y, z))


def blob(canvas, cx, cy, cz, rx, ry, rz, block, warp=0.32, subtract=0.0, seed=0, only_air=False):
    """Noise-warped organic volume (boulders, leaf clusters, cloud tufts)."""
    ix = int(math.ceil(rx * (1.0 + warp) + 1))
    iy = int(math.ceil(ry * (1.0 + warp) + 1))
    iz = int(math.ceil(rz * (1.0 + warp) + 1))
    placed = []
    for dy in range(-iy, iy + 1):
        for dz in range(-iz, iz + 1):
            for dx in range(-ix, ix + 1):
                x, y, z = int(round(cx + dx)), int(round(cy + dy)), int(round(cz + dz))
                n = noise3d(x, y, z, scale=3.2, seed=seed) * warp
                d = math.sqrt(
                    (dx / max(0.6, rx)) ** 2
                    + (dy / max(0.6, ry)) ** 2
                    + (dz / max(0.6, rz)) ** 2
                )
                if d <= 1.0 + n:
                    if subtract > 0.0 and d > 0.45 and rand01(x, y, z, seed + 77) < subtract:
                        continue
                    if only_air and canvas.get(x, y, z) != 'air':
                        continue
                    canvas.set(x, y, z, _resolve(block, x, y, z))
                    placed.append((x, y, z))
    return placed


def bezier_point(pts, t):
    """Evaluate N-point Bézier curve at `t` in `[0, 1]`."""
    work = [tuple(map(float, p)) for p in pts]
    while len(work) > 1:
        work = [
            tuple(_lerp(work[i][k], work[i + 1][k], t) for k in range(len(work[0])))
            for i in range(len(work) - 1)
        ]
    return work[0]


def line3d_points(p0, p1):
    """6-connected / dense step points between two 3D points."""
    x0, y0, z0 = p0
    x1, y1, z1 = p1
    dist = max(abs(x1 - x0), abs(y1 - y0), abs(z1 - z0))
    steps = max(1, int(math.ceil(dist * 2.5)))
    seen = []
    last = None
    for i in range(steps + 1):
        t = i / float(steps)
        p = (
            int(round(_lerp(x0, x1, t))),
            int(round(_lerp(y0, y1, t))),
            int(round(_lerp(z0, z1, t))),
        )
        if p != last:
            seen.append(p)
            last = p
    return seen


def tube(canvas, control_points, r_start, r_end, block):
    """Sweep a tapering sphere along a 3D Bézier spline. Returns spine points."""
    total_len = sum(
        math.dist(control_points[i], control_points[i + 1])
        for i in range(len(control_points) - 1)
    )
    steps = max(8, int(math.ceil(total_len * 3.0)))
    spine = []
    placed = set()
    for i in range(steps + 1):
        t = i / float(steps)
        px, py, pz = bezier_point(control_points, t)
        r = _lerp(r_start, r_end, t)
        ip = (int(round(px)), int(round(py)), int(round(pz)))
        if not spine or spine[-1] != ip:
            spine.append(ip)
        if r <= 0.65:
            if ip not in placed:
                canvas.set(ip[0], ip[1], ip[2], _resolve(block, *ip))
                placed.add(ip)
        else:
            ir = int(math.ceil(r))
            r2 = r * r
            for dy in range(-ir, ir + 1):
                for dz in range(-ir, ir + 1):
                    for dx in range(-ir, ir + 1):
                        if dx * dx + dy * dy + dz * dz <= r2:
                            q = (int(round(px)) + dx, int(round(py)) + dy, int(round(pz)) + dz)
                            if q not in placed:
                                canvas.set(q[0], q[1], q[2], _resolve(block, *q))
                                placed.add(q)
    return spine, placed


def polygon_contains(poly, x, z):
    """Ray-casting point-in-polygon for 2D `(x, z)` tuples."""
    inside = False
    n = len(poly)
    j = n - 1
    for i in range(n):
        xi, zi = poly[i]
        xj, zj = poly[j]
        if ((zi > z) != (zj > z)) and (x < (xj - xi) * (z - zi) / ((zj - zi) or 1e-9) + xi):
            inside = not inside
        j = i
    return inside
