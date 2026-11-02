// THE CELESTIAL FORGE
// A colossal ancient sky-machine: an artificial sun caged in orbiting
// mechanical rings, pouring molten light onto a giant anvil, surrounded by a
// millennia-old city of towers, bridges, observatories and airship docks —
// all floating above the clouds, chained to the heavens.

const SIZE = [200, 190, 200]
const CX = 100
const CZ = 100
const TAU = Math.PI * 2

// Sun + machine geometry
const SUN = { x: CX, y: 118, z: CZ, r: 9 }
const PLAZA_Y = 62
const ISLAND_R = 40

export default function build(api) {
  const structure = api.createStructure(SIZE)

  // ---------------------------------------------------------------- helpers
  const set = (x, y, z, block) => {
    x = Math.round(x)
    y = Math.round(y)
    z = Math.round(z)
    if (x < 0 || y < 0 || z < 0 || x >= SIZE[0] || y >= SIZE[1] || z >= SIZE[2]) return
    api.setBlock(structure, [x, y, z], block)
  }

  const hash = (x, y, z) => {
    let h = (Math.round(x) * 374761393 + Math.round(y) * 668265263 + Math.round(z) * 2147483647) | 0
    h = (h ^ (h >> 13)) * 1274126177
    return ((h ^ (h >> 16)) >>> 0)
  }

  const pick = (x, y, z, entries) => {
    // entries: [[weight, block], ...] deterministic weighted pick
    const total = entries.reduce((s, e) => s + e[0], 0)
    let n = hash(x, y, z) % total
    for (const [w, b] of entries) {
      if (n < w) return b
      n -= w
    }
    return entries[entries.length - 1][1]
  }

  const fillBox = (from, to, block) => {
    const min = from.map((v, i) => Math.min(v, to[i]))
    const max = from.map((v, i) => Math.max(v, to[i]))
    for (let x = min[0]; x <= max[0]; x += 1)
      for (let y = min[1]; y <= max[1]; y += 1)
        for (let z = min[2]; z <= max[2]; z += 1) set(x, y, z, block)
  }

  const ball = (cx, cy, cz, r, block) => {
    const ri = Math.ceil(r)
    for (let x = -ri; x <= ri; x += 1)
      for (let y = -ri; y <= ri; y += 1)
        for (let z = -ri; z <= ri; z += 1) {
          if (x * x + y * y + z * z > r * r) continue
          const b = typeof block === 'function' ? block(cx + x, cy + y, cz + z) : block
          if (b) set(cx + x, cy + y, cz + z, b)
        }
  }

  const discAt = (px, pz, y, r, block, inner = -1) => {
    const r2 = r * r
    const in2 = inner * inner
    for (let x = Math.floor(px - r); x <= Math.ceil(px + r); x += 1)
      for (let z = Math.floor(pz - r); z <= Math.ceil(pz + r); z += 1) {
        const d2 = (x - px) ** 2 + (z - pz) ** 2
        if (d2 > r2 || d2 <= in2) continue
        const b = typeof block === 'function' ? block(x, z, Math.sqrt(d2), Math.atan2(z - pz, x - px)) : block
        if (b) set(x, y, z, b)
      }
  }

  const ringAt = (px, pz, y, r, block, steps) => {
    const n = steps ?? Math.max(48, Math.ceil(r * 8))
    for (let i = 0; i < n; i += 1) {
      const a = (i / n) * TAU
      const b = typeof block === 'function' ? block(i, a) : block
      if (b) set(px + Math.cos(a) * r, y, pz + Math.sin(a) * r, b)
    }
  }

  const norm = v => {
    const l = Math.hypot(v[0], v[1], v[2]) || 1
    return [v[0] / l, v[1] / l, v[2] / l]
  }
  const cross = (a, b) => [a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0]]

  // Giant torus ring, tiltable, with gear teeth and glowing studs.
  const machineRing = (cy, R, tubeR, tilt, phase, opts = {}) => {
    const steps = Math.ceil(R * 9)
    for (let i = 0; i < steps; i += 1) {
      const a = (i / steps) * TAU
      const xl = Math.cos(a) * R
      const zl = Math.sin(a) * R * Math.cos(tilt)
      const yl = Math.sin(a) * R * Math.sin(tilt)
      const x = CX + Math.cos(phase) * xl - Math.sin(phase) * zl
      const z = CZ + Math.sin(phase) * xl + Math.cos(phase) * zl
      const y = cy + yl
      const seg = Math.floor((i / steps) * (opts.segments ?? 24))
      const body = seg % 3 === 0
        ? 'minecraft:deepslate_tiles'
        : (xx, yy, zz) => pick(xx, yy, zz, [
            [5, 'minecraft:oxidized_copper'],
            [4, 'minecraft:oxidized_cut_copper'],
            [3, 'minecraft:weathered_copper'],
            [1, 'minecraft:exposed_copper'],
          ])
      ball(x, y, z, tubeR, body)

      // radial direction (outward from sun center, within ring plane)
      const dir = norm([x - CX, y - cy, z - CZ])
      if (opts.teethEvery && i % opts.teethEvery === 0) {
        for (let k = 1; k <= 2; k += 1)
          set(x + dir[0] * (tubeR + k), y + dir[1] * (tubeR + k), z + dir[2] * (tubeR + k),
            k === 2 ? 'minecraft:gold_block' : 'minecraft:oxidized_cut_copper')
      }
      if (opts.studsEvery && i % opts.studsEvery === Math.floor(opts.studsEvery / 2)) {
        set(x + dir[0] * (tubeR + 1), y + dir[1] * (tubeR + 1), z + dir[2] * (tubeR + 1),
          'minecraft:copper_bulb[lit=true,powered=false]')
        // inner glow facing the sun
        set(x - dir[0] * (tubeR + 1), y - dir[1] * (tubeR + 1), z - dir[2] * (tubeR + 1), 'minecraft:sea_lantern')
      }
    }
  }

  // Massive chain of interlocked oval links.
  const chainRun = (from, to, linkR) => {
    const u = norm([to[0] - from[0], to[1] - from[1], to[2] - from[2]])
    const len = Math.hypot(to[0] - from[0], to[1] - from[1], to[2] - from[2])
    let v1 = cross(u, Math.abs(u[1]) > 0.9 ? [1, 0, 0] : [0, 1, 0])
    v1 = norm(v1)
    const v2 = norm(cross(u, v1))
    const spacing = linkR * 2.6
    const links = Math.max(2, Math.floor(len / spacing))
    for (let i = 0; i <= links; i += 1) {
      const t = i * spacing
      const c = [from[0] + u[0] * t, from[1] + u[1] * t, from[2] + u[2] * t]
      const v = i % 2 === 0 ? v1 : v2
      const mat = i % 5 === 4
        ? 'minecraft:oxidized_copper'
        : (x, y, z) => pick(x, y, z, [[6, 'minecraft:polished_blackstone'], [2, 'minecraft:blackstone'], [1, 'minecraft:gilded_blackstone']])
      const steps = Math.ceil(linkR * 14)
      for (let s = 0; s < steps; s += 1) {
        const a = (s / steps) * TAU
        const q = [
          c[0] + u[0] * Math.cos(a) * linkR * 1.7 + v[0] * Math.sin(a) * linkR,
          c[1] + u[1] * Math.cos(a) * linkR * 1.7 + v[1] * Math.sin(a) * linkR,
          c[2] + u[2] * Math.cos(a) * linkR * 1.7 + v[2] * Math.sin(a) * linkR,
        ]
        ball(q[0], q[1], q[2], Math.max(1.05, linkR * 0.34), mat)
      }
    }
  }

  // Floating island: flat top disc, tapered rocky teardrop underside (shell only).
  const island = (px, pz, topY, R, opts = {}) => {
    const depth = Math.round(R * (opts.depthScale ?? 1.15))
    const bottomY = topY - depth
    for (let y = topY - 1; y >= bottomY; y -= 1) {
      const f = (y - bottomY) / depth
      const r = R * Math.pow(Math.max(f, 0.02), 0.5)
      for (let x = Math.floor(px - r - 3); x <= Math.ceil(px + r + 3); x += 1)
        for (let z = Math.floor(pz - r - 3); z <= Math.ceil(pz + r + 3); z += 1) {
          const ang = Math.atan2(z - pz, x - px)
          const wob = 1 + 0.08 * Math.sin(ang * 5 + y * 0.35) + 0.05 * Math.sin(ang * 9 - y * 0.2)
          const rr = r * wob
          const d = Math.hypot(x - px, z - pz)
          if (d > rr) continue
          // shell only: skip deep interior to keep the file light
          if (d < rr - 4 && y < topY - 3 && y > bottomY + 3) continue
          let b
          if (y >= topY - 3) b = pick(x, y, z, [[5, 'minecraft:tuff'], [3, 'minecraft:cobbled_deepslate'], [1, 'minecraft:deepslate_bricks']])
          else if (f > 0.45) b = pick(x, y, z, [[6, 'minecraft:cobbled_deepslate'], [2, 'minecraft:tuff'], [1, 'minecraft:cracked_deepslate_tiles']])
          else b = pick(x, y, z, [[5, 'minecraft:blackstone'], [3, 'minecraft:basalt[axis=y]'], [1, 'minecraft:gilded_blackstone'], [1, 'minecraft:crying_obsidian']])
          // ancient power veins glinting in the underside
          if (f < 0.5 && hash(x, y, z * 3) % 53 === 0) b = 'minecraft:shroomlight'
          if (f < 0.4 && hash(x * 3, y, z) % 67 === 0) b = 'minecraft:amethyst_block'
          set(x, y, z, b)
        }
    }
    // hanging rock spikes
    const spikes = opts.spikes ?? Math.round(R / 3)
    for (let s = 0; s < spikes; s += 1) {
      const a = (s / spikes) * TAU + hash(s, px, pz) % 7 * 0.13
      const rd = R * (0.25 + (hash(s * 7, px, pz) % 50) / 100)
      const sx = px + Math.cos(a) * rd
      const sz = pz + Math.sin(a) * rd
      const f = Math.max(0.06, 1 - rd / R)
      const startY = bottomY + Math.round(depth * Math.pow(f, 0.5) * 0.9)
      const sLen = 5 + hash(s, sx, sz) % 9
      for (let i = 0; i <= sLen; i += 1) {
        const rr = Math.max(0.8, 2.6 * (1 - i / sLen))
        ball(sx, startY - i, sz, rr, (x, y, z) =>
          pick(x, y, z, [[5, 'minecraft:blackstone'], [3, 'minecraft:basalt[axis=y]'], [1, 'minecraft:cobbled_deepslate']]))
      }
      if (hash(s, px * 2, pz) % 3 === 0) set(sx, startY - sLen - 1, sz, 'minecraft:amethyst_cluster[facing=down]')
    }
  }

  // ======================================================== 1. MAIN ISLAND
  island(CX, CZ, PLAZA_Y, ISLAND_R, { depthScale: 1.2, spikes: 16 })

  // ====================================================== 2. ANCIENT PLAZA
  discAt(CX, CZ, PLAZA_Y, ISLAND_R, (x, z, d, ang) => {
    // mossy cracks of deep age, everywhere
    const age = hash(x, PLAZA_Y, z) % 100
    if (d > 38.2) return age < 12 ? 'minecraft:cracked_polished_blackstone_bricks' : 'minecraft:polished_blackstone'
    if (d > 33.5) {
      if (age < 8) return 'minecraft:moss_block'
      if (age < 16) return 'minecraft:cracked_deepslate_tiles'
      return 'minecraft:deepslate_tiles'
    }
    if (d > 31.5) {
      // golden processional ring
      const seg = Math.floor(((ang + TAU) % TAU) / TAU * 48)
      return seg % 4 === 0 ? 'minecraft:gold_block' : 'minecraft:polished_blackstone'
    }
    if (d > 12) {
      // quartz field with 16 dark sunburst rays
      const rays = ((ang + TAU) % TAU) / TAU * 16
      const rayDist = Math.abs(rays - Math.round(rays))
      if (rayDist < 0.055) return d < 16 ? 'minecraft:gold_block' : 'minecraft:polished_blackstone'
      if (age < 6) return 'minecraft:moss_block'
      if (age < 11) return 'minecraft:quartz_bricks'
      return 'minecraft:smooth_quartz'
    }
    if (d > 9) return Math.floor(((ang + TAU) % TAU) / TAU * 32) % 2 === 0 ? 'minecraft:gold_block' : 'minecraft:chiseled_quartz_block'
    return 'minecraft:polished_blackstone'
  })

  // rim lantern posts (skip where bridges, towers, waterfalls live)
  const featureAngles = [45, 140, 224, 322, 0, 90, 180, 270, 112, 158, 230, 292, 67, 203, 256].map(d => (d * Math.PI) / 180)
  for (let deg = 0; deg < 360; deg += 12) {
    const a = (deg * Math.PI) / 180
    if (featureAngles.some(f => Math.abs(Math.atan2(Math.sin(a - f), Math.cos(a - f))) < 0.12)) continue
    const x = CX + Math.cos(a) * 39
    const z = CZ + Math.sin(a) * 39
    set(x, PLAZA_Y + 1, z, 'minecraft:polished_blackstone_wall')
    set(x, PLAZA_Y + 2, z, 'minecraft:polished_blackstone_wall')
    set(x, PLAZA_Y + 3, z, deg % 24 === 0 ? 'minecraft:lantern[hanging=false]' : 'minecraft:soul_lantern[hanging=false]')
  }

  // ruined arches — fragments of an older forge, mostly collapsed
  const ruinArc = (x1, z1, x2, z2, h) => {
    const steps = 40
    for (let i = 0; i <= steps; i += 1) {
      const t = i / steps
      if (hash(i, x1, z2) % 5 === 0) continue // broken gaps
      const x = x1 + (x2 - x1) * t
      const z = z1 + (z2 - z1) * t
      const y = PLAZA_Y + 1 + Math.sin(t * Math.PI) * h
      set(x, y, z, pick(x, y, z, [[4, 'minecraft:deepslate_bricks'], [2, 'minecraft:cracked_deepslate_tiles'], [1, 'minecraft:moss_block']]))
      if (t < 0.12 || t > 0.88) set(x, y - 1, z, 'minecraft:deepslate_bricks')
    }
  }
  ruinArc(CX - 26, CZ + 8, CX - 14, CZ + 22, 9)
  ruinArc(CX + 16, CZ - 24, CX + 27, CZ - 10, 7)
  ball(CX - 19, PLAZA_Y + 1, CZ + 16, 2.2, (x, y, z) => pick(x, y, z, [[3, 'minecraft:cobbled_deepslate'], [1, 'minecraft:moss_block']]))
  ball(CX + 22, PLAZA_Y + 1, CZ - 18, 1.8, 'minecraft:cobbled_deepslate')

  // ====================================== 3. THE GREAT ANVIL + MOLTEN BEAM
  // base
  fillBox([CX - 5, PLAZA_Y + 1, CZ - 5], [CX + 5, PLAZA_Y + 2, CZ + 5], 'minecraft:polished_blackstone')
  for (const [ox, oz] of [[-5, -5], [-5, 5], [5, -5], [5, 5]]) set(CX + ox, PLAZA_Y + 3, CZ + oz, 'minecraft:gold_block')
  fillBox([CX - 4, PLAZA_Y + 3, CZ - 4], [CX + 4, PLAZA_Y + 4, CZ + 4], 'minecraft:deepslate_tiles')
  // waist
  fillBox([CX - 2, PLAZA_Y + 5, CZ - 2], [CX + 2, PLAZA_Y + 6, CZ + 2], 'minecraft:blackstone')
  // anvil head (overhanging slab, oriented x)
  fillBox([CX - 6, PLAZA_Y + 7, CZ - 4], [CX + 6, PLAZA_Y + 8, CZ + 4], 'minecraft:polished_deepslate')
  fillBox([CX - 5, PLAZA_Y + 9, CZ - 3], [CX + 5, PLAZA_Y + 9, CZ + 3], 'minecraft:iron_block')
  // horn
  fillBox([CX + 7, PLAZA_Y + 7, CZ - 2], [CX + 8, PLAZA_Y + 8, CZ + 2], 'minecraft:polished_deepslate')
  fillBox([CX + 9, PLAZA_Y + 8, CZ - 1], [CX + 10, PLAZA_Y + 8, CZ + 1], 'minecraft:polished_deepslate')
  // molten splash where the beam strikes
  discAt(CX, CZ, PLAZA_Y + 10, 3.2, (x, z, d) => d < 1.8 ? 'minecraft:magma_block' : pick(x, 72, z, [[2, 'minecraft:orange_stained_glass'], [1, 'minecraft:magma_block']]))
  set(CX, PLAZA_Y + 10, CZ, 'minecraft:glowstone')
  for (const [ox, oz] of [[4, 2], [-3, 4], [-4, -3], [3, -4]]) set(CX + ox, PLAZA_Y + 10, CZ + oz, 'minecraft:end_rod[facing=up]')

  // beam of molten light from sun to anvil
  for (let y = PLAZA_Y + 11; y <= SUN.y - SUN.r - 1; y += 1) {
    for (const [ox, oz] of [[1, 0], [-1, 0], [0, 1], [0, -1]]) set(CX + ox, y, CZ + oz, 'minecraft:orange_stained_glass')
    set(CX, y, CZ, y % 5 === 0 ? 'minecraft:shroomlight' : 'minecraft:yellow_stained_glass')
    // spark spiral
    const sa = y * 0.55
    set(CX + Math.cos(sa) * 3, y, CZ + Math.sin(sa) * 3, y % 3 === 0 ? 'minecraft:end_rod[facing=up]' : 'minecraft:orange_stained_glass')
  }

  // ============================================== 4. THE ARTIFICIAL SUN
  ball(SUN.x, SUN.y, SUN.z, 4.5, 'minecraft:glowstone') // core glow
  for (let x = -11; x <= 11; x += 1)
    for (let y = -11; y <= 11; y += 1)
      for (let z = -11; z <= 11; z += 1) {
        const d = Math.hypot(x, y, z)
        const px = SUN.x + x, py = SUN.y + y, pz = SUN.z + z
        if (d >= SUN.r - 1.2 && d <= SUN.r + 0.3) {
          set(px, py, pz, pick(px, py, pz, [
            [8, 'minecraft:glowstone'],
            [6, 'minecraft:shroomlight'],
            [3, 'minecraft:magma_block'],
            [3, 'minecraft:orange_stained_glass'],
            [2, 'minecraft:ochre_froglight'],
          ]))
        } else if (d > SUN.r + 1.5 && d <= SUN.r + 3.6) {
          // flickering corona wisps
          const n = hash(px, py, pz) % 19
          if (n === 0) set(px, py, pz, 'minecraft:orange_stained_glass')
          else if (n === 1) set(px, py, pz, 'minecraft:yellow_stained_glass')
        }
      }
  // solar flare rods
  for (let i = 0; i < 14; i += 1) {
    const ay = Math.acos(1 - (2 * (i + 0.5)) / 14)
    const az = i * 2.39996
    const dir = [Math.sin(ay) * Math.cos(az), Math.cos(ay), Math.sin(ay) * Math.sin(az)]
    const facing = Math.abs(dir[1]) > Math.abs(dir[0]) && Math.abs(dir[1]) > Math.abs(dir[2])
      ? (dir[1] > 0 ? 'up' : 'down')
      : Math.abs(dir[0]) > Math.abs(dir[2]) ? (dir[0] > 0 ? 'east' : 'west') : (dir[2] > 0 ? 'south' : 'north')
    for (let k = 0; k < 3; k += 1) {
      const rr = SUN.r + 1 + k
      set(SUN.x + dir[0] * rr, SUN.y + dir[1] * rr, SUN.z + dir[2] * rr, `minecraft:end_rod[facing=${facing}]`)
    }
  }

  // containment cage — gold armillary bands at radius 13
  const cageBand = (plane, r) => {
    const steps = 110
    for (let i = 0; i < steps; i += 1) {
      const a = (i / steps) * TAU
      const m = Math.cos(a) * r
      const n = Math.sin(a) * r
      let x = SUN.x, y = SUN.y, z = SUN.z
      if (plane === 'xz') { x += m; z += n }
      if (plane === 'xy') { x += m; y += n }
      if (plane === 'yz') { y += m; z += n }
      set(x, y, z, i % 9 === 0 ? 'minecraft:sea_lantern' : i % 2 === 0 ? 'minecraft:gold_block' : 'minecraft:polished_blackstone')
    }
  }
  cageBand('xz', 13)
  cageBand('xy', 13)
  cageBand('yz', 13)

  // ============================================ 5. THE MECHANICAL RINGS
  machineRing(SUN.y, 26, 2.4, 0, 0, { teethEvery: 9, studsEvery: 13, segments: 24 })
  machineRing(SUN.y, 33, 2.2, 1.1, 0, { teethEvery: 11, studsEvery: 15, segments: 28 })
  machineRing(SUN.y, 40, 2.0, 1.1, Math.PI / 2, { teethEvery: 12, studsEvery: 17, segments: 32 })

  // ========================================= 6. PILLARS OF THE MACHINE
  for (const [sx, sz] of [[1, 1], [1, -1], [-1, 1], [-1, -1]]) {
    const px = CX + sx * 18
    const pz = CZ + sz * 18
    // base
    fillBox([px - 3, PLAZA_Y + 1, pz - 3], [px + 3, PLAZA_Y + 3, pz + 3], 'minecraft:polished_blackstone')
    fillBox([px - 3, PLAZA_Y + 4, pz - 3], [px + 3, PLAZA_Y + 4, pz + 3], 'minecraft:chiseled_quartz_block')
    // shaft
    for (let y = PLAZA_Y + 5; y <= PLAZA_Y + 33; y += 1) {
      const band = (y - PLAZA_Y) % 9 === 0
      fillBox([px - 2, y, pz - 2], [px + 2, y, pz + 2], band ? 'minecraft:chiseled_quartz_block' : 'minecraft:smooth_quartz')
      if (!band) {
        set(px - 2, y, pz - 2, 'minecraft:quartz_pillar[axis=y]')
        set(px + 2, y, pz - 2, 'minecraft:quartz_pillar[axis=y]')
        set(px - 2, y, pz + 2, 'minecraft:quartz_pillar[axis=y]')
        set(px + 2, y, pz + 2, 'minecraft:quartz_pillar[axis=y]')
      }
      // glowing conduit strip facing the anvil
      if (y % 2 === 0) set(px - sx * 3, y, pz - sz * 3, 'minecraft:copper_bulb[lit=true,powered=false]')
    }
    // capital
    fillBox([px - 3, PLAZA_Y + 34, pz - 3], [px + 3, PLAZA_Y + 34, pz + 3], 'minecraft:polished_blackstone')
    fillBox([px - 3, PLAZA_Y + 35, pz - 3], [px + 3, PLAZA_Y + 35, pz + 3], 'minecraft:gold_block')
    set(px, PLAZA_Y + 36, pz, 'minecraft:lightning_rod[facing=up,powered=true]')
    // chain from capital up to the sun cage
    chainRun([px, PLAZA_Y + 37, pz], [CX + sx * 9.5, SUN.y - 8, CZ + sz * 9.5], 1.7)
  }

  // ====================================== 7. COLOSSAL CHAINS TO THE HEAVENS
  for (const [sx, sz] of [[1, 1], [1, -1], [-1, 1], [-1, -1]]) {
    const ax = CX + sx * 18.4
    const az = CZ + sz * 18.4
    chainRun([ax, SUN.y + 2, az], [CX + sx * 36, 188, CZ + sz * 36], 3.2)
  }
  // two extra chains anchored to the outermost ring, vanishing upward
  chainRun([CX + 40, SUN.y, CZ], [CX + 58, 189, CZ + 14], 2.6)
  chainRun([CX - 40, SUN.y, CZ], [CX - 58, 189, CZ - 14], 2.6)

  // ============================================== 8. RIM TOWERS OF THE CITY
  const tower = (tx, tz, baseY, h, r) => {
    // base plinth
    api.cylinder(structure, [tx, baseY, tz], r + 1, [baseY, baseY + 2], 'minecraft:polished_blackstone', { filled: true })
    // shaft
    for (let y = baseY + 3; y <= baseY + h; y += 1) {
      const n = Math.max(24, Math.ceil(r * 9))
      for (let i = 0; i < n; i += 1) {
        const a = (i / n) * TAU
        const x = tx + Math.cos(a) * r
        const z = tz + Math.sin(a) * r
        const cardinal = Math.abs(Math.cos(a)) > 0.94 || Math.abs(Math.sin(a)) > 0.94
        let b = pick(x, y, z, [[6, 'minecraft:deepslate_bricks'], [2, 'minecraft:cracked_deepslate_tiles'], [1, 'minecraft:tuff']])
        if (cardinal) b = 'minecraft:smooth_quartz'
        if (cardinal && y > baseY + 5 && (y - baseY) % 6 === 3) b = 'minecraft:orange_stained_glass'
        set(x, y, z, b)
      }
    }
    // glow windows
    for (let y = baseY + 6; y <= baseY + h - 3; y += 5) {
      set(tx + r, y, tz, 'minecraft:copper_bulb[lit=true,powered=false]')
      set(tx - r, y, tz, 'minecraft:copper_bulb[lit=true,powered=false]')
      set(tx, y, tz + r, 'minecraft:copper_bulb[lit=true,powered=false]')
      set(tx, y, tz - r, 'minecraft:copper_bulb[lit=true,powered=false]')
    }
    // balcony + oxidized copper cone roof
    discAt(tx, tz, baseY + h + 1, r + 1.6, 'minecraft:polished_blackstone')
    ringAt(tx, tz, baseY + h + 2, r + 1.6, (i) => i % 5 === 0 ? 'minecraft:lantern[hanging=false]' : 'minecraft:polished_blackstone_wall')
    const roofH = r + 4
    for (let k = 0; k <= roofH; k += 1) {
      const rr = (r + 1) * (1 - k / roofH) + 0.4
      discAt(tx, tz, baseY + h + 2 + k, rr, (x, z) => pick(x, baseY + h + 2 + k, z, [[5, 'minecraft:oxidized_copper'], [3, 'minecraft:oxidized_cut_copper'], [1, 'minecraft:weathered_copper']]))
    }
    set(tx, baseY + h + 3 + roofH, tz, 'minecraft:gold_block')
    set(tx, baseY + h + 4 + roofH, tz, 'minecraft:end_rod[facing=up]')
  }

  const towerAngles = [0, 90, 180, 270, 112, 158, 230, 292]
  const towerHeights = [26, 18, 30, 20, 15, 22, 16, 24]
  const towerRadii = [4, 3, 5, 3, 3, 4, 3, 4]
  for (let i = 0; i < towerAngles.length; i += 1) {
    const a = (towerAngles[i] * Math.PI) / 180
    tower(Math.round(CX + Math.cos(a) * 33), Math.round(CZ + Math.sin(a) * 33), PLAZA_Y, towerHeights[i], towerRadii[i])
  }

  // =========================================== 9. SATELLITE SKY ISLANDS
  island(158, 55, 74, 13, { spikes: 5 })
  island(42, 148, 70, 14, { spikes: 5 })
  island(152, 152, 66, 11, { spikes: 4 })
  island(46, 48, 82, 10, { spikes: 4 })

  // --- 9a. observatory
  discAt(158, 55, 74, 13, (x, z, d) => d > 11 ? 'minecraft:polished_blackstone' : pick(x, 74, z, [[4, 'minecraft:deepslate_tiles'], [1, 'minecraft:moss_block'], [1, 'minecraft:cracked_deepslate_tiles']]))
  for (let y = 75; y <= 93; y += 1) {
    const n = 40
    for (let i = 0; i < n; i += 1) {
      const a = (i / n) * TAU
      const x = 158 + Math.cos(a) * 5.5
      const z = 55 + Math.sin(a) * 5.5
      const pilaster = i % 5 === 0
      let b = pilaster ? 'minecraft:smooth_quartz' : pick(x, y, z, [[5, 'minecraft:deepslate_bricks'], [1, 'minecraft:cracked_deepslate_tiles']])
      if (!pilaster && y >= 80 && y <= 88 && i % 5 === 2) b = 'minecraft:tinted_glass'
      set(x, y, z, b)
    }
  }
  discAt(158, 55, 93, 8, 'minecraft:polished_blackstone')
  ringAt(158, 55, 94, 8, (i) => i % 6 === 0 ? 'minecraft:soul_lantern[hanging=false]' : 'minecraft:polished_blackstone_wall')
  // copper dome
  for (let y = 94; y <= 102; y += 1) {
    const dy = y - 94
    const rr = Math.sqrt(Math.max(0, 7 * 7 - dy * dy))
    const n = Math.max(8, Math.ceil(rr * 8))
    for (let i = 0; i < n; i += 1) {
      const a = (i / n) * TAU
      const x = 158 + Math.cos(a) * rr
      const z = 55 + Math.sin(a) * rr
      const meridian = i % Math.max(2, Math.floor(n / 8)) === 0
      set(x, y, z, meridian ? 'minecraft:oxidized_cut_copper' : pick(x, y, z, [[5, 'minecraft:oxidized_copper'], [2, 'minecraft:weathered_copper']]))
    }
  }
  set(158, 103, 55, 'minecraft:gold_block')
  set(158, 104, 55, 'minecraft:lightning_rod[facing=up,powered=true]')
  // telescope barrel aimed at the artificial sun
  {
    const dir = norm([SUN.x - 158, SUN.y - 99, SUN.z - 55])
    for (let k = 2; k <= 12; k += 1) {
      ball(158 + dir[0] * k, 99 + dir[1] * k, 55 + dir[2] * k, k > 10 ? 1.8 : 1.4,
        k > 11 ? 'minecraft:tinted_glass' : 'minecraft:polished_blackstone')
    }
    set(158 + dir[0] * 13, 99 + dir[1] * 13, 55 + dir[2] * 13, 'minecraft:sea_lantern')
  }

  // --- 9b. airship dock
  discAt(42, 148, 70, 14, (x, z, d) => d > 12 ? 'minecraft:polished_blackstone' : pick(x, 70, z, [[4, 'minecraft:deepslate_tiles'], [1, 'minecraft:moss_block']]))
  // timber pier reaching into the void
  for (let x = 16; x <= 30; x += 1)
    for (let z = 145; z <= 151; z += 1) set(x, 70, z, (x + z) % 7 === 0 ? 'minecraft:dark_oak_planks' : 'minecraft:spruce_planks')
  for (const px of [17, 23, 29]) {
    for (const pz of [145, 151]) {
      for (let y = 67; y <= 69; y += 1) set(px, y, pz, 'minecraft:dark_oak_log')
      set(px, 71, pz, 'minecraft:spruce_fence')
      set(px, 72, pz, 'minecraft:lantern[hanging=false]')
    }
  }
  // mooring bollards
  set(16, 71, 146, 'minecraft:dark_oak_log')
  set(16, 71, 150, 'minecraft:dark_oak_log')
  // the airship
  {
    const hx = 18, hy = 77, hz = 148
    // hull
    for (let x = -9; x <= 9; x += 1)
      for (let y = -3; y <= 1; y += 1)
        for (let z = -3; z <= 3; z += 1) {
          const v = (x / 9.5) ** 2 + (y / 3.2) ** 2 + (z / 3.4) ** 2
          if (v > 1) continue
          if (y === 1) { if (v < 0.82) set(hx + x, hy + y, hz + z, 'minecraft:spruce_planks'); continue }
          const shellOnly = v < 0.55 && y > -3
          if (shellOnly) continue
          set(hx + x, hy + y, hz + z, y === -3 || Math.abs(z) === 3 ? 'minecraft:dark_oak_planks' : 'minecraft:spruce_planks')
        }
    // railing + stern cabin
    for (let x = -8; x <= 8; x += 2) {
      set(hx + x, hy + 2, hz - 2, 'minecraft:spruce_fence')
      set(hx + x, hy + 2, hz + 2, 'minecraft:spruce_fence')
    }
    fillBox([hx + 5, hy + 2, hz - 1], [hx + 7, hy + 4, hz + 1], 'minecraft:dark_oak_planks')
    set(hx + 6, hy + 3, hz - 1, 'minecraft:orange_stained_glass')
    set(hx + 6, hy + 3, hz + 1, 'minecraft:orange_stained_glass')
    set(hx - 9, hy + 1, hz, 'minecraft:lantern[hanging=false]')
    // balloon — striped, gilded
    for (let x = -11; x <= 11; x += 1)
      for (let y = -4; y <= 4; y += 1)
        for (let z = -4; z <= 4; z += 1) {
          const v = (x / 11.5) ** 2 + (y / 4.5) ** 2 + (z / 4.5) ** 2
          if (v > 1 || v < 0.62) continue
          const stripe = Math.floor((Math.atan2(y, z) / TAU + 1) * 8) % 2
          let b = stripe === 0 ? 'minecraft:white_wool' : 'minecraft:orange_wool'
          if (Math.abs(x) <= 1) b = 'minecraft:gold_block'
          if (x === -11 || x === 11) b = 'minecraft:dark_oak_planks'
          set(hx + x, hy + 11 + y, hz + z, b)
        }
    set(hx + 12, hy + 11, hz, 'minecraft:end_rod[facing=east]')
    // rigging
    for (const [ox, oz] of [[-7, -2], [-7, 2], [7, -2], [7, 2]]) {
      for (let y = hy + 3; y <= hy + 7; y += 1) set(hx + ox, y, hz + oz, 'minecraft:chain[axis=y]')
    }
    // mooring chain to the dock
    chainRun([hx + 2, hy - 2, hz + 3], [17, 71, 150], 1.1)
  }

  // --- 9c. bell-tower cathedral spire
  {
    const bx = 152, bz = 152
    discAt(bx, bz, 66, 11, (x, z, d) => d > 9 ? 'minecraft:polished_blackstone' : pick(x, 66, z, [[4, 'minecraft:deepslate_tiles'], [1, 'minecraft:moss_block']]))
    for (let y = 67; y <= 96; y += 1) {
      for (let x = bx - 3; x <= bx + 3; x += 1)
        for (let z = bz - 3; z <= bz + 3; z += 1) {
          if (Math.abs(x - bx) !== 3 && Math.abs(z - bz) !== 3) continue
          const corner = Math.abs(x - bx) === 3 && Math.abs(z - bz) === 3
          let b = corner ? 'minecraft:polished_blackstone' : pick(x, y, z, [[6, 'minecraft:deepslate_bricks'], [2, 'minecraft:cracked_deepslate_tiles'], [1, 'minecraft:moss_block']])
          // tall lancet windows
          if (!corner && (x === bx || z === bz) && y >= 72 && y <= 90)
            b = y >= 88 ? 'minecraft:orange_stained_glass' : 'minecraft:black_stained_glass_pane'
          set(x, y, z, b)
        }
      // buttresses on lower third
      if (y <= 76) {
        const w = 76 - y <= 4 ? 4 : 5
        set(bx + w, y, bz, 'minecraft:deepslate_bricks')
        set(bx - w, y, bz, 'minecraft:deepslate_bricks')
        set(bx, y, bz + w, 'minecraft:deepslate_bricks')
        set(bx, y, bz - w, 'minecraft:deepslate_bricks')
      }
    }
    // open belfry with golden bell
    fillBox([bx - 4, 97, bz - 4], [bx + 4, 97, bz + 4], 'minecraft:polished_blackstone')
    for (const [ox, oz] of [[-4, -4], [-4, 4], [4, -4], [4, 4]]) {
      for (let y = 98; y <= 103; y += 1) set(bx + ox, y, bz + oz, 'minecraft:polished_basalt[axis=y]')
    }
    fillBox([bx - 4, 104, bz - 4], [bx + 4, 104, bz + 4], 'minecraft:polished_blackstone')
    set(bx, 103, bz, 'minecraft:chain[axis=y]')
    fillBox([bx - 1, 100, bz - 1], [bx + 1, 102, bz + 1], 'minecraft:gold_block')
    set(bx, 99, bz, 'minecraft:gold_block')
    // spire
    for (let k = 0; k <= 12; k += 1) {
      const rr = Math.max(0.4, 4.5 * (1 - k / 12))
      discAt(bx, bz, 105 + k, rr, (x, z) => pick(x, 105 + k, z, [[5, 'minecraft:polished_blackstone'], [2, 'minecraft:blackstone']]))
    }
    set(bx, 118, bz, 'minecraft:gold_block')
    set(bx, 119, bz, 'minecraft:end_rod[facing=up]')
  }

  // --- 9d. garden shrine
  {
    const gx = 46, gz = 48
    discAt(gx, gz, 82, 10, (x, z, d) => d > 8.5 ? 'minecraft:polished_blackstone' : pick(x, 82, z, [[5, 'minecraft:moss_block'], [3, 'minecraft:grass_block'], [1, 'minecraft:deepslate_tiles']]))
    for (let i = 0; i < 6; i += 1) {
      const a = (i / 6) * TAU
      const px = Math.round(gx + Math.cos(a) * 6)
      const pz = Math.round(gz + Math.sin(a) * 6)
      for (let y = 83; y <= 88; y += 1) set(px, y, pz, 'minecraft:quartz_pillar[axis=y]')
      set(px, 89, pz, 'minecraft:chiseled_quartz_block')
    }
    ringAt(gx, gz, 90, 6, (i) => i % 7 === 0 ? 'minecraft:sea_lantern' : 'minecraft:gold_block', 40)
    // shrine pool feeding the falls
    discAt(gx, gz, 82, 2.4, 'minecraft:water')
    set(gx, 83, gz, 'minecraft:amethyst_cluster[facing=up]')
    // moss carpet scatter + leaves
    for (let i = 0; i < 40; i += 1) {
      const a = (hash(i, gx, gz) % 360) * (Math.PI / 180)
      const d = 3 + (hash(i * 3, gx, gz) % 50) / 10
      const x = Math.round(gx + Math.cos(a) * d)
      const z = Math.round(gz + Math.sin(a) * d)
      if (hash(x, 83, z) % 3 === 0) set(x, 83, z, 'minecraft:moss_carpet')
    }
    ball(gx - 4, 85, gz + 4, 2.2, (x, y, z) => hash(x, y, z) % 4 === 0 ? undefined : 'minecraft:flowering_azalea_leaves')
    set(gx - 4, 83, gz + 4, 'minecraft:dark_oak_log')
    set(gx - 4, 84, gz + 4, 'minecraft:dark_oak_log')
    // waterfall off the garden's edge
    for (let w = -1; w <= 1; w += 1) {
      const a = Math.PI * 1.25
      const x = gx + Math.cos(a) * 9.6 + Math.cos(a + Math.PI / 2) * w * 1.2
      const z = gz + Math.sin(a) * 9.6 + Math.sin(a + Math.PI / 2) * w * 1.2
      set(gx + Math.cos(a) * 8 + Math.cos(a + Math.PI / 2) * w, 82, gz + Math.sin(a) * 8 + Math.sin(a + Math.PI / 2) * w, 'minecraft:water')
      for (let y = 81; y >= 34; y -= 1) set(x, y, z, 'minecraft:water')
    }
  }

  // ================================================== 10. SKY BRIDGES
  const bridge = (from, to) => {
    const len = Math.hypot(to[0] - from[0], to[2] - from[2])
    const steps = Math.ceil(len * 2)
    const dirA = Math.atan2(to[2] - from[2], to[0] - from[0])
    const sideX = Math.cos(dirA + Math.PI / 2)
    const sideZ = Math.sin(dirA + Math.PI / 2)
    for (let i = 0; i <= steps; i += 1) {
      const t = i / steps
      const x = from[0] + (to[0] - from[0]) * t
      const z = from[2] + (to[2] - from[2]) * t
      const y = Math.round(from[1] + (to[1] - from[1]) * t + Math.sin(t * Math.PI) * 3)
      for (let w = -1; w <= 1; w += 1) {
        const bx = x + sideX * w
        const bz = z + sideZ * w
        set(bx, y, bz, w === 0
          ? pick(bx, y, bz, [[5, 'minecraft:deepslate_tiles'], [1, 'minecraft:cracked_deepslate_tiles'], [1, 'minecraft:moss_block']])
          : 'minecraft:polished_blackstone')
        if (w === 0) set(bx, y - 1, bz, 'minecraft:polished_blackstone')
      }
      if (i % 16 === 8) {
        set(x + sideX * 2, y + 1, z + sideZ * 2, 'minecraft:polished_blackstone_wall')
        set(x + sideX * 2, y + 2, z + sideZ * 2, 'minecraft:lantern[hanging=false]')
        set(x - sideX * 2, y + 1, z - sideZ * 2, 'minecraft:polished_blackstone_wall')
        set(x - sideX * 2, y + 2, z - sideZ * 2, 'minecraft:lantern[hanging=false]')
        set(x, y - 1, z, 'minecraft:chain[axis=y]')
        set(x, y - 2, z, 'minecraft:lantern[hanging=true]')
      }
    }
  }
  bridge([130.8, PLAZA_Y, 76.2], [149.5, 74, 61.5])   // → observatory
  bridge([70, PLAZA_Y, 125], [51, 70, 140.5])         // → airship dock
  bridge([127.6, PLAZA_Y, 127.6], [145.5, 66, 145.5]) // → cathedral
  bridge([72.4, PLAZA_Y, 72.4], [52.5, 82, 54])       // → garden shrine

  // ================================================= 11. GREAT WATERFALLS
  for (const deg of [67, 203, 256]) {
    const a = (deg * Math.PI) / 180
    const ca = Math.cos(a), sa = Math.sin(a)
    const px2 = Math.cos(a + Math.PI / 2), pz2 = Math.sin(a + Math.PI / 2)
    // spring pool recessed into the plaza
    for (let u = 0; u <= 4; u += 1)
      for (let w = -2; w <= 2; w += 1) {
        const x = CX + ca * (34 + u) + px2 * w
        const z = CZ + sa * (34 + u) + pz2 * w
        set(x, PLAZA_Y, z, Math.abs(w) === 2 || u === 0 ? 'minecraft:polished_blackstone' : 'minecraft:water')
      }
    // the fall itself
    for (let w = -1.5; w <= 1.5; w += 0.75) {
      const x = CX + ca * 40.6 + px2 * w
      const z = CZ + sa * 40.6 + pz2 * w
      set(CX + ca * 39.5 + px2 * w, PLAZA_Y, CZ + sa * 39.5 + pz2 * w, 'minecraft:water')
      for (let y = PLAZA_Y - 1; y >= 6; y -= 1) set(x, y, z, 'minecraft:water')
    }
    // mist where it vanishes into the void
    ball(CX + ca * 40.6, 5, CZ + sa * 40.6, 3.4, (x, y, z) => hash(x, y, z) % 3 === 0 ? undefined : 'minecraft:white_stained_glass')
  }

  // ====================================================== 12. CLOUD BANKS
  const clouds = [
    [35, 32, 95, 15, 3, 9], [70, 26, 40, 12, 2.5, 8], [150, 30, 122, 13, 3, 10],
    [120, 22, 170, 11, 2.5, 8], [172, 40, 88, 9, 2, 6], [60, 36, 172, 10, 2.5, 7],
    [24, 44, 55, 8, 2, 6], [142, 18, 38, 12, 3, 9], [95, 12, 142, 10, 2.5, 7],
    [168, 50, 166, 7, 2, 5], [30, 55, 130, 8, 2, 6], [105, 8, 60, 13, 2.5, 9],
  ]
  for (const [px, py, pz, rx, ry, rz] of clouds) {
    for (let x = -rx; x <= rx; x += 1)
      for (let y = -ry; y <= ry; y += 1)
        for (let z = -rz; z <= rz; z += 1) {
          const wob = 1 + 0.18 * Math.sin(x * 0.7 + pz) + 0.14 * Math.sin(z * 0.9 + px)
          const v = (x / (rx * wob)) ** 2 + (y / ry) ** 2 + (z / (rz * wob)) ** 2
          if (v > 1) continue
          set(px + x, py + y, pz + z, v > 0.55 ? 'minecraft:white_stained_glass' : 'minecraft:white_wool')
        }
  }

  // ============================================= 13. DRIFTING SKY SHARDS
  const shards = [
    [60, 95, 70, 3], [135, 100, 135, 3], [78, 140, 60, 2], [125, 84, 162, 4],
    [38, 60, 110, 3], [162, 70, 40, 3], [88, 30, 30, 3], [28, 100, 162, 2],
    [108, 152, 70, 2], [70, 162, 130, 2], [170, 120, 100, 2.5], [30, 140, 100, 2.5],
  ]
  for (const [px, py, pz, r] of shards) {
    ball(px, py, pz, r, (x, y, z) => pick(x, y, z, [[4, 'minecraft:blackstone'], [3, 'minecraft:cobbled_deepslate'], [1, 'minecraft:gilded_blackstone']]))
    discAt(px, pz, py + Math.ceil(r), r * 0.7, 'minecraft:moss_block')
    if (hash(px, py, pz) % 3 === 0) set(px, py + Math.ceil(r) + 1, pz, 'minecraft:end_rod[facing=up]')
    if (hash(px, py, pz) % 3 === 1) {
      for (let k = 1; k <= 4; k += 1) set(px, py - r - k, pz, 'minecraft:chain[axis=y]')
      set(px, py - r - 5, pz, 'minecraft:lantern[hanging=true]')
    }
  }

  return {
    structure,
    metadata: {
      name: 'celestial-forge',
      description: 'An ancient celestial forge: an artificial sun caged in orbiting mechanical rings, chained to the heavens above a floating city of towers, bridges, observatories and airship docks.',
    },
  }
}
