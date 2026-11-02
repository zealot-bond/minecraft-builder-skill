"""Dependency-light orthographic voxel renderer (Pillow only) with ambient occlusion."""
import sys, gzip, struct, math
from PIL import Image, ImageDraw


def read_struct(path):
    raw = gzip.open(path, 'rb').read(); i = 0
    def rd(f):
        nonlocal i; v = struct.unpack_from(f, raw, i); i += struct.calcsize(f); return v[0]
    def rstr():
        nonlocal i; n = struct.unpack_from('>H', raw, i)[0]; i += 2
        s = raw[i:i + n].decode('utf-8', 'replace'); i += n; return s
    def parse(t):
        nonlocal i
        if t == 1: return rd('>b')
        if t == 2: return rd('>h')
        if t == 3: return rd('>i')
        if t == 4: return rd('>q')
        if t == 5: return rd('>f')
        if t == 6: return rd('>d')
        if t == 7: n = rd('>i'); v = raw[i:i + n]; i += n; return v
        if t == 8: return rstr()
        if t == 9:
            et = rd('>B'); n = rd('>i'); return [parse(et) for _ in range(n)]
        if t == 10:
            d = {}
            while True:
                tt = rd('>B')
                if tt == 0: return d
                k = rstr(); d[k] = parse(tt)
        if t == 11: n = rd('>i'); return [rd('>i') for _ in range(n)]
        if t == 12: n = rd('>i'); return [rd('>q') for _ in range(n)]
        raise ValueError(t)
    t = rd('>B'); rstr(); return parse(t)


PAL = {
    'red_concrete': (180, 36, 36), 'blue_stained_glass': (48, 96, 214), 'water': (56, 128, 224),
    'grass_block': (106, 164, 74), 'short_grass': (126, 178, 84), 'grass': (126, 178, 84),
    'fern': (92, 148, 70), 'tall_grass': (126, 178, 84), 'dirt': (134, 96, 67),
    'rooted_dirt': (124, 88, 62), 'coarse_dirt': (118, 84, 58), 'podzol': (112, 82, 50),
    'mud': (62, 58, 64), 'clay': (158, 164, 176), 'sand': (226, 214, 166),
    'terracotta': (152, 94, 72), 'polished_granite': (160, 110, 95),
    'stone': (136, 136, 138), 'andesite': (132, 132, 134), 'tuff': (108, 112, 104),
    'calcite': (228, 228, 224), 'deepslate': (76, 76, 84), 'deepslate_tiles': (58, 58, 66),
    'deepslate_bricks': (68, 68, 76), 'polished_deepslate': (74, 74, 82),
    'polished_andesite': (138, 138, 140), 'quartz_block': (238, 232, 224),
    'smooth_quartz': (240, 236, 230), 'dark_prismarine': (54, 108, 98),
    'prismarine': (98, 168, 158), 'sea_lantern': (210, 238, 232),
    'dirt_path': (158, 128, 84), 'warped_planks': (44, 140, 132), 'warped_hyphae': (56, 98, 110),
    'jungle_leaves': (56, 126, 42), 'oak_leaves': (64, 132, 48), 'spruce_leaves': (48, 92, 54),
    'birch_leaves': (118, 152, 78), 'dark_oak_leaves': (46, 108, 38),
    'cherry_leaves': (242, 168, 198), 'azalea_leaves': (94, 142, 62),
    'flowering_azalea_leaves': (176, 122, 156), 'mangrove_leaves': (78, 136, 52),
    'cherry_wood': (68, 42, 52), 'cherry_log': (68, 42, 52),
    'cherry_planks': (228, 174, 172), 'cherry_slab': (228, 174, 172), 'cherry_stairs': (228, 174, 172),
    'mangrove_wood': (108, 46, 42), 'mangrove_planks': (138, 58, 50), 'mangrove_slab': (138, 58, 50),
    'dark_oak_wood': (68, 50, 34), 'dark_oak_planks': (74, 52, 34),
    'spruce_wood': (92, 68, 42), 'spruce_planks': (126, 96, 58), 'spruce_slab': (126, 96, 58),
    'oak_wood': (126, 98, 60), 'oak_planks': (168, 134, 84),
    'bamboo': (124, 168, 66), 'bamboo_planks': (204, 184, 98),
    'pink_petals': (244, 176, 208), 'lily_pad': (46, 128, 52), 'sugar_cane': (146, 190, 92),
    'campfire': (242, 148, 58), 'soul_campfire': (84, 212, 224),
    'lantern': (252, 224, 140), 'soul_lantern': (112, 224, 236), 'end_rod': (245, 240, 235),
    'chain': (92, 96, 104), 'iron_chain': (92, 96, 104),
    'pearlescent_froglight': (244, 214, 236), 'ochre_froglight': (246, 228, 168),
    'verdant_froglight': (196, 242, 198), 'amethyst_block': (138, 98, 188),
    'cyan_stained_glass': (76, 186, 208), 'pink_stained_glass': (240, 168, 202),
    'white_concrete': (226, 228, 232), 'gray_concrete': (64, 68, 74), 'cyan_terracotta': (86, 92, 92),
    'pink_wool': (238, 148, 182), 'white_wool': (236, 236, 238), 'magenta_wool': (190, 78, 178),
    'cyan_wool': (36, 148, 162), 'red_wool': (172, 44, 42),
}


