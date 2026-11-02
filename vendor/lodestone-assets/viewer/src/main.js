import { mat4, vec3 } from 'gl-matrix'
import { NbtFile, Structure, ThreeStructureRenderer, loadDefaultPackResources } from '@mattzh72/lodestone'
import './style.css'

const originalWarn = console.warn.bind(console)
console.warn = (...args) => {
  if (args.length === 1 && args[0] === 'parent minecraft:builtin/entity does not exist!') return
  originalWarn(...args)
}

const LIGHTING_PRESETS = {
  day: {
    direction: vec3.fromValues(0.35, 0.85, 0.25),
    intensity: 1.15,
    ambientIntensity: 0.62,
    fillIntensity: 0.32,
    rimIntensity: 0.35,
    exposure: 1.08,
    sky: {
      zenithColor: [0.24, 0.48, 0.84],
      horizonColor: [0.78, 0.9, 1.0],
      groundColor: [0.18, 0.2, 0.22],
      stars: {
        enabled: false,
      },
    },
    fog: {
      color: [0.78, 0.86, 0.94],
      density: 0.00012,
      heightFalloff: 0.001,
    },
  },
  night: {
    direction: vec3.fromValues(-0.32, 0.5, -0.42),
    color: [0.62, 0.72, 1.0],
    ambientColor: [0.34, 0.43, 0.72],
    fillColor: [0.13, 0.18, 0.36],
    rimColor: [0.5, 0.64, 1.0],
    intensity: 0.28,
    ambientIntensity: 0.52,
    fillIntensity: 0.2,
    rimIntensity: 0.42,
    exposure: 0.92,
    sky: {
      zenithColor: [0.015, 0.025, 0.08],
      horizonColor: [0.055, 0.085, 0.18],
      groundColor: [0.018, 0.022, 0.038],
      sunGlowColor: [0.48, 0.6, 1.0],
      sunGlowIntensity: 0.22,
      sunGlowExponent: 20,
      stars: {
        enabled: true,
        density: 0.72,
        brightness: 0.92,
      },
    },
    disc: {
      size: 42,
      coreColor: [0.72, 0.78, 1.0],
      glowColor: [0.34, 0.45, 0.92],
      coreIntensity: 0.42,
      glowIntensity: 0.16,
      softness: 0.4,
    },
    fog: {
      color: [0.035, 0.05, 0.1],
      density: 0.00008,
      heightFalloff: 0.00065,
    },
    shadow: {
      enabled: true,
      intensity: 0.2,
      softness: 0.82,
    },
    emissive: {
      range: 18,
      intensity: 1.35,
      tint: [1.0, 0.88, 0.68],
    },
  },
}

class OrbitCamera {
  constructor(canvas, center, distance, onChange = () => undefined) {
    this.canvas = canvas
    this.center = center
    this.distance = distance
    this.xRotation = 0.62
    this.yRotation = 0.82
    this.dragging = false
    this.lastPos = null
    this.onChange = onChange

    canvas.addEventListener('pointerdown', event => {
      this.dragging = true
      this.lastPos = [event.clientX, event.clientY]
      canvas.setPointerCapture?.(event.pointerId)
    })
    const stopDragging = event => {
      this.dragging = false
      this.lastPos = null
      if (event?.pointerId !== undefined && canvas.hasPointerCapture?.(event.pointerId)) {
        canvas.releasePointerCapture(event.pointerId)
      }
    }
    canvas.addEventListener('pointerup', stopDragging)
    canvas.addEventListener('pointercancel', stopDragging)
    canvas.addEventListener('lostpointercapture', stopDragging)
    canvas.addEventListener('pointermove', event => {
      if (!this.dragging || !this.lastPos) return
      this.yRotation += (event.clientX - this.lastPos[0]) / 160
      this.xRotation += (event.clientY - this.lastPos[1]) / 160
      this.xRotation = Math.max(-1.05, Math.min(1.35, this.xRotation))
      this.lastPos = [event.clientX, event.clientY]
      this.onChange()
    })
    canvas.addEventListener('wheel', event => {
      event.preventDefault()
      const distance = Math.max(4, Math.min(500, this.distance + event.deltaY * 0.08))
      if (distance !== this.distance) {
        this.distance = distance
        this.onChange()
      }
    }, { passive: false })
  }

  getView() {
    const view = mat4.create()
    mat4.translate(view, view, [0, 0, -this.distance])
    mat4.rotateX(view, view, this.xRotation)
    mat4.rotateY(view, view, this.yRotation)
    mat4.translate(view, view, [-this.center[0], -this.center[1], -this.center[2]])
    return view
  }

