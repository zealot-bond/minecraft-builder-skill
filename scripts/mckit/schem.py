"""Universal Schematic (`.schem` Sponge v2/v3 & `.nbt` Structure) loader, exporter,
asset catalog lookup, rotation engine, and terrain-aware `stamp_asset` for `mckit`.
"""

from array import array
from collections import Counter
import gzip
import json
import os
import struct
import sys

_SCRIPTS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)

import streamnbt
from validate import read_nbt
from .blocks import (
    AIR_NAMES,
    DEFAULT_DATA_VERSION,
    FLAT_PLANTS,
    FLUID_NAMES,
    HANGING_ONLY,
    NO_SUPPORT,
    is_foliage,
    is_leaves,
    is_log,
    is_solid_full,
    parse_block_spec,
    short_name,
)

ASSETS_ROOT = os.path.abspath(os.path.join(_SCRIPTS_DIR, '..', 'assets'))

_CARDINAL_CW = {'north': 'east', 'east': 'south', 'south': 'west', 'west': 'north'}


def _decode_varints(data, expected):
    out = array('H')
    i = 0
    n = len(data)
    append = out.append
    while i < n and len(out) < expected:
        val = 0
        shift = 0
        while True:
            b = data[i]
            i += 1
            val |= (b & 0x7F) << shift
            if not (b & 0x80):
                break
            shift += 7
        append(val)
    return out


def _encode_varints(values):
    buf = bytearray()
    append = buf.append
    for v in values:
        while v > 0x7F:
            append((v & 0x7F) | 0x80)
            v >>= 7
        append(v & 0x7F)
    return bytes(buf)


def rotate_props(props, turns=0):
    """Rotate blockstate properties clockwise around +Y by `turns` (0..3) * 90 deg."""
    turns = turns % 4
    if turns == 0 or not props:
        return dict(props)
    p = dict(props)
    for _ in range(turns):
        np = dict(p)
        if 'facing' in p and p['facing'] in _CARDINAL_CW:
            np['facing'] = _CARDINAL_CW[p['facing']]
        if 'axis' in p:
            if p['axis'] == 'x':
                np['axis'] = 'z'
            elif p['axis'] == 'z':
                np['axis'] = 'x'
        if any(d in p for d in ('north', 'east', 'south', 'west')):
            for src, dst in _CARDINAL_CW.items():
                if src in p:
                    np[dst] = p[src]
        if 'rotation' in p and p['rotation'].isdigit():
            np['rotation'] = str((int(p['rotation']) + 4) % 16)
        # Straight rail shapes
        if 'shape' in p:
            sh = p['shape']
            rail_map = {
                'north_south': 'east_west',
                'east_west': 'north_south',
                'ascending_north': 'ascending_east',
                'ascending_east': 'ascending_south',
                'ascending_south': 'ascending_west',
                'ascending_west': 'ascending_north',
                'south_east': 'south_west',
                'south_west': 'north_west',
                'north_west': 'north_east',
                'north_east': 'south_east',
            }
            if sh in rail_map:
                np['shape'] = rail_map[sh]
        p = np
    return p


