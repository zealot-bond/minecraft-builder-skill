#!/usr/bin/env node

import fs from 'node:fs/promises'
import path from 'node:path'
import { pathToFileURL } from 'node:url'
import * as lodestone from '@mattzh72/lodestone'

const {
  BlockState,
  NbtByte,
  NbtCompound,
  NbtDouble,
  NbtFloat,
  NbtInt,
  NbtList,
  NbtLong,
  NbtShort,
  NbtString,
  NbtFile,
  Structure,
} = lodestone

const DEFAULT_DATA_VERSION = 3465

function usage() {
  return `Usage:
  node scripts/run-build.mjs <recipe.mjs> [--out-dir <dir>] [--name <name>] [--data-version <number>] [--compression gzip|zlib|none] [--no-block-state-updates] [--json]
`
}

function parseArgs(argv) {
  const options = {
    recipe: undefined,
    outDir: undefined,
    name: undefined,
    dataVersion: DEFAULT_DATA_VERSION,
    compression: 'gzip',
    updateBlockStates: true,
    json: false,
    help: false,
  }

  const readValue = (arg, index) => {
    const value = argv[index + 1]
    if (!value || value.startsWith('-')) throw new Error(`${arg} requires a value`)
    return value
  }

  for (let index = 0; index < argv.length; index += 1) {
    const arg = argv[index]
    if (arg === '-h' || arg === '--help') {
      options.help = true
    } else if (arg === '--json') {
      options.json = true
    } else if (arg === '--no-block-state-updates') {
      options.updateBlockStates = false
    } else if (arg === '--out-dir') {
      options.outDir = readValue(arg, index)
      index += 1
    } else if (arg.startsWith('--out-dir=')) {
      options.outDir = arg.slice('--out-dir='.length)
    } else if (arg === '--name') {
      options.name = readValue(arg, index)
      index += 1
    } else if (arg.startsWith('--name=')) {
      options.name = arg.slice('--name='.length)
    } else if (arg === '--data-version') {
      options.dataVersion = Number(readValue(arg, index))
      index += 1
    } else if (arg.startsWith('--data-version=')) {
      options.dataVersion = Number(arg.slice('--data-version='.length))
    } else if (arg === '--compression') {
      options.compression = readValue(arg, index)
      index += 1
    } else if (arg.startsWith('--compression=')) {
      options.compression = arg.slice('--compression='.length)
    } else if (!options.recipe) {
      options.recipe = arg
    } else {
      throw new Error(`Unexpected argument: ${arg}`)
    }
  }

  if (!Number.isInteger(options.dataVersion) || options.dataVersion <= 0) {
    throw new Error('--data-version must be a positive integer')
  }
  if (!['gzip', 'zlib', 'none'].includes(options.compression)) {
    throw new Error('--compression must be gzip, zlib, or none')
  }

  return options
}

function slugify(value) {
  const slug = String(value ?? '')
    .trim()
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-+|-+$/g, '')
  return slug || 'minecraft-build'
}

function tuple(value, label) {
  if (!Array.isArray(value) || value.length !== 3) {
    throw new Error(`${label} must be a three-number array`)
  }
  const out = value.map(Number)
  if (!out.every(Number.isFinite)) {
    throw new Error(`${label} must contain finite numbers`)
  }
  return out.map(Math.trunc)
}

function normalizeSize(size) {
  const out = tuple(size, 'size')
  if (!out.every(value => value > 0)) {
    throw new Error('size values must be positive')
  }
  return out
}

function normalizeBlock(block, properties) {
  if (block instanceof BlockState) {
    return { name: block.getName().toString(), properties: normalizeProperties(properties ?? block.getProperties(), 'properties') }
  }
  if (typeof block === 'string') {
    const state = BlockState.parse(block)
    return {
      name: state.getName().toString(),
      properties: normalizeProperties(properties ?? state.getProperties(), 'properties'),
    }
  }
  if (block && typeof block === 'object') {
    const name = block.name ?? block.id
    if (!name) throw new Error('block object requires name or id')
    return { name: String(name), properties: normalizeProperties(properties ?? block.properties, 'properties') }
  }
  throw new Error('block must be a block id string, state string, BlockState, or block object')
}

function normalizeProperties(properties, label) {
  if (properties === undefined) return undefined
  if (!properties || typeof properties !== 'object' || Array.isArray(properties)) {
    throw new Error(`${label} must be an object with string values`)
  }
  const normalized = {}
  for (const [key, value] of Object.entries(properties)) {
    if (typeof value !== 'string') {
      throw new Error(`${label}.${key} must be a string`)
    }
    normalized[key] = value
  }
  return normalized
}

