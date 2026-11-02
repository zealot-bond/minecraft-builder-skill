# Minecraft Builder Recipe API

This file documents the helper API exposed to recipe files by `scripts/run-build.mjs`.

Recipes are ESM modules that export a default function or named `build` function:

```js
export default function build(api) {
  const structure = api.createStructure([16, 8, 16])
  api.fill(structure, [0, 0, 0], [15, 0, 15], 'minecraft:stone')
  return { structure, metadata: { name: 'example' } }
}
```

## Recipe Return Value

Supported return values:

- `Structure`
- `{ structure, metadata? }`

Supported `metadata` fields:

- `name?: string`
  - Used for the output filename unless `--name` is provided.

Unsupported:

- Returning multiple structures.
- Returning raw NBT instead of a Lodestone `Structure`.
- Returning async iterables or streaming build output.

## CLI Options

Usage:

```bash
node scripts/run-build.mjs <recipe.mjs> [--out-dir <dir>] [--name <name>] [--data-version <number>] [--compression gzip|zlib|none] [--no-block-state-updates] [--json]
```

Supported options:

- `<recipe.mjs>`
  - Required path to an ESM recipe.
- `--out-dir <dir>` or `--out-dir=<dir>`
  - Output directory.
  - Default: `minecraft-builds/<name>`.
- `--name <name>` or `--name=<name>`
  - Overrides output filename.
  - Slugified to lowercase ASCII with `-` separators.
- `--data-version <number>` or `--data-version=<number>`
  - Positive integer.
  - Default: `3465`.
- `--compression gzip|zlib|none` or `--compression=<mode>`
  - Default: `gzip`.
- `--no-block-state-updates`
  - Disables Lodestone `updateBlockStates()` before export.
- `--json`
  - Prints JSON summary.
- `-h`, `--help`
  - Prints usage.

No other CLI options are read.

## `api`

Fields exposed to recipes:

- `api.lodestone`
- `api.Structure`
- `api.BlockState`
- `api.NbtByte`
- `api.NbtCompound`
- `api.NbtDouble`
- `api.NbtFloat`
- `api.NbtInt`
- `api.NbtList`
- `api.NbtLong`
- `api.NbtShort`
- `api.NbtString`
- `api.createStructure`
- `api.normalizeBlock`
- `api.setBlock`
- `api.fill`
- `api.hollowBox`
- `api.line`
- `api.sphere`
- `api.cylinder`
- `api.createBlockNbt`

For Lodestone class details, search `references/lodestone/`.

## Tuples and Bounds

All positions and sizes use three-number arrays:

- `[x, y, z]`

Behavior:

- Values are converted with `Number`.
- Values must be finite.
- Values are truncated with `Math.trunc`.
- Block positions must be inside the structure.

Unsupported:

- Two-number tuples.
- Four-number tuples.
- Non-finite values.
- Placing blocks outside the structure.

## Blocks

`block` parameters accept:

- `string`
  - Block id: `minecraft:stone`
  - Block-state string: `minecraft:oak_stairs[facing=east,half=bottom,shape=straight]`
- `BlockState`
- object with `name` or `id`
  - `{ name: 'minecraft:stone' }`
  - `{ id: 'minecraft:stone', properties: { ... } }`

Property behavior:

- Explicit `properties` arguments override parsed string/object properties.
- Properties must be string-valued maps.

Unsupported:

- Automatic validation that a block id exists.
- Automatic validation that properties are valid for a block id.
- Non-string property values.

## `createStructure(size)`

Creates a Lodestone `Structure`.

Supported fields:

- `size: [number, number, number]`
  - Must contain positive finite numbers.
  - Values are truncated.

Return value:

- `Structure`

## `normalizeBlock(block, properties?)`

Normalizes a block input.

Supported fields:

- `block: string | BlockState | { name?: string, id?: string, properties?: Record<string, string> }`
- `properties?: Record<string, string>`

Return value:

```js
{
  name: string,
  properties: Record<string, string> | undefined
}
```

Unsupported:

- Objects without `name` or `id`.
- Plain numbers, booleans, arrays, or null.

