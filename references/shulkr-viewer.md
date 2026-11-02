# Rendering on Shulkr (the human-facing screenshot)

<https://www.shulkr.com/en/viewer> — a browser schematic viewer. Accepts
`.litematic`, `.schem`, `.nbt` (vanilla structure) and `.mcstructure`, up to 32 MB,
renders in WebGL fully client-side ("your file never leaves your device").

`scripts/shulkr_shot.mjs` drives it: launch Chromium, open the viewer, hand the file to
its file input, wait, screenshot.

```bash
node scripts/shulkr_shot.mjs --nbt out.nbt --out renders/shulkr.png
node scripts/shulkr_shot.mjs --nbt out.nbt --out r.png --wait 30000 --headless
```

## Two failures that look like "the viewer is broken"

Both were hit and diagnosed on a real run. Neither is a problem with your NBT — the page
had already parsed the file and read the palette in both cases.

### 1. `--disable-gpu` kills the 3D view

With the GPU disabled, the page loads, greys through `Reading file` / `Parsing NBT` /
`Building block palette`, and then reports:

```
Couldn't load this build in 3D
```

This is a **WebGL** failure, not a data failure. It reproduces with the `.litematic` the
same build was made from, which is the tell: if two different formats fail identically,
the problem is the renderer, not the file.

Do **not** pass `--disable-gpu`. Use software WebGL instead:

```
--use-gl=angle --use-angle=swiftshader --enable-unsafe-swiftshader --ignore-gpu-blocklist
```

### 2. Filling the file input before hydration throws the file away

The viewer is a client-side app. If you set the file input immediately after
`Page.navigate`, React mounts over your input and the build silently never loads — the
screenshot comes back showing the landing page with a drop zone, which is easy to
mistake for "it worked".

Wait ~10 s for the input to exist, set the files, then dispatch **both** `input` and
`change` (React listens for `input`):

```js
i.dispatchEvent(new Event('input',  { bubbles: true }))
i.dispatchEvent(new Event('change', { bubbles: true }))
```

### Always log the page state

Take the screenshot *and* print the page text, so a landing page or an error is never
reported as a successful render:

```
page state: shulkr Schematics Viewer ... flat-plaza.nbt ... 48 × 9 × 48 20,736 blocks Orbit Plan Explore
```

If that string contains `Couldn't load this build in 3D` or shows no dimensions, the
render failed — say so instead of attaching the image.

## What the numbers mean

Shulkr reports the trimmed content bounds, not your NBT `size`. A structure declared
`48 x 20 x 48` with its floor at ly 8 shows as `48 × 9 × 48`. Block counts must still
match exactly (`20,736 blocks`).

## DataVersion is not the problem

Tested: `5023` (1.21.9) and `3465` (1.20.1) behave identically. Do not "fix" a Shulkr
failure by downgrading `DataVersion`.

## Fallback

`scripts/render3d.py` and `scripts/chunk_sheet.py` are local and dependency-light (Pillow
only). Use them for iteration; use Shulkr for the screenshot you show a human.