  getCamera() {
    const inverse = mat4.create()
    mat4.invert(inverse, this.getView())
    return {
      position: vec3.fromValues(inverse[12], inverse[13], inverse[14]),
      target: this.center,
    }
  }
}

function getParam(name, fallback) {
  const params = new URLSearchParams(window.location.search)
  return params.get(name) ?? fallback
}

function getLightingMode() {
  const value = getParam('lighting', 'day').toLowerCase()
  return value === 'night' ? 'night' : 'day'
}

function setLightingUrl(mode) {
  const url = new URL(window.location.href)
  if (mode === 'day') {
    url.searchParams.delete('lighting')
  } else {
    url.searchParams.set('lighting', mode)
  }
  window.history.replaceState({}, '', url)
}

function updateLightingButton(button, mode) {
  button.textContent = mode === 'night' ? 'Day' : 'Night'
  button.title = mode === 'night' ? 'Switch to day lighting' : 'Switch to night lighting'
  button.setAttribute('aria-pressed', String(mode === 'night'))
}

async function loadStructure() {
  const nbtUrl = getParam('nbt', '/__minecraft_builder__/build.nbt')
  const response = await fetch(nbtUrl)
  if (!response.ok) {
    throw new Error(`Failed to fetch NBT: ${response.status} ${response.statusText}`)
  }
  const bytes = new Uint8Array(await response.arrayBuffer())
  return Structure.fromNbt(NbtFile.read(bytes).root)
}

function resize(renderer, canvas) {
  const rect = canvas.getBoundingClientRect()
  if (rect.width <= 0 || rect.height <= 0) return false
  renderer.setViewport(0, 0, rect.width, rect.height, Math.min(window.devicePixelRatio, 1.5))
  return true
}

async function main() {
  const canvas = document.getElementById('preview')
  const loading = document.getElementById('loading')
  const nameEl = document.getElementById('build-name')
  const statsEl = document.getElementById('build-stats')
  const lightingToggle = document.getElementById('lighting-toggle')
  let lightingMode = getLightingMode()

  if (!(canvas instanceof HTMLCanvasElement)) throw new Error('Missing #preview canvas')
  if (!loading || !nameEl || !statsEl || !(lightingToggle instanceof HTMLButtonElement)) {
    throw new Error('Missing viewer controls')
  }

  nameEl.textContent = getParam('name', 'Minecraft Build')
  updateLightingButton(lightingToggle, lightingMode)

  const [structure, pack] = await Promise.all([
    loadStructure(),
    loadDefaultPackResources({ baseUrl: new URL('/__minecraft_builder__/default-pack/', window.location.href).toString() }),
  ])
  const size = structure.getSize()
  const blockCount = structure.getBlocks().length
  statsEl.textContent = `${size[0]} x ${size[1]} x ${size[2]} | ${blockCount.toLocaleString()} blocks`

  const renderer = new ThreeStructureRenderer(canvas, structure, pack.resources, {
    chunkSize: 16,
    drawDistance: 1000,
    useInvisibleBlockBuffer: false,
    asyncBuild: true,
    asyncChunkBuildTimeMs: 8,
    sunlight: LIGHTING_PRESETS[lightingMode],
  })

  const center = vec3.fromValues(size[0] / 2, Math.max(1, size[1] / 2.5), size[2] / 2)
  let frameRequest = 0
  const camera = new OrbitCamera(canvas, center, Math.max(18, Math.max(...size) * 1.9), requestRender)

  function render() {
    frameRequest = 0
    const state = camera.getCamera()
    renderer.lookAt(state.position, state.target)
    renderer.drawStructure()
  }

  function requestRender() {
    if (frameRequest) return
    frameRequest = requestAnimationFrame(render)
  }

  lightingToggle.addEventListener('click', () => {
    lightingMode = lightingMode === 'night' ? 'day' : 'night'
    renderer.setSunlight(LIGHTING_PRESETS[lightingMode])
    updateLightingButton(lightingToggle, lightingMode)
    setLightingUrl(lightingMode)
    requestRender()
  })

  resize(renderer, canvas)
  await renderer.whenReady()
  render()
  loading.classList.add('hidden')

  const resizeObserver = new ResizeObserver(() => {
    if (resize(renderer, canvas)) requestRender()
  })
  resizeObserver.observe(canvas)
}

main().catch(error => {
  console.error(error)
  document.getElementById('loading').textContent = error.message
})
