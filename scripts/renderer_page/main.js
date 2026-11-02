import { vec3 } from 'gl-matrix'
import {
  NbtFile,
  NbtString,
  Structure,
  ThreeStructureRenderer,
  loadDefaultPackResources,
} from '@mattzh72/lodestone'

const missingBlocks = new Set()
const origWarn = console.warn.bind(console)
console.warn = (...args) => {
  const msg = args.map(String).join(' ')
  if (msg === 'parent minecraft:builtin/entity does not exist!') return
  const m = msg.match(/minecraft:[a-z0-9_]+/g)
  if (m && (msg.toLowerCase().includes('missing') || msg.toLowerCase().includes('not exist') || msg.toLowerCase().includes('unknown'))) {
    for (const id of m) missingBlocks.add(id)
  }
  origWarn(...args)
}

const LIGHTING = {
  day: {
    direction: vec3.fromValues(0.42, 0.82, 0.34),
    intensity: 1.18,
    ambientIntensity: 0.64,
    fillIntensity: 0.34,
    rimIntensity: 0.36,
    exposure: 1.08,
    sky: {
      zenithColor: [0.22, 0.48, 0.86],
      horizonColor: [0.80, 0.90, 1.0],
      groundColor: [0.16, 0.20, 0.24],
      stars: { enabled: false },
    },
    fog: {
      color: [0.78, 0.87, 0.95],
      density: 0.00010,
      heightFalloff: 0.001,
    },
    shadow: {
      enabled: true,
      intensity: 0.36,
      softness: 0.72,
    },
    emissive: {
      range: 14,
      intensity: 0.85,
      tint: [1.0, 0.90, 0.72],
    },
  },
  golden: {
    direction: vec3.fromValues(0.62, 0.42, 0.48),
    color: [1.0, 0.86, 0.68],
    ambientColor: [0.68, 0.66, 0.82],
    fillColor: [0.42, 0.46, 0.66],
    rimColor: [1.0, 0.80, 0.56],
    intensity: 1.15,
    ambientIntensity: 0.58,
    fillIntensity: 0.30,
    rimIntensity: 0.44,
    exposure: 1.08,
    sky: {
      zenithColor: [0.20, 0.34, 0.68],
      horizonColor: [0.96, 0.76, 0.62],
      groundColor: [0.18, 0.16, 0.20],
      stars: { enabled: false },
    },
    fog: {
      color: [0.88, 0.76, 0.72],
      density: 0.00012,
      heightFalloff: 0.001,
    },
    shadow: {
      enabled: true,
      intensity: 0.38,
      softness: 0.76,
    },
    emissive: {
      range: 16,
      intensity: 1.05,
      tint: [1.0, 0.88, 0.66],
    },
  },
  night: {
    direction: vec3.fromValues(-0.32, 0.52, -0.42),
    color: [0.62, 0.72, 1.0],
    ambientColor: [0.36, 0.45, 0.74],
    fillColor: [0.15, 0.20, 0.38],
    rimColor: [0.52, 0.66, 1.0],
    intensity: 0.32,
    ambientIntensity: 0.56,
    fillIntensity: 0.24,
    rimIntensity: 0.44,
    exposure: 0.98,
    sky: {
      zenithColor: [0.018, 0.03, 0.09],
      horizonColor: [0.06, 0.095, 0.20],
      groundColor: [0.02, 0.025, 0.04],
      sunGlowColor: [0.48, 0.6, 1.0],
      sunGlowIntensity: 0.22,
      sunGlowExponent: 20,
      stars: { enabled: true, density: 0.75, brightness: 0.95 },
    },
    fog: {
      color: [0.04, 0.055, 0.11],
      density: 0.00008,
      heightFalloff: 0.00065,
    },
    shadow: {
      enabled: true,
      intensity: 0.22,
      softness: 0.82,
    },
    emissive: {
      range: 20,
      intensity: 1.45,
      tint: [1.0, 0.88, 0.68],
    },
  },
}

// Rename map for newer 1.21.9+ / 26.x IDs so Lodestone 0.6.0's 1.21.4 pack renders real meshes
const PACK_ALIASES = {
  'minecraft:iron_chain': 'minecraft:chain',
}

function normalizePaletteForPack(rootCompound, resources) {
  const unmapped = []
  try {
    const palList = rootCompound.getList?.('palette')
    const items = palList?.items ?? []
    for (const entry of items) {
      const nameStr = entry.getString?.('Name')
      if (!nameStr) continue
      const mapped = PACK_ALIASES[nameStr] ?? nameStr
      if (mapped !== nameStr && entry.set) {
        entry.set('Name', new NbtString(mapped))
      }
      const shortId = mapped.replace(/^minecraft:/, '')
      if (resources?.getBlockDefinition && !resources.getBlockDefinition(mapped) && !resources.getBlockDefinition(shortId) && shortId !== 'air') {
        unmapped.push(nameStr)
      }
    }
  } catch (err) {
    console.warn('Palette alias check warning:', err)
  }
  return [...new Set(unmapped)]
}

async function init() {
  const canvas = document.getElementById('render-canvas')
  const [nbtResp, pack] = await Promise.all([
    fetch('/__mc_render__/build.nbt'),
    loadDefaultPackResources({
      baseUrl: new URL('/__mc_render__/default-pack/', window.location.href).toString(),
    }),
  ])
  if (!nbtResp.ok) throw new Error(`NBT fetch failed: ${nbtResp.status}`)
  const bytes = new Uint8Array(await nbtResp.arrayBuffer())
  const nbt = NbtFile.read(bytes)
  const unmapped = normalizePaletteForPack(nbt.root, pack.resources)
  const structure = Structure.fromNbt(nbt.root)
  const size = structure.getSize()
  const blockCount = structure.getBlocks().length

  const renderer = new ThreeStructureRenderer(canvas, structure, pack.resources, {
    chunkSize: 16,
    drawDistance: 1500,
    useInvisibleBlockBuffer: false,
    preserveDrawingBuffer: true,
    antialias: true,
    asyncBuild: false,
    sunlight: LIGHTING.day,
  })

  renderer.setViewport(0, 0, window.innerWidth, window.innerHeight, 1.0)
  await renderer.whenReady()

  window.__MC_RENDER__ = {
    ready: true,
    size: [...size],
    blocks: blockCount,
    untextured: () => [...new Set([...unmapped, ...missingBlocks])],
    renderShot: async ({ position, target, fov = 48, lighting = 'day', width, height }) => {
      if (width && height) {
        canvas.style.width = `${width}px`
        canvas.style.height = `${height}px`
        renderer.setViewport(0, 0, width, height, 1.0)
      }
      renderer.setSunlight(LIGHTING[lighting] ?? LIGHTING.day)
      renderer.setCamera({
        position: vec3.fromValues(position[0], position[1], position[2]),
        target: vec3.fromValues(target[0], target[1], target[2]),
        up: vec3.fromValues(0, 1, 0),
        fov,
      })
      renderer.drawStructure()
      await new Promise(r => requestAnimationFrame(() => requestAnimationFrame(r)))
      renderer.drawStructure()
      const dataUrl = canvas.toDataURL('image/png')
      return {
        dataUrl,
        untextured: [...new Set([...unmapped, ...missingBlocks])],
      }
    },
  }
}

init().catch(err => {
  console.error(err)
  window.__MC_RENDER__ = { ready: false, error: String(err?.stack || err) }
})
