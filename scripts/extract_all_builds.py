#!/usr/bin/env python3
"""Extract and slice `all-builds.zip` into:
1. `assets/` — Hundreds of tight-cropped individual `.nbt` assets (`trees_oak`,
   `trees_assorted`, `houses`, `stalls`, `rocks`) + `assets/catalog.json`.
2. `examples/01..05-*` — Curated full-build reference spawns from `all-builds.zip`
   (both original `.schem` and converted `.nbt` + structural analysis `README.md`).
"""

from array import array
from collections import Counter, deque
import ctypes
import json
import os
import shutil
import sys
import tempfile
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
SKILL_ROOT = os.path.abspath(os.path.join(HERE, '..'))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

from mckit.blocks import AIR_NAMES, is_leaves, is_log, short_name
from mckit.schem import Asset, load_schematic


def _extract_rar(rar_path, dest_dir):
    """Extract `.rar` (including RAR5) via system `libarchive.so.13`."""
    os.makedirs(dest_dir, exist_ok=True)
    la = ctypes.cdll.LoadLibrary('libarchive.so.13')
    la.archive_read_new.restype = ctypes.c_void_p
    la.archive_read_support_filter_all.argtypes = [ctypes.c_void_p]
    la.archive_read_support_format_all.argtypes = [ctypes.c_void_p]
    la.archive_read_open_filename.argtypes = [ctypes.c_void_p, ctypes.c_char_p, ctypes.c_size_t]
    la.archive_read_next_header.argtypes = [ctypes.c_void_p, ctypes.POINTER(ctypes.c_void_p)]
    la.archive_entry_pathname.argtypes = [ctypes.c_void_p]
    la.archive_entry_pathname.restype = ctypes.c_char_p
    la.archive_entry_size.argtypes = [ctypes.c_void_p]
    la.archive_entry_size.restype = ctypes.c_int64
    la.archive_read_data.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_size_t]
    la.archive_read_data.restype = ctypes.c_ssize_t
    la.archive_read_free.argtypes = [ctypes.c_void_p]

    a = la.archive_read_new()
    la.archive_read_support_filter_all(a)
    la.archive_read_support_format_all(a)
    la.archive_read_open_filename(a, rar_path.encode('utf-8'), 65536)
    ent = ctypes.c_void_p()
    extracted = []
    while la.archive_read_next_header(a, ctypes.byref(ent)) == 0:
        name = la.archive_entry_pathname(ent).decode('utf-8', 'replace')
        sz = la.archive_entry_size(ent)
        if sz > 0 and name.lower().endswith('.schem'):
            buf = ctypes.create_string_buffer(sz)
            got = la.archive_read_data(a, buf, sz)
            outp = os.path.join(dest_dir, os.path.basename(name))
            with open(outp, 'wb') as f:
                f.write(buf.raw[:max(0, got)])
            extracted.append(outp)
    la.archive_read_free(a)
    return extracted


