"""Block state rules, material families, support tables and auto-connections.

Single source of truth shared by `mckit`, `validate.py`, and `quality.py`.
"""

DEFAULT_DATA_VERSION = 4189  # Minecraft 1.21.4 (cherry, bamboo, tuff, copper bulb, froglights; DFU-upgrades cleanly on 1.21.9+/26.x)

# ---------------------------------------------------------------- classifications
AIR_NAMES = frozenset({'air', 'cave_air', 'void_air'})
FLUID_NAMES = frozenset({'water', 'lava'})

SOILS = frozenset({
    'grass_block', 'dirt', 'coarse_dirt', 'rooted_dirt', 'moss_block',
    'podzol', 'mycelium', 'farmland', 'mud', 'muddy_mangrove_roots',
    'dirt_path', 'clay', 'sand', 'red_sand', 'gravel', 'soul_soil', 'soul_sand',
})

FLAT_PLANTS = frozenset({
    'short_grass', 'grass', 'tall_grass', 'fern', 'large_fern', 'dead_bush',
    'poppy', 'dandelion', 'red_tulip', 'orange_tulip', 'white_tulip', 'pink_tulip',
    'blue_orchid', 'allium', 'azure_bluet', 'oxeye_daisy', 'cornflower',
    'lily_of_the_valley', 'wither_rose', 'torchflower', 'pitcher_plant',
    'sunflower', 'lilac', 'rose_bush', 'peony',
    'pink_petals', 'moss_carpet', 'small_dripleaf', 'big_dripleaf',
    'crimson_roots', 'warped_roots', 'nether_sprouts',
    'brown_mushroom', 'red_mushroom', 'crimson_fungus', 'warped_fungus',
    'carrots', 'potatoes', 'wheat', 'beetroots', 'sweet_berry_bush',
    'bamboo_sapling', 'oak_sapling', 'spruce_sapling', 'birch_sapling',
    'jungle_sapling', 'acacia_sapling', 'dark_oak_sapling', 'cherry_sapling',
    'azalea', 'flowering_azalea', 'mangrove_propagule',
    'sugar_cane', 'bamboo', 'kelp', 'kelp_plant', 'seagrass', 'tall_seagrass',
    'sea_pickle', 'lily_pad', 'snow',
})

SURFACE_CLING = frozenset({'vine', 'glow_lichen', 'sculk_vein'})

HANGING_ONLY = frozenset({
    'hanging_roots', 'spore_blossom', 'cave_vines', 'cave_vines_plant',
    'weeping_vines', 'weeping_vines_plant', 'pointed_dripstone',
})

CHAINS = frozenset({'chain', 'iron_chain'})

LIGHT_SOURCES = frozenset({
    'lantern', 'soul_lantern', 'torch', 'wall_torch', 'soul_torch', 'soul_wall_torch',
    'redstone_torch', 'redstone_wall_torch', 'campfire', 'soul_campfire',
    'sea_lantern', 'glowstone', 'shroomlight', 'ochre_froglight',
    'verdant_froglight', 'pearlescent_froglight', 'end_rod', 'jack_o_lantern',
    'beacon', 'conduit', 'crying_obsidian', 'respawn_anchor', 'copper_bulb',
    'exposed_copper_bulb', 'weathered_copper_bulb', 'oxidized_copper_bulb',
    'waxed_copper_bulb', 'waxed_exposed_copper_bulb', 'waxed_weathered_copper_bulb',
    'waxed_oxidized_copper_bulb', 'amethyst_cluster', 'large_amethyst_bud',
    'sea_pickle', 'cave_vines', 'cave_vines_plant', 'glow_lichen',
    'candle', 'white_candle', 'orange_candle', 'magenta_candle', 'light_blue_candle',
    'yellow_candle', 'lime_candle', 'pink_candle', 'gray_candle', 'light_gray_candle',
    'cyan_candle', 'purple_candle', 'blue_candle', 'brown_candle', 'green_candle',
    'red_candle', 'black_candle', 'redstone_lamp',
})

