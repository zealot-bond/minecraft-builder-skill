#!/usr/bin/env python3
"""Anti-emptiness & aesthetic quality gate for Minecraft spawns and hubs.

Where `validate.py` asks "is anything broken?", `quality.py` asks "is this build
actually rich, composed, themed, lit, and free of empty flat slabs?".

An empty 50x50 flat plaza passes `validate.py` and FAILS `quality.py`.

Usage:
    python3 scripts/quality.py out.nbt [--manifest out.manifest.json]
                               [--heatmap renders/quality-heatmap.png]
                               [--theme sakura]
"""

import argparse
from collections import Counter
import json
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mckit.blocks import (
    AIR_NAMES,
    FLAT_PLANTS,
    FLUID_NAMES,
    LIGHT_SOURCES,
    NO_SUPPORT,
    is_fence,
    is_foliage,
    is_pane,
    is_wall,
    short_name,
)
from mckit.palette import theme_allowed_blocks
from mckit.themes import get_theme
from mckit.zones import ZoneGrid
from validate import load_nbt


DEFAULT_THRESHOLDS = {
    'min_footprint_ratio': 0.62,
    'min_relief_std': 0.90,
    'min_hero_prominence': 8,
    'min_mean_density': 0.65,
    'min_cell_density': 0.25,
    'min_cell_variety': 3.5,
    'max_dominant_surface': 0.55,
    'min_named_parts': 8,
    'max_unassigned_ratio': 0.10,
    'max_cols_per_light': 64.0,
    'min_palette_coherence': 0.88,
}


TERRAIN_BASE_BLOCKS = frozenset({
    'grass_block', 'dirt', 'coarse_dirt', 'rooted_dirt', 'podzol', 'moss_block',
    'mycelium', 'farmland', 'mud', 'clay', 'sand', 'red_sand', 'gravel', 'dirt_path',
    'stone', 'andesite', 'granite', 'diorite', 'tuff', 'calcite', 'deepslate',
    'cobbled_deepslate', 'polished_deepslate', 'cobblestone', 'mossy_cobblestone',
    'black_concrete', 'gray_concrete', 'light_gray_concrete', 'cyan_terracotta',
    'yellow_terracotta', 'terracotta', 'obsidian', 'crying_obsidian',
})


