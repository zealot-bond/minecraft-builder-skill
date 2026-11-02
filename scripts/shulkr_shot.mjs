#!/usr/bin/env node
/**
 * Render a structure NBT on Shulkr's viewer and save a screenshot.
 *
 *   node shulkr_shot.mjs --nbt out.nbt --out render.png
 *   node shulkr_shot.mjs --nbt out.nbt --out render.png --url https://www.shulkr.com/en/viewer
 *
 * Why this exists: a model that has not LOOKED at the build is guessing. The
 * viewer (https://www.shulkr.com/en/viewer) accepts .litematic / .schem / .nbt /
 * .mcstructure via drag-and-drop, renders it in the browser, and this script
 * drives that and captures the pixels.
 *
 * Requirements: a Chromium/Chrome binary and Node 21+ (for global WebSocket).
 * Set CHROME=/path/to/chrome if it is not auto-detected.
 *
 * Honest limitations:
 *  - It is a third-party website. If its markup changes, the file input selector
 *    may stop matching; the script then prints the DOM hints it found and exits
 *    non-zero instead of silently producing a blank image.
 *  - The browser must be headful-ish for WebGL in some environments; pass
 *    --headless to try without a display.
 */
import { spawn } from 'node:child_process'
import { setTimeout as sleep } from 'node:timers/promises'
import { writeFileSync, existsSync, mkdirSync } from 'node:fs'
import { dirname, resolve } from 'node:path'

const CANDIDATES = [
  process.env.CHROME,
  '/home/rhythm/.cache/ms-playwright/chromium-1243/chrome-linux64/chrome',
  '/usr/bin/chromium', '/usr/bin/chromium-browser', '/usr/bin/google-chrome',
  '/usr/bin/google-chrome-stable', '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
].filter(Boolean)

function pickChrome () {
  for (const c of CANDIDATES) if (existsSync(c)) return c
  throw new Error('no chromium found; set CHROME=/path/to/chrome')
}

const args = process.argv.slice(2)
const opt = { url: 'https://www.shulkr.com/en/viewer', wait: 25000, headless: false }
for (let i = 0; i < args.length; i++) {
  const a = args[i]
  if (a === '--nbt') opt.nbt = args[++i]
  else if (a === '--out') opt.out = args[++i]
  else if (a === '--url') opt.url = args[++i]
  else if (a === '--wait') opt.wait = parseInt(args[++i], 10)
  else if (a === '--headless') opt.headless = true
}
if (!opt.nbt || !opt.out) {
  console.error('usage: node shulkr_shot.mjs --nbt out.nbt --out render.png [--wait ms] [--headless]')
  process.exit(2)
}
const nbtPath = resolve(opt.nbt)
if (!existsSync(nbtPath)) { console.error('missing ' + nbtPath); process.exit(2) }
if (opt.out) mkdirSync(dirname(resolve(opt.out)), { recursive: true })

const PORT = 9500 + Math.floor(Math.random() * 300)
const chrome = pickChrome()
const flags = [
  `--remote-debugging-port=${PORT}`,
  '--no-sandbox', '--disable-gpu', '--disable-dev-shm-usage',
  '--no-first-run', '--no-default-browser-check', '--disable-extensions',
  '--disable-background-networking', '--window-size=1400,1000',
  `--user-data-dir=/tmp/shulkr-profile-${PORT}`,
]
if (opt.headless) flags.unshift('--headless=new')
const proc = spawn(chrome, flags, { stdio: 'ignore' })

let wsUrl = null
for (let i = 0; i < 200; i++) {
  try {
    const r = await fetch(`http://127.0.0.1:${PORT}/json/version`)
    const j = await r.json()
    if (j.webSocketDebuggerUrl) { wsUrl = j.webSocketDebuggerUrl; break }
  } catch {}
  await sleep(200)
}
if (!wsUrl) { proc.kill(); console.error('chromium failed to start'); process.exit(1) }

const ws = new WebSocket(wsUrl)
await new Promise((res, rej) => { ws.onopen = res; ws.onerror = rej })
let id = 0
const pending = new Map()
ws.onmessage = (ev) => {
  const m = JSON.parse(ev.data)
  if (m.id && pending.has(m.id)) {
    const { res, rej } = pending.get(m.id); pending.delete(m.id)
    m.error ? rej(new Error(JSON.stringify(m.error))) : res(m.result)
  }
}
const send = (method, params = {}, sessionId) => new Promise((res, rej) => {
  const mid = ++id
  pending.set(mid, { res, rej })
  ws.send(JSON.stringify({ id: mid, method, params, sessionId }))
})

try {
  // attach to a fresh tab
  const { targetId } = await send('Target.createTarget', { url: 'about:blank' })
  const { sessionId } = await send('Target.attachToTarget', { targetId, flatten: true })
  const S = (m, p) => send(m, p, sessionId)
  await S('Page.enable'); await S('DOM.enable'); await S('Runtime.enable')
  await S('Page.navigate', { url: opt.url })
  await sleep(6000)

  // find the file input (the viewer's drop zone)
  const { root } = await S('DOM.getDocument', { depth: -1, pierce: true })
  const { nodeId } = await S('DOM.querySelector', { nodeId: root.nodeId, selector: 'input[type=file]' })
  if (!nodeId) {
    const hints = await S('Runtime.evaluate', {
      returnByValue: true,
      expression: `JSON.stringify({title: document.title, inputs: [...document.querySelectorAll('input')].map(i=>i.type), text: document.body.innerText.slice(0,400)})`,
    })
    console.error('no input[type=file] found. Page said: ' + hints.result.value)
    throw new Error('viewer markup changed or the page did not finish loading')
  }
  await S('DOM.setFileInputFiles', { nodeId, files: [nbtPath] })
  console.log('uploaded ' + nbtPath + ' — waiting ' + opt.wait + 'ms for the render')

  // the viewer also accepts a drop event; nudge it in case the input is hidden
  await S('Runtime.evaluate', {
    expression: `(() => { const i=document.querySelector('input[type=file]'); if(i){ i.dispatchEvent(new Event('change',{bubbles:true})); } })()`,
  })

  await sleep(opt.wait)
  const { data } = await S('Page.captureScreenshot', { format: 'png' })
  writeFileSync(resolve(opt.out), Buffer.from(data, 'base64'))
  console.log('wrote ' + resolve(opt.out))
} catch (e) {
  console.error('shulkr_shot: ' + e.message)
  process.exitCode = 1
} finally {
  try { ws.close() } catch {}
  proc.kill()
  await sleep(300)
}