def col(nm):
    n = nm.replace('minecraft:', '')
    if n in PAL:
        return PAL[n]
    for k in ('cherry', 'mangrove', 'dark_oak', 'spruce', 'birch', 'oak', 'bamboo', 'warped', 'crimson'):
        if n.startswith(k):
            base = {
                'cherry': (226, 170, 170), 'mangrove': (136, 56, 48), 'dark_oak': (72, 52, 34),
                'spruce': (124, 94, 56), 'birch': (208, 192, 138), 'oak': (164, 130, 80),
                'bamboo': (198, 178, 94), 'warped': (46, 136, 128), 'crimson': (126, 52, 76),
            }[k]
            return base
    if 'deepslate' in n: return (68, 68, 76)
    if 'quartz' in n: return (236, 232, 226)
    if 'prismarine' in n: return (64, 128, 118)
    if 'leaves' in n: return (62, 132, 48)
    if 'glass' in n: return (140, 196, 224)
    if 'stone' in n or 'cobble' in n or 'andesite' in n: return (130, 132, 134)
    if 'dirt' in n: return (126, 90, 62)
    h = (abs(hash(n)) * 2654435761) & 0xFFFFFF
    return (96 + (h & 63), 96 + ((h >> 8) & 63), 96 + ((h >> 16) & 63))


def load(path):
    r = read_struct(path); sx, sy, sz = r['size']; pal = r['palette']
    g = {}
    for b in r['blocks']:
        p = pal[b['state']]['Name']
        if not p.endswith(('air', 'cave_air', 'void_air')):
            g[(b['pos'][0], b['pos'][1], b['pos'][2])] = p
    return sx, sy, sz, g


FACE = {'px': (1, 0, 0), 'nx': (-1, 0, 0), 'py': (0, 1, 0), 'ny': (0, -1, 0), 'pz': (0, 0, 1), 'nz': (0, 0, -1)}
SHADE = {'py': 1.02, 'ny': 0.42, 'px': 0.80, 'nx': 0.62, 'pz': 0.90, 'nz': 0.56}


def corners(x, y, z, d):
    if d == 'py': return [(x, y + 1, z), (x + 1, y + 1, z), (x + 1, y + 1, z + 1), (x, y + 1, z + 1)]
    if d == 'ny': return [(x, y, z), (x, y, z + 1), (x + 1, y, z + 1), (x + 1, y, z)]
    if d == 'px': return [(x + 1, y, z), (x + 1, y, z + 1), (x + 1, y + 1, z + 1), (x + 1, y + 1, z)]
    if d == 'nx': return [(x, y, z + 1), (x, y, z), (x, y + 1, z), (x, y + 1, z + 1)]
    if d == 'pz': return [(x, y, z + 1), (x + 1, y, z + 1), (x + 1, y + 1, z + 1), (x, y + 1, z + 1)]
    return [(x + 1, y, z), (x, y, z), (x, y + 1, z), (x, y + 1, z)]


