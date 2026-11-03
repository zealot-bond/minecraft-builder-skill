# Build Design Plan — Skyhaven Box-in-Box PvP Spawn (`100x100`)

## 1. Brief & Theme
- **Dimensions:** `100 × 64 × 100` (`x = 0..99`, `z = 0..99`)
- **Layout Architecture ("Box Inside Box"):**
  - **Inner `50x50` Safezone Spawn (`x = 25..74`, `z = 25..74`):** Flattened, airy `vanilla_plus` haven with open free-roam courtyard, central compass gazebo, compact medieval cottages & merchant stalls (`assets/houses/`, `assets/stalls/`), crystal fishing pond with arched bridge & pier, custom oak/sakura trees + tree swing, PvP enchant/anvil prep station, campfire rest spot, small rocks, and **3 floating Hot Air Balloons** overhead.
  - **Inner Border (`x = 25, 74`, `z = 25, 74`):** Unbroken flush `red_concrete` Safezone/PvP boundary line with red corner & exit marker posts.
  - **Outer `100x100` PvP Warzone Ring (`25`-block belt surrounding the `50x50`):** Flat `y = 10` combat floor with flush inlaid stone-brick/prismarine battle lanes, combat ring, and 4 corner duel/KOTH medallions, accented simply with 8 outer custom oak trees and tactical rock cover (~85% open fighting space).
  - **Outer Border (`x = 0, 99`, `z = 0, 99`):** Continuous `blue_concrete` perimeter line topped by a 3-block-tall `blue_stained_glass` arena barrier wall with soul-lantern pylons.
- **Theme:** `vanilla_plus` (spruce, oak, stone bricks, diorite, dark prismarine, moss, red safezone border, blue stained-glass warzone border).

## 2. Inspiration Digest & Playability Rules
- **Flattened, Combat-Ready Relief:** Both the safezone courtyard and the `25`-block PvP combat ring sit at `y = 10` across `x = 5..94, z = 5..94` so players can sprint, kite, and strafe across the Red Line in all 360° without getting snagged on ledges, while a gentle 3-block stadium rim (`d_edge <= 4`) frames the outer Blue Glass wall.
- **Zero Hitbox Clutter in PvP:** Tall double-grass is omitted in the PvP ring so sword/fishing-rod combat sightlines stay clean; floor patterns (`stone_bricks`, `mossy_stone_bricks`, `dark_prismarine`, `blue_stained_glass` over `sea_lantern`) are 100% flush with the `y = 10` turf.
- **Airy Safezone Breathing Room:** Compact `9x12x7` cottages (`house_65`, `house_212`) + one `19x26x15` NW Guild Hall (`house_188`) leave ~55% of the `50x50` interior as open free-roam plaza, lawn, and water.
- **Vertical Sky Interest:** Three striped Montgolfier Hot Air Balloons at staggered altitudes (`y = 33..56`) crown the skyline without occupying ground space.

## 3. Zone Grid (`5 × 5` cells of `20 × 20` blocks)
```
D W N W D
W G A C W
N R S P N
W T K F W
D W N W D
```
- `S` (`[2,2]`): Central Spawn Gazebo & Open Free-Roam Courtyard (`(50, 11, 50)`)
- `G` (`[1,1]`): NW Guild Tavern (`house_188`), Stall & Red Corner Post
- `A` (`[2,1]`): North Safezone Promenade, Balloon #3 Overhead & Red Exit
- `C` (`[3,1]`): NE Guild Cottage (`house_212`), Stall & Wishing Fountain
- `R` (`[1,2]`): West Free-Roam Lawn, Balloon #1 Overhead & Red Exit
- `P` (`[3,2]`): East Pond Overlook, Blossom Tree & Balloon #2 Overhead
- `T` (`[1,3]`): SW Brick Cottage (`house_65`), Swing Oak & Enchant/Anvil Prep
- `K` (`[2,3]`): South Campfire Healing Nook & Red Exit
- `F` (`[3,3]`): SE Crystal Fishing Pond, Arched Bridge & Fishing Pier
- `D` (4 outer corners): PvP Corner Duel / KOTH Medallions + Blue Glass Corner Pylons
- `N` (4 cardinal outer cells): PvP Cardinal Stone Battle Lanes + Tactical Rock Cover
- `W` (8 outer flank cells): Open PvP Warzone Turf, Flush Combat Ring, Custom Oaks & Boulders
