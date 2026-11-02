# Pasting with FAWE: the four rules, and the arithmetic proof of a perfect paste

## Rule 1 - `//paste` anchors at `//pos1`, the minimum corner

```
//pos1 <x> <y> <z>        <- this becomes the schematic's local (0,0,0)
//schem load <name>
//paste
```

World coordinate of a local block = `pos1 + local`.

**Do not use `//paste -o`.** That pastes at the clipboard *origin*, which for a freshly
loaded schematic is the server's saved origin — in this project it dropped a whole strip
at world `(0,0,0)`. Plain `//paste` is the only safe form.

**Set `pos1` from the destination, never from the edge of what you are replacing.** An
off-by-45 anchor once produced a build that was "all misaligned" and had to be deleted:
verify by reading the region back, not by eyeballing the console output.

## Rule 2 - `//paste` is DESTRUCTIVE

Cells the schematic does not define are filled with `minecraft:structure_void`, not
left alone. That is how you get invisible junk that stops blocks being placed and
mangles lighting.

Always follow the paste with:

```
//pos1 <x1> <y1> <z1>
//pos2 <x2> <y2> <z2>     <- the full pasted box
//replace minecraft:structure_void minecraft:air
```

`//count minecraft:structure_void` afterwards must return **0**.

## Rule 3 - the box volume is a checksum, so use it

This is the single most valuable verification in the whole workflow, and it costs one
command.

```
box volume      = sx * sy * sz
your blocks     = the block count you wrote
void to clear   = box volume - your blocks
```

`//replace minecraft:structure_void minecraft:air` prints:

```
<N> blocks have been replaced.
```

**If `N` equals `box volume - your blocks`, the paste is provably complete: every cell
in the box is accounted for.** If it differs, something is wrong — a stale schematic was
loaded, the paste was interrupted, or the box is not what you think.

Worked example from a real run:

```
270 * 98 * 270 = 7,144,200
blocks written = 2,126,796
expected void  = 5,017,404      <- server said "5017404 blocks have been replaced"
```

## Rule 4 - region files lie until they are flushed

After pasting, `save-all flush`, then read the world back. But note:

- **Region files lag behind the server.** `//count` reads live memory and is
  authoritative; a freshly downloaded `.mca` may still show the *previous* build. Do
  not conclude "the paste failed" from a stale file.
- A downloaded region can be byte-identical in size to the pre-paste one and still be
  stale. Compare block counts, not file size.
- `save-all flush` sometimes prints `FAIL` in a tool's summary while still succeeding —
  check for `Saved the game` in the log output instead of the exit status.

Verify with both:
1. `//count <block>` for a few distinctive blocks vs the source count (**exact match
   expected**), and
2. `scripts/diff_live_vs_nbt.py` on the re-downloaded regions, if you want per-block
   proof.

## Console automation quirks (Pterodactyl/FAWE)

- Command output is sometimes **offset by one**: each result appears after the next
  command's echo. When mapping counts to commands, align them from the *end* or run one
  command per session.
- `//count` occasionally returns nothing at all. Re-run it alone rather than
  interpolating a value.
- Paths: `//schem load` resolves names inside `plugins/FastAsyncWorldEdit/schematics/`.
  Upload there, no absolute path.

## Ready-made command lists

`scripts/paste_commands.py` emits the three JSON command files this project used:

```bash
python3 scripts/paste_commands.py --pos 195 42 259 --size 270 98 270 \
        --schem macetopia-v6 --outdir cmds/
# cmds/p6a.json  load + paste
# cmds/p6b.json  selection + void clear
# cmds/p6c.json  save + counts
```

Run them as **separate** console sessions. A single session that pastes *and* waits for
the void clear times out on large builds (2M+ blocks).
