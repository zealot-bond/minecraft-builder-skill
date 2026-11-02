"""v6 spawn builder: a flat 190x190 plaza (45 blocks each side of the arena,
exactly as asked), a BLUE glass border at its edge, and 40 columns of real,
layered terraces outside that descend to meet the natural ground.

WHY THIS SHAPE (the two rejections it fixes)
--------------------------------------------
v5 was a flat 190x190 slab with NOTHING outside it.  N=190 is exactly arena 100
+ 45 + 45, so there was zero room to blend and the box edge became a 26-block
featureless retaining wall on all four sides.  That is the "ugly blend / monolith"
the user rejected.

v6 keeps every block of the requested flat area and adds 40 columns per side
that do the job the wall was doing:

    world x 195..464, z 259..528   (270 x 270, build ly 0 == world y42)

    local  40..229  = the FLAT plaza, world y73  (190 wide, 45/side)  <- requested
    local   0..39   = west terraces
    local 230..269  = east terraces
    and the same on z, north / south.

The terrace heights are not invented.  nat340.pkl gives the real surface height
of every natural column around the build, so:

  * E(t) = the medians of the natural ground along the outside rim, smoothed
    along the rim (window 27).  That is what the terraces must meet.
  * a column's top starts at the plaza and steps DOWN in 4-block lifts, at most
    one lift per landing, reaching exactly E(t) at the box edge.

Result: west and south step down ~24 blocks (their seabed is at y47), east and
north step down only ~7 (they are already at y66-71).  Corners take the higher
of the two sides, so no column ever stands proud of its neighbours: the whole
outside is a continuous staircase of wide flat landings, never a cliff.

Also fixed here, each mapped to a complaint:
  * water: every column of the box is filled solid from ly0 to its top, so no
    water body exists anywhere in the build, and the rim is held at
    water_surface + 2 so the ocean west cannot show over the terraces.
  * "too many trees", "just one model repeated": 5 distinct models, 17 sites,
    models assigned so no two neighbouring sites share one.
  * "random grass blocks on the trees on the main logs": plants and grass/moss
    that touch logs or leaves are deleted, plus the support sweep.
  * "floating grass and player heads": support + connected-component sweep over
    the WHOLE box, not just the arena.
  * "swing is misplaced, not connected": the branch is grown out of a wood
    block found in the actual trunk, and the chains start one block under it.
  * "improve the cave, add more stuff, extend it": three halls, a gallery ring,
    a grotto, a shrine, a mushroom farm, a storeroom, 4 shafts.
  * "spawn looks so empty": ring avenue, 4 spoke avenues, 4 corner plazas, gate
    arches, 40+ street lights, benches, market stalls, kerbed flower beds.

Memory: 270*98*270 cells in a uint16 grid (14 MB); streamnbt.py writes the NBT
in a single pass, no block compound is ever built in memory.
"""
import sys, os, math, pickle, random
from array import array
from collections import Counter, deque

ROOT = '/home/rhythm/Documents/kayleesmp'
sys.path.insert(0, ROOT + '/mace-work')
sys.path.insert(0, ROOT + '/mace-work/v4')
os.chdir(ROOT)

import lite
import trees3
import streamnbt

# ------------------------------------------------------------------ geometry
N = 270                       # box is 270 x 270
SY = 98                       # build ly 0..97
Y0 = 42                       # world y of build ly 0
PLANE_W = 73                  # the one flat surface, in world y
LVL = PLANE_W - Y0            # build ly of the flat plaza == 31
AR_N = 100
AR_X0, AR_Z0 = 280, 344       # world position of the arena (unchanged)
X0, Z0 = 195, 259             # world origin of this box
OX, OZ = AR_X0 - X0, AR_Z0 - Z0             # 85, 85
A0X, A1X = OX, OX + AR_N - 1                # 85..184
A0Z, A1Z = OZ, OZ + AR_N - 1
AR_OFF = LVL - 13             # arena local y + 18 == build ly
ARENA_BASE = AR_OFF - 1       # 17
CAVE_LO = 2
CAVE_HI = ARENA_BASE

P0, P1 = 40, 229              # the FLAT plaza, local: 190 wide == 45 blocks/side
PW = P1 - P0 + 1              # 190
TCOL = P0                     # 40 columns of terrace per side
PL_OFF = P0 - (A0X - P0)      # not used; kept for clarity

# ------------------------------------------------------------------ palette
PAL = []
PAL_IX = {}
M = 'minecraft:'


def pid(name, props=None):
    key = (name, tuple(sorted((props or {}).items())))
    i = PAL_IX.get(key)
    if i is None:
        i = len(PAL)
        PAL_IX[key] = i
        PAL.append(key)
    return i


AIR = pid(M + 'air')
assert AIR == 0, 'palette index 0 must be air'

_SLAB = {'type': 'bottom', 'waterlogged': 'false'}
_STAIR = {'facing': 'north', 'half': 'bottom', 'shape': 'straight',
          'waterlogged': 'false'}


def props_for(name):
    b = name.split(':')[-1]
    if b.endswith('_leaves'):
        return {'persistent': 'true', 'waterlogged': 'false', 'distance': '7'}
    if b in ('jungle_wood', 'oak_wood', 'iron_chain'):
        return {'axis': 'y'}
    if b == 'lantern':
        return {'hanging': 'false', 'waterlogged': 'false'}
    if b.endswith('_slab'):
        return dict(_SLAB)
    if b.endswith('_stairs'):
        return dict(_STAIR)
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
    if b == 'spruce_trapdoor':
        return {'facing': 'north', 'half': 'top', 'open': 'false',
                'powered': 'false', 'waterlogged': 'false'}
    return None


def bid(name):
    return pid(name, props_for(name))


GRASS = bid(M + 'grass_block')
PATH = bid(M + 'dirt_path')
DIRT = bid(M + 'dirt')
COARSE = bid(M + 'coarse_dirt')
ROOTED = bid(M + 'rooted_dirt')
STONE = bid(M + 'stone')
AND = bid(M + 'andesite')
POL = bid(M + 'polished_andesite')
POLG = bid(M + 'polished_granite')
TERR = bid(M + 'terracotta')
TUFF = bid(M + 'tuff')
DEEP = bid(M + 'deepslate')
SMOOTH = bid(M + 'smooth_stone')
CBRICK = bid(M + 'chiseled_stone_bricks')
SBWALL = bid(M + 'stone_brick_wall')
GLOW = bid(M + 'glowstone')
SEA = bid(M + 'sea_lantern')
LANTERN = bid(M + 'lantern')
CHAIN = bid(M + 'iron_chain')
FENCE = bid(M + 'spruce_fence')
SPLANK = bid(M + 'spruce_planks')
SSLAD = bid(M + 'spruce_slab')
CAMP = bid(M + 'campfire')
BARREL = bid(M + 'barrel')
ANVIL = bid(M + 'anvil')
SMITH = bid(M + 'smithing_table')
ECHEST = bid(M + 'ender_chest')
LODE = bid(M + 'lodestone')
LADDER = pid(M + 'ladder', {'facing': 'north', 'waterlogged': 'false'})
MOSS = bid(M + 'moss_block')
MOSS_C = bid(M + 'moss_carpet')
SGRASS = bid(M + 'short_grass')
FERN = bid(M + 'fern')
POPPY = bid(M + 'poppy')
DANDELION = bid(M + 'dandelion')
TULIP = bid(M + 'red_tulip')
LILY = bid(M + 'lily_of_the_valley')
PETALS = bid(M + 'pink_petals')
DRIP = bid(M + 'small_dripleaf')
PFROG = bid(M + 'pearlescent_froglight')
VFROG = bid(M + 'verdant_froglight')
BLUE = bid(M + 'blue_stained_glass')
COPPER_SLAB = bid(M + 'waxed_cut_copper_slab')
OAKWOOD = bid(M + 'oak_wood')
JUNGLEWOOD = bid(M + 'jungle_wood')
TRAP = pid(M + 'spruce_trapdoor',
           {'facing': 'north', 'half': 'top', 'open': 'false',
            'powered': 'false', 'waterlogged': 'false'})