def compute_metrics(nbt_path, manifest=None, theme_override=None):
    root, _ = load_nbt(nbt_path)
    sx, sy, sz = tuple(root['size'])
    pal = [short_name(e.get('Name') if isinstance(e, dict) else e) for e in root['palette']]

    # Build column stacks
    cols = [[[] for _ in range(sx)] for _ in range(sz)]
    block_counts = Counter()
    light_count = 0
    total_blocks = 0

    for b in root['blocks']:
        x, y, z = b['pos']
        if not (0 <= x < sx and 0 <= y < sy and 0 <= z < sz):
            continue
        nm = pal[b['state']]
        if nm in AIR_NAMES:
            continue
        cols[z][x].append((y, nm))
        block_counts[nm] += 1
        total_blocks += 1
        if nm in LIGHT_SOURCES:
            light_count += 1

    # Per-column ground height, peak height, surface material, and above-ground detail count
    ground_y = [[None for _ in range(sx)] for _ in range(sz)]
    peak_y = [[None for _ in range(sx)] for _ in range(sz)]
    surf_block = [[None for _ in range(sx)] for _ in range(sz)]
    detail_above = [[0 for _ in range(sx)] for _ in range(sz)]

    active_cols = 0
    ground_heights = []
    surface_counter = Counter()

    for z in range(sz):
        for x in range(sx):
            stack = cols[z][x]
            if not stack:
                continue
            active_cols += 1
            stack.sort(key=lambda t: t[0])
            peak_y[z][x] = stack[-1][0]

            # Walk bottom-up along the contiguous natural terrain base so roofs,
            # arches, bridges, tents & stalls count as architectural detail above ground!
            gy = stack[0][0]
            sblk = stack[0][1]
            prev_y = stack[0][0]
            for idx_s, (y, nm) in enumerate(stack):
                if idx_s > 0 and y > prev_y + 1:
                    break  # hit an air gap (under arch, bridge, tent, pavilion roof, tree)
                if nm in TERRAIN_BASE_BLOCKS:
                    gy = y
                    sblk = nm
                    prev_y = y
                elif idx_s == 0:
                    gy = y
                    sblk = nm
                    prev_y = y
                else:
                    break

            has_water = any(nm in FLUID_NAMES for _, nm in stack)
            if has_water:
                sblk = 'water'
            ground_y[z][x] = gy
            ground_heights.append(gy)

            # Visible non-foliage top material (paths, roofs, water, flora, grass)
            vis = sblk
            for y, nm in reversed(stack):
                if not is_foliage(nm):
                    vis = nm
                    break
            surf_block[z][x] = vis
            surface_counter[vis] += 1

            # Count all architectural, water, prop, tree & flora blocks above terrain base
            det = sum(1 for y, nm in stack if y > gy or nm in FLUID_NAMES)
            detail_above[z][x] = det

    # Terrain relief & hero landmark prominence
    if ground_heights:
        sorted_g = sorted(ground_heights)
        median_g = sorted_g[len(sorted_g) // 2]
        mean_g = sum(ground_heights) / float(len(ground_heights))
        relief_std = math.sqrt(sum((h - mean_g) ** 2 for h in ground_heights) / float(len(ground_heights)))
    else:
        median_g, relief_std = 0, 0.0

    all_peaks = [peak_y[z][x] for z in range(sz) for x in range(sx) if peak_y[z][x] is not None]
    max_peak = max(all_peaks) if all_peaks else 0
    hero_prominence = max_peak - median_g

    # Zone cells evaluation
    if manifest and manifest.get('zones'):
        zdata = manifest['zones']
        zgrid = ZoneGrid(sx, sz, ascii_map='\n'.join(zdata['ascii']), legend=zdata.get('legend'))
    else:
        zgrid = ZoneGrid(sx, sz)

    cell_reports = []
    for cx, cz, code, role, (x0, z0, x1, z1) in zgrid.iter_cells():
        c_active = 0
        c_det = 0
        c_types = set()
        is_rim = cx in (0, zgrid.gx - 1) and cz in (0, zgrid.gz - 1)
        for z in range(z0, z1 + 1):
            for x in range(x0, x1 + 1):
                if ground_y[z][x] is not None:
                    c_active += 1
                    c_det += detail_above[z][x]
                    c_types.add(surf_block[z][x])
        area = (x1 - x0 + 1) * (z1 - z0 + 1)
        # Normalize density over active columns (if cell has substantial land)
        denom = max(1, c_active)
        density = c_det / float(denom) if c_active >= area * 0.25 else 0.0
        cell_reports.append({
            'cx': cx, 'cz': cz, 'code': code, 'role': role,
            'bounds': [x0, z0, x1, z1],
            'active_cols': c_active, 'area': area,
            'is_corner_rim': is_rim,
            'density': round(density, 2),
            'variety': len(c_types),
        })

    # Interior / active cells (ignore tiny clipped island corner slivers < 35% land)
    judged_cells = [c for c in cell_reports if c['active_cols'] >= c['area'] * 0.35]
    mean_density = (sum(c['density'] for c in judged_cells) / len(judged_cells)) if judged_cells else 0.0
    mean_variety = (sum(c['variety'] for c in judged_cells) / len(judged_cells)) if judged_cells else 0.0

    dominant_blk, dominant_cnt = surface_counter.most_common(1)[0] if surface_counter else ('none', 0)
    dominant_share = dominant_cnt / float(max(1, active_cols))

    # Theme coherence
    theme_id = theme_override or (manifest.get('theme') if manifest else None)
    coherence = None
    off_theme = []
    if theme_id and theme_id != 'custom':
        try:
            t_obj = get_theme(theme_id)
            allowed = theme_allowed_blocks(t_obj)
            in_cnt = sum(cnt for blk, cnt in block_counts.items() if blk in allowed)
            coherence = in_cnt / float(max(1, total_blocks))
            off_theme = [blk for blk, _ in block_counts.most_common() if blk not in allowed][:6]
        except KeyError:
            coherence = None

    return {
        'size': (sx, sy, sz),
        'total_blocks': total_blocks,
        'active_cols': active_cols,
        'footprint_ratio': active_cols / float(max(1, sx * sz)),
        'relief_std': relief_std,
        'median_ground': median_g,
        'max_peak': max_peak,
        'hero_prominence': hero_prominence,
        'mean_density': mean_density,
        'mean_variety': mean_variety,
        'dominant_block': dominant_blk,
        'dominant_share': dominant_share,
        'light_count': light_count,
        'cols_per_light': active_cols / float(max(1, light_count)) if light_count else 9999.0,
        'coherence': coherence,
        'off_theme': off_theme,
        'cells': cell_reports,
        'judged_cells': judged_cells,
        'zgrid': zgrid,
    }


def write_heatmap(metrics, manifest, out_path, min_cell_density):
    try:
        from PIL import Image, ImageDraw
    except ImportError:
        return False

    os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)
    zgrid = metrics['zgrid']
    tile = 120
    pad = 28
    W = zgrid.gx * tile + pad * 2
    H = zgrid.gz * tile + pad * 2 + 34
    img = Image.new('RGB', (W, H), (18, 20, 26))
    dr = ImageDraw.Draw(img)

    dr.text((pad, 8), 'Quality Zone Heatmap — %dx%d  (mean density %.2f, min %.2f)'
            % (metrics['size'][0], metrics['size'][2], metrics['mean_density'], min_cell_density),
            fill=(235, 238, 245))

    for c in metrics['cells']:
        x0 = pad + c['cx'] * tile
        y0 = pad + 26 + c['cz'] * tile
        x1 = x0 + tile - 4
        y1 = y0 + tile - 4
        d = c['density']
        judged = c['active_cols'] >= c['area'] * 0.35
        if not judged:
            bg, border = (38, 42, 52), (75, 82, 98)
            status = 'RIM'
        elif d < min_cell_density:
            bg, border = (92, 28, 32), (235, 75, 80)
            status = 'DEAD'
        elif d < 0.65:
            bg, border = (78, 66, 26), (225, 190, 70)
            status = 'LIGHT'
        else:
            g = min(135, int(52 + d * 24))
            bg, border = (26, g, 54), (80, 215, 125)
            status = 'RICH'

        dr.rectangle([x0, y0, x1, y1], fill=bg, outline=border, width=2)
        dr.text((x0 + 7, y0 + 7), '[%d,%d] %s' % (c['cx'], c['cz'], c['code']), fill=(255, 255, 255))
        dr.text((x0 + 7, y0 + 25), str(c['role'])[:15], fill=(210, 220, 230))
        dr.text((x0 + 7, y0 + 48), 'dens: %.2f' % d, fill=(255, 245, 190))
        dr.text((x0 + 7, y0 + 66), 'var : %d blk' % c['variety'], fill=(200, 225, 255))
        dr.text((x0 + 7, y0 + 88), status, fill=border)

    img.save(out_path)
    return True


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument('nbt')
    ap.add_argument('--manifest', default=None, help='path to .manifest.json (auto-detected if omitted)')
    ap.add_argument('--project', default=None, help='optional project.json threshold overrides')
    ap.add_argument('--theme', default=None, help='override theme id for palette check')
    ap.add_argument('--heatmap', default=None, help='output PNG path for per-cell density heatmap')
    ap.add_argument('--allow-no-manifest', action='store_true')
    a = ap.parse_args(argv)

    mpath = a.manifest or (os.path.splitext(a.nbt)[0] + '.manifest.json')
    manifest = None
    if os.path.exists(mpath):
        with open(mpath, 'r', encoding='utf-8') as f:
            manifest = json.load(f)

    thresholds = dict(DEFAULT_THRESHOLDS)
    if manifest and isinstance(manifest.get('config', {}).get('quality'), dict):
        thresholds.update(manifest['config']['quality'])
    if a.project and os.path.exists(a.project):
        with open(a.project, 'r', encoding='utf-8') as f:
            pdata = json.load(f)
            if isinstance(pdata.get('quality'), dict):
                thresholds.update(pdata['quality'])
            if pdata.get('flat_floor') is not None:
                thresholds['min_relief_std'] = 0.0

    m = compute_metrics(a.nbt, manifest=manifest, theme_override=a.theme)
    sx, sy, sz = m['size']
    # Scale required part count gently for compact (<36) plots
    min_parts = thresholds['min_named_parts'] if min(sx, sz) >= 40 else max(5, thresholds['min_named_parts'] - 2)

    results = []

    def check(name, ok, detail):
        results.append((name, ok, detail))
        print('%-24s %-4s %s' % (name, 'PASS' if ok else 'FAIL', detail))

    print('== QUALITY GATE: %s ==' % a.nbt)
    print('size %dx%dx%d  blocks %d  active_cols %d (%.0f%%)'
          % (sx, sy, sz, m['total_blocks'], m['active_cols'], m['footprint_ratio'] * 100))
    print()

    # 1. Footprint coverage
    check('footprint.coverage',
          m['footprint_ratio'] >= thresholds['min_footprint_ratio'],
          '%.1f%% active columns (min %.0f%%)' % (m['footprint_ratio'] * 100, thresholds['min_footprint_ratio'] * 100))

    # 2. Terrain relief (anti-flat-pancake)
    check('terrain.relief',
          m['relief_std'] >= thresholds['min_relief_std'],
          'ground std=%.2f blocks (min %.2f — no flat slabs!)' % (m['relief_std'], thresholds['min_relief_std']))

    # 3. Hero landmark prominence
    check('landmark.prominence',
          m['hero_prominence'] >= thresholds['min_hero_prominence'],
          'peak +%d above median ground y=%d (min +%d)'
          % (m['hero_prominence'], m['median_ground'], thresholds['min_hero_prominence']))

    # 4. Per-cell anti-dead-zone check
    dead = [c for c in m['judged_cells'] if c['density'] < thresholds['min_cell_density']]
    dead_str = ', '.join('[%d,%d %s=%.2f]' % (c['cx'], c['cz'], c['role'], c['density']) for c in dead[:5])
    check('cells.no_dead_zones',
          len(dead) == 0 and m['mean_density'] >= thresholds['min_mean_density'],
          'mean_density=%.2f (min %.2f), dead_cells=%d%s'
          % (m['mean_density'], thresholds['min_mean_density'], len(dead),
             (' -> ' + dead_str) if dead else ''))

    # 5. Surface variety & anti-monoculture
    check('surface.variety',
          m['mean_variety'] >= thresholds['min_cell_variety']
          and m['dominant_share'] <= thresholds['max_dominant_surface'],
          'cell_variety=%.1f (min %.1f), top_surface=%s %.1f%% (max %.0f%%)'
          % (m['mean_variety'], thresholds['min_cell_variety'],
             m['dominant_block'], m['dominant_share'] * 100, thresholds['max_dominant_surface'] * 100))

    # 6. Lighting
    check('lighting.density',
          m['light_count'] > 0 and m['cols_per_light'] <= thresholds['max_cols_per_light'],
          '%d lights = 1 per %.1f cols (max 1 per %.0f)'
          % (m['light_count'], m['cols_per_light'], thresholds['max_cols_per_light']))

    # 7. Compositional structure (manifest parts + spawn)
    if manifest is not None:
        parts = [p for p in manifest.get('parts', []) if p['name'] != 'unassigned']
        unassigned = sum(p['blocks'] for p in manifest.get('parts', []) if p['name'] == 'unassigned')
        un_ratio = unassigned / float(max(1, m['total_blocks']))
        check('structure.named_parts',
              len(parts) >= min_parts and un_ratio <= thresholds['max_unassigned_ratio'],
              '%d named parts (min %d), unassigned=%.1f%%' % (len(parts), min_parts, un_ratio * 100))
        has_spawn = bool(manifest.get('spawn') and manifest['spawn'].get('pos'))
        check('player.spawn_pad', has_spawn,
              'spawn=%s' % (manifest.get('spawn') if has_spawn else 'MISSING (call place_spawn_pad / set_spawn)'))
    elif not a.allow_no_manifest:
        check('structure.manifest', False,
              'missing %s (build with mckit.Canvas so parts, zones & spawn are recorded)' % os.path.basename(mpath))

    # 8. Theme palette coherence
    if m['coherence'] is not None:
        check('palette.coherence',
              m['coherence'] >= thresholds['min_palette_coherence'],
              '%.1f%% on-theme (min %.0f%%)%s'
              % (m['coherence'] * 100, thresholds['min_palette_coherence'] * 100,
                 (' off-theme: ' + ','.join(m['off_theme'])) if m['off_theme'] and m['coherence'] < thresholds['min_palette_coherence'] else ''))

    heatmap_path = a.heatmap or os.path.join(os.path.dirname(os.path.abspath(a.nbt)), 'renders', 'quality-heatmap.png')
    if write_heatmap(m, manifest, heatmap_path, thresholds['min_cell_density']):
        print('\nheatmap -> %s' % heatmap_path)

    failed = [r for r in results if not r[1]]
    print('%d quality checks: %d passed, %d failed' % (len(results), len(results) - len(failed), len(failed)))
    if failed:
        print('QUALITY GATE FAILED: ' + ', '.join(r[0] for r in failed))
        return 1
    print('QUALITY GATE PASSED — rich, cohesive, zero dead cells')
    return 0


if __name__ == '__main__':
    sys.exit(main())