class Asset:
    """Compact in-memory 3D schematic (`sx, sy, sz`, `uint16` `grid`, `palette`)."""

    def __init__(self, sx, sy, sz, palette, grid, name='asset', data_version=DEFAULT_DATA_VERSION):
        self.sx = int(sx)
        self.sy = int(sy)
        self.sz = int(sz)
        self.palette = list(palette)  # list of (full_name, sorted_props_tuple)
        self.grid = grid              # array('H') indexed (y * sz + z) * sx + x
        self.name = name
        self.data_version = int(data_version)

    def idx(self, x, y, z):
        return (y * self.sz + z) * self.sx + x

    @property
    def non_air_blocks(self):
        return sum(1 for v in self.grid if v != 0)

    @property
    def count(self):
        return self.non_air_blocks

    def iter_blocks(self):
        """Yield `(x, y, z, short_block_name, props_dict)` for all non-air blocks."""
        sx, sy, sz = self.sx, self.sy, self.sz
        grid = self.grid
        pal = self.palette
        i = 0
        for y in range(sy):
            for z in range(sz):
                for x in range(sx):
                    v = grid[i]
                    i += 1
                    if v:
                        nm, pr = pal[v]
                        yield (x, y, z, short_name(nm), dict(pr))

    def save_nbt(self, path):
        os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
        pal_out = [(nm, dict(pr) if pr else None) for nm, pr in self.palette]
        total = self.non_air_blocks
        sx, sy, sz = self.sx, self.sy, self.sz
        grid = self.grid

        def emit():
            i = 0
            for y in range(sy):
                for z in range(sz):
                    for x in range(sx):
                        v = grid[i]
                        i += 1
                        if v:
                            yield (x, y, z, v)

        nbytes = streamnbt.write_structure(
            path, (sx, sy, sz), pal_out, total, emit(), data_version=self.data_version
        )
        return {'path': path, 'blocks': total, 'bytes': nbytes, 'size': [sx, sy, sz]}

    def save_schem(self, path):
        """Export Sponge Schematic v2 `.schem` (universally loadable by WorldEdit/FAWE)."""
        os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
        pal_strings = []
        for nm, pr in self.palette:
            if pr:
                kv = ','.join('%s=%s' % (k, v) for k, v in pr)
                pal_strings.append('%s[%s]' % (nm, kv))
            else:
                pal_strings.append(nm)

        raw_varints = _encode_varints(self.grid)
        buf = bytearray()

        def w_tag_hdr(tag_type, name):
            nb = name.encode('utf-8')
            buf.append(tag_type)
            buf.extend(struct.pack('>H', len(nb)))
            buf.extend(nb)

        def w_int(name, val):
            w_tag_hdr(3, name)
            buf.extend(struct.pack('>i', int(val)))

        def w_short(name, val):
            w_tag_hdr(2, name)
            buf.extend(struct.pack('>h', int(val) if val < 32768 else int(val) - 65536))

        # Root compound named "Schematic"
        w_tag_hdr(10, 'Schematic')
        w_int('Version', 2)
        w_int('DataVersion', self.data_version)
        w_short('Width', self.sx)
        w_short('Height', self.sy)
        w_short('Length', self.sz)
        w_int('PaletteMax', len(pal_strings))

        # Palette compound
        w_tag_hdr(10, 'Palette')
        for idx, state_str in enumerate(pal_strings):
            w_int(state_str, idx)
        buf.append(0)  # END Palette

        # BlockData byte array
        w_tag_hdr(7, 'BlockData')
        buf.extend(struct.pack('>i', len(raw_varints)))
        buf.extend(raw_varints)

        buf.append(0)  # END Schematic
        with gzip.open(path, 'wb', compresslevel=6) as f:
            f.write(buf)
        return {'path': path, 'bytes': os.path.getsize(path), 'size': [self.sx, self.sy, self.sz]}


def load_schematic(path, data_version=DEFAULT_DATA_VERSION):
    """Load either a Sponge `.schem` (v2/v3) or Vanilla Structure `.nbt` into an `Asset`."""
    with open(path, 'rb') as f:
        raw = f.read()
    if raw[:2] == b'\x1f\x8b':
        raw = gzip.decompress(raw)
    (_, root), _ = read_nbt(raw, 0)
    name = os.path.splitext(os.path.basename(path))[0]

    # Case 1: Vanilla Structure `.nbt` (`size`, `palette`, `blocks`)
    if 'size' in root and 'palette' in root and 'blocks' in root:
        sx, sy, sz = (int(v) for v in root['size'])
        pal = []
        remap = {}
        # Ensure palette[0] == minecraft:air
        pal.append(('minecraft:air', ()))
        pal_ix = {('minecraft:air', ()): 0}
        for old_i, entry in enumerate(root['palette']):
            nm_raw = entry['Name'] if isinstance(entry, dict) else str(entry)
            pr_raw = dict(entry.get('Properties', {})) if isinstance(entry, dict) else {}
            nm, pr = parse_block_spec((nm_raw, pr_raw), data_version=data_version)
            if short_name(nm) in AIR_NAMES:
                remap[old_i] = 0
                continue
            key = (nm, tuple(sorted(pr.items())))
            if key not in pal_ix:
                pal_ix[key] = len(pal)
                pal.append(key)
            remap[old_i] = pal_ix[key]

        grid = array('H', bytes(2 * sx * sy * sz))
        for b in root['blocks']:
            x, y, z = b['pos']
            if 0 <= x < sx and 0 <= y < sy and 0 <= z < sz:
                nid = remap.get(b['state'], 0)
                if nid:
                    grid[(y * sz + z) * sx + x] = nid
        return Asset(sx, sy, sz, pal, grid, name=name, data_version=data_version)

    # Case 2: Sponge `.schem` v2 or v3
    sch = root.get('Schematic', root)
    sx = sch['Width'] & 0xFFFF
    sy = sch['Height'] & 0xFFFF
    sz = sch['Length'] & 0xFFFF
    if 'Blocks' in sch and isinstance(sch['Blocks'], dict):
        raw_pal = sch['Blocks']['Palette']
        bdata = sch['Blocks']['Data']
    else:
        raw_pal = sch['Palette']
        bdata = sch['BlockData']
    if isinstance(bdata, list):
        bdata = bytes(b & 0xFF for b in bdata)

    pal = [('minecraft:air', ())]
    pal_ix = {('minecraft:air', ()): 0}
    remap_arr = [0] * (max(raw_pal.values(), default=0) + 1)
    for state_str, old_id in raw_pal.items():
        nm, pr = parse_block_spec(state_str, data_version=data_version)
        sn = short_name(nm)
        if sn in AIR_NAMES or sn == 'structure_void' or sn == 'barrier' or sn == 'light':
            remap_arr[old_id] = 0
            continue
        if is_leaves(sn):
            pr['persistent'] = 'true'
        key = (nm, tuple(sorted(pr.items())))
        if key not in pal_ix:
            pal_ix[key] = len(pal)
            pal.append(key)
        remap_arr[old_id] = pal_ix[key]

    decoded = _decode_varints(bdata, sx * sy * sz)
    grid = array('H', (remap_arr[v] if v < len(remap_arr) else 0 for v in decoded))
    if len(grid) < sx * sy * sz:
        grid.extend([0] * (sx * sy * sz - len(grid)))
    return Asset(sx, sy, sz, pal, grid, name=name, data_version=data_version)