# Blocks that cannot support plants, trees, lanterns, or soil from below.
NO_SUPPORT = (
    AIR_NAMES
    | FLUID_NAMES
    | FLAT_PLANTS
    | SURFACE_CLING
    | HANGING_ONLY
    | CHAINS
    | frozenset({
        'lantern', 'soul_lantern', 'scaffolding', 'ladder', 'tripwire',
        'light', 'barrier', 'structure_void', 'cobweb', 'end_rod',
        'torch', 'wall_torch', 'soul_torch', 'soul_wall_torch',
    })
)

WOOD_TYPES = (
    'oak', 'spruce', 'birch', 'jungle', 'acacia', 'dark_oak',
    'mangrove', 'cherry', 'bamboo', 'crimson', 'warped',
)


def short_name(name):
    """Strip `minecraft:` prefix and any `[state]` suffix."""
    s = name.split('[', 1)[0].strip()
    return s.split(':', 1)[-1]


def full_name(name, data_version=DEFAULT_DATA_VERSION):
    """Canonical `minecraft:<id>`, mapping chain <-> iron_chain for DataVersion."""
    b = short_name(name)
    if b in CHAINS:
        b = 'iron_chain' if data_version >= 4600 else 'chain'
    return 'minecraft:' + b


def parse_block_spec(spec, extra_props=None, data_version=DEFAULT_DATA_VERSION):
    """Parse `'cherry_stairs[facing=east,half=top]'` + keyword overrides -> `(full_name, props_dict)`."""
    if isinstance(spec, tuple) and len(spec) == 2:
        nm, pr = spec
        merged = dict(default_props(nm) or {})
        if pr:
            merged.update({k: str(v).lower() if isinstance(v, bool) else str(v) for k, v in pr.items()})
        if extra_props:
            merged.update({k: str(v).lower() if isinstance(v, bool) else str(v) for k, v in extra_props.items()})
        return full_name(nm, data_version), merged

    raw = str(spec).strip()
    inline = {}
    if '[' in raw and raw.endswith(']'):
        raw, rest = raw[:-1].split('[', 1)
        for part in rest.split(','):
            part = part.strip()
            if '=' in part:
                k, v = part.split('=', 1)
                inline[k.strip()] = v.strip()
    nm = full_name(raw, data_version)
    props = dict(default_props(nm) or {})
    props.update(inline)
    if extra_props:
        for k, v in extra_props.items():
            if v is None:
                continue
            props[k] = str(v).lower() if isinstance(v, bool) else str(v)
    return nm, props


def is_leaves(b):
    b = short_name(b)
    return b.endswith('_leaves')


def is_log(b):
    b = short_name(b)
    return (
        b.endswith(('_log', '_wood', '_stem', '_hyphae'))
        or b in ('bamboo_block', 'stripped_bamboo_block', 'mangrove_roots')
    )


def is_foliage(b):
    return is_leaves(b) or is_log(b)


def is_fence(b):
    b = short_name(b)
    return b.endswith('_fence') and not b.endswith('_fence_gate')


def is_wall(b):
    b = short_name(b)
    return b.endswith('_wall')


def is_pane(b):
    b = short_name(b)
    return b.endswith('_stained_glass_pane') or b in ('glass_pane', 'iron_bars')


def is_stairs(b):
    return short_name(b).endswith('_stairs')


def is_slab(b):
    return short_name(b).endswith('_slab')


def is_trapdoor(b):
    return short_name(b).endswith('_trapdoor')


