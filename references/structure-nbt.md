# Vanilla structure NBT: the exact byte layout, and the bug that eats a file

The format FAWE loads with `//schem load <name>.nbt` is the **vanilla structure**
format (not WorldEdit `.schem`). It is gzip-compressed NBT:

```
TAG_Compound ""                       root, unnamed
├── TAG_Int "DataVersion"             5023 == MC 1.21.9
├── TAG_List "size"  of TAG_Int       3 ints: [sx, sy, sz]
├── TAG_List "palette" of TAG_Compound
│     └── TAG_String "Name"           "minecraft:stone"
│         TAG_Compound "Properties"   optional
│             TAG_String "axis" = "y" ...
└── TAG_List "blocks" of TAG_Compound
      └── TAG_List "pos" of TAG_Int   3 ints, local coords
          TAG_Int "state"             index into palette
```

## THE BUG: a compound inside a TAG_List has no type byte and no name

This is the one that silently corrupts everything, and it is easy to get wrong because
the *root* compound does have a type byte (`0x0a`) and a name.

```python
# WRONG - 3 stray bytes per block. The file is 3*nbytes too long and unparseable.
per_block += b'\x0a' + b'\x00\x00'      # type + empty name

# RIGHT - an entry is a bare payload: no 0x0a, no name length, no name.
per_block += b''                        # then straight into the named tags
```

The symptom is a parse error whose byte count is suspiciously small:

```
struct.error: unpack_from requires a buffer of at least 44302730 bytes
              ... (actual buffer size is 44302729)
```

One byte short for a 1-block change, three bytes per block for a big file. If you see
an off-by-3n-ish error, this is why.

**Always assert the round trip before using a file:**

```bash
python3 scripts/nbt_query.py out.nbt --summary     # must print the same block count
```

## Palette rules

1. **Put air at index 0.** `assert AIR == 0`. FAWE's destructive paste fills
   unspecified cells with `structure_void`; a palette that starts with stone makes
   "empty" indistinguishable from real blocks when you debug.
2. **Deduplicate with a real key.** `(name, tuple(sorted(props.items())))` — the
   same block with properties in a different order is the same state:
   ```python
   def pid(name, props=None):
       key = (name, tuple(sorted((props or {}).items())))
       i = PAL_IX.get(key)
       if i is None:
           i = len(PAL); PAL_IX[key] = i; PAL.append(key)
       return i
   ```
3. **Never emit a block you did not mean to place.** A common corruption is writing
   whole *sections* of air into the `blocks` list "for completeness" — that costs
   file size and makes the destructive paste slower, with no benefit.

## DataVersion

`DataVersion` is the world's data version. Get it from the target world, do not guess:

```bash
python3 scripts/read_region.py --dataversion
```

Known values in this repo's experience: **5023 = Minecraft 1.21.9 (Paper 26.3)**.
If it is wrong, FAWE may refuse the schematic or upgrade/repair blocks in surprising
ways.

## Coordinate system

- `pos` is **local**, `0 <= pos < size`. The validator rejects anything outside.
- `build ly 0` == the world Y you anchor `//pos1` at. Keep a single constant for the
  offset and derive every coordinate from it (`Y0`), or you will drift:
  ```python
  def put(lx, ly, lz, idx):          # build-local
      if 0 <= lx < N and 0 <= ly < SY and 0 <= lz < N:
          G[ly * N * N + lz * N + lx] = idx
  world_y = Y0 + ly
  ```
- **The paste anchors at `//pos1` = the minimum corner.** So world = `pos1 + local`.

## Memory: do not build block compounds

A 270x270x98 build is 7.1M cells. Python dicts of tuples, or lists of per-block
compound objects, will exhaust RAM long before the build is finished.

Use a flat `array('H')` palette grid and stream the NBT in one pass:

```python
G = array('H', bytes(2 * N * SY * N))         # 14 MB for 7.1M cells
def I(lx, ly, lz): return ly * N * N + lz * N + lx
```

`scripts/streamnbt.py` writes the palette and the block list incrementally, so peak
memory is the grid plus one block of buffer.

## Empty regions are not free

The writer is streaming; the `blocks` count in the header must be **known before**
writing the list. Count first (one pass over the grid), then stream (second pass):

```python
total = sum(1 for i in G if i)
streamnbt.write_structure(out, (N, SY, N), pal_out, total, emit())
```
