#!/usr/bin/env node
/**
 * Headless real-texture Minecraft structure renderer (Lodestone + Three.js + SwiftShader WebGL).
 *
 * Usage:
 *   node scripts/render_textured.mjs build.nbt --outdir renders/
 *   node scripts/render_textured.mjs build.nbt --outdir renders/ --shots hero,top,ne,nw,se,sw,eye,night
 */

import { spawn } from 'node:child_process'
import { createReadStream, existsSync, mkdirSync, readdirSync, readFileSync, writeFileSync } from 'node:fs'
import fs from 'node:fs/promises'
import os from 'node:os'
import path from 'node:path'
import { setTimeout as sleep } from 'node:timers/promises'
import { fileURLToPath } from 'node:url'
import { createServer } from 'vite'

const scriptDir = path.dirname(fileURLToPath(import.meta.url))
const viewerRoot = path.join(scriptDir, 'renderer_page')

function findPlaywrightChromes() {
  const found = []
  const pwDir = path.join(os.homedir(), '.cache', 'ms-playwright')
  if (!existsSync(pwDir)) return found
  try {
    const entries = readdirSync(pwDir).sort().reverse()
    for (const e of entries) {
      if (e.startsWith('chromium_headless_shell-')) {
        const p = path.join(pwDir, e, 'chrome-headless-shell-linux64', 'chrome-headless-shell')
        if (existsSync(p)) found.push(p)
      }
    }
    for (const e of entries) {
      if (e.startsWith('chromium-')) {
        const p = path.join(pwDir, e, 'chrome-linux64', 'chrome')
        if (existsSync(p)) found.push(p)
      }
    }
  } catch {}
  return found
}

function pickChrome() {
  const candidates = [
    process.env.CHROME,
    ...findPlaywrightChromes(),
    '/usr/bin/chromium',
    '/usr/bin/chromium-browser',
    '/usr/bin/google-chrome',
    '/usr/bin/google-chrome-stable',
    '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
  ].filter(Boolean)
  for (const c of candidates) {
    if (existsSync(c)) return c
  }
  throw new Error('No Chromium binary found. Set CHROME=/path/to/chrome')
}

function parseArgs(argv) {
  const opt = {
    nbt: null,
    manifest: null,
    outdir: 'renders',
    shots: 'hero,top,ne,nw,se,sw,eye,night',
    width: 1280,
    height: 860,
    prefix: null,
  }
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i]
    if (a === '--nbt') opt.nbt = argv[++i]
    else if (a === '--manifest') opt.manifest = argv[++i]
    else if (a === '--outdir') opt.outdir = argv[++i]
    else if (a === '--shots') opt.shots = argv[++i]
    else if (a === '--width') opt.width = parseInt(argv[++i], 10)
    else if (a === '--height') opt.height = parseInt(argv[++i], 10)
    else if (a === '--prefix') opt.prefix = argv[++i]
    else if (!a.startsWith('-') && !opt.nbt) opt.nbt = a
  }
  if (!opt.nbt) {
    throw new Error('Usage: node scripts/render_textured.mjs <build.nbt> [--outdir renders] [--shots hero,top,ne,nw,se,sw,eye,night]')
  }
  return opt
}

function contentType(p) {
  if (p.endsWith('.json')) return 'application/json'
  if (p.endsWith('.png')) return 'image/png'
  return 'application/octet-stream'
}

function serveFile(res, filePath) {
  res.statusCode = 200
  res.setHeader('Content-Type', contentType(filePath))
  createReadStream(filePath).pipe(res)
}

async function resolveDefaultPackRoot() {
  const indexUrl = await import.meta.resolve('@mattzh72/lodestone')
  const indexPath = fileURLToPath(indexUrl)
  return path.join(path.resolve(path.dirname(indexPath), '..'), 'assets', 'default-pack')
}

