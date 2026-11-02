#!/usr/bin/env python3
"""Read natural ground truth out of live `.mca` region files.

This is what stops a build from hallucinating terrain. Measure the real ground,
then blend to it.

    read_region.py --dir region/ --box 195 259 270 270 --csv ground.csv
    read_region.py --dir region/ --probe 195 394 464 394 330 259      # key columns
    read_region.py --dir region/ --at 300 394                         # one column
    read_region.py --dir region/ --dataversion
    read_region.py --dir region/ --props minecraft:oak_stairs --at 300 73 394

Correctness notes that matter (see references/region-read.md):
  * sections are read in ASCENDING Y with LAST-WRITE-WINS, or "surface" becomes the
    lowest solid block and every median is wrong
  * surface water may lift the ground; underground water must not
  * columns whose "top solid" is implausibly deep (a cave floor) are rejected
"""
import sys, os, gzip, zlib, struct, argparse, collections

SKIP = set('''
air cave_air void_air short_grass tall_grass fern large_fern poppy dandelion
red_tulip orange_tulip white_tulip pink_tulip blue_orchid allium azure_bluet
oxeye_daisy cornflower lily_of_the_valley pink_petals leaf_litter firefly_bush
brown_mushroom red_mushroom dead_bush vine bamboo_sapling sugar_cane snow
torch wall_torch soul_torch lily_pad structure_void
oak_leaves jungle_leaves spruce_leaves birch_leaves azalea_leaves
flowering_azalea_leaves dark_oak_leaves mangrove_leaves cherry_leaves
acacia_leaves pale_oak_leaves
oak_log birch_log spruce_log jungle_log dark_oak_log acacia_log mangrove_log
cherry_log pale_oak_log oak_wood jungle_wood spruce_wood birch_wood
azalea moss_carpet moss_block pale_moss_carpet bamboo player_head skeleton_skull
candle light_blue_candle sea_pickle turtle_egg snow_block powder_snow
big_dripleaf small_dripleaf glow_lichen hanging_roots pointed_dripstone
sweet_berry_bush wheat carrots potatoes beetroots melon pumpkin carved_pumpkin
jack_o_lantern tall_seagrass seagrass kelp bubble_column barrier light
water lava
'''.split())


# --------------------------------------------------------------------- NBT
def read_nbt(raw, i=0):
    t = raw[i]; i += 1
    if t == 0:
        return None, i
    nl = struct.unpack_from('>H', raw, i)[0]; i += 2
    name = raw[i:i + nl].decode('utf-8', 'replace'); i += nl
    v, i = payload(raw, i, t)
    return (name, v), i


def payload(raw, i, t):
    if t == 1: return struct.unpack_from('>b', raw, i)[0], i + 1
    if t == 2: return struct.unpack_from('>h', raw, i)[0], i + 2
    if t == 3: return struct.unpack_from('>i', raw, i)[0], i + 4
    if t == 4: return struct.unpack_from('>q', raw, i)[0], i + 8
    if t == 5: return struct.unpack_from('>f', raw, i)[0], i + 4
    if t == 6: return struct.unpack_from('>d', raw, i)[0], i + 8
    if t == 7:
        n = struct.unpack_from('>i', raw, i)[0]; i += 4
        return raw[i:i + n], i + n
    if t == 8:
        n = struct.unpack_from('>H', raw, i)[0]; i += 2
        return raw[i:i + n].decode('utf-8', 'replace'), i + n
    if t == 9:
        et = raw[i]; n = struct.unpack_from('>i', raw, i + 1)[0]; i += 5
        out = []
        for _ in range(n):
            v, i = payload(raw, i, et); out.append(v)
        return out, i
    if t == 10:
        out = {}
        while True:
            tt = raw[i]; i += 1
            if tt == 0: break
            nl = struct.unpack_from('>H', raw, i)[0]; i += 2
            nm = raw[i:i + nl].decode('utf-8', 'replace'); i += nl
            v, i = payload(raw, i, tt); out[nm] = v
        return out, i
    if t == 11:
        n = struct.unpack_from('>i', raw, i)[0]; i += 4
        return [struct.unpack_from('>i', raw, i + 4 * k)[0] for k in range(n)], i + 4 * n
    if t == 12:
        n = struct.unpack_from('>i', raw, i)[0]; i += 4
        return [struct.unpack_from('>q', raw, i + 8 * k)[0] for k in range(n)], i + 8 * n
    raise ValueError('bad tag %d' % t)


