# Block states: the properties you MUST emit

**Rule zero: if a block has `Properties` in the real world, your structure NBT must
carry them explicitly.** Minecraft does *not* infer them on paste. Whatever you omit
is silently replaced by the block's default, which is very often not what you meant.

The consequences are not cosmetic:

| Block | You omit | What actually lands | Why it matters |
|---|---|---|---|
| `*_leaves` | `persistent`, `distance` | leaves **decay** | whole tree canopies vanish after a while |
| `*_stairs` | `facing`, `half`, `shape` | default north/bottom/straight | every staircase faces the wrong way |
| `*_slab` | `type` | `bottom` | fine by luck, but `top`/`double` designs break |
| `water` | `level` | flowing water | floods, or turns into source blocks |
| `grass_block` | `snowy` | usually fine | but emits a different state than the source |
| `*_wood` / `*_log` | `axis` | `y` | horizontal logs become vertical |
| `lantern` | `hanging` | `false` | hanging lanterns float off their chain |

## The verified table

This is the exact property set that pasted **block-for-block identical** on Paper
26.3 / FAWE. Copy it; do not retype from memory.

```python
def props_for(name):
    b = name.split(':')[-1]
    if b.endswith('_leaves'):
        return {'persistent': 'true', 'waterlogged': 'false', 'distance': '7'}
    if b in ('jungle_wood', 'oak_wood', 'iron_chain'):
        return {'axis': 'y'}
    if b == 'lantern':
        return {'hanging': 'false', 'waterlogged': 'false'}
    if b.endswith('_slab'):
        return {'type': 'bottom', 'waterlogged': 'false'}
    if b.endswith('_stairs'):
        return {'facing': 'north', 'half': 'bottom', 'shape': 'straight',
                'waterlogged': 'false'}
    if b == 'grass_block':
        return {'snowy': 'false'}
    if b == 'moss_carpet':
        return {'bottom': 'true'}
    if b == 'small_dripleaf':
        return {'facing': 'north', 'half': 'lower', 'waterlogged': 'false'}
    if b == 'carrots':
        return {'age': '3'}
    if b == 'farmland':
        return {'moisture': '0'}
    if b == 'campfire':
        return {'facing': 'north', 'lit': 'true', 'signal_fire': 'false',
                'waterlogged': 'false'}
    if b == 'sea_pickle':
        return {'pickles': '2', 'waterlogged': 'false'}
    if b == 'pink_petals':
        return {'facing': 'north', 'flower_amount': '2'}
    if b == 'suspicious_sand':
        return {'dusted': '0'}
    if b == 'barrel':
        return {'facing': 'up', 'open': 'false'}
    if b == 'hopper':
        return {'enabled': 'true', 'facing': 'down'}
    if b == 'anvil':
        return {'facing': 'north'}
    if b == 'ender_chest':
        return {'facing': 'north', 'waterlogged': 'false'}
    if b == 'ladder':
        return {'facing': 'north', 'waterlogged': 'false'}
    if b == 'scaffolding':
        return {'bottom': 'true', 'distance': '0', 'waterlogged': 'false'}
    if b == 'bee_nest':
        return {'facing': 'north', 'honey_level': '3'}
    if b == 'stone_button':
        return {'face': 'floor', 'facing': 'north', 'powered': 'false'}
    if b == 'stone_pressure_plate':
        return {'powered': 'false'}
    if b.endswith('_wall_banner'):
        return {'facing': 'north'}
    if b in ('player_head', 'skeleton_skull', 'zombie_head', 'creeper_head'):
        return {'rotation': '0'}
    if b.endswith('_wall_head') or b == 'player_wall_head':
        return {'facing': 'north'}
    if b == 'spruce_trapdoor':
        return {'facing': 'north', 'half': 'top', 'open': 'false',
                'powered': 'false', 'waterlogged': 'false'}
    if b == 'water':
        return {'level': '0'}
    if b.endswith('_wall_sign'):
        return {'facing': 'north', 'waterlogged': 'false'}
    return None
```

## Directional blocks are not symmetric - set them per-instance

The table above gives a *default* facing. For anything you place deliberately you must
compute the real value:

```python
STAIRS = {f: pid('minecraft:spruce_stairs',
                 {'facing': f, 'half': 'bottom', 'shape': 'straight',
                  'waterlogged': 'false'})
          for f in ('north', 'south', 'east', 'west')}
```

`facing` means the direction the block's **front** points:
`north` = towards `-z`, `south` = `+z`, `east` = `+x`, `west` = `-x`.

## Blocks that need a support and will look broken without one

Anything in this family must be checked by the validator (see `verification.md`):

`short_grass, tall_grass, fern, large_fern, poppy, dandelion, red_tulip,
lily_of_the_valley, pink_petals, moss_carpet, small_dripleaf, carrots,
sea_pickle, tripwire, lantern, iron_chain, player_head, skeleton_skull,
player_wall_head, *_wall_banner, *_wall_sign, scaffolding, ladder,
*_trapdoor, *_fence, *_pane, *_wall`

These are exactly the blocks that produce the classic complaints
*"floating grass"*, *"heads invisible in the air"*, *"floating strings"* and
*"banners not at the right position"*.

**`tripwire` is a trap.** It needs no support, so it happily sits in mid-air and
renders as a thin floating string. If you find tripwire you did not deliberately
design, delete it.

## Wall-mounted blocks must actually have a wall behind them

For `*_wall_banner`, `*_wall_sign`, `*_wall_head`, the block **behind** the stated
facing must be a solid full block:

```python
FACING = {'north': (0, -1), 'south': (0, 1), 'east': (1, 0), 'west': (-1, 0)}
dx, dz = FACING[props['facing']]
assert solid(get(x + dx, y, z + dz)), 'banner hanging on air'
```

A banner whose backing block is air or another banner is the single most common
"misplaced decoration" failure.

## Finding real values instead of guessing

Never invent a property. Read it from a world that already works:

```bash
python3 scripts/nbt_query.py world.nbt --props minecraft:oak_stairs   # sample values
python3 scripts/read_region.py --props minecraft:oak_stairs --at 100 64 200
```

The vendored `vendor/lodestone-docs/default-pack-block-states.md` lists every legal
value for every vanilla block — grep it before choosing:

```bash
rg -n -A 80 '### `minecraft:oak_stairs`' vendor/lodestone-docs/default-pack-block-states.md
```