## `setBlock(structure, pos, block, properties?, nbt?)`

Places or replaces one block.

Supported fields:

- `structure: Structure`
- `pos: [number, number, number]`
- `block: string | BlockState | object`
- `properties?: Record<string, string>`
- `nbt?: NbtCompound`

Return value:

- `structure`

Validation:

- Fails if `pos` is outside the structure.

## `fill(structure, from, to, block, properties?, nbt?)`

Fills every block in an axis-aligned inclusive box.

Supported fields:

- `from: [number, number, number]`
- `to: [number, number, number]`
- `block`
- `properties?`
- `nbt?`

Behavior:

- Inclusive of both endpoints.
- Automatically uses min/max per axis.
- Calls `setBlock` for each position.

Unsupported:

- Hollow fill. Use `hollowBox`.
- Non-axis-aligned fill.

## `hollowBox(structure, from, to, block, properties?, nbt?)`

Fills only the surface of an axis-aligned inclusive box.

Behavior:

- A position is on the surface if any coordinate equals the min or max for its axis.
- Calls `setBlock` for each surface position.

Unsupported:

- Different blocks for edges/corners/faces.
- Interior fill.

## `line(structure, from, to, block, properties?, nbt?)`

Draws a straight voxel line.

Behavior:

- Number of steps is the largest absolute axis delta.
- Uses linear interpolation and `Math.round`.
- Deduplicates repeated rounded positions.

Unsupported:

- Curves.
- Anti-aliased or weighted lines.
- Bresenham-specific guarantees.

## `sphere(structure, center, radius, block, options?)`

Places a voxel sphere.

Supported fields:

- `center: [number, number, number]`
- `radius: number`
  - Must be positive and finite.
- `block`
- `options.filled?: boolean`
  - Default: `true`.
- `options.properties?: Record<string, string>`
- `options.nbt?: NbtCompound`

Behavior:

- Includes positions with squared distance `<= radius * radius`.
- Hollow spheres use an inner radius of `radius - 1`.

No other option fields are read.

## `cylinder(structure, center, radius, yRange, block, options?)`

Places a vertical voxel cylinder.

Supported fields:

- `center: [number, number, number]`
- `radius: number`
  - Must be positive and finite.
- `yRange: [number, number] | number`
  - Array form means `[minY, maxY]`.
  - Number form means `[centerY, number]`.
- `block`
- `options.filled?: boolean`
  - Default: `true`.
- `options.properties?: Record<string, string>`
- `options.nbt?: NbtCompound`

Behavior:

- Includes positions with horizontal squared distance `<= radius * radius`.
- Hollow cylinders use an inner radius of `radius - 1`.
- Inclusive of both min and max Y.

No other option fields are read.

## `createBlockNbt(object)`

Creates an `NbtCompound` from a plain object.

Supported JS values:

- `NbtTag` instances
- `string` -> `NbtString`
- `boolean` -> `NbtByte(1 | 0)`
- integer `number` -> `NbtInt`
- non-integer `number` -> `NbtDouble`
- array -> `NbtList` after converting each entry
- plain object -> nested `NbtCompound`

Unsupported:

- `null`
- `undefined`
- `bigint`
- functions
- symbols
- mixed-type `NbtList` values that violate NBT list homogeneity

Example:

```js
const chestNbt = api.createBlockNbt({
  id: 'minecraft:chest',
  CustomName: '{"text":"Supplies"}',
})
api.setBlock(structure, [1, 1, 1], 'minecraft:chest', { facing: 'north' }, chestNbt)
```

## Export Behavior

Before writing the `.nbt`, the runner:

1. Clones the recipe structure when block-state updates are enabled.
2. Calls `updateBlockStates()` on the clone.
3. Writes vanilla structure NBT with the selected data version and compression.
4. Reads the bytes back through Lodestone.
5. Fails if round-trip size or block count changes.

Supported summary fields:

- `name`
- `dataVersion`
- `compression`
- `updateBlockStates`
- `blockStateUpdates.updatedBlocks`
- `nbtPath`
- `summaryPath`
- `size`
- `blockCount`
- `paletteCount`
- `recipePath`
