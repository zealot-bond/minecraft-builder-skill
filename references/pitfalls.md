# Pitfalls: environment and tooling traps

These are not Minecraft problems, they are the things that make an agent *believe* it
did work it did not do. Each one cost real time in the project this skill came from.

## Shell and process control

**Never `pkill -f <pattern>` where the pattern appears in your own command line.**
`pkill -f "chrome-linux64/chrome"` matches the `bash -c` process running that very
command and kills it — the job silently dies and the log stays empty. Use a bracketed
pattern so the regex cannot match itself:

```bash
pkill -f "chrome-linux64/[c]hrome"
```

**Long jobs must be detached, not backgrounded.**
`nohup cmd &` inside a tool call still shares the process group; when the call hits its
timeout the whole group is killed and you get a 0-byte log. Do this instead:

```bash
setsid nohup timeout 500 cmd > /tmp/x.log 2>&1 < /dev/null & disown
sleep 3; echo launched        # return immediately, poll in a later call
```

**Never `head`-pipe a generator.** The pipeline closes the writer and the generator dies
with `SIGPIPE` at the first buffer — use a plain redirect to a file.

**Poll, do not block.** A tool call that sleeps longer than its timeout takes the job
with it. Sleep in short increments in separate calls and `tail` the log.

## Browsers and panels

**`earlyoom` will kill your browser.** On a small machine earlyoom prefers `chrome`,
`node`, `python3`. A headful Chromium needs ~300-400 MB; if `free -m` shows < 600 MB
available, launches fail with a generic `chromium failed to start` after the 60 s
debug-port wait. Check memory before blaming the code.

**Cloudflare-protected panels need a real (headful) browser** carrying `cf_clearance`.
Plain `curl` with an API key returns `Cloudflare blocked the call`. The panel API has to
be driven from inside the browser page.

**The panel can hiccup.** `panel/cloudflare not ready` is transient — wait 25-45 s and
retry rather than changing the approach.

**SFTP and the panel are different transports.** Use SFTP for file upload (no Cloudflare
in the way) and the browser/panel only for power actions and console commands.

## FAWE console

- Output can be **offset by one command**; a result printed under `[4]` may belong to
  command `[3]`. Match counts from the end of the log, or run one command per session.
- `//count` sometimes prints nothing. Do not fill in a value by assumption.
- `save-all flush` can report `FAIL` while having saved successfully — look for
  `Saved the game`.
- Split big operations across sessions: a 2M-block paste plus a 7M-cell void clear in one
  session times out.

## NBT and formatting

- A compound inside a `TAG_List` has **no type byte and no name** — see
  `structure-nbt.md`. Three stray bytes per block is a truncated-looking file.
- `array('H')` for the grid, `array('b')` for a `-1`-carrying heightmap.
- `PAL` entries are `(name, props_tuple)`, not dicts.
- Palette index 0 should be `air`; assert it.

## Region files

- Region `r.0.0` stops at `z = 511`. A box reaching `z >= 512` needs `r.0.1` as well.
- Sections must be read in **ascending `Y`**, last write wins, or the "surface" is the
  lowest solid block (`y = -49`, no water, broken medians).
- Downloaded regions lag the running server. `//count` is authoritative; a stale file is
  not evidence of a failed paste.
- Identical file size does **not** mean identical contents.

## Design traps (they look like style choices, they are bugs)

- **Width consumed by the flat area** -> a retaining wall instead of a blend. Check
  `box_width > flat_width` before generating.
- **`min()` instead of `max()`** for distance outside a rectangle -> cliff at the seam.
- **Per-side medians** instead of one continuous rim loop -> stacked stone at corners.
- **Quantised risers on every side** -> wedding cake.
- **Soil body shallower than the riser** -> grey stone bands on a "dirt" face.
- **A 6-neighbour support rule for soil** -> holes under every tree.
- **`tripwire` placed by a schematic** -> floating strings in mid-air.

## Reporting honestly

- Never say a build is live because a paste command was accepted. Say it is live when a
  `//count` matches the source **and** the box arithmetic balances.
- If a check could not run (stale region, panel down), say so explicitly instead of
  implying it passed.
- Quote measured numbers (counts, heights, component counts), not adjectives.