def is_solid_full(b):
    """Conservative full-cube check for wall-mounting and fence/wall attachment."""
    b = short_name(b)
    if b in NO_SUPPORT or b in FLUID_NAMES or b in AIR_NAMES:
        return False
    if (
        is_leaves(b) or is_fence(b) or is_wall(b) or is_pane(b)
        or is_stairs(b) or is_slab(b) or is_trapdoor(b)
        or b.endswith(('_fence_gate', '_door', '_banner', '_sign', '_hanging_sign',
                       '_button', '_pressure_plate', '_carpet', '_candle',
                       '_head', '_skull', '_coral', '_coral_fan', '_amethyst_bud'))
        or b in ('campfire', 'soul_campfire', 'lectern', 'bell', 'grindstone',
                 'anvil', 'chipped_anvil', 'damaged_anvil', 'chest', 'trapped_chest',
                 'ender_chest', 'brewing_stand', 'flower_pot', 'decorated_pot',
                 'amethyst_cluster', 'bamboo', 'Lightning_rod', 'lightning_rod',
                 'composter', 'cauldron', 'water_cauldron', 'hopper')
    ):
        return False
    return True


def default_props(name):
    """Verified default `Properties` so pasted blocks never decay or mis-orient."""
    b = short_name(name)
    if is_leaves(b):
        p = {'persistent': 'true', 'distance': '7', 'waterlogged': 'false'}
        return p
    if is_log(b) and b != 'mangrove_roots':
        return {'axis': 'y'}
    if b.endswith(('_pillar', '_froglight')) or b in (
        'deepslate', 'basalt', 'polished_basalt', 'bone_block', 'hay_block', 'muddy_mangrove_roots',
    ):
        return {'axis': 'y'}
    if b == 'mangrove_roots':
        return {'waterlogged': 'false'}
    if b in CHAINS:
        return {'axis': 'y', 'waterlogged': 'false'}
    if b in ('lantern', 'soul_lantern'):
        return {'hanging': 'false', 'waterlogged': 'false'}
    if is_slab(b):
        return {'type': 'bottom', 'waterlogged': 'false'}
    if is_stairs(b):
        return {'facing': 'north', 'half': 'bottom', 'shape': 'straight', 'waterlogged': 'false'}
    if is_fence(b) or is_pane(b):
        return {'north': 'false', 'south': 'false', 'east': 'false', 'west': 'false', 'waterlogged': 'false'}
    if b.endswith('_fence_gate'):
        return {'facing': 'north', 'in_wall': 'false', 'open': 'false', 'powered': 'false'}
    if is_wall(b):
        return {'north': 'none', 'south': 'none', 'east': 'none', 'west': 'none',
                'up': 'true', 'waterlogged': 'false'}
    if is_trapdoor(b):
        return {'facing': 'north', 'half': 'bottom', 'open': 'false',
                'powered': 'false', 'waterlogged': 'false'}
    if b.endswith('_door'):
        return {'facing': 'north', 'half': 'lower', 'hinge': 'left',
                'open': 'false', 'powered': 'false'}
    if b in ('grass_block', 'podzol', 'mycelium'):
        return {'snowy': 'false'}
    if b in ('campfire', 'soul_campfire'):
        return {'facing': 'north', 'lit': 'true', 'signal_fire': 'false', 'waterlogged': 'false'}
    if b == 'pink_petals':
        return {'facing': 'north', 'flower_amount': '3'}
    if b == 'sea_pickle':
        return {'pickles': '2', 'waterlogged': 'true'}
    if b in ('seagrass', 'kelp', 'kelp_plant'):
        return None
    if b == 'tall_seagrass':
        return {'half': 'lower'}
    if b in ('tall_grass', 'large_fern', 'sunflower', 'lilac', 'rose_bush', 'peony', 'pitcher_plant'):
        return {'half': 'lower'}
    if b == 'small_dripleaf':
        return {'facing': 'north', 'half': 'lower', 'waterlogged': 'false'}
    if b == 'big_dripleaf':
        return {'facing': 'north', 'tilt': 'none', 'waterlogged': 'false'}
    if b == 'bamboo':
        return {'age': '1', 'leaves': 'none', 'stage': '0'}
    if b in ('cave_vines', 'cave_vines_plant'):
        return {'berries': 'false'}
    if b == 'hanging_roots':
        return {'waterlogged': 'false'}
    if b in ('water', 'lava'):
        return {'level': '0'}
    if b == 'barrel':
        return {'facing': 'up', 'open': 'false'}
    if b in ('chest', 'trapped_chest', 'ender_chest'):
        return {'facing': 'north', 'waterlogged': 'false'}
    if b == 'lectern':
        return {'facing': 'north', 'has_book': 'true', 'powered': 'false'}
    if b == 'bell':
        return {'attachment': 'ceiling', 'facing': 'north', 'powered': 'false'}
    if b == 'end_rod' or b == 'lightning_rod':
        p = {'facing': 'up'}
        if b == 'lightning_rod':
            p['powered'] = 'false'
            p['waterlogged'] = 'false'
        return p
    if b == 'amethyst_cluster' or b.endswith('_amethyst_bud'):
        return {'facing': 'up', 'waterlogged': 'false'}
    if b == 'candle' or b.endswith('_candle'):
        return {'candles': '2', 'lit': 'true', 'waterlogged': 'false'}
    if b.endswith('copper_bulb'):
        return {'lit': 'true', 'powered': 'false'}
    if b.endswith('_button'):
        return {'face': 'floor', 'facing': 'north', 'powered': 'false'}
    if b.endswith('_pressure_plate'):
        return {'powered': 'false'}
    if b.endswith('_wall_banner'):
        return {'facing': 'north'}
    if b.endswith('_banner'):
        return {'rotation': '0'}
    if b.endswith('_wall_sign'):
        return {'facing': 'north', 'waterlogged': 'false'}
    if b.endswith('_hanging_sign') and not b.endswith('_wall_hanging_sign'):
        return {'attached': 'false', 'rotation': '0', 'waterlogged': 'false'}
    if b.endswith('_wall_hanging_sign'):
        return {'facing': 'north', 'waterlogged': 'false'}
    if b.endswith('_sign'):
        return {'rotation': '0', 'waterlogged': 'false'}
    if b in ('wall_torch', 'soul_wall_torch', 'redstone_wall_torch'):
        return {'facing': 'north'}
    if b == 'ladder':
        return {'facing': 'north', 'waterlogged': 'false'}
    if b == 'vine':
        return {'north': 'true', 'south': 'false', 'east': 'false', 'west': 'false', 'up': 'false'}
    if b == 'farmland':
        return {'moisture': '7'}
    if b in ('wheat', 'carrots', 'potatoes'):
        return {'age': '7'}
    if b == 'beetroots' or b == 'sweet_berry_bush':
        return {'age': '3'}
    if b == 'composter':
        return {'level': '6'}
    return None