function assertInside(structure, pos) {
  if (!structure.isInside(pos)) {
    const size = structure.getSize()
    throw new Error(`Position [${pos.join(', ')}] is outside structure size [${size.join(', ')}]`)
  }
}

function setBlock(structure, posInput, block, properties, nbt) {
  const pos = tuple(posInput, 'pos')
  assertInside(structure, pos)
  const normalized = normalizeBlock(block, properties)
  structure.addBlock(pos, normalized.name, normalized.properties, nbt)
  return structure
}

function forBox(fromInput, toInput, fn) {
  const from = tuple(fromInput, 'from')
  const to = tuple(toInput, 'to')
  const min = from.map((value, index) => Math.min(value, to[index]))
  const max = from.map((value, index) => Math.max(value, to[index]))
  for (let x = min[0]; x <= max[0]; x += 1) {
    for (let y = min[1]; y <= max[1]; y += 1) {
      for (let z = min[2]; z <= max[2]; z += 1) {
        fn([x, y, z], min, max)
      }
    }
  }
}

function fill(structure, from, to, block, properties, nbt) {
  forBox(from, to, pos => setBlock(structure, pos, block, properties, nbt))
  return structure
}

function hollowBox(structure, from, to, block, properties, nbt) {
  forBox(from, to, (pos, min, max) => {
    const isSurface = pos.some((value, index) => value === min[index] || value === max[index])
    if (isSurface) setBlock(structure, pos, block, properties, nbt)
  })
  return structure
}

function line(structure, fromInput, toInput, block, properties, nbt) {
  const from = tuple(fromInput, 'from')
  const to = tuple(toInput, 'to')
  const steps = Math.max(...from.map((value, index) => Math.abs(to[index] - value)))
  if (steps === 0) return setBlock(structure, from, block, properties, nbt)
  const seen = new Set()
  for (let step = 0; step <= steps; step += 1) {
    const t = step / steps
    const pos = from.map((value, index) => Math.round(value + (to[index] - value) * t))
    const key = pos.join(',')
    if (!seen.has(key)) {
      seen.add(key)
      setBlock(structure, pos, block, properties, nbt)
    }
  }
  return structure
}

function sphere(structure, centerInput, radiusInput, block, options = {}) {
  const center = tuple(centerInput, 'center')
  const radius = Number(radiusInput)
  if (!Number.isFinite(radius) || radius <= 0) throw new Error('radius must be positive')
  const filled = options.filled ?? true
  const radiusSq = radius * radius
  const innerRadiusSq = Math.max(0, radius - 1) * Math.max(0, radius - 1)
  const ceil = Math.ceil(radius)
  for (let x = center[0] - ceil; x <= center[0] + ceil; x += 1) {
    for (let y = center[1] - ceil; y <= center[1] + ceil; y += 1) {
      for (let z = center[2] - ceil; z <= center[2] + ceil; z += 1) {
        const distanceSq = (x - center[0]) ** 2 + (y - center[1]) ** 2 + (z - center[2]) ** 2
        if (distanceSq <= radiusSq && (filled || distanceSq >= innerRadiusSq)) {
          setBlock(structure, [x, y, z], block, options.properties, options.nbt)
        }
      }
    }
  }
  return structure
}

function cylinder(structure, centerInput, radiusInput, yRangeInput, block, options = {}) {
  const center = tuple(centerInput, 'center')
  const yRange = Array.isArray(yRangeInput) ? yRangeInput.map(Number) : [center[1], Number(yRangeInput)]
  if (yRange.length !== 2 || !yRange.every(Number.isFinite)) throw new Error('yRange must be [minY, maxY]')
  const radius = Number(radiusInput)
  if (!Number.isFinite(radius) || radius <= 0) throw new Error('radius must be positive')
  const filled = options.filled ?? true
  const radiusSq = radius * radius
  const innerRadiusSq = Math.max(0, radius - 1) * Math.max(0, radius - 1)
  const ceil = Math.ceil(radius)
  const minY = Math.trunc(Math.min(...yRange))
  const maxY = Math.trunc(Math.max(...yRange))
  for (let x = center[0] - ceil; x <= center[0] + ceil; x += 1) {
    for (let z = center[2] - ceil; z <= center[2] + ceil; z += 1) {
      const distanceSq = (x - center[0]) ** 2 + (z - center[2]) ** 2
      if (distanceSq <= radiusSq && (filled || distanceSq >= innerRadiusSq)) {
        for (let y = minY; y <= maxY; y += 1) {
          setBlock(structure, [x, y, z], block, options.properties, options.nbt)
        }
      }
    }
  }
  return structure
}