_ASSET_CACHE = {}
_CATALOG_CACHE = None


def load_catalog(assets_root=None):
    """Load `assets/catalog.json` indexing all extracted trees, houses, stalls, and rocks."""
    global _CATALOG_CACHE
    root = assets_root or ASSETS_ROOT
    cpath = os.path.join(root, 'catalog.json')
    if _CATALOG_CACHE is not None and assets_root is None:
        return _CATALOG_CACHE
    if not os.path.exists(cpath):
        return {}
    with open(cpath, 'r', encoding='utf-8') as f:
        data = json.load(f)
    if assets_root is None:
        _CATALOG_CACHE = data
    return data


def get_asset(spec, name=None, assets_root=None):
    """Resolve an `Asset` by file path or catalog ID (`'stalls/stall_01'` or `('stalls', 'stall_01')`)."""
    if isinstance(spec, Asset):
        return spec
    if name is not None and '/' not in str(spec) and not os.path.exists(str(spec)):
        spec = '%s/%s' % (spec, name)
    root = assets_root or ASSETS_ROOT
    if os.path.exists(spec):
        path = os.path.abspath(spec)
    else:
        cand = os.path.join(root, spec if spec.endswith(('.nbt', '.schem')) else spec + '.nbt')
        if os.path.exists(cand):
            path = cand
        else:
            raise FileNotFoundError('Asset not found: %s' % spec)
    if path not in _ASSET_CACHE:
        _ASSET_CACHE[path] = load_schematic(path)
    return _ASSET_CACHE[path]


def _find_base_anchor(asset, mode='center'):
    """Compute `(ax, az)` anchor in asset local coords."""
    if mode == 'origin':
        return 0, 0
    if mode == 'trunk':
        # Find centroid of lowest wood/solid column for organic trees
        pts = []
        for y in range(min(5, asset.sy)):
            for z in range(asset.sz):
                for x in range(asset.sx):
                    v = asset.grid[asset.idx(x, y, z)]
                    if v:
                        sn = short_name(asset.palette[v][0])
                        if is_log(sn) or sn in ('dirt', 'coarse_dirt', 'rooted_dirt', 'podzol', 'moss_block', 'stone'):
                            pts.append((x, z))
            if pts:
                break
        if pts:
            return (
                int(round(sum(p[0] for p in pts) / len(pts))),
                int(round(sum(p[1] for p in pts) / len(pts))),
            )
    return asset.sx // 2, asset.sz // 2