def family(material):
    """Return a dict of block forms for a wood or stone material.

    Examples:
        family('cherry')       -> planks, stairs, slab, fence, trapdoor, log, wood, ...
        family('stone_bricks') -> block, stairs, slab, wall, cracked, mossy, chiseled
        family('deepslate_bricks') -> block, stairs, slab, wall, cracked
    """
    m = short_name(material)
    if m == 'bamboo':
        return {
            'block': 'bamboo_planks',
            'planks': 'bamboo_planks',
            'mosaic': 'bamboo_mosaic',
            'stairs': 'bamboo_stairs',
            'slab': 'bamboo_slab',
            'fence': 'bamboo_fence',
            'fence_gate': 'bamboo_fence_gate',
            'trapdoor': 'bamboo_trapdoor',
            'door': 'bamboo_door',
            'button': 'bamboo_button',
            'pressure_plate': 'bamboo_pressure_plate',
            'sign': 'bamboo_sign',
            'wall_sign': 'bamboo_wall_sign',
            'hanging_sign': 'bamboo_hanging_sign',
            'log': 'bamboo_block',
            'stripped_log': 'stripped_bamboo_block',
            'wood': 'bamboo_block',
            'stripped_wood': 'stripped_bamboo_block',
            'leaves': 'jungle_leaves',
        }
    if m in ('crimson', 'warped'):
        return {
            'block': f'{m}_planks',
            'planks': f'{m}_planks',
            'stairs': f'{m}_stairs',
            'slab': f'{m}_slab',
            'fence': f'{m}_fence',
            'fence_gate': f'{m}_fence_gate',
            'trapdoor': f'{m}_trapdoor',
            'door': f'{m}_door',
            'button': f'{m}_button',
            'pressure_plate': f'{m}_pressure_plate',
            'sign': f'{m}_sign',
            'wall_sign': f'{m}_wall_sign',
            'hanging_sign': f'{m}_hanging_sign',
            'log': f'{m}_stem',
            'stripped_log': f'stripped_{m}_stem',
            'wood': f'{m}_hyphae',
            'stripped_wood': f'stripped_{m}_hyphae',
            'leaves': 'nether_wart_block' if m == 'crimson' else 'warped_wart_block',
        }
    if m in WOOD_TYPES:
        leaves = 'azalea_leaves' if m == 'mangrove' else f'{m}_leaves'
        if m == 'mangrove':
            leaves = 'mangrove_leaves'
        return {
            'block': f'{m}_planks',
            'planks': f'{m}_planks',
            'stairs': f'{m}_stairs',
            'slab': f'{m}_slab',
            'fence': f'{m}_fence',
            'fence_gate': f'{m}_fence_gate',
            'trapdoor': f'{m}_trapdoor',
            'door': f'{m}_door',
            'button': f'{m}_button',
            'pressure_plate': f'{m}_pressure_plate',
            'sign': f'{m}_sign',
            'wall_sign': f'{m}_wall_sign',
            'hanging_sign': f'{m}_hanging_sign',
            'log': f'{m}_log',
            'stripped_log': f'stripped_{m}_log',
            'wood': f'{m}_wood',
            'stripped_wood': f'stripped_{m}_wood',
            'leaves': leaves,
        }

    # Stone / brick / tile / mineral families
    stem = m[:-1] if m.endswith(('bricks', 'tiles')) else m
    wall_block = f'{stem}_wall'
    no_wall = {
        'quartz_block': ('quartz_block', 'quartz_stairs', 'quartz_slab', 'smooth_quartz_slab'),
        'smooth_quartz': ('smooth_quartz', 'smooth_quartz_stairs', 'smooth_quartz_slab', 'quartz_pillar'),
        'dark_prismarine': ('dark_prismarine', 'dark_prismarine_stairs', 'dark_prismarine_slab', 'prismarine_wall'),
        'prismarine_bricks': ('prismarine_bricks', 'prismarine_brick_stairs', 'prismarine_brick_slab', 'prismarine_wall'),
        'purpur_block': ('purpur_block', 'purpur_stairs', 'purpur_slab', 'purpur_pillar'),
        'stone': ('stone', 'stone_stairs', 'stone_slab', 'cobblestone_wall'),
        'polished_andesite': ('polished_andesite', 'polished_andesite_stairs', 'polished_andesite_slab', 'andesite_wall'),
        'polished_granite': ('polished_granite', 'polished_granite_stairs', 'polished_granite_slab', 'granite_wall'),
        'polished_diorite': ('polished_diorite', 'polished_diorite_stairs', 'polished_diorite_slab', 'diorite_wall'),
    }
    if m in no_wall:
        blk, st, sl, wl = no_wall[m]
        return {'block': blk, 'stairs': st, 'slab': sl, 'wall': wl, 'fence': wl}
    return {
        'block': m,
        'stairs': f'{stem}_stairs',
        'slab': f'{stem}_slab',
        'wall': wall_block,
        'fence': wall_block,
    }


def facing_toward(dx, dz):
    """Cardinal direction pointing toward `(dx, dz)` (`north` = -Z, `south` = +Z, `east` = +X, `west` = -X)."""
    if abs(dx) >= abs(dz):
        return 'east' if dx >= 0 else 'west'
    return 'south' if dz >= 0 else 'north'


OPPOSITE = {'north': 'south', 'south': 'north', 'east': 'west', 'west': 'east', 'up': 'down', 'down': 'up'}