function buildShotPlan(shotNames, size, manifest) {
  const [sx, sy, sz] = size
  const cx = sx / 2
  const cz = sz / 2
  const baseTargetY = Math.min(sy * 0.42, 13)
  const span = Math.max(sx, sz)
  const dist = Math.max(28, span * 1.24)
  const elev = Math.max(18, span * 0.66)
  const target = [cx, baseTargetY, cz]

  const shots = []
  for (const raw of shotNames) {
    const s = raw.trim().toLowerCase()
    if (!s) continue
    if (s === 'hero') {
      // Frame from spawn direction toward hero landmark if known, else classic SE 3/4 view
      let pos = [cx + dist * 0.76, baseTargetY + elev * 0.84, cz + dist * 0.78]
      if (manifest?.spawn?.pos && manifest?.spawn?.look_at) {
        const sp = manifest.spawn.pos
        const lk = manifest.spawn.look_at
        let vx = sp[0] - lk[0]
        let vz = sp[2] - lk[2]
        const len = Math.hypot(vx, vz) || 1
        vx /= len; vz /= len
        // Rotate 22 deg sideways for dynamic 3/4 depth
        const ang = 0.38
        const rx = vx * Math.cos(ang) - vz * Math.sin(ang)
        const rz = vx * Math.sin(ang) + vz * Math.cos(ang)
        pos = [cx + rx * dist * 0.96, baseTargetY + elev * 0.80, cz + rz * dist * 0.96]
      }
      shots.push({ name: 'hero', position: pos, target, fov: 46, lighting: 'golden' })
    } else if (s === 'top') {
      shots.push({
        name: 'top',
        position: [cx + 0.01, Math.max(sy + 24, span * 1.48), cz + span * 0.24],
        target: [cx, baseTargetY * 0.7, cz],
        fov: 46,
        lighting: 'day',
      })
    } else if (s === 'se') {
      shots.push({ name: 'se', position: [cx + dist * 0.78, baseTargetY + elev * 0.85, cz + dist * 0.78], target, fov: 46, lighting: 'day' })
    } else if (s === 'sw') {
      shots.push({ name: 'sw', position: [cx - dist * 0.78, baseTargetY + elev * 0.85, cz + dist * 0.78], target, fov: 46, lighting: 'day' })
    } else if (s === 'ne') {
      shots.push({ name: 'ne', position: [cx + dist * 0.78, baseTargetY + elev * 0.85, cz - dist * 0.78], target, fov: 46, lighting: 'day' })
    } else if (s === 'nw') {
      shots.push({ name: 'nw', position: [cx - dist * 0.78, baseTargetY + elev * 0.85, cz - dist * 0.78], target, fov: 46, lighting: 'day' })
    } else if (s === 'night') {
      shots.push({
        name: 'night',
        position: [cx + dist * 0.74, baseTargetY + elev * 0.76, cz + dist * 0.78],
        target,
        fov: 46,
        lighting: 'night',
      })
    } else if (s === 'eye' || s === 'eye:auto') {
      if (manifest?.spawn?.pos) {
        const [px, py, pz] = manifest.spawn.pos
        const lk = manifest.spawn.look_at ?? [cx, py + 3, cz]
        shots.push({
          name: 'eye-spawn',
          position: [px + 0.5, py + 1.75, pz + 0.5],
          target: [lk[0] + 0.5, lk[1] + 2.0, lk[2] + 0.5],
          fov: 66,
          lighting: 'day',
        })
      } else {
        shots.push({
          name: 'eye-spawn',
          position: [cx, baseTargetY + 3.5, sz - 4],
          target: [cx, baseTargetY + 4.5, cz * 0.6],
          fov: 66,
          lighting: 'day',
        })
      }
    }
  }
  return shots
}

