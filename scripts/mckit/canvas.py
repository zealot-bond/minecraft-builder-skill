"""`Canvas`: memory-efficient voxel grid with named parts, theme access,
automatic fence/wall/pane connection, streaming NBT export, and manifest output.
"""

import json
import os
import sys
from array import array
from contextlib import contextmanager

_SCRIPTS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)

import streamnbt
from .blocks import (
    AIR_NAMES,
    CHAINS,
    DEFAULT_DATA_VERSION,
    FLAT_PLANTS,
    FLUID_NAMES,
    HANGING_ONLY,
    NO_SUPPORT,
    SOILS,
    full_name,
    is_fence,
    is_foliage,
    is_leaves,
    is_pane,
    is_solid_full,
    is_wall,
    parse_block_spec,
    short_name,
)
from .themes import get_theme


class Canvas:
    """Voxel build canvas backed by a compact `uint16` palette grid."""

    def __init__(self, sx, sy, sz, theme='sakura', data_version=None, project_config=None):
        self.sx = int(sx)
        self.sy = int(sy)
        self.sz = int(sz)
        self.config = dict(project_config or {})
        env_dv = os.environ.get('MC_DATA_VERSION')
        self.data_version = int(
            data_version
            or self.config.get('data_version')
            or (int(env_dv) if env_dv else DEFAULT_DATA_VERSION)
        )
        self.theme = get_theme(theme) if isinstance(theme, str) else dict(theme)
        self.grid = array('H', bytes(2 * self.sx * self.sy * self.sz))
        self.part_grid = array('H', bytes(2 * self.sx * self.sy * self.sz))
        self._pal = []
        self._pal_ix = {}
        self._parts = ['unassigned']
        self._part_ix = {'unassigned': 0}
        self._part_stack = [0]
        self._explicit_conn = set()  # palette indices where caller explicitly set N/S/E/W
        self.zones = None
        self.spawn = None  # {'pos': [x, y, z], 'facing': [tx, ty, tz]}
        self.landmarks = []  # [{'name': ..., 'pos': [x, y, z]}]
        self.cameras = []    # optional extra named camera shots for render_textured.mjs

        air_id = self.pid('minecraft:air')
        assert air_id == 0, 'palette[0] must be minecraft:air'

    # ------------------------------------------------------------ coordinates
    def in_bounds(self, x, y, z):
        return 0 <= x < self.sx and 0 <= y < self.sy and 0 <= z < self.sz

    def _idx(self, x, y, z):
        return (y * self.sz + z) * self.sx + x

    # ------------------------------------------------------------ palette & parts
    def pid(self, spec, **override_props):
        has_explicit_dirs = any(k in override_props for k in ('north', 'south', 'east', 'west'))
        if isinstance(spec, str) and '[' in spec and any(d in spec for d in ('north=', 'south=', 'east=', 'west=')):
            has_explicit_dirs = True
        nm, props = parse_block_spec(spec, override_props or None, data_version=self.data_version)
        if short_name(nm) in AIR_NAMES:
            nm, props = 'minecraft:air', {}
        key = (nm, tuple(sorted(props.items())))
        idx = self._pal_ix.get(key)
        if idx is None:
            idx = len(self._pal)
            if idx >= 65535:
                raise OverflowError('Palette exceeded uint16 limit (65535 states)')
            self._pal_ix[key] = idx
            self._pal.append(key)
        if has_explicit_dirs:
            self._explicit_conn.add(idx)
        return idx

    @contextmanager
    def part(self, path):
        """Assign all blocks placed inside this `with` block to a named part."""
        p = str(path).strip() or 'unassigned'
        idx = self._part_ix.get(p)
        if idx is None:
            idx = len(self._parts)
            self._part_ix[p] = idx
            self._parts.append(p)
        self._part_stack.append(idx)
        try:
            yield p
        finally:
            self._part_stack.pop()

    def register_landmark(self, name, x, y, z):
        self.landmarks.append({'name': str(name), 'pos': [int(round(x)), int(round(y)), int(round(z))]})

    def add_camera(self, name, position, target, fov=52, lighting='day'):
        self.cameras.append({
            'name': str(name),
            'position': [float(v) for v in position],
            'target': [float(v) for v in target],
            'fov': float(fov),
            'lighting': str(lighting),
        })

    def stamp(self, asset_or_id, x, z, **kwargs):
        from .schem import stamp_asset
        return stamp_asset(self, asset_or_id, x, z, **kwargs)

    def set_spawn(self, x, y, z, look_at=None):
        sp = {'pos': [int(round(x)), int(round(y)), int(round(z))]}
        if look_at is not None:
            sp['look_at'] = [int(round(v)) for v in look_at]
        self.spawn = sp

    # ------------------------------------------------------------ block ops
    def set(self, x, y, z, spec, **override_props):
        x, y, z = int(round(x)), int(round(y)), int(round(z))
        if not self.in_bounds(x, y, z):
            return False
        v = spec if isinstance(spec, int) else self.pid(spec, **override_props)
        i = self._idx(x, y, z)
        self.grid[i] = v
        self.part_grid[i] = 0 if v == 0 else self._part_stack[-1]
        return True

    def set_if_air(self, x, y, z, spec, **override_props):
        x, y, z = int(round(x)), int(round(y)), int(round(z))
        if not self.in_bounds(x, y, z):
            return False
        if self.grid[self._idx(x, y, z)] != 0:
            return False
        return self.set(x, y, z, spec, **override_props)

    def get(self, x, y, z):
        """Return short block name at `(x, y, z)`, or `'air'` if out of bounds."""
        x, y, z = int(round(x)), int(round(y)), int(round(z))
        if not self.in_bounds(x, y, z):
            return 'air'
        v = self.grid[self._idx(x, y, z)]
        return short_name(self._pal[v][0])

    def get_state(self, x, y, z):
        """Return `(short_name, props_dict)` at `(x, y, z)`."""
        x, y, z = int(round(x)), int(round(y)), int(round(z))
        if not self.in_bounds(x, y, z):
            return 'air', {}
        nm, pr = self._pal[self.grid[self._idx(x, y, z)]]
        return short_name(nm), dict(pr)

    def fill(self, x0, y0, z0, x1, y1, z1, spec, **override_props):
        ax, bx = sorted((int(round(x0)), int(round(x1))))
        ay, by = sorted((int(round(y0)), int(round(y1))))
        az, bz = sorted((int(round(z0)), int(round(z1))))
        for y in range(max(0, ay), min(self.sy - 1, by) + 1):
            for z in range(max(0, az), min(self.sz - 1, bz) + 1):
                for x in range(max(0, ax), min(self.sx - 1, bx) + 1):
                    blk = spec(x, y, z) if callable(spec) else spec
                    self.set(x, y, z, blk, **override_props)

    fill_box = fill

    def top(self, x, z, ignore_foliage=False):
        """Highest non-air `y` in column `(x, z)`, or `-1` if column is empty."""
        x, z = int(round(x)), int(round(z))
        if not (0 <= x < self.sx and 0 <= z < self.sz):
            return -1
        for y in range(self.sy - 1, -1, -1):
            v = self.grid[self._idx(x, y, z)]
            if v == 0:
                continue
            b = short_name(self._pal[v][0])
            if ignore_foliage and (is_foliage(b) or b in FLAT_PLANTS or b in NO_SUPPORT):
                continue
            return y
        return -1

    def ground_y(self, x, z):
        """Contiguous terrain/floor top `y` in `(x, z)` (stops before air gaps under
        roofs, bridges, wool canopies, or floating balloons), or `-1`.
        """
        x, z = int(round(x)), int(round(z))
        if not (0 <= x < self.sx and 0 <= z < self.sz):
            return -1
        gy = -1
        in_col = False
        for y in range(self.sy):
            v = self.grid[self._idx(x, y, z)]
            if v == 0:
                if in_col:
                    break
                continue
            b = short_name(self._pal[v][0])
            if is_foliage(b) or b in FLAT_PLANTS or b in NO_SUPPORT or b in FLUID_NAMES:
                if in_col:
                    break
                continue
            if is_fence(b) or is_wall(b) or is_pane(b):
                if in_col:
                    break
                continue
            in_col = True
            gy = y
        return gy

    # ------------------------------------------------------------ cleanup & auto-connect
    def auto_connect(self):
        """Connect fences, walls, and panes to adjacent compatible blocks."""
        dirs = (('north', 0, -1), ('south', 0, 1), ('east', 1, 0), ('west', -1, 0))
        updates = []
        for y in range(self.sy):
            for z in range(self.sz):
                for x in range(self.sx):
                    i = self._idx(x, y, z)
                    v = self.grid[i]
                    if v == 0 or v in self._explicit_conn:
                        continue
                    full_nm, pr_tup = self._pal[v]
                    b = short_name(full_nm)
                    if is_fence(b):
                        pr = dict(pr_tup)
                        nether = (b == 'nether_brick_fence')
                        for dname, dx, dz in dirs:
                            nb = self.get(x + dx, y, z + dz)
                            conn = (
                                (is_fence(nb) and (nb == 'nether_brick_fence') == nether)
                                or nb.endswith('_fence_gate')
                                or is_solid_full(nb)
                            )
                            pr[dname] = 'true' if conn else 'false'
                        updates.append((i, self.pid((full_nm, pr))))
                    elif is_pane(b):
                        pr = dict(pr_tup)
                        for dname, dx, dz in dirs:
                            nb = self.get(x + dx, y, z + dz)
                            conn = (
                                is_pane(nb)
                                or nb == 'glass'
                                or nb.endswith('_stained_glass')
                                or is_solid_full(nb)
                            )
                            pr[dname] = 'true' if conn else 'false'
                        updates.append((i, self.pid((full_nm, pr))))
                    elif is_wall(b):
                        pr = dict(pr_tup)
                        conns = {}
                        for dname, dx, dz in dirs:
                            nb = self.get(x + dx, y, z + dz)
                            conn = is_wall(nb) or is_pane(nb) or nb.endswith('_fence_gate') or is_solid_full(nb)
                            conns[dname] = conn
                            pr[dname] = 'low' if conn else 'none'
                        above = self.get(x, y + 1, z)
                        straight_ns = conns['north'] and conns['south'] and not conns['east'] and not conns['west']
                        straight_ew = conns['east'] and conns['west'] and not conns['north'] and not conns['south']
                        pr['up'] = 'false' if ((straight_ns or straight_ew) and above == 'air') else 'true'
                        updates.append((i, self.pid((full_nm, pr))))
        for i, new_v in updates:
            self.grid[i] = new_v

    def clean_unsupported_plants(self):
        """Remove any flat plants, clipped wall signs/torches, or soil-on-logs after edits."""
        facing_vec = {'north': (0, -1), 'south': (0, 1), 'east': (1, 0), 'west': (-1, 0)}
        removed = 0
        for y in range(self.sy):
            for z in range(self.sz):
                for x in range(self.sx):
                    b, pr = self.get_state(x, y, z)
                    if b == 'air':
                        continue
                    below = self.get(x, y - 1, z)
                    above = self.get(x, y + 1, z)
                    if b == 'tripwire':
                        self.set(x, y, z, 'air'); removed += 1; continue
                    if b in SOILS and is_foliage(below):
                        self.set(x, y, z, 'flowering_azalea_leaves', persistent='true')
                        continue
                    if b in ('lantern', 'soul_lantern'):
                        if pr.get('hanging') == 'true':
                            if above in AIR_NAMES or above in FLUID_NAMES or above in FLAT_PLANTS:
                                self.set(x, y, z, 'air'); removed += 1
                        elif below in NO_SUPPORT:
                            self.set(x, y, z, 'air'); removed += 1
                        continue
                    if b in HANGING_ONLY:
                        if above in AIR_NAMES or above in FLUID_NAMES or above in FLAT_PLANTS:
                            self.set(x, y, z, 'air'); removed += 1
                        continue
                    if (b.endswith(('_wall_banner', '_wall_sign', '_wall_head'))
                            or b in ('player_wall_head', 'wall_torch', 'soul_wall_torch', 'redstone_wall_torch')):
                        dx, dz = facing_vec.get(pr.get('facing', 'north'), (0, -1))
                        bv = self.get(x - dx, y, z - dz)
                        ba = self.get(x + dx, y, z + dz)
                        ok_v = bv not in NO_SUPPORT and not bv.endswith(('banner', 'sign'))
                        ok_a = ba not in NO_SUPPORT and not ba.endswith(('banner', 'sign'))
                        if not (ok_v or ok_a):
                            self.set(x, y, z, 'air'); removed += 1
                        continue
                    if b not in FLAT_PLANTS or b in ('seagrass', 'tall_seagrass', 'kelp', 'kelp_plant', 'sea_pickle'):
                        continue
                    tall_pot_map = {
                        'rose_bush': 'potted_poppy',
                        'peony': 'potted_pink_tulip',
                        'lilac': 'potted_allium',
                        'sunflower': 'potted_dandelion',
                        'large_fern': 'potted_fern',
                    }
                    if b in ('sunflower', 'lilac', 'rose_bush', 'peony', 'tall_grass', 'large_fern', 'pitcher_plant'):
                        if pr.get('half') == 'upper' and below != b:
                            pot = tall_pot_map.get(b)
                            if pot and below not in NO_SUPPORT and not is_foliage(below):
                                self.set(x, y, z, pot)
                            else:
                                self.set(x, y, z, 'air'); removed += 1
                            continue
                        if pr.get('half', 'lower') == 'lower' and above != b:
                            if below in NO_SUPPORT or is_foliage(below):
                                self.set(x, y, z, 'air'); removed += 1
                            else:
                                pot = tall_pot_map.get(b)
                                self.set(x, y, z, pot if pot else 'short_grass')
                            continue
                    if b == 'lily_pad':
                        if below != 'water':
                            self.set(x, y, z, 'air')
                            removed += 1
                    elif b == 'bamboo':
                        if below not in ('bamboo', 'grass_block', 'dirt', 'coarse_dirt', 'podzol',
                                         'rooted_dirt', 'moss_block', 'mud', 'sand', 'gravel', 'mycelium'):
                            self.set(x, y, z, 'air')
                            removed += 1
                    elif b == 'sugar_cane':
                        if below not in ('sugar_cane', 'grass_block', 'dirt', 'coarse_dirt', 'podzol',
                                         'rooted_dirt', 'moss_block', 'mud', 'sand', 'red_sand'):
                            self.set(x, y, z, 'air')
                            removed += 1
                    elif below in NO_SUPPORT or is_foliage(below):
                        self.set(x, y, z, 'air')
                        removed += 1
        return removed

    def clean_floating_foliage(self):
        """Delete any foliage component severed by later architecture carvings."""
        from collections import deque
        n6 = ((1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1))
        fol = set()
        for y in range(self.sy):
            for z in range(self.sz):
                for x in range(self.sx):
                    if is_foliage(self.get(x, y, z)):
                        fol.add((x, y, z))
        seen = set()
        removed = 0
        for p in list(fol):
            if p in seen:
                continue
            q = deque([p]); seen.add(p); comp = []
            while q:
                cx, cy, cz = q.popleft(); comp.append((cx, cy, cz))
                for dx, dy, dz in n6:
                    nb = (cx + dx, cy + dy, cz + dz)
                    if nb in fol and nb not in seen:
                        seen.add(nb); q.append(nb)
            grounded = any(
                any(
                    self.get(x + dx, y + dy, z + dz) not in NO_SUPPORT
                    and not is_foliage(self.get(x + dx, y + dy, z + dz))
                    for dx, dy, dz in n6
                )
                for (x, y, z) in comp
            )
            if not grounded:
                for x, y, z in comp:
                    self.set(x, y, z, 'air')
                    removed += 1
        return removed

    # ------------------------------------------------------------ manifest & export
    def compute_part_stats(self):
        stats = {}
        for y in range(self.sy):
            for z in range(self.sz):
                base = (y * self.sz + z) * self.sx
                for x in range(self.sx):
                    i = base + x
                    v = self.grid[i]
                    if v == 0:
                        continue
                    p_idx = self.part_grid[i]
                    pname = self._parts[p_idx]
                    st = stats.get(pname)
                    if st is None:
                        st = {'name': pname, 'blocks': 1, 'bbox': [x, y, z, x, y, z]}
                        stats[pname] = st
                    else:
                        st['blocks'] += 1
                        bb = st['bbox']
                        if x < bb[0]: bb[0] = x
                        if y < bb[1]: bb[1] = y
                        if z < bb[2]: bb[2] = z
                        if x > bb[3]: bb[3] = x
                        if y > bb[4]: bb[4] = y
                        if z > bb[5]: bb[5] = z
        return [stats[k] for k in sorted(stats)]

    def save(self, nbt_path, auto_connect=True, clean=True, manifest_path=None, schem_path=None):
        """Finalize connections, stream structure `.nbt` (and optional `.schem`), and write `.manifest.json`."""
        if clean:
            self.clean_floating_foliage()
            self.clean_unsupported_plants()
        if auto_connect:
            self.auto_connect()

        os.makedirs(os.path.dirname(os.path.abspath(nbt_path)), exist_ok=True)
        total = sum(1 for v in self.grid if v != 0)
        pal_out = [(nm, dict(pr) if pr else None) for nm, pr in self._pal]

        def emit():
            for y in range(self.sy):
                for z in range(self.sz):
                    base = (y * self.sz + z) * self.sx
                    for x in range(self.sx):
                        v = self.grid[base + x]
                        if v:
                            yield (x, y, z, v)

        nbytes = streamnbt.write_structure(
            nbt_path,
            (self.sx, self.sy, self.sz),
            pal_out,
            total,
            emit(),
            data_version=self.data_version,
        )

        if schem_path:
            from .schem import Asset
            Asset(self.sx, self.sy, self.sz, self._pal, self.grid, data_version=self.data_version).save_schem(schem_path)

        mpath = manifest_path or (os.path.splitext(nbt_path)[0] + '.manifest.json')
        manifest = {
            'size': [self.sx, self.sy, self.sz],
            'data_version': self.data_version,
            'theme': self.theme.get('id', 'custom'),
            'theme_title': self.theme.get('title', 'Custom'),
            'blocks': total,
            'palette_states': len(pal_out),
            'spawn': self.spawn,
            'landmarks': self.landmarks,
            'cameras': self.cameras,
            'parts': self.compute_part_stats(),
            'zones': self.zones.to_manifest() if self.zones else None,
            'config': self.config,
        }
        with open(mpath, 'w', encoding='utf-8') as f:
            json.dump(manifest, f, indent=2)
        return {'nbt': nbt_path, 'schem': schem_path, 'manifest': mpath, 'bytes': nbytes, 'blocks': total}
