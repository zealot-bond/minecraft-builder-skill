"""Deterministic block texturing, weighted mixes, and spatial gradients."""

import math
from .blocks import short_name


def hash3(x, y, z, seed=0):
    """Fast deterministic 32-bit coordinate hash."""
    h = (int(x) * 374761393 + int(y) * 668265263 + int(z) * 2147483647 + int(seed) * 1597334677) & 0xFFFFFFFF
    h = ((h ^ (h >> 13)) * 1274126177) & 0xFFFFFFFF
    return (h ^ (h >> 16)) & 0xFFFFFFFF


def rand01(x, y, z, seed=0):
    return (hash3(x, y, z, seed) & 0xFFFFFF) / float(0x1000000)


def mix(entries, seed=0):
    """Create a callable `picker(x, y, z) -> block` from weights or a plain list.

    `entries` may be:
      - `{'stone_bricks': 6, 'cracked_stone_bricks': 2, 'mossy_stone_bricks': 2}`
      - `[('stone_bricks', 6), ('mossy_stone_bricks', 2)]`
      - `['grass_block', 'moss_block']` (equal weights)
    """
    if isinstance(entries, dict):
        items = list(entries.items())
    elif entries and isinstance(entries[0], tuple) and len(entries[0]) == 2 and isinstance(entries[0][1], (int, float)):
        items = list(entries)
    else:
        items = [(e, 1) for e in entries]
    scaled = [(b, max(1, int(round(w * 100)))) for b, w in items]
    total = sum(w for _, w in scaled)

    def pick(x, y=0, z=0):
        n = hash3(x, y, z, seed) % total
        acc = 0
        for b, w in scaled:
            acc += w
            if n < acc:
                return b
        return scaled[-1][0]

    return pick


def gradient(chain, seed=0, jitter=0.14):
    """Create `grad(t, x=0, y=0, z=0) -> block` for `t` in `[0.0, 1.0]`.

    Adds subtle coordinate dither so transitions feather naturally instead of
    forming ruler-straight horizontal stripes.
    """
    chain = list(chain)
    n = len(chain)
    if n == 0:
        raise ValueError('empty gradient chain')

    def pick(t, x=0, y=0, z=0):
        if n == 1:
            return chain[0]
        dither = (rand01(x, y, z, seed) - 0.5) * 2.0 * jitter
        u = max(0.0, min(1.0, float(t) + dither))
        idx = int(round(u * (n - 1)))
        return chain[max(0, min(n - 1, idx))]

    return pick


# Neutrals allowed alongside any theme palette without hurting palette coherence.
UNIVERSAL_NEUTRALS = frozenset({
    'air', 'water', 'dirt', 'coarse_dirt', 'rooted_dirt', 'grass_block', 'moss_block',
    'moss_carpet', 'podzol', 'mud', 'clay', 'sand', 'gravel', 'stone', 'andesite',
    'tuff', 'cobblestone', 'mossy_cobblestone', 'deepslate', 'cobbled_deepslate',
    'stone_bricks', 'cracked_stone_bricks', 'mossy_stone_bricks',
    'chain', 'iron_chain', 'lantern', 'soul_lantern', 'campfire', 'soul_campfire',
    'barrel', 'chest', 'ender_chest', 'crafting_table', 'anvil', 'lectern', 'bell',
    'flower_pot', 'decorated_pot', 'composter', 'cauldron', 'water_cauldron',
    'short_grass', 'tall_grass', 'fern', 'large_fern', 'lily_pad', 'seagrass',
    'tall_seagrass', 'sea_pickle', 'sugar_cane', 'vine', 'glow_lichen',
    'hanging_roots', 'cave_vines', 'cave_vines_plant', 'spore_blossom',
    'dirt_path', 'oak_sign', 'spruce_sign', 'dark_oak_sign',
})


def theme_allowed_blocks(theme):
    """Collect the set of short block names belonging to a theme + universal neutrals."""
    allowed = set(UNIVERSAL_NEUTRALS)
    for k, v in theme.items():
        if k in ('id', 'title', 'vibe', 'inspiration_queries'):
            continue
        if isinstance(v, str):
            allowed.add(short_name(v))
        elif isinstance(v, dict):
            for sv in v.values():
                if isinstance(sv, str):
                    allowed.add(short_name(sv))
        elif isinstance(v, (list, tuple)):
            for item in v:
                if isinstance(item, str):
                    allowed.add(short_name(item))
                elif isinstance(item, (list, tuple)):
                    for sub in item:
                        if isinstance(sub, str):
                            allowed.add(short_name(sub))
    # Also expand common stair/slab/wall/fence/wood siblings of any themed base material
    extra = set()
    for b in list(allowed):
        for suf in ('_planks', '_block', '_bricks', '_tiles'):
            if b.endswith(suf):
                stem = b[:-len(suf)]
                for f in ('_stairs', '_slab', '_wall', '_fence', '_fence_gate',
                          '_trapdoor', '_door', '_button', '_pressure_plate',
                          '_log', '_wood', '_stem', '_hyphae', '_sign', '_wall_sign',
                          '_hanging_sign', '_wall_hanging_sign', '_mosaic', '_pillar',
                          '_chiseled'):
                    extra.add(stem + f)
                extra.add('stripped_' + stem + '_log')
                extra.add('stripped_' + stem + '_wood')
                extra.add('cracked_' + b)
                extra.add('mossy_' + b)
                extra.add('polished_' + stem)
    bc = theme.get('banner_color')
    if bc:
        for suf in ('_banner', '_wall_banner', '_wool', '_carpet', '_candle',
                    '_stained_glass', '_stained_glass_pane', '_terracotta', '_concrete'):
            extra.add(bc + suf)
    for suf in ('_banner', '_wall_banner', '_wool', '_carpet', '_candle'):
        extra.add('white' + suf)
    return allowed | extra