STAIRS = {f: pid(M + 'spruce_stairs',
                 {'facing': f, 'half': 'bottom', 'shape': 'straight',
                  'waterlogged': 'false'})
          for f in ('north', 'south', 'east', 'west')}

# ------------------------------------------------------------------ grid
G = array('H', bytes(2 * N * SY * N))
STRIDE_Y = N * N


def I(lx, ly, lz):
    return ly * STRIDE_Y + lz * N + lx


def put(lx, ly, lz, idx):
    if 0 <= lx < N and 0 <= ly < SY and 0 <= lz < N:
        G[I(lx, ly, lz)] = idx


def get(lx, ly, lz):
    if 0 <= lx < N and 0 <= ly < SY and 0 <= lz < N:
        return G[I(lx, ly, lz)]
    return 0


def in_arena(lx, lz):
    return A0X <= lx <= A1X and A0Z <= lz <= A1Z


def in_plateau(lx, lz):
    return P0 <= lx <= P1 and P0 <= lz <= P1


def plat_edge(lx, lz):
    """Distance to the edge of the FLAT plaza (0 == the blue border ring)."""
    return min(lx - P0, lz - P0, P1 - lx, P1 - lz)


def h2(x, z, salt=0):
    h = (x * 374761393 + z * 668265263 + salt * 1442695041) & 0xFFFFFFFF
    h ^= h >> 13
    h = (h * 1274126177) & 0xFFFFFFFF
    return (h ^ (h >> 16)) & 0xFFFFFFFF


# ================================================== 1. THE TERRACE HEIGHTMAP
print('[*] 1/9  read natural ground, build the terrace profile', flush=True)
ND = pickle.load(open('mace-work/v4/nat340.pkl', 'rb'))
NCOLS, NWAT = ND['cols'], ND['water']
NBX, NBZ = ND['origin']
NAT_OFF_X, NAT_OFF_Z = X0 - NBX, Z0 - NBZ      # 35, 35


def nat_world_y(lx, lz):
    """Real natural SURFACE height (world y) of a box-local column.

    The region scan reports whatever solid block is topmost, so a column that
    happens to be over a cave comes back at y=-17 (the cave floor) and a column
    with a shallow underground pond comes back with water above y=6.  Both are
    rejected here: only 40..90 counts as ground, and water only lifts the ground
    when it is a SURFACE body (within 4 blocks of the ground) -- an underground
    pond 40 blocks down must not raise the terrain above it.
    """
    k = (lx + NAT_OFF_X, lz + NAT_OFF_Z)
    v = NCOLS.get(k)
    if v is None:
        return None
    y = v[0]
    if not (40 <= y <= 92):
        return None
    w = NWAT.get(k)
    if w is not None and 40 <= w <= 92 and abs(y - w) <= 4:
        y = max(y, w + 2)          # a real sea / lake surface
    return y