def render(g, size, out, cam=(1.0, 0.72, 1.0), W=1100, scale=None, bg=(18, 22, 30)):
    sx, sy, sz = size
    cx, cy, cz = sx / 2.0, sy / 2.0, sz / 2.0
    vx, vy, vz = cam
    L = math.sqrt(vx * vx + vy * vy + vz * vz); vx, vy, vz = vx / L, vy / L, vz / L
    rx, ry, rz = -vz, 0.0, vx
    rl = max(1e-9, math.sqrt(rx * rx + rz * rz)); rx, rz = rx / rl, rz / rl
    ux = ry * vz - rz * vy
    uy = rz * vx - rx * vz
    uz = rx * vy - ry * vx
    ul = max(1e-9, math.sqrt(ux * ux + uy * uy + uz * uz)); ux, uy, uz = ux / ul, uy / ul, uz / ul

    pts = []
    for (x, y, z), nm in g.items():
        for d, (dx, dy, dz) in FACE.items():
            # Back-face cull relative to camera direction for 2x speedup
            if dx * vx + dy * vy + dz * vz <= -0.05:
                continue
            if (x + dx, y + dy, z + dz) in g:
                continue
            # Simple ambient occlusion: darken top faces tucked beside taller neighbours
            ao = 1.0
            if d == 'py':
                occ = sum(1 for ox, oz in ((1, 0), (-1, 0), (0, 1), (0, -1)) if (x + ox, y + 1, z + oz) in g)
                ao = 1.0 - occ * 0.065
            pts.append((x, y, z, d, nm, ao))

    if not pts:
        img = Image.new('RGB', (W, W), bg)
        img.save(out)
        return img.size, 0

    def depth(p):
        x, y, z, _, _, _ = p
        return (x + 0.5 - cx) * vx + (y + 0.5 - cy) * vy + (z + 0.5 - cz) * vz

    pts.sort(key=depth)
    proj = []
    for x, y, z, d, nm, ao in pts:
        q = []
        for (a, b, c) in corners(x, y, z, d):
            a -= cx; b -= cy; c -= cz
            q.append((a * rx + b * ry + c * rz, a * ux + b * uy + c * uz))
        proj.append((q, d, nm, ao))

    us = [p[0] for f in proj for p in f[0]]
    vs = [p[1] for f in proj for p in f[0]]
    minu, maxu = min(us), max(us)
    minv, maxv = min(vs), max(vs)
    if scale is None:
        scale = (W - 40) / max(maxu - minu, 1e-9)
    H = max(60, int((maxv - minv) * scale) + 40)
    img = Image.new('RGB', (W, H), bg); dr = ImageDraw.Draw(img)
    ox = 20 - minu * scale; oy = H - 20 + minv * scale
    for q, d, nm, ao in proj:
        s = SHADE[d] * ao
        c = col(nm)
        poly = [(p[0] * scale + ox, -p[1] * scale + oy) for p in q]
        fill = (min(255, int(c[0] * s)), min(255, int(c[1] * s)), min(255, int(c[2] * s)))
        dr.polygon(poly, fill=fill)
    img.save(out)
    return img.size, len(proj)


VIEWS = {
    'iso':    (1.00, 0.72, 1.00),
    'top':    (0.00, 1.00, 0.001),
    'low':    (1.00, 0.24, 0.45),
    'west':   (-1.00, 0.52, 0.55),
    'east':   (1.00, 0.38, 0.30),
    'corner': (-1.00, 0.50, -1.00),
}


if __name__ == '__main__':
    if len(sys.argv) > 2 and sys.argv[2].startswith('--'):
        import argparse, os
        ap = argparse.ArgumentParser()
        ap.add_argument('nbt')
        ap.add_argument('--views', default='iso,top')
        ap.add_argument('--outdir', default='renders')
        ap.add_argument('--width', type=int, default=1100)
        ap.add_argument('--prefix', default=None)
        a = ap.parse_args()
        os.makedirs(a.outdir, exist_ok=True)
        sx, sy, szk, g = load(a.nbt)
        base = a.prefix or os.path.splitext(os.path.basename(a.nbt))[0]
        want = [v.strip() for v in a.views.split(',') if v.strip()]
        for v in want:
            cam = VIEWS.get(v)
            if cam is None:
                print('unknown view %r (have %s)' % (v, ','.join(VIEWS)))
                continue
            out = os.path.join(a.outdir, '%s-%s.png' % (base, v))
            render(g, (sx, sy, szk), out, cam=cam, W=a.width)
            print('%-8s -> %s' % (v, out))
    else:
        src = sys.argv[1]; out = sys.argv[2]
        W = int(sys.argv[3]) if len(sys.argv) > 3 else 1100
        cx = float(sys.argv[4]) if len(sys.argv) > 4 else 1.0
        cy = float(sys.argv[5]) if len(sys.argv) > 5 else 0.72
        cz = float(sys.argv[6]) if len(sys.argv) > 6 else 1.0
        sx, sy, sz, g = load(src)
        sz2, faces = render(g, (sx, sy, sz), out, cam=(cx, cy, cz), W=W)
        print(f'{src}: {sx}x{sy}x{sz}, {len(g)} blocks, {faces} visible faces -> {out} {sz2}')