def stamp_asset(
    canvas,
    asset_or_id,
    x,
    z,
    y=None,
    rotate=0,
    anchor='center',
    sink=0,
    ground_fill=None,
    max_foundation=8,
    skip_blocks=None,
    part_name=None,
):
    """Stamp a `.nbt` / `.schem` asset onto `canvas` at `(x, z)` with rotation & terrain grounding.

    - `rotate`: `0`, `90`, `180`, or `270` degrees clockwise (rotates stairs/doors/logs/fences!).
    - `anchor`: `'center'`, `'trunk'` (ideal for trees), or `'origin'`.
    - `y`: explicit base `y`, or `None` to sample `canvas.ground_y` under the anchor + 1 - `sink`.
    - `ground_fill`: block spec (e.g. `'stone_bricks'`, `'cobblestone'`, `'oak_wood'`) to extend
      underneath solid `dy=0` blocks so buildings/rocks/roots never float over sloped ground.
    """
    asset = get_asset(asset_or_id)
    turns = (int(rotate) // 90) % 4 if abs(int(rotate)) >= 4 else (int(rotate) % 4)
    ax, az = _find_base_anchor(asset, mode=anchor)

    def rot_xz(lx, lz):
        dx, dz = lx - ax, lz - az
        if turns == 1:
            return -dz, dx
        if turns == 2:
            return -dx, -dz
        if turns == 3:
            return dz, -dx
        return dx, dz

    if y is None:
        # Sample median ground height near anchor
        samples = []
        for sdz in range(-1, 2):
            for sdx in range(-1, 2):
                gy = canvas.ground_y(x + sdx, z + sdz)
                if gy >= 1:
                    samples.append(gy)
        if not samples:
            return {'placed': 0, 'occupied': set()}
        samples.sort()
        base_y = samples[len(samples) // 2] + 1 - int(sink)
    else:
        base_y = int(y) - int(sink)

    # Pre-map asset palette -> canvas palette IDs (with rotation & survival safety applied!)
    is_tree_asset = asset.name.startswith(('oak_', 'tree_'))
    skip_set = set(skip_blocks or ()) | {'sponge', 'barrier', 'structure_void', 'light', 'nether_sprouts'}
    pal_map = [0] * len(asset.palette)
    pal_short = ['air'] * len(asset.palette)
    for pid_i, (nm, pr_tup) in enumerate(asset.palette):
        if pid_i == 0:
            continue
        sn = short_name(nm)
        if sn in skip_set or sn in AIR_NAMES:
            continue
        rpr = rotate_props(dict(pr_tup), turns)
        # Convert gravity concrete_powder in custom assets to wool so blocks never fall in survival
        if sn.endswith('_concrete_powder'):
            sn = sn.replace('_concrete_powder', '_wool')
            nm = 'minecraft:' + sn
            rpr = {}
        # Convert canopy moss_block inside custom trees to flowering_azalea_leaves so soil_on_logs=0
        if is_tree_asset and sn in ('moss_block', 'grass_block', 'green_concrete'):
            sn = 'flowering_azalea_leaves'
            nm = 'minecraft:flowering_azalea_leaves'
            rpr = {'persistent': 'true', 'distance': '7', 'waterlogged': 'false'}
        if is_leaves(sn):
            rpr['persistent'] = 'true'
        pal_map[pid_i] = canvas.pid((nm, rpr))
        pal_short[pid_i] = sn

    placed = 0
    occupied = set()
    pname = part_name or ('Assets/' + asset.name)
    sx, sy, sz = asset.sx, asset.sy, asset.sz
    grid = asset.grid

    with canvas.part(pname):
        # Pass 1: Stamp all non-air blocks
        i = 0
        for ly in range(sy):
            wy = base_y + ly
            if wy < 0 or wy >= canvas.sy:
                i += sx * sz
                continue
            for lz in range(sz):
                for lx in range(sx):
                    v = grid[i]
                    i += 1
                    if v == 0:
                        continue
                    cv = pal_map[v]
                    if cv == 0:
                        continue
                    rx, rz = rot_xz(lx, lz)
                    wx, wz = int(x + rx), int(z + rz)
                    if not (0 <= wx < canvas.sx and 0 <= wz < canvas.sz):
                        continue
                    sn = pal_short[v]
                    # Don't overwrite solid architecture with outer tree leaves
                    if is_leaves(sn) and canvas.get(wx, wy, wz) not in ('air', 'short_grass', 'fern', 'tall_grass') and not is_foliage(canvas.get(wx, wy, wz)):
                        continue
                    canvas.set(wx, wy, wz, cv)
                    occupied.add((wx, wz))
                    placed += 1

        # Pass 2: Ground bottom layer (`ly == 0`) so nothing floats on sloped hills
        for lz in range(sz):
            for lx in range(sx):
                v = grid[lx + lz * sx]
                if v == 0 or pal_map[v] == 0:
                    continue
                sn = pal_short[v]
                if sn in FLAT_PLANTS or sn in HANGING_ONLY or sn in NO_SUPPORT or is_leaves(sn):
                    continue
                rx, rz = rot_xz(lx, lz)
                wx, wz = int(x + rx), int(z + rz)
                if not (0 <= wx < canvas.sx and 0 <= wz < canvas.sz):
                    continue
                fill_blk = ground_fill
                if fill_blk is None:
                    if is_log(sn):
                        fill_blk = sn
                    elif is_solid_full(sn):
                        fill_blk = sn
                    else:
                        continue
                for fy in range(base_y - 1, max(0, base_y - max_foundation) - 1, -1):
                    cur = canvas.get(wx, fy, wz)
                    if cur not in ('air', 'water', 'short_grass', 'fern', 'tall_grass', 'pink_petals', 'moss_carpet') and not is_leaves(cur):
                        break
                    canvas.set(wx, fy, wz, fill_blk)

    return {'placed': placed, 'occupied': occupied, 'base_y': base_y}