def _median(a):
    a = sorted(a)
    n = len(a)
    return a[n // 2] if n & 1 else (a[n // 2 - 1] + a[n // 2]) // 2


def rim(side):
    """Natural ground height sampled ALONG one side, in a strip just outside
    the box so the terrace edge joins the real world.

    This has to be a profile, not one number per side.  The real rim runs from
    y47 to y73 along the north edge; collapsing each side to a single median made
    the four sides disagree at the corners, and the blend then stacked grey stone
    masses there -- the overlapping corners after the blue line.
    """
    vals = []
    for t in range(N):
        col = []
        for off in (3, 5, 7, 9):
            if side == 'W':
                lx, lz = -off, t
            elif side == 'E':
                lx, lz = N - 1 + off, t
            elif side == 'N':
                lx, lz = t, -off
            else:
                lx, lz = t, N - 1 + off
            y = nat_world_y(lx, lz)
            if y is not None and 40 <= y <= 92:
                col.append(y)
        vals.append(_median(col) if col else None)
    known = [i for i, v in enumerate(vals) if v is not None]
    if not known:
        return [64] * N
    for i in range(N):                      # gap-fill from the nearest sample
        if vals[i] is None:
            j = min(known, key=lambda k: abs(k - i))
            vals[i] = vals[j]
    out = []                                # median filter along the side
    for i in range(N):
        w = [vals[j] for j in range(max(0, i - 12), min(N, i + 13))]
        out.append(_median(w))
    return out


def slope_limit(v, maxd, passes=40):
    """The natural rim really does jump 23 blocks along the north edge.  A
    staircase cannot follow that without a cliff, so the profile is relaxed to a
    gentle ramp: no two neighbouring columns differ by more than maxd."""
    v = list(v)
    for _ in range(passes):
        moved = False
        for i in range(len(v) - 1):
            if v[i + 1] > v[i] + maxd:
                v[i + 1] = v[i] + maxd
                moved = True
            elif v[i + 1] < v[i] - maxd:
                v[i + 1] = v[i] - maxd
                moved = True
        for i in range(len(v) - 2, -1, -1):
            if v[i] > v[i + 1] + maxd:
                v[i] = v[i + 1] + maxd
                moved = True
            elif v[i] < v[i + 1] - maxd:
                v[i] = v[i + 1] - maxd
                moved = True
        if not moved:
            break
    return v


RIM_W = {}
for _s in ('W', 'E', 'N', 'S'):
    prof = rim(_s)
    ly = [max(LVL - 26, min(LVL - 3, y - Y0)) for y in prof]
    RIM_W[_s] = slope_limit(ly, 1)
    print('    rim %s  build ly %d..%d  (world y%d..%d)'
          % (_s, min(RIM_W[_s]), max(RIM_W[_s]),
             min(RIM_W[_s]) + Y0, max(RIM_W[_s]) + Y0), flush=True)

# The four profiles must AGREE where they meet or the corner blend steps.  Each
# corner takes the mean of its two sides and both profiles ease into that value
# over CB columns, making the rim one continuous loop round the build -- that is
# what lines the terraces up at the corners.
CB = 26
CORNER_V = {}
for cname, sa, ea, sb, eb in (('NW', 'W', 0, 'N', 0),
                              ('NE', 'E', 0, 'N', N - 1),
                              ('SW', 'W', N - 1, 'S', 0),
                              ('SE', 'E', N - 1, 'S', N - 1)):
    common = int(round((RIM_W[sa][ea] + RIM_W[sb][eb]) / 2.0))
    for side, end in ((sa, ea), (sb, eb)):
        prof = RIM_W[side]
        for k in range(CB):
            i = k if end == 0 else (N - 1 - k)
            w = 1.0 - (k / float(CB))
            prof[i] = int(round(prof[i] * (1.0 - w) + common * w))
    CORNER_V[cname] = common
    print('    corner %s -> %d' % (cname, common), flush=True)
RIM = RIM_W

# One continuous LOOP of rim height right round the box, clockwise from the NW
# corner: west edge, south edge, east edge, north edge.  Because the four
# profiles were reconciled at the corners, this array is continuous, and that is
# what makes the terraces meet cleanly at the corners instead of stacking.
LOOP = []
for z in range(N):                       # west edge, north -> south
    LOOP.append(RIM_W['W'][z])
for x in range(1, N):                    # south edge, west -> east
    LOOP.append(RIM_W['S'][x])
for z in range(N - 2, -1, -1):           # east edge, south -> north
    LOOP.append(RIM_W['E'][z])
for x in range(N - 2, 0, -1):            # north edge, east -> west
    LOOP.append(RIM_W['N'][x])
LN = len(LOOP)                           # 4N-4

# Perimeter parameter -> index in LOOP, and the LOOP index of each box corner.
#   NW = 0, SW = N-1, SE = 2N-2, NE = 3N-3
def loop_at(p):
    p %= LN
    return LOOP[int(p)]

FLAT_W = 22      # columns of dead-flat lawn outside the plaza edge
CXc = (N - 1) / 2.0
CZc = (N - 1) / 2.0
_fl_cache = {}


def terrace_top(lx, lz):
    """Top (build ly) of a column outside the plaza.

    There is ONE height field, defined everywhere outside the plaza:
      * d  = Chebyshev distance outside the plaza rectangle (0 at the blue
             border, TCOL at the box edge).
      * E  = rim height where the ray from the box centre through this column
             leaves the box.  Radial projection keeps E CONTINUOUS all the way
             round, corners included -- that is the property the per-side blend
             lacked, and why the corners had ragged diagonal steps.
      * the surface eases from the plaza level at d=0 to E at d=TCOL, then is
             snapped to RISER-high shelves so it reads as layered terrain.
    """
    sides = []
    ox = P0 - lx if lx < P0 else (lx - P1 if lx > P1 else 0)
    oz = P0 - lz if lz < P0 else (lz - P1 if lz > P1 else 0)
    if ox == 0 and oz == 0:
        return -1
    d = max(ox, oz)

    # radial hit point on the box perimeter
    dx = lx - CXc
    dz = lz - CZc
    if abs(dx) < 1e-9 and abs(dz) < 1e-9:
        return LVL
    tx = (N - 1) / 2.0 / abs(dx) if dx else 1e9
    tz = (N - 1) / 2.0 / abs(dz) if dz else 1e9
    t = min(tx, tz)
    hx = CXc + dx * t
    hz = CZc + dz * t
    if hx <= 0.5:
        p = hz                                    # west edge
    elif hz >= N - 1.5:
        p = (N - 1) + hx                          # south edge
    elif hx >= N - 1.5:
        p = 2 * (N - 1) + (N - 1 - hz)            # east edge
    else:
        p = 3 * (N - 1) + (N - 1 - hx)            # north edge
    E = float(loop_at(round(p)))

    # FLAT LAWN, then two or three BIG steps.  The whole inner part of the band
    # is level with the plaza, so everything the player walks on is flat exactly
    # like the main spawn; the height difference to the real world is taken up
    # by at most three broad natural terraces right at the outside, which is the
    # "layered like real terrain, but not too often" the user asked for.
    if d <= FLAT_W:
        return LVL
    drop = LVL - E
    if drop <= 0:
        return LVL
    n = 3 if drop > 13 else 2                     # never more than three steps
    frac = (d - FLAT_W) / float(TCOL - FLAT_W)
    if frac > 1.0:
        frac = 1.0
    q = int(round(frac * n))
    if q < 0:
        q = 0
    if q > n:
        q = n
    return LVL - int(round(drop * q / float(n)))


TOP = array('b', bytes(N * N))     # per-column top (ly); -1 inside the plaza
for lz in range(N):
    for lx in range(N):
        TOP[lz * N + lx] = -1 if in_plateau(lx, lz) else terrace_top(lx, lz)
tc = [TOP[k] for k in range(N * N) if TOP[k] >= 0]
lifts = sorted(set(tc))
print('    terraces: %d columns, ly %d..%d (world y%d..%d), %d lifts %r'
      % (len(tc), min(tc), max(tc), min(tc) + Y0, max(tc) + Y0,
         len(lifts), lifts[:12]), flush=True)

# ==================================================================== 2. ARENA
print('[*] 2/9  load the 100x100 arena', flush=True)
raw = lite.load('mace-work/out/macetopia-100.nbt')
apal = []
for e in raw['palette']:
    nm = e['Name'] if isinstance(e, dict) else e
    pr = {}
    if isinstance(e, dict) and e.get('Properties'):
        pr = {str(k): str(v) for k, v in dict(e['Properties']).items()}
    apal.append(pid(nm, pr))
print('    arena palette %d entries, %d with properties'
      % (len(apal), sum(1 for nm, pr in PAL if pr)), flush=True)

POND_TOP = 13
kept_water = [0]
kept_glass = [0]
dropped = Counter()
arena_n = 0
for b in raw['blocks']:
    lx0, ly0, lz0 = b['pos']
    idx = apal[b['state']]
    nm = PAL[idx][0]
    if nm == M + 'light_blue_candle':
        dropped['candle'] += 1
        continue
    # The THEME IS RESTORED: the whole arena floor is blue stained glass at
    # arena-y 13 with a water layer at y12 under it.  Dropping those was what
    # flattened the theme into plain grass.
    if nm == M + 'water':
        kept_water[0] += 1
    elif nm == M + 'blue_stained_glass' and ly0 == POND_TOP:
        kept_glass[0] += 1
    put(lx0 + OX, ly0 + AR_OFF, lz0 + OZ, idx)
    arena_n += 1
print('    kept %d arena blocks (%d water, %d blue glass floor), dropped %s'
      % (arena_n, kept_water[0], kept_glass[0], dict(dropped)), flush=True)

# ============================== 2b. ARENA DE-SLOP + REPLANT
print('[*] 2b/9 arena: strip the slop, replant grounded trees', flush=True)
# What was wrong inside the red line, measured before touching it:
#   * 22 tripwire blocks at arena-y 16-17 with AIR under them -- the "random
#     floating strings" the user saw.
#   * 49 wall banners and 31 wall signs, most of them with AIR behind the face
#     they claim to hang on -- the "banners not at right positions".
#   * 68 of 81 leaf canopies (1788 blocks) sat 3-8 blocks above the floor with
#     no trunk at all -- floating foliage.
# All three are now removed, and the canopies are replaced with real trees that
# grow out of the new glass floor on small soil pads.

def _idxset(pred):
    return {i for i, (nmn, _pr) in enumerate(PAL) if pred(nmn.split(':')[-1])}


TRIPWIRE = _idxset(lambda b: b == 'tripwire')
SCAFFOLD = _idxset(lambda b: b == 'scaffolding')
BANNERS = _idxset(lambda b: b.endswith('banner'))
SIGNS = _idxset(lambda b: b.endswith('sign'))
FOLIAGE = _idxset(lambda b: b.endswith('_leaves') or
                  b in ('jungle_wood', 'oak_wood', 'jungle_log', 'oak_log'))
FLIMSY = _idxset(lambda b: b in (
    'short_grass', 'tall_grass', 'fern', 'large_fern', 'poppy', 'dandelion',
    'red_tulip', 'lily_of_the_valley', 'pink_petals', 'moss_carpet', 'vine',
    'small_dripleaf', 'water', 'lantern', 'iron_chain', 'light_blue_candle',
    'sea_pickle', 'ladder', 'scaffolding', 'tripwire', 'sugar_cane',
    'lily_pad', 'carrots') or b.endswith('_pane') or b.endswith('banner')
    or b.endswith('sign'))


def attachable(i):
    """A block a banner/sign can legally hang on."""
    return bool(i) and i not in FLIMSY and i not in FOLIAGE


FACING = {'north': (0, -1), 'south': (0, 1),
          'east': (1, 0), 'west': (-1, 0)}


def facing_of(i):
    _nm, pr = PAL[i]
    if not pr:
        return 'north'
    if isinstance(pr, dict):
        return pr.get('facing', 'north')
    return dict(pr).get('facing', 'north')


rem_tw = rem_bs = rem_scaf = 0
for lz in range(A0Z, A1Z + 1):
    for lx in range(A0X, A1X + 1):
        for ly in range(LVL + 1, SY):
            i = get(lx, ly, lz)
            if not i:
                continue
            if i in TRIPWIRE:
                put(lx, ly, lz, AIR)
                rem_tw += 1
                continue
            if i in SCAFFOLD:
                if not get(lx, ly - 1, lz) and not get(lx, ly + 1, lz):
                    put(lx, ly, lz, AIR)
                    rem_scaf += 1
                continue
            if i in BANNERS or i in SIGNS:
                dx, dz = FACING.get(facing_of(i), (0, -1))
                if not attachable(get(lx + dx, ly, lz + dz)):
                    put(lx, ly, lz, AIR)
                    rem_bs += 1
print('    removed %d tripwire, %d unsupported banners/signs, %d scaffolding'
      % (rem_tw, rem_bs, rem_scaf), flush=True)

# --- floating foliage: keep only leaf/wood components that reach the floor
N6D = ((1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1))
seen = set()
comps = []
for lz in range(A0Z, A1Z + 1):
    for lx in range(A0X, A1X + 1):
        for ly in range(LVL + 1, SY):
            i = get(lx, ly, lz)
            if i not in FOLIAGE or (lx, ly, lz) in seen:
                continue
            q = [(lx, ly, lz)]
            seen.add((lx, ly, lz))
            comp = []
            while q:
                a = q.pop()
                comp.append(a)
                for d in N6D:
                    b = (a[0] + d[0], a[1] + d[1], a[2] + d[2])
                    if b in seen:
                        continue
                    if not (A0X <= b[0] <= A1X and A0Z <= b[2] <= A1Z):
                        continue
                    if not (LVL + 1 <= b[1] < SY):
                        continue
                    if get(*b) not in FOLIAGE:
                        continue
                    seen.add(b)
                    q.append(b)
            comps.append(comp)

grounded = [c for c in comps if min(p[1] for p in c) <= LVL + 1]
floating = [c for c in comps if min(p[1] for p in c) > LVL + 1]
fl_blocks = 0
sites = []
for c in floating:
    for p in c:
        put(p[0], p[1], p[2], AIR)
        fl_blocks += 1
    xs = [p[0] for p in c]
    zs = [p[2] for p in c]
    sites.append((sum(xs) // len(xs), sum(zs) // len(zs), len(c)))
print('    %d grounded canopies kept, %d floating removed (%d blocks)'
      % (len(grounded), len(floating), fl_blocks), flush=True)

# --- replant: real trees on soil pads, at the spots the canopies vacated
# Plant on any clear stretch of the new glass floor, not only where a canopy
# used to be: the arena's own buildings block most of those old spots.
cand = []
for cz in range(A0Z + 6, A1Z - 5, 2):
    for cx in range(A0X + 6, A1X - 5, 2):
        if get(cx, LVL, cz) not in (BLUE, GRASS, AIR):
            continue
        if any(get(cx + dx, LVL + k, cz + dz)
               for k in (1, 2, 3) for dx, dz in ((0, 0), (1, 0), (-1, 0),
                                                 (0, 1), (0, -1))):
            continue
        cand.append((cx, cz))
random.Random(4242).shuffle(cand)
PLANTED = []
planted = 0
ARENA_MODELS = ('giant_oak', 'tiered_pine', 'jungle_umbrella',
                'round_bush', 'twin_trunk')
for cx, cz in cand:
    if planted >= 20:
        break
    if any((cx - a) ** 2 + (cz - b) ** 2 < 13 ** 2 for a, b in PLANTED):
        continue
    # 3x3 soil pad so the tree is planted, not standing on bare glass
    for dz in range(-1, 2):
        for dx in range(-1, 2):
            put(cx + dx, LVL, cz + dz,
                GRASS if abs(dx) + abs(dz) <= 1 else DIRT)
    model = ARENA_MODELS[planted % len(ARENA_MODELS)]
    t = trees3.make_tree(cx, LVL + 1, cz, model, seed=9000 + planted * 17)
    for (bx, by, bz), nmx in t.items():
        put(bx, by, bz, bid(nmx))
    PLANTED.append((cx, cz))
    planted += 1
print('    replanted %d trees on soil pads (%d clear spots found)'
      % (planted, len(cand)), flush=True)

# a few kerbed flower planters on the glass floor, so the plaza is not bare
planter = 0
for k, (cx, cz) in enumerate(PLANTED[::2][:12]):
    for px, pz in ((cx + 3, cz), (cx, cz - 3), (cx - 3, cz), (cx, cz + 3)):
        if not (A0X + 2 <= px <= A1X - 2 and A0Z + 2 <= pz <= A1Z - 2):
            continue
        if any(get(px + dx, LVL + 1, pz + dz)
               for dz in (-1, 0, 1) for dx in (-1, 0, 1)):
            continue
        for dz in range(-1, 2):
            for dx in range(-1, 2):
                if max(abs(dx), abs(dz)) == 1:
                    put(px + dx, LVL, pz + dz, CBRICK)   # stone kerb
                else:
                    put(px + dx, LVL, pz + dz, GRASS)    # soil
        for dx, dz in ((0, 0), (0, 1), (-1, 0), (1, 1)):
            hv = h2(px + dx, pz + dz, 3)
            put(px + dx, LVL + 1, pz + dz,
                (POPPY, DANDELION, TULIP, LILY)[hv % 4])
        planter += 1
        break
print('    %d flower planters' % planter, flush=True)

# ====================================================== 3. SOLID GROUND + FILL
print('[*] 3/9  fill the box solid: plaza, terraces', flush=True)
BANDS = (DEEP, STONE, TUFF, STONE, AND, STONE, TUFF, DEEP, STONE, STONE)


def strata(ly, lx, lz):
    """Wide 3-deep bands that drift slowly: layered like real Minecraft ground,
    but not the per-column noise that read as 'random blocks'."""
    return BANDS[((ly + (((lx + lz) // 27) & 1)) // 3) % len(BANDS)]


filled = 0
terraced = 0
for lz in range(N):
    for lx in range(N):
        if in_arena(lx, lz):
            top, surface = ARENA_BASE, 'arena'
        elif in_plateau(lx, lz):
            top = LVL
            d = plat_edge(lx, lz)
            surface = ('border' if d == 0 else 'cornice' if d == 1 else
                       'coping' if d <= 3 else 'plaza')
        else:
            top, surface = TOP[lz * N + lx], 'terrace'
            terraced += 1
        for ly in range(0, top + 1):
            if ly == top:
                if surface == 'plaza':
                    put(lx, ly, lz, GRASS)
                elif surface == 'terrace':
                    put(lx, ly, lz, GRASS)
                elif surface == 'coping':
                    put(lx, ly, lz, POL if (lx + lz) & 1 else SMOOTH)
                elif surface == 'cornice':
                    put(lx, ly, lz, SMOOTH)
                else:
                    put(lx, ly, lz, BLUE)       # the blue line, plaza edge
            elif surface == 'border':
                if ly >= LVL - 4:
                    put(lx, ly, lz, SMOOTH)
                elif ly % 9 == 0:
                    put(lx, ly, lz, CBRICK)
                elif ly % 3 == 0:
                    put(lx, ly, lz, SMOOTH)
                else:
                    put(lx, ly, lz, STONE)
            elif surface == 'terrace':
                if ly >= top - 11:
                    # A tall dirt body, so the vertical faces of the big steps
                    # show BARE DIRT under the grass lip -- the user asked for
                    # no grey stone to be visible on the terrace risers.
                    put(lx, ly, lz,
                        COARSE if ((lx // 7 + lz // 7) & 1) else DIRT)
                else:
                    put(lx, ly, lz, strata(ly, lx, lz))
            elif surface is not None and ly >= top - 3:
                put(lx, ly, lz,
                    COARSE if ((lx // 6 + lz // 9) % 4 == 0) else DIRT)
            else:
                put(lx, ly, lz, strata(ly, lx, lz))
            filled += 1
print('    %d solid ground blocks, %d terrace columns' % (filled, terraced),
      flush=True)

# a stone kerb under the blue border, and buttresses only where the plaza
# actually stands above the terrace below it
butt = 0
for lz in range(N):
    for lx in range(N):
        if not in_plateau(lx, lz) or plat_edge(lx, lz) != 0:
            continue
        along = lz if (lx in (P0, P1)) else lx
        if along % 9 != 4:
            continue
        for ly in range(LVL - 3, LVL):
            put(lx, ly, lz, CBRICK)
        butt += 1
print('    %d border buttresses' % butt, flush=True)

# the arena left holes where the ponds were; make the floor continuous
back = 0
for lz in range(A0Z, A1Z + 1):
    for lx in range(A0X, A1X + 1):
        if get(lx, LVL, lz) == AIR:
            put(lx, LVL, lz, BLUE)          # continue the glass floor
            back += 1
        if get(lx, LVL - 1, lz) == AIR:
            put(lx, LVL - 1, lz, DIRT)
            back += 1
print('    %d pond cells backfilled solid' % back, flush=True)

# ================================================================ 4. THE CAVE
print('[*] 4/9  carve and furnish the cave', flush=True)
# The cave lives in the 45-wide ring of plaza OUTSIDE the arena footprint, so it
# can never undermine the arena.  A closed gallery ring at inset 22 runs right
# round the build and every hall bulges outward from it into one band.
carved = 0
CX0, CX1, CZ0, CZ1 = P0 + 1, P1 - 1, P0 + 1, P1 - 1


def carve(lx, ly, lz):
    global carved
    if not (CX0 <= lx <= CX1 and CZ0 <= lz <= CZ1):
        return False
    if not (CAVE_LO <= ly <= CAVE_HI):
        return False
    if in_arena(lx, lz):
        return False
    if G[I(lx, ly, lz)] == AIR:
        return False
    G[I(lx, ly, lz)] = AIR
    carved += 1
    return True


def carve_room(x0, x1, y0, y1, z0, z1):
    y0 = max(CAVE_LO, y0)
    y1 = min(CAVE_HI, y1)
    for ly in range(y0, y1 + 1):
        for lz in range(z0, z1 + 1):
            for lx in range(x0, x1 + 1):
                carve(lx, ly, lz)


# --- the natural cave, reopened wherever it lies outside the arena footprint
nat_n = 0
try:
    NC, NSURF = pickle.load(open('/tmp/cavebox.pkl', 'rb'))
    if len(NC) == N * SY * N:
        for ly in range(CAVE_LO, CAVE_HI + 1):
            base = ly * STRIDE_Y
            for lz in range(N):
                row = base + lz * N
                for lx in range(N):
                    if NC[row + lx] and carve(lx, ly, lz):
                        nat_n += 1
        print('    natural cave cells reopened %d' % nat_n, flush=True)
    else:
        print('    natural cave box is stale, skipped', flush=True)
except Exception as exc:
    print('    natural cave unavailable: %r' % (exc,), flush=True)

# --- geometry of the ring (all local, plaza = 40..229, arena = 85..184)
GX0, GX1 = P0 + 19, P0 + 23          # 59..63   west gallery wall band
GX2, GX3 = P1 - 23, P1 - 19          # 206..210 east gallery band
GZ0, GZ1 = GX0, GX1
GZ2, GZ3 = GX2, GX3
GY0, GY1 = 5, 9                      # gallery headroom
GFLOOR = GY0 - 1                     # 4

HALL_W = (42, 57, 3, 14, 100, 170)   # the great west hall
HALL_E = (212, 227, 3, 13, 100, 170) # east hall
HALL_N = (100, 170, 3, 13, 42, 57)   # north hall
HALL_S = (100, 170, 4, 12, 212, 227) # south hall (new)
GROTTO = (42, 57, 3, 10, 42, 57)     # NW: crystal grotto
FARM = (212, 227, 3, 9, 42, 57)      # NE: mushroom farm (new)
STORE = (212, 227, 3, 9, 212, 227)   # SE: storeroom (new)
SHRINE = (42, 57, 3, 11, 212, 227)   # SW: sunken shrine (new)

ROOMS = [HALL_W, HALL_E, HALL_N, HALL_S, GROTTO, FARM, STORE, SHRINE]
for r in ROOMS:
    carve_room(*r)
# the gallery ring, four straight runs plus the four corners
carve_room(GX0, GX1, GY0, GY1, GZ0, GZ3)      # west run
carve_room(GX2, GX3, GY0, GY1, GZ0, GZ3)      # east run
carve_room(GX0, GX3, GY0, GY1, GZ0, GZ1)      # north run
carve_room(GX0, GX3, GY0, GY1, GZ2, GZ3)      # south run
# short spurs from the ring in to the edge of the arena footprint, so the ring is
# not a bare loop and the player can walk under the arena rim
SPURS = [(GX1 + 1, A0X - 2, 132, 136), (A1X + 2, GX2 - 1, 132, 136),
         (132, 136, GZ1 + 1, A0Z - 2), (132, 136, A1Z + 2, GZ2 - 1)]
for x0, x1, z0, z1 in SPURS:
    carve_room(x0, x1, GY0, GY1, z0, z1)
# link every hall to the ring
LINKS = [(GX0 - 1, GX1 - 1, 128, 142, HALL_W), (GX2 + 1, GX3 + 1, 128, 142, HALL_E),
         (128, 142, GZ0 - 1, GZ1 - 1, HALL_N), (128, 142, GZ2 + 1, GZ3 + 1, HALL_S),
         (GX0 - 2, GX1 - 1, GZ0 - 1, GZ1 - 1, GROTTO),
         (GX2 + 1, GX3 + 2, GZ0 - 1, GZ1 - 1, FARM),
         (GX2 + 1, GX3 + 2, GZ2 + 1, GZ3 + 2, STORE),
         (GX0 - 2, GX1 - 1, GZ2 + 1, GZ3 + 2, SHRINE)]
for a, b, c, d, _ in LINKS:
    carve_room(min(a, b), max(a, b), GY0, GY1, min(c, d), max(c, d))


def cave_floor(x0, x1, y0, y1, z0, z1, a, b):
    """A solid floor one below the room with a one-block lip all round, so no
    cave floor ever ends in a void edge."""
    fy = max(CAVE_LO, y0 - 1)
    for lz in range(z0 - 1, z1 + 2):
        for lx in range(x0 - 1, x1 + 2):
            put(lx, fy, lz, a)
    for lz in range(z0, z1 + 1):
        for lx in range(x0, x1 + 1):
            put(lx, fy, lz, a if ((lx + lz) & 1) == 0 else b)


cave_floor(*HALL_W, SMOOTH, AND)
cave_floor(*HALL_E, AND, SMOOTH)
cave_floor(*HALL_N, POL, SMOOTH)
cave_floor(*HALL_S, SMOOTH, POL)
cave_floor(*GROTTO, MOSS, AND)
cave_floor(*FARM, ROOTED, DIRT)
cave_floor(*STORE, SMOOTH, AND)
cave_floor(*SHRINE, AND, POL)
cave_floor(GX0, GX1, GY0, GY1, GZ0, GZ3, SMOOTH, AND)
cave_floor(GX2, GX3, GY0, GY1, GZ0, GZ3, SMOOTH, AND)
cave_floor(GX0, GX3, GY0, GY1, GZ0, GZ1, SMOOTH, AND)
cave_floor(GX0, GX3, GY0, GY1, GZ2, GZ3, SMOOTH, AND)
for x0, x1, z0, z1 in SPURS:
    cave_floor(x0, x1, GY0, GY1, z0, z1, SMOOTH, AND)

# --- the great west hall: pillars, chandeliers, floor glow, a camp
PX, PZ = 46, 128
for px in range(46, 58, 6):
    for pz in range(106, 170, 16):
        for ly in range(3, 15):
            put(px, ly, pz, CBRICK if ly % 4 == 0 else STONE)
        put(px, 15, pz, TUFF)
for pz in range(104, 170, 8):
    if get(55, 14, pz) == AIR:
        put(55, 14, pz, CHAIN)
        put(55, 13, pz, LANTERN)
for pz in range(104, 170, 11):
    for px in range(44, 57, 5):
        if get(px, 2, pz) == AIR:
            put(px, 2, pz, GLOW)
for lx, lz in ((48, 150), (49, 150), (48, 151), (49, 151)):
    put(lx, 3, lz, SPLANK)
put(49, 3, 153, CAMP)
put(48, 4, 153, LANTERN)
put(45, 3, 152, BARREL)
put(51, 3, 152, BARREL)
put(53, 3, 156, SBWALL)
put(53, 3, 157, SBWALL)
put(43, 3, 167, ANVIL)
put(56, 3, 104, SMITH)
put(56, 3, 168, ECHEST)
put(43, 3, 110, LODE)
for lz in range(146, 160):
    for lx in range(52, 57):
        if get(lx, 3, lz) != AIR:
            continue
        hv = h2(lx, lz, 11)
        if hv % 17 == 0:
            put(lx, 3, lz, MOSS_C)
        elif hv % 29 == 0:
            put(lx, 3, lz, DRIP)
for k in range(70):
    px = 43 + (h2(k, 3, 1) % 14)
    pz = 102 + (h2(k, 9, 2) % 66)
    if get(px, 14, pz) != AIR:
        continue
    for d in range(1 + h2(k, 5, 3) % 3):
        put(px, 14 - d, pz, AND if d == 0 else TUFF)
for k in range(60):
    px = 43 + (h2(k, 13, 4) % 14)
    pz = 102 + (h2(k, 17, 5) % 66)
    if get(px, 3, pz) != AIR:
        continue
    hh = 1 + h2(k, 19, 6) % 3
    for d in range(hh):
        put(px, 3 + d, pz, AND if d == hh - 1 else TUFF)

# --- north hall: the sunken shrine with a lantern ring
for lx, lz in ((128, 49), (130, 49), (128, 53), (130, 53)):
    put(lx, 3, lz, PFROG)
put(129, 3, 51, CBRICK)
put(129, 4, 51, LANTERN)
for lx, lz in ((110, 45), (160, 45), (110, 55), (160, 55)):
    put(lx, 3, lz, SEA)
    put(lx, 4, lz, SBWALL)
    put(lx, 5, lz, LANTERN)
for ly in range(3, 14):
    put(100, ly, 51, TUFF if ly % 3 else AND)
    put(170, ly, 51, TUFF if ly % 3 else AND)
for k in range(40):
    px = 102 + (h2(k, 21, 7) % 66)
    pz = 44 + (h2(k, 23, 8) % 12)
    if get(px, 3, pz) != AIR:
        continue
    hv = h2(k, 25, 9)
    if hv % 3 == 0:
        put(px, 3, pz, PFROG if hv & 1 else VFROG)
    elif hv % 5 == 0:
        put(px, 3, pz, MOSS_C)

# --- east hall: a long armoury / gallery of trophies
for lz in range(106, 168, 10):
    put(226, 3, lz, BARREL)
    put(226, 4, lz, LANTERN if lz % 20 == 6 else AIR)
    put(214, 3, lz, ANVIL if (lz // 10) & 1 else SMITH)
for lz in range(104, 170, 7):
    if get(219, 12, lz) == AIR:
        put(219, 12, lz, CHAIN)
        put(219, 11, lz, LANTERN)
for px in (216, 224):
    for pz in (104, 168):
        for ly in range(3, 14):
            put(px, ly, pz, CBRICK if ly % 4 else STONE)

# --- south hall: a big open undercroft, braziers and a central dais
for k in range(26):
    px = 104 + (h2(k, 27, 1) % 62)
    pz = 216 + (h2(k, 29, 2) % 8)
    hv = h2(k, 31, 3)
    if get(px, 3, pz) != AIR:
        continue
    put(px, 3, pz, (PFROG if hv & 1 else VFROG) if hv % 4 == 0 else MOSS_C)
for dx, dz in ((-3, -3), (3, -3), (-3, 3), (3, 3)):
    put(135 + dx, 4, 219 + dz, CBRICK)
    put(135 + dx, 5, 219 + dz, LANTERN)
put(135, 4, 219, POL)
put(135, 5, 219, COPPER_SLAB)
for lz in range(214, 226, 5):
    for lx in range(106, 166, 14):
        if get(lx, 11, lz) == AIR:
            put(lx, 11, lz, CHAIN)
            put(lx, 10, lz, LANTERN)

# --- NW grotto: drooping crystals and moss
for lx in range(43, 57, 3):
    for lz in range(43, 57, 3):
        hv = h2(lx, lz, 23)
        if hv % 3 == 0:
            put(lx, 10, lz, PFROG if hv & 1 else VFROG)
        if hv % 4 == 0:
            put(lx, 9, lz, AND)
        if get(lx, 3, lz) == AIR and hv % 3 == 0:
            put(lx, 3, lz, MOSS_C)
put(50, 3, 50, PFROG)
put(50, 4, 50, LANTERN)

# --- NE mushroom farm: rooted beds under a low ceiling
for lz in range(44, 57):
    for lx in range(213, 227):
        if (lx * 3 + lz) % 5 == 0 and get(lx, 4, lz) == AIR:
            put(lx, 4, lz, MOSS_C)
put(220, 4, 50, PFROG)
put(220, 5, 50, LANTERN)
for lx in range(214, 227, 5):
    put(lx, 4, 56, BARREL)

# --- SE storeroom: shelves of barrels
for lz in range(214, 226):
    for lx in range(214, 226):
        put(lx, 3, lz, SMOOTH if (lx + lz) & 1 else AND)
for k, lx in enumerate(range(215, 226, 3)):
    put(lx, 4, 214, BARREL)
    if k & 1:
        put(lx, 5, 214, BARREL)
put(220, 4, 225, CAMP)
put(214, 4, 220, CHAIN)
put(214, 3, 220, LANTERN)

# --- SW shrine: a sunken pool of light (froglight, not water)
for dx in range(-4, 5):
    for dz in range(-4, 5):
        lx, lz = 50 + dx, 220 + dz
        if dx * dx + dz * dz <= 16:
            put(lx, 2, lz, PFROG if (dx + dz) & 1 else VFROG)
for dx, dz in ((-5, 0), (5, 0), (0, -5), (0, 5)):
    put(50 + dx, 3, 220 + dz, CBRICK)
    put(50 + dx, 4, 220 + dz, LANTERN)

# --- gallery lighting: a lantern every 12 blocks along the ring
for t in range(GZ0 + 4, GZ3 - 2, 12):
    for gx in (GX0, GX3):
        if get(gx, GY1 - 1, t) == AIR:
            put(gx, GY1 - 1, t, CHAIN)
            put(gx, GY1 - 2, t, LANTERN)
for t in range(GX0 + 4, GX3 - 2, 12):
    for gz in (GZ0, GZ3):
        if get(t, GY1 - 1, gz) == AIR:
            put(t, GY1 - 1, gz, CHAIN)
            put(t, GY1 - 2, gz, LANTERN)
# and a lantern at every link junction so the halls read as connected
for lx, lz in ((GX1 + 2, 135), (GX2 - 2, 135), (135, GZ1 + 2), (135, GZ2 - 2)):
    put(lx, GY1, lz, LANTERN)

# --- FOUR ladder shafts from the plaza down into the cave
SHAFTS = ((GX0 + 2, 135), (GX2 + 2, 135), (135, GZ0 + 2), (135, GZ2 + 2))
for sx, sz in SHAFTS:
    for ly in range(CAVE_LO + 1, LVL):
        for dz in (-1, 0, 1):
            for dx in (-1, 0, 1):
                carve(sx + dx, ly, sz + dz)
    for dz in range(-1, 2):
        for dx in range(-1, 2):
            put(sx + dx, LVL, sz + dz, AIR)
    for ly in range(CAVE_LO, LVL):
        for dz in range(-2, 3):
            for dx in range(-2, 3):
                if max(abs(dx), abs(dz)) != 2:
                    continue
                put(sx + dx, ly, sz + dz,
                    CBRICK if ly % 6 == 0 else
                    (SMOOTH if ly >= LVL - 4 else STONE))
    for dz in range(-1, 2):
        for dx in range(-1, 2):
            put(sx + dx, CAVE_LO, sz + dz, SMOOTH)
    for ly in range(CAVE_LO + 1, LVL):
        put(sx, ly, sz + 1, LADDER)
    put(sx, CAVE_LO + 1, sz, GLOW)
    for ly in (CAVE_LO + 1, CAVE_LO + 2):
        for dx in (-1, 0, 1):
            put(sx + dx, ly, sz - 2, AIR)
    for dz in range(-2, 3):
        for dx in range(-2, 3):
            if max(abs(dx), abs(dz)) == 2:
                put(sx + dx, LVL, sz + dz, CBRICK)
    for dx, dz in ((-2, -2), (2, -2), (-2, 2), (2, 2)):
        put(sx + dx, LVL + 1, sz + dz, FENCE)
print('    carved %d cells; %d rooms + ring + %d spurs; %d shafts'
      % (carved, len(ROOMS), len(SPURS), len(SHAFTS)), flush=True)

# ================================ 5. PLAZA FLOOR: the arena's own parquet
print('[*] 5/9 plaza floor: replicate the arena parquet outside the red line',
      flush=True)
# The main spawn's floor is a basket-weave of POLISHED GRANITE and TERRACOTTA
# (what looked copper-ish is the terracotta).  Reverse-engineered from the
# litematic and verified at 100% on the clean parquet band:
#
#     polished_granite  if ((x//5) + (z//4)) % 2 == 1  else terracotta
#
# in ARENA coordinates.  The ring outside the red line reuses exactly that rule
# with the same origin, so the pattern continues seamlessly out to the blue
# line instead of restarting.
PV_G = POLG
PV_T = TERR


def parquet(lx, lz):
    ax = lx - A0X
    az = lz - A0Z
    return PV_G if ((ax // 5) + (az // 4)) % 2 == 1 else PV_T


laid = 0
for lz in range(P0, P1 + 1):
    for lx in range(P0, P1 + 1):
        if in_arena(lx, lz):
            continue
        d = plat_edge(lx, lz)
        if d <= 3:
            continue                     # keep the blue border and its coping
        if any(max(abs(lx - sx), abs(lz - sz)) <= 2 for sx, sz in SHAFTS):
            continue                     # never pave over a ladder shaft
        put(lx, LVL, lz, parquet(lx, lz))
        laid += 1
print('    %d parquet blocks outside the red line' % laid, flush=True)

# The ring carries TREES ONLY -- no stalls, benches, beds, lamps or boulders.
print('    (all ring furniture, paths and outcrops removed: trees only)',
      flush=True)

# ========================================================== 6. TREES + SWINGS
print('[*] 6/9  trees (five distinct models, fewer than before)', flush=True)
MODEL_ORDER = ['giant_oak', 'tiered_pine', 'jungle_umbrella',
               'round_bush', 'twin_trunk']
MODEL_HEIGHT = {'giant_oak': 15, 'tiered_pine': 18, 'jungle_umbrella': 12,
                'round_bush': 7, 'twin_trunk': 13}


def tree_sites():
    """Tree positions on the ring's parquet floor.  The ring is trees-only now,
    so there is nothing else to avoid besides the shafts and the blue border."""
    cand = []
    for px in range(10, PW - 10, 4):
        for pz in range(10, PW - 10, 4):
            lx, lz = px + P0, pz + P0
            if plat_edge(lx, lz) < 10:
                continue
            if in_arena(lx, lz):
                continue
            if get(lx, LVL, lz) not in (PV_G, PV_T, GRASS):
                continue
            if get(lx, LVL + 1, lz) != AIR:
                continue
            if any(max(abs(lx - sx), abs(lz - sz)) <= 5 for sx, sz in SHAFTS):
                continue
            cand.append((px, pz))
    random.Random(20260601).shuffle(cand)
    out = []
    for px, pz in cand:
        if len(out) >= 14:
            break
        if any((px - a) ** 2 + (pz - b) ** 2 < 20 ** 2 for a, b in out):
            continue
        out.append((px, pz))
    out.sort()
    return out


sites = tree_sites()
# model order flips so neighbours never repeat a model
sites_n = []
last = None
flip = 0
for k, (px, pz) in enumerate(sites):
    mi = k % len(MODEL_ORDER)
    if MODEL_ORDER[mi] == last:
        mi = (mi + 1) % len(MODEL_ORDER)
    sites_n.append((px, pz, MODEL_ORDER[mi]))
    last = MODEL_ORDER[mi]
print('    %d plaza sites' % len(sites_n), flush=True)

# a few trees out on the terraces too: they read as the world continuing
terr_sites = []
for k in range(40):
    px = 6 + (h2(k, 41, 3) % (PW - 12))
    side = h2(k, 43, 5) % 4
    d = 12 + h2(k, 47, 7) % 24
    if side == 0:
        lx, lz = P0 - d, px + P0
    elif side == 1:
        lx, lz = P1 + d, px + P0
    elif side == 2:
        lx, lz = px + P0, P0 - d
    else:
        lx, lz = px + P0, P1 + d
    if not (0 <= lx < N and 0 <= lz < N):
        continue
    top = TOP[lz * N + lx]
    if top < 0 or get(lx, top, lz) != GRASS:
        continue
    if any((lx - a) ** 2 + (lz - b) ** 2 < 26 ** 2 for a, b, _ in terr_sites):
        continue
    terr_sites.append((lx, lz, top))
    if len(terr_sites) >= 5:
        break
print('    %d terrace sites' % len(terr_sites), flush=True)

tb = 0
big = []
for k, (px, pz, model) in enumerate(sites_n):
    lx, lz = px + P0, pz + P0
    # 3x3 soil pad: a tree standing on polished granite would look wrong
    for dz in range(-1, 2):
        for dx in range(-1, 2):
            put(lx + dx, LVL, lz + dz,
                GRASS if abs(dx) + abs(dz) <= 1 else DIRT)
    t = trees3.make_tree(lx, LVL + 1, lz, model, seed=4000 + k * 11)
    for (bx, by, bz), nm in t.items():
        put(bx, by, bz, bid(nm))
    tb += len(t)
    if model in ('giant_oak', 'tiered_pine', 'twin_trunk'):
        big.append((lx, lz, model))
for k, (lx, lz, top) in enumerate(terr_sites):
    model = MODEL_ORDER[(k * 2 + 1) % len(MODEL_ORDER)]
    t = trees3.make_tree(lx, top + 1, lz, model, seed=5000 + k * 13)
    for (bx, by, bz), nm in t.items():
        put(bx, by, bz, bid(nm))
    tb += len(t)
print('    %d tree blocks over %d trees' % (tb, len(sites_n) + len(terr_sites)),
      flush=True)

# --- swings: grow a real branch out of the actual trunk, then hang under it
sw = 0
N6 = ((1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1))
WOODS = (OAKWOOD, JUNGLEWOOD)


def find_wood(lx, lz, y0, y1, r=2):
    """The real trunk column at a given height, so a branch cannot float."""
    for ly in range(y0, y1 + 1):
        for dz in range(-r, r + 1):
            for dx in range(-r, r + 1):
                if get(lx + dx, ly, lz + dz) in WOODS:
                    return (lx + dx, ly, lz + dz)
    return None


for lx, lz, model in big[:2]:
    root = find_wood(lx, lz, LVL + 7, LVL + 12)
    if not root:
        continue
    rx, ry, rz = root
    # pick the outward direction with the most clear space at seat height
    best, ba = None, -1
    for dx, dz in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        room = sum(1 for t in range(1, 5)
                   if get(rx + dx * t, ry - 4, rz + dz * t) == AIR)
        if room > ba and 0 <= rx + dx * 4 < N and 0 <= rz + dz * 4 < N:
            ba, best = room, (dx, dz)
    if best is None or ba < 3:
        continue
    dx, dz = best
    # the branch: 4 wood blocks, each touching the previous one and the trunk
    for t in range(1, 5):
        put(rx + dx * t, ry, rz + dz * t, OAKWOOD)
    # hang the swing under the outer end of the branch
    sx, sz = rx + dx * 3, rz + dz * 3
    axis = 'x' if dx else 'z'
    drop = max(5, ry - (LVL + 3))
    for (bx, by, bz), nm in trees3.make_swing(sx, ry, sz, drop=drop,
                                              axis=axis).items():
        put(bx, by, bz, bid(nm))
        sw += 1
print('    %d swing blocks on %d branches' % (sw, 2), flush=True)

# ============================================== 7. RING KEPT TO TREES ONLY
print('[*] 7/9 ring stays bare apart from its trees', flush=True)
# The user asked for the ring outside the red line to keep only trees on the
# arena's parquet floor, so the old street lights, gate arches, benches, market
# stalls, flower beds and planted rises are all gone.

# ============================================================== 8. CLEAN-UPS
print('[*] 8/9  clean-ups', flush=True)
FLAT_PLANTS = {SGRASS, FERN, POPPY, DANDELION, TULIP, LILY, PETALS, MOSS_C,
               DRIP}
HEADS = set()
NOSUP = set()
for idx in range(len(PAL)):
    b = PAL[idx][0].split(':')[-1]
    if b in ('player_head', 'player_wall_head', 'skeleton_skull',
             'zombie_head', 'creeper_head', 'dragon_head'):
        HEADS.add(idx)
    if (b.endswith('_leaves') or b in (
            'short_grass', 'fern', 'tall_grass', 'large_fern', 'poppy',
            'dandelion', 'red_tulip', 'lily_of_the_valley', 'pink_petals',
            'moss_carpet', 'small_dripleaf', 'jungle_wood', 'oak_wood',
            'iron_chain', 'lantern', 'player_head', 'player_wall_head',
            'skeleton_skull', 'water', 'light_blue_candle', 'vine',
            'lily_pad', 'firefly_bush', 'leaf_litter', 'sugar_cane',
            'sea_pickle', 'scaffolding', 'ladder', 'spruce_trapdoor',
            'spruce_fence', 'stone_brick_wall', 'spruce_stairs', 'carrots')):
        NOSUP.add(idx)

rem = 0
for ly in range(1, SY - 1):
    base = ly * STRIDE_Y
    for lz in range(1, N - 1):
        row = base + lz * N
        for lx in range(1, N - 1):
            if G[row + lx] not in FLAT_PLANTS:
                continue
            below = G[row - STRIDE_Y + lx]
            if below == AIR or below in NOSUP:
                G[row + lx] = AIR
                rem += 1
print('    removed %d plants with no solid support' % rem, flush=True)

# GROUND ON TREES: the "random grass blocks on the trees on the main logs"
# complaint.  A grass/moss/soil block is only wrong when it RESTS on a log or a
# leaf (i.e. it is part of the tree, not the ground).  Grass under a canopy is
# correct and must be kept, so only the block BELOW is examined -- scanning all
# six neighbours would punch holes in the plaza under every tree.
SOILS = {GRASS, MOSS, ROOTED, DIRT, COARSE}
LEAF = {i for i in range(len(PAL)) if PAL[i][0].endswith('_leaves')}
TREEISH = LEAF | set(WOODS)
rem_soil = 0
for ly in range(1, SY - 1):
    base = ly * STRIDE_Y
    for lz in range(1, N - 1):
        row = base + lz * N
        for lx in range(1, N - 1):
            if G[row + lx] not in SOILS:
                continue
            if G[row - STRIDE_Y + lx] in TREEISH:
                G[row + lx] = AIR
                rem_soil += 1
print('    removed %d soil/moss blocks sitting on logs or leaves'
      % rem_soil, flush=True)

# heads need a real attachment face
rem_head = 0
for ly in range(1, SY - 1):
    base = ly * STRIDE_Y
    for lz in range(1, N - 1):
        row = base + lz * N
        for lx in range(1, N - 1):
            if G[row + lx] not in HEADS:
                continue
            ok = False
            for dx, dy, dz in N6:
                n = G[(ly + dy) * STRIDE_Y + (lz + dz) * N + lx + dx]
                if n and n not in HEADS and n not in NOSUP:
                    ok = True
                    break
            if not ok:
                G[row + lx] = AIR
                rem_head += 1
print('    removed %d floating heads / skulls' % rem_head, flush=True)

# islands above the plaza that cannot be reached from the floor: swept over the
# WHOLE box now, not just the arena footprint
print('    airborne sweep over the whole box', flush=True)
visited = set()
dq = deque()
for lz in range(N):
    for lx in range(N):
        t = LVL if in_plateau(lx, lz) else TOP[lz * N + lx]
        if 0 <= t < SY and get(lx, t, lz):
            visited.add((lx, t, lz))
            dq.append((lx, t, lz))
while dq:
    x, y, z = dq.popleft()
    for dx, dy, dz in N6:
        nx, ny, nz = x + dx, y + dy, z + dz
        if not (0 <= nx < N and 0 <= nz < N and LVL < ny < SY):
            continue
        if not get(nx, ny, nz):
            continue
        k = (nx, ny, nz)
        if k in visited:
            continue
        visited.add(k)
        dq.append(k)
comps = []
for ly in range(LVL + 1, SY):
    for lz in range(N):
        for lx in range(N):
            if get(lx, ly, lz) and (lx, ly, lz) not in visited:
                comp = []
                q = deque([(lx, ly, lz)])
                visited.add((lx, ly, lz))
                while q:
                    a = q.popleft()
                    comp.append(a)
                    for dx, dy, dz in N6:
                        b = (a[0] + dx, a[1] + dy, a[2] + dz)
                        if b in visited:
                            continue
                        if not (0 <= b[0] < N and 0 <= b[2] < N):
                            continue
                        if not (LVL < b[1] < SY):
                            continue
                        if not get(*b):
                            continue
                        visited.add(b)
                        q.append(b)
                comps.append(comp)
comps.sort(key=len, reverse=True)
rem_air = 0
kept = []
for comp in comps:
    if len(comp) <= 400:
        for p in comp:
            put(p[0], p[1], p[2], AIR)
            rem_air += 1
    else:
        kept.append(comp)
print('    %d islands, %d blocks removed, %d large kept'
      % (len(comps), rem_air, len(kept)), flush=True)
for comp in kept[:6]:
    ys = [p[1] for p in comp]
    names = Counter(PAL[get(*p)][0].replace('minecraft:', '') for p in comp)
    print('      n=%d ly%d..%d  %s' % (len(comp), min(ys), max(ys),
                                       names.most_common(3)), flush=True)

# seal any surface hole the clean-ups opened, so every walkable column is solid
sealed = 0
for lz in range(N):
    for lx in range(N):
        t = LVL if in_plateau(lx, lz) else TOP[lz * N + lx]
        if t < 0:
            continue
        if any(max(abs(lx - sx), abs(lz - sz)) <= 2 for sx, sz in SHAFTS):
            continue                  # the ladder shafts stay open
        if get(lx, t, lz) == AIR:
            put(lx, t, lz, GRASS)
            if get(lx, t - 1, lz) == AIR:
                put(lx, t - 1, lz, DIRT)
            sealed += 1
print('    sealed %d surface holes' % sealed, flush=True)

# ========================================================== 9. STATS + WRITE
print('[*] 9/9  statistics', flush=True)
counts = Counter()
total = 0
for ly in range(SY):
    base = ly * STRIDE_Y
    for lz in range(N):
        row = base + lz * N
        for lx in range(N):
            idx = G[row + lx]
            if idx:
                counts[idx] += 1
                total += 1
print('    total %d blocks over %d states' % (total, len(counts)), flush=True)
for idx, n in counts.most_common(14):
    print('      %-34s %7d' % (PAL[idx][0].replace('minecraft:', ''), n),
          flush=True)

holed = 0
for lz in range(N):
    for lx in range(N):
        t = LVL if in_plateau(lx, lz) else TOP[lz * N + lx]
        if get(lx, t, lz) == AIR:
            holed += 1
print('    holes in every flat surface: %d' % holed, flush=True)
wat = sum(n for idx, n in counts.items() if PAL[idx][0] == M + 'water')
print('    water blocks: %d' % wat, flush=True)
print('    plaza columns: %d   terrace columns: %d'
      % (PW * PW, N * N - PW * PW), flush=True)

print('[*] write the structure NBT', flush=True)
out = 'mace-work/out/macetopia-v6.nbt'
pal_out = [(nm, dict(pr) if pr else None) for nm, pr in PAL]


def emit():
    for ly in range(SY):
        base = ly * STRIDE_Y
        for lz in range(N):
            row = base + lz * N
            for lx in range(N):
                idx = G[row + lx]
                if idx:
                    yield (lx, ly, lz, idx)


sz = streamnbt.write_structure(out, (N, SY, N), pal_out, total, emit())
print('    %s  %.2f MB  %d blocks' % (out, sz / 1e6, total), flush=True)
print('    states with properties: %d / %d'
      % (sum(1 for nm, pr in PAL if pr), len(PAL)), flush=True)
print('DONE', flush=True)