class Region:
    def __init__(self, root):
        self.root = root
        self._rb = {}
        self._ch = {}

    def _bytes(self, rcx, rcz):
        k = (rcx, rcz)
        if k not in self._rb:
            p = os.path.join(self.root, 'r.%d.%d.mca' % (rcx, rcz))
            try:
                self._rb[k] = open(p, 'rb').read()
            except OSError:
                self._rb[k] = None          # r.0.1 may simply not exist yet
        return self._rb[k]

    def chunk(self, cx, cz):
        k = (cx, cz)
        if k in self._ch:
            return self._ch[k]
        raw = self._bytes(cx >> 5, cz >> 5)
        res = None
        if raw:
            loc = struct.unpack_from('>I', raw, 4 * ((cx & 31) + (cz & 31) * 32))[0]
            off = (loc >> 8) * 4096
            if off:
                ln = struct.unpack_from('>I', raw, off)[0]
                comp = raw[off + 4]
                body = raw[off + 5:off + 4 + ln]
                try:
                    if comp == 1:
                        body = gzip.decompress(body)
                    elif comp == 2:
                        body = zlib.decompress(body)
                    else:
                        body = None
                    if body:
                        res = read_nbt(body, 0)[1]
                except Exception:
                    res = None
        self._ch[k] = res
        return res

    def section_tables(self, wx, wz):
        r = self.chunk(wx >> 4, wz >> 4)
        if not r:
            return None
        secs = []
        for sec in r.get('sections', []):
            sy = sec.get('Y')
            bs = sec.get('block_states')
            if sy is None or not bs:
                continue
            pal = [(e.get('Name') if isinstance(e, dict) else e) or 'minecraft:air'
                   for e in bs['palette']]
            secs.append((sy, pal, bs.get('data')))
        secs.sort(key=lambda t: t[0])              # ASCENDING: last write wins
        return secs

    def block(self, wx, wy, wz):
        secs = self.section_tables(wx, wy if False else wz)
        if not secs:
            return None
        sy_want = wy >> 4
        for sy, pal, data in secs:
            if sy != sy_want:
                continue
            bits = max(4, (len(pal) - 1).bit_length())
            per = 64 // bits
            i = ((wy & 15) * 16 + (wz & 15)) * 16 + (wx & 15)
            v = (data[i // per] >> ((i % per) * bits)) & ((1 << bits) - 1) if data else 0
            return (pal[v] if v < len(pal) else 'minecraft:air').split(':')[-1]
        return None

    def surface(self, wx, wz):
        """-> (top solid y, material, water surface y or None)"""
        secs = self.section_tables(wx, wz)
        if not secs:
            return None, None, None
        idx0 = (wz & 15) * 16 + (wx & 15)
        out = wat = None
        for sy, pal, data in secs:
            bits = max(4, (len(pal) - 1).bit_length())
            per = 64 // bits
            mask = (1 << bits) - 1
            base = sy * 16
            for ly in range(15, -1, -1):
                i = ly * 256 + idx0
                v = (data[i // per] >> ((i % per) * bits)) & mask if data else 0
                nm = (pal[v] if v < len(pal) else 'minecraft:air').split(':')[-1]
                if nm in ('water', 'lava'):
                    wat = base + ly            # keep the highest
                    continue
                if nm in SKIP:
                    continue
                out = (base + ly, nm)          # last write wins == highest solid
                break
        if out is None:
            return None, None, wat
        return out[0], out[1], wat


def ground(reg, wx, wz):
    """Plausible natural ground height, with surface water applied."""
    y, mat, w = reg.surface(wx, wz)
    if y is None:
        return None, None, w
    if not (0 <= y <= 200):
        return None, mat, w
    if w is not None and abs(y - w) <= 4:
        y = max(y, w + 2)
    return y, mat, w


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--dir', required=True, help='directory holding r.X.Z.mca')
    ap.add_argument('--box', nargs=4, type=int, metavar=('X0', 'Z0', 'W', 'H'))
    ap.add_argument('--probe', nargs='+', type=int, metavar='XZ')
    ap.add_argument('--at', nargs='+', type=int, metavar='X [Y] Z')
    ap.add_argument('--props')
    ap.add_argument('--dataversion', action='store_true')
    ap.add_argument('--csv')
    ap.add_argument('--side-medians', action='store_true',
                    help='per-side medians for a box (what a blend needs)')
    a = ap.parse_args()

    reg = Region(a.dir)

    if a.dataversion:
        found = None
        for rcx, rcz in ((0, 0), (-1, 0), (0, -1)):
            raw = reg._bytes(rcx, rcz)
            if not raw:
                continue
            for k in range(1024):
                loc = struct.unpack_from('>I', raw, 4 * k)[0]
                off = (loc >> 8) * 4096
                if not off:
                    continue
                ln = struct.unpack_from('>I', raw, off)[0]
                comp = raw[off + 4]
                body = raw[off + 5:off + 4 + ln]
                try:
                    body = gzip.decompress(body) if comp == 1 else zlib.decompress(body)
                    root = read_nbt(body, 0)[1]
                    found = root.get('DataVersion')
                except Exception:
                    pass
                if found:
                    break
            if found:
                break
        print('DataVersion: %s' % found)
        return 0

    if a.at:
        vals = a.at
        if len(vals) == 2:
            wx, wz = vals
            y, mat, w = reg.surface(wx, wz)
            print('(%d,%d) surface y=%s %s  water=%s' % (wx, wz, y, mat, w))
            if a.props:
                yy = (y or 64) + 1
                print('   %s at y%d -> %s' % (a.props, yy,
                                              reg.block(wx, yy, wz)))
        else:
            wx, wy, wz = vals
            print('(%d,%d,%d) = %s' % (wx, wy, wz, reg.block(wx, wy, wz)))
        return 0

    if a.props and a.box:
        x0, z0, w, h = a.box
        seen = collections.Counter()
        for z in range(z0, z0 + h):
            for x in range(x0, x0 + w):
                y, mat, _ = reg.surface(x, z)
                if y is None:
                    continue
                b = reg.block(x, y + 1, z)
                if b == a.props.split(':')[-1]:
                    seen[b] += 1
        print('%s on the surface: %d' % (a.props, sum(seen.values())))
        return 0

    if a.probe:
        pts = a.probe
        for i in range(0, len(pts) - 1, 2):
            wx, wz = pts[i], pts[i + 1]
            y, mat, w = ground(reg, wx, wz)
            print('(%4d,%4d)  ground y=%-5s %-16s water=%s' % (wx, wz, y, mat, w))
        return 0

    if a.box:
        x0, z0, w, h = a.box
        rows = []
        ys = []
        for z in range(z0, z0 + h):
            for x in range(x0, x0 + w):
                y, mat, wl = ground(reg, x, z)
                rows.append((x, z, y, mat or '', wl))
                if y is not None:
                    ys.append(y)
        if a.csv:
            with open(a.csv, 'w') as f:
                f.write('x,z,y,material,water\n')
                for r in rows:
                    f.write('%d,%d,%s,%s,%s\n' % r)
            print('wrote %s (%d columns)' % (a.csv, len(rows)))
        good = sorted(ys)
        if good:
            n = len(good)
            print('columns %d, usable %d' % (len(rows), n))
            print('ground y: min %d p5 %d p25 %d med %d p75 %d p95 %d max %d'
                  % (good[0], good[n // 20], good[n // 4], good[n // 2],
                     good[3 * n // 4], good[19 * n // 20], good[-1]))
        water_cols = sum(1 for r in rows if r[4] is not None)
        print('columns with water: %d' % water_cols)

        if a.side_medians:
            def side_med(pred):
                v = sorted(y for (x, z, y, m, wl) in rows
                           if pred(x - x0, z - z0) and y is not None)
                if not v:
                    return None
                return v[len(v) // 2]
            print()
            print('per-side median ground height (blend targets):')
            print('  NORTH (z near 0)      : %s' % side_med(lambda lx, lz: lz < h // 8))
            print('  SOUTH (z near %d)     : %s' % (h, side_med(lambda lx, lz: lz > h - h // 8)))
            print('  WEST  (x near 0)      : %s' % side_med(lambda lx, lz: lx < w // 8))
            print('  EAST  (x near %d)     : %s' % (w, side_med(lambda lx, lz: lx > w - w // 8)))
        return 0

    print('nothing to do; see --help', file=sys.stderr)
    return 2


if __name__ == '__main__':
    sys.exit(main())