function toNbtTag(value) {
  if (value && typeof value.getId === 'function') return value
  if (typeof value === 'string') return new NbtString(value)
  if (typeof value === 'boolean') return new NbtByte(value ? 1 : 0)
  if (typeof value === 'number') return Number.isInteger(value) ? new NbtInt(value) : new NbtDouble(value)
  if (Array.isArray(value)) return new NbtList(value.map(toNbtTag))
  if (value && typeof value === 'object') return createBlockNbt(value)
  throw new Error(`Unsupported NBT value: ${value}`)
}

function createBlockNbt(object) {
  const compound = new NbtCompound()
  for (const [key, value] of Object.entries(object)) {
    compound.set(key, toNbtTag(value))
  }
  return compound
}

function createApi() {
  return {
    lodestone,
    Structure,
    BlockState,
    NbtByte,
    NbtCompound,
    NbtDouble,
    NbtFloat,
    NbtInt,
    NbtList,
    NbtLong,
    NbtShort,
    NbtString,
    createStructure: size => new Structure(normalizeSize(size)),
    normalizeBlock,
    setBlock,
    fill,
    hollowBox,
    line,
    sphere,
    cylinder,
    createBlockNbt,
  }
}

function summarize(structure) {
  const blocks = structure.getBlocks()
  return {
    size: structure.getSize(),
    blockCount: blocks.length,
    paletteCount: new Set(blocks.map(block => block.state.toString())).size,
  }
}

async function main() {
  const options = parseArgs(process.argv.slice(2))
  if (options.help) {
    console.log(usage())
    return
  }
  if (!options.recipe) {
    throw new Error(`Missing recipe file.\n${usage()}`)
  }

  const recipePath = path.resolve(options.recipe)
  const recipe = await import(`${pathToFileURL(recipePath).href}?v=${Date.now()}`)
  const buildFn = recipe.default ?? recipe.build
  if (typeof buildFn !== 'function') {
    throw new Error('Recipe must export a default function or named build function')
  }

  const result = await buildFn(createApi())
  const structure = result instanceof Structure ? result : result?.structure
  if (!(structure instanceof Structure)) {
    throw new Error('Recipe must return a Lodestone Structure or { structure, metadata }')
  }

  const metadata = {
    ...(recipe.metadata ?? {}),
    ...(result?.metadata ?? {}),
  }
  const outputStructure = options.updateBlockStates ? structure.clone() : structure
  const blockStateUpdates = options.updateBlockStates ? outputStructure.updateBlockStates() : { updatedBlocks: 0 }
  const name = slugify(options.name ?? metadata.name ?? path.basename(recipePath, path.extname(recipePath)))
  const outDir = path.resolve(options.outDir ?? path.join('minecraft-builds', name))
  await fs.mkdir(outDir, { recursive: true })

  const nbtPath = path.join(outDir, `${name}.nbt`)
  const bytes = outputStructure.writeNbt({
    name: '',
    dataVersion: options.dataVersion,
    compression: options.compression,
  })
  await fs.writeFile(nbtPath, bytes)

  const file = NbtFile.read(bytes)
  const roundTrip = Structure.fromNbt(file.root)
  const stats = summarize(outputStructure)
  const roundTripStats = summarize(roundTrip)
  if (JSON.stringify(stats.size) !== JSON.stringify(roundTripStats.size) || stats.blockCount !== roundTripStats.blockCount) {
    throw new Error('Generated NBT failed Lodestone round-trip validation')
  }

  const summary = {
    name,
    dataVersion: options.dataVersion,
    compression: options.compression,
    updateBlockStates: options.updateBlockStates,
    blockStateUpdates,
    nbtPath,
    summaryPath: path.join(outDir, 'summary.json'),
    ...stats,
    recipePath,
  }
  await fs.writeFile(summary.summaryPath, `${JSON.stringify(summary, null, 2)}\n`)

  if (options.json) {
    console.log(JSON.stringify(summary, null, 2))
  } else {
    console.log(`Generated ${summary.name}`)
    console.log(`  NBT: ${summary.nbtPath}`)
    console.log(`  Size: ${summary.size.join(' x ')}`)
    console.log(`  Blocks: ${summary.blockCount}`)
    console.log(`  Palette: ${summary.paletteCount}`)
  }
}

main().catch(err => {
  console.error(`run-build: ${err.message}`)
  process.exitCode = 1
})