async function main() {
  const opt = parseArgs(process.argv.slice(2))
  const nbtPath = path.resolve(opt.nbt)
  if (!existsSync(nbtPath)) throw new Error(`Missing NBT file: ${nbtPath}`)
  mkdirSync(path.resolve(opt.outdir), { recursive: true })

  const mpath = opt.manifest
    ? path.resolve(opt.manifest)
    : nbtPath.replace(/\.nbt$/i, '.manifest.json')
  const manifest = existsSync(mpath) ? JSON.parse(readFileSync(mpath, 'utf8')) : null
  const prefix = opt.prefix || path.basename(nbtPath, path.extname(nbtPath))
  const defaultPackRoot = await resolveDefaultPackRoot()

  const server = await createServer({
    root: viewerRoot,
    appType: 'spa',
    logLevel: 'error',
    clearScreen: false,
    plugins: [
      {
        name: 'mc-render-middleware',
        configureServer(srv) {
          srv.middlewares.use('/__mc_render__/build.nbt', (_req, res) => serveFile(res, nbtPath))
          srv.middlewares.use('/__mc_render__/default-pack/', async (req, res) => {
            try {
              const reqUrl = new URL(req.url ?? '/', 'http://localhost')
              const rel = decodeURIComponent(reqUrl.pathname.replace(/^\/+/, ''))
              const fp = path.resolve(defaultPackRoot, rel)
              if (fp !== defaultPackRoot && !fp.startsWith(`${defaultPackRoot}${path.sep}`)) {
                res.statusCode = 403; res.end('Forbidden'); return
              }
              await fs.access(fp)
              serveFile(res, fp)
            } catch {
              res.statusCode = 404; res.end('Not found')
            }
          })
        },
      },
    ],
    server: { host: '127.0.0.1', port: 0, strictPort: false, open: false, fs: { strict: false } },
  })
  await server.listen()
  const baseUrl = server.resolvedUrls?.local?.[0]
  if (!baseUrl) throw new Error('Vite server failed to resolve local URL')

  const dbgPort = 9200 + Math.floor(Math.random() * 600)
  const chrome = pickChrome()
  const isHeadlessShell = chrome.endsWith('chrome-headless-shell')
  const flags = [
    ...(isHeadlessShell ? [] : ['--headless=new']),
    `--remote-debugging-port=${dbgPort}`,
    '--no-sandbox',
    '--no-zygote',
    '--disable-dev-shm-usage',
    '--use-gl=angle',
    '--use-angle=swiftshader',
    '--enable-unsafe-swiftshader',
    '--ignore-gpu-blocklist',
    '--no-first-run',
    '--no-default-browser-check',
    '--disable-extensions',
    `--window-size=${opt.width},${opt.height}`,
    `--user-data-dir=/tmp/mc-render-profile-${dbgPort}`,
    'about:blank',
  ]
  const proc = spawn(chrome, flags, { stdio: ['ignore', 'ignore', 'pipe'] })
  let stderrLog = ''
  let stderrWsUrl = null
  proc.stderr.on('data', chunk => {
    stderrLog += chunk.toString()
    const m = stderrLog.match(/DevTools listening on (ws:\/\/\S+)/)
    if (m) stderrWsUrl = m[1]
  })

  let ws = null
  try {
    let wsUrl = null
    for (let i = 0; i < 150; i++) {
      if (stderrWsUrl) { wsUrl = stderrWsUrl; break }
      try {
        const r = await fetch(`http://127.0.0.1:${dbgPort}/json/version`)
        const j = await r.json()
        if (j.webSocketDebuggerUrl) { wsUrl = j.webSocketDebuggerUrl; break }
      } catch {}
      await sleep(150)
    }
    if (!wsUrl) throw new Error(`Chromium CDP failed to start: ${stderrLog.slice(0, 400)}`)

    ws = new WebSocket(wsUrl)
    await new Promise((res, rej) => { ws.onopen = res; ws.onerror = rej })
    let mid = 0
    const pending = new Map()
    ws.onmessage = ev => {
      const m = JSON.parse(ev.data)
      if (m.id && pending.has(m.id)) {
        const { res, rej } = pending.get(m.id); pending.delete(m.id)
        m.error ? rej(new Error(JSON.stringify(m.error))) : res(m.result)
      }
    }
    const send = (method, params = {}, sessionId) => new Promise((res, rej) => {
      const id = ++mid
      pending.set(id, { res, rej })
      ws.send(JSON.stringify({ id, method, params, sessionId }))
    })

    const { targetId } = await send('Target.createTarget', { url: 'about:blank' })
    const { sessionId } = await send('Target.attachToTarget', { targetId, flatten: true })
    const S = (m, p) => send(m, p, sessionId)
    await S('Page.enable')
    await S('Runtime.enable')
    await S('Emulation.setDeviceMetricsOverride', {
      width: opt.width,
      height: opt.height,
      deviceScaleFactor: 1,
      mobile: false,
    })
    await S('Page.navigate', { url: baseUrl })

    // Wait for Lodestone chunk meshes & default pack to finish initializing
    let initState = null
    for (let i = 0; i < 200; i++) {
      const r = await S('Runtime.evaluate', {
        returnByValue: true,
        expression: `window.__MC_RENDER__ ? JSON.stringify({ ready: window.__MC_RENDER__.ready, error: window.__MC_RENDER__.error, size: window.__MC_RENDER__.size, blocks: window.__MC_RENDER__.blocks }) : null`,
      })
      if (r.result?.value) {
        const parsed = JSON.parse(r.result.value)
        if (parsed.error) throw new Error(`Renderer page error: ${parsed.error}`)
        if (parsed.ready) { initState = parsed; break }
      }
      await sleep(150)
    }
    if (!initState) throw new Error('Timed out waiting for Lodestone ThreeStructureRenderer')

    const shotList = buildShotPlan(opt.shots.split(','), initState.size, manifest)
    console.log(`Loaded ${path.basename(nbtPath)} (${initState.size.join('x')}, ${initState.blocks.toLocaleString()} blocks) — rendering ${shotList.length} textured views...`)

    let untexturedAll = new Set()
    for (const shot of shotList) {
      const payload = JSON.stringify({ ...shot, width: opt.width, height: opt.height })
      const evalRes = await S('Runtime.evaluate', {
        awaitPromise: true,
        returnByValue: true,
        expression: `window.__MC_RENDER__.renderShot(${payload})`,
      })
      if (evalRes.exceptionDetails) {
        throw new Error(`renderShot(${shot.name}) failed: ${JSON.stringify(evalRes.exceptionDetails)}`)
      }
      const val = evalRes.result.value
      for (const u of (val.untextured || [])) untexturedAll.add(u)
      const b64 = val.dataUrl.replace(/^data:image\/png;base64,/, '')
      const buf = Buffer.from(b64, 'base64')
      if (buf.length < 4000) {
        throw new Error(`Blank or degenerate PNG on shot ${shot.name} (${buf.length} bytes)`)
      }
      const outPath = path.resolve(opt.outdir, `${prefix}-${shot.name}.png`)
      writeFileSync(outPath, buf)
      console.log(`  ${shot.name.padEnd(10)} -> ${outPath} (${(buf.length / 1024).toFixed(1)} KB)`)
    }

    if (untexturedAll.size > 0) {
      console.warn(`WARNING: Untextured block IDs in default pack: ${[...untexturedAll].join(', ')}`)
    } else {
      console.log('All palette blocks matched default pack definitions.')
    }
  } finally {
    try { ws?.close() } catch {}
    proc.kill('SIGKILL')
    await server.close()
    await fs.rm(`/tmp/mc-render-profile-${dbgPort}`, { recursive: true, force: true }).catch(() => {})
  }
}

main().catch(err => {
  console.error(`render_textured: ${err.message}`)
  process.exitCode = 1
})