def slice_showcase_pack(schem_path, category, prefix, min_y=1, min_blocks=18, pad_merge=1):
    """Slice a showcase grid `.schem` above `min_y` into individual tight-cropped `Asset`s."""
    src = load_schematic(schem_path)
    sx, sy, sz = src.sx, src.sy, src.sz
    grid = src.grid

    # Project non-air voxels for y >= min_y onto 2D (x, z) occupancy mask
    occ = bytearray(sx * sz)
    for y in range(min_y, sy):
        yoff = y * sz * sx
        for i in range(sx * sz):
            if grid[yoff + i] != 0:
                occ[i] = 1

    # Connected components in 2D with Chebyshev radius `pad_merge`
    vis = bytearray(sx * sz)
    comps_bbox = []
    rng = range(-pad_merge, pad_merge + 1)
    for z0 in range(sz):
        for x0 in range(sx):
            idx0 = z0 * sx + x0
            if not occ[idx0] or vis[idx0]:
                continue
            vis[idx0] = 1
            q = deque([(x0, z0)])
            bx0 = bx1 = x0
            bz0 = bz1 = z0
            cols = []
            while q:
                cx, cz = q.popleft()
                cols.append((cx, cz))
                if cx < bx0: bx0 = cx
                if cx > bx1: bx1 = cx
                if cz < bz0: bz0 = cz
                if cz > bz1: bz1 = cz
                for dz in rng:
                    nz = cz + dz
                    if 0 <= nz < sz:
                        zbase = nz * sx
                        for dx in rng:
                            nx = cx + dx
                            if 0 <= nx < sx:
                                ni = zbase + nx
                                if occ[ni] and not vis[ni]:
                                    vis[ni] = 1
                                    q.append((nx, nz))
            comps_bbox.append((bx0, bz0, bx1, bz1, cols))

    # Sort deterministically by grid order (z band then x)
    comps_bbox.sort(key=lambda b: (b[1] // 20, b[0]))

    assets_out = []
    out_dir = os.path.join(SKILL_ROOT, 'assets', category)
    os.makedirs(out_dir, exist_ok=True)

    pal_short = [short_name(nm) for nm, _ in src.palette]
    counter = 0

    for bx0, bz0, bx1, bz1, cols in comps_bbox:
        col_set = set(cols)
        # Find exact vertical [by0, by1] bounds inside col_set
        by0, by1 = sy, -1
        hist = Counter()
        for y in range(min_y, sy):
            yoff = y * sz * sx
            for cx, cz in cols:
                v = grid[yoff + cz * sx + cx]
                if v:
                    if y < by0: by0 = y
                    if y > by1: by1 = y
                    hist[pal_short[v]] += 1

        total = sum(hist.values())
        if total < min_blocks or by1 < by0:
            continue

        # Filter out pack title banners/walls or sponge placeholder masks
        if hist.get('sponge', 0) > total * 0.05:
            continue
        if category.startswith('trees') and hist.get('light_gray_concrete', 0) + hist.get('black_concrete', 0) + hist.get('white_concrete', 0) > total * 0.25:
            continue
        if category.startswith('trees') and not any(is_leaves(k) or is_log(k) for k in hist):
            continue

        csx = bx1 - bx0 + 1
        csy = by1 - by0 + 1
        csz = bz1 - bz0 + 1

        # Compact local palette
        new_pal = [('minecraft:air', ())]
        new_ix = {('minecraft:air', ()): 0}
        sub_grid = array('H', bytes(2 * csx * csy * csz))

        for ly in range(csy):
            sy_i = by0 + ly
            yoff = sy_i * sz * sx
            for cx, cz in col_set:
                v = grid[yoff + cz * sx + cx]
                if v == 0:
                    continue
                entry = src.palette[v]
                nid = new_ix.get(entry)
                if nid is None:
                    nid = len(new_pal)
                    new_ix[entry] = nid
                    new_pal.append(entry)
                lx = cx - bx0
                lz = cz - bz0
                sub_grid[(ly * csz + lz) * csx + lx] = nid

        counter += 1
        aid = f'{prefix}_{counter:02d}'
        asset = Asset(csx, csy, csz, new_pal, sub_grid, name=aid)
        nbt_rel = f'{category}/{aid}.nbt'
        asset.save_nbt(os.path.join(SKILL_ROOT, 'assets', nbt_rel))

        max_span = max(csx, csz, csy)
        if max_span >= 32:
            tier = 'massive'
        elif max_span >= 20:
            tier = 'large'
        elif max_span >= 11:
            tier = 'medium'
        else:
            tier = 'small'

        assets_out.append({
            'id': f'{category}/{aid}',
            'name': aid,
            'category': category,
            'tier': tier,
            'size': [csx, csy, csz],
            'blocks': total,
            'top_blocks': [k for k, _ in hist.most_common(6)],
        })

    return assets_out


def export_full_example(schem_src_path, folder_name, title, description):
    """Copy `.schem`, convert to `.nbt`, and write an analysis `README.md` in `examples/`."""
    ex_dir = os.path.join(SKILL_ROOT, 'examples', folder_name)
    os.makedirs(ex_dir, exist_ok=True)
    slug = folder_name.split('-', 1)[1]
    schem_dst = os.path.join(ex_dir, f'{slug}.schem')
    nbt_dst = os.path.join(ex_dir, f'{slug}.nbt')
    shutil.copy2(schem_src_path, schem_dst)

    asset = load_schematic(schem_src_path)
    info = asset.save_nbt(nbt_dst)

    # Compute top 12 materials for reference study
    pal_short = [short_name(nm) for nm, _ in asset.palette]
    hist = Counter()
    for v in asset.grid:
        if v:
            hist[pal_short[v]] += 1

    top_rows = '\n'.join(
        f'| `{blk}` | {cnt:,} | {cnt * 100.0 / max(1, info["blocks"]):.1f}% |'
        for blk, cnt in hist.most_common(12)
    )
    readme = f"""# {title}

{description}

## Build Specifications
- **Dimensions:** `{asset.sx} x {asset.sy} x {asset.sz}` (`Width x Height x Length`)
- **Non-Air Blocks:** `{info['blocks']:,}`
- **Unique Blockstates:** `{len(asset.palette):,}`
- **Files:** `{slug}.schem` (WorldEdit/FAWE) · `{slug}.nbt` (Vanilla Structure / `mckit` / `render_textured.mjs`)

## Dominant Palette Breakdown
| Block | Count | Share |
|---|---:|---:|
{top_rows}

## Inspect & Render Commands
```bash
python3 ../../scripts/nbt_query.py {slug}.nbt --summary --top 25
node ../../scripts/render_textured.mjs {slug}.nbt --shots hero,top,night --outdir renders/
```
"""
    with open(os.path.join(ex_dir, 'README.md'), 'w', encoding='utf-8') as f:
        f.write(readme)
    return {'folder': folder_name, 'size': [asset.sx, asset.sy, asset.sz], 'blocks': info['blocks']}


def main():
    zip_path = os.path.expanduser('~/Downloads/all-builds.zip')
    if not os.path.exists(zip_path):
        raise SystemExit(f'Missing {zip_path}')

    with tempfile.TemporaryDirectory() as tmp:
        print(f'Extracting {zip_path}...')
        with zipfile.ZipFile(zip_path) as zf:
            zf.extractall(tmp)

        # Extract relevant nested .zip and .rar packs
        def unzip_nested(name_sub):
            for fn in os.listdir(tmp):
                if name_sub.lower() in fn.lower() and fn.endswith('.zip'):
                    out = os.path.join(tmp, '_unz_' + os.path.splitext(fn)[0])
                    with zipfile.ZipFile(os.path.join(tmp, fn)) as nz:
                        nz.extractall(out)
                    return out
            return None

        stalls_dir = unzip_nested('Asset pack - Stalls')
        econ_dir = unzip_nested('Ecomomy SMP Spawn')
        redk_dir = unzip_nested('RedKingdom-Spawn')
        trad_dir = unzip_nested('TradingPost')

        rar_dir = os.path.join(tmp, '_rars')
        for rname in ("60 Oak Tree's Pack.rar", "[BoutiqueBuilds] 40AssortedTreesPack.rar", "MAPA HOUSE PACK.rar"):
            rp = os.path.join(tmp, rname)
            if os.path.exists(rp):
                _extract_rar(rp, rar_dir)

        # Clean & rebuild assets/
        assets_dir = os.path.join(SKILL_ROOT, 'assets')
        if os.path.exists(assets_dir):
            shutil.rmtree(assets_dir)
        os.makedirs(assets_dir, exist_ok=True)

        catalog = {'categories': {}, 'assets': []}

        packs = [
            (os.path.join(rar_dir, '60_oak_tree_pack.schem'), 'trees_oak', 'oak', 1, 25, 1),
            (os.path.join(rar_dir, '[SCHEMATIC] 40AssortedTreesPack.schem'), 'trees_assorted', 'tree', 2, 45, 2),
            (os.path.join(rar_dir, 'HousePackassets.schem'), 'houses', 'house', 2, 120, 1),
            (os.path.join(stalls_dir, 'Assets - stalls', '1.21.8', 'valturystallfreepack.schem'), 'stalls', 'stall', 1, 20, 1),
            (os.path.join(tmp, '10_free_rock.schem'), 'rocks', 'rock', 1, 25, 1),
        ]

        for spath, cat, pref, min_y, min_blk, pad in packs:
            items = slice_showcase_pack(spath, cat, pref, min_y=min_y, min_blocks=min_blk, pad_merge=pad)
            catalog['categories'][cat] = {
                'count': len(items),
                'tiers': dict(Counter(it['tier'] for it in items)),
            }
            catalog['assets'].extend(items)
            print(f'  Sliced {cat:16s}: {len(items):3d} assets  tiers={catalog["categories"][cat]["tiers"]}')

        with open(os.path.join(assets_dir, 'catalog.json'), 'w', encoding='utf-8') as f:
            json.dump(catalog, f, indent=2)

        # Export curated full builds from all-builds.zip into examples/01..05
        full_builds = [
            (
                os.path.join(econ_dir, 'Spawn', 'economy_smp_spawn.schem'),
                '01-economy-smp-spawn',
                'Example 01 — Economy SMP Spawn (`78x81x78`)',
                'Compact medieval/fantasy Economy SMP hub from `all-builds.zip` featuring an elevated central plaza, steep timber-and-stone towers, custom trees, and market stalls.',
            ),
            (
                os.path.join(tmp, 'Japanese_Spring.schem'),
                '02-japanese-spring-spawn',
                'Example 02 — Japanese Spring Sanctuary (`100x58x100`)',
                '100x100 Japanese spring sanctuary from `all-builds.zip` showcasing traditional curved roofs, blossom trees, lantern paths, and sculpted terrain.',
            ),
            (
                os.path.join(tmp, 'survival_spawn.schem'),
                '03-survival-spawn',
                'Example 03 — Survival Woodland Spawn (`133x106x151`)',
                'Full-scale survival spawn build from `all-builds.zip` blending organic cliffs, custom conifers/oaks, pathways, and rustic timber architecture.',
            ),
            (
                os.path.join(redk_dir, 'RedKingdom-Spawn26.3.schem'),
                '04-red-kingdom-spawn',
                'Example 04 — Red Kingdom Citadel Spawn (`190x179x190`)',
                'Grand 190x190 crimson-and-stone castle kingdom spawn from `all-builds.zip` (DataVersion 5023 / 26.3) demonstrating monumental fortress massing and courtyard hierarchy.',
            ),
            (
                os.path.join(trad_dir, 'TradingPost', 'TradingPost.schem'),
                '05-trading-post',
                'Example 05 — Harbor & Highland Trading Post (`317x176x249`)',
                'Expansive multi-building trading settlement from `all-builds.zip` demonstrating multi-house village clustering, docks, cranes, and terrain terracing.',
            ),
        ]

        print('Exporting full-build examples into examples/01..05...')
        for src_p, folder, title, desc in full_builds:
            meta = export_full_example(src_p, folder, title, desc)
            print(f'  Exported {meta["folder"]:28s} size={meta["size"]} blocks={meta["blocks"]:,}')


if __name__ == '__main__':
    main()
