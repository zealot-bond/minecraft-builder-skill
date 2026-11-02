#!/usr/bin/env node

import { spawn } from 'node:child_process'
import { createReadStream } from 'node:fs'
import fs from 'node:fs/promises'
import path from 'node:path'
import { fileURLToPath } from 'node:url'
import { createServer } from 'vite'

const scriptDir = path.dirname(fileURLToPath(import.meta.url))
const skillRoot = path.resolve(scriptDir, '..')
const viewerRoot = path.join(skillRoot, 'assets', 'viewer')

function usage() {
  return `Usage:
  node scripts/preview.mjs --nbt <path/to/build.nbt> [--host 127.0.0.1] [--port 5173] [--lighting day|night] [--open|--no-open]
`
}

function parseArgs(argv) {
  const options = {
    nbt: undefined,
    host: '127.0.0.1',
    port: 5173,
    lighting: 'day',
    open: true,
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
    } else if (arg === '--nbt') {
      options.nbt = readValue(arg, index)
      index += 1
    } else if (arg.startsWith('--nbt=')) {
      options.nbt = arg.slice('--nbt='.length)
    } else if (arg === '--host') {
      options.host = readValue(arg, index)
      index += 1
    } else if (arg.startsWith('--host=')) {
      options.host = arg.slice('--host='.length)
    } else if (arg === '--port') {
      options.port = Number(readValue(arg, index))
      index += 1
    } else if (arg.startsWith('--port=')) {
      options.port = Number(arg.slice('--port='.length))
    } else if (arg === '--lighting') {
      options.lighting = readValue(arg, index)
      index += 1
    } else if (arg.startsWith('--lighting=')) {
      options.lighting = arg.slice('--lighting='.length)
    } else if (arg === '--open') {
      options.open = true
    } else if (arg === '--no-open') {
      options.open = false
    } else if (!options.nbt) {
      options.nbt = arg
    } else {
      throw new Error(`Unexpected argument: ${arg}`)
    }
  }
  if (!Number.isInteger(options.port) || options.port < 0) {
    throw new Error('--port must be a non-negative integer')
  }
  if (!['day', 'night'].includes(options.lighting)) {
    throw new Error('--lighting must be day or night')
  }
  return options
}

function contentType(filePath) {
  if (filePath.endsWith('.json')) return 'application/json'
  if (filePath.endsWith('.png')) return 'image/png'
  if (filePath.endsWith('.txt')) return 'text/plain; charset=utf-8'
  if (filePath.endsWith('.nbt')) return 'application/octet-stream'
  return 'application/octet-stream'
}

async function resolveLodestoneRoot() {
  const indexUrl = await import.meta.resolve('@mattzh72/lodestone')
  const indexPath = fileURLToPath(indexUrl)
  return path.resolve(path.dirname(indexPath), '..')
}

async function openUrl(url) {
  const command = process.platform === 'darwin'
    ? 'open'
    : process.platform === 'win32'
      ? 'cmd'
      : 'xdg-open'
  const args = process.platform === 'win32' ? ['/c', 'start', '', url] : [url]
  const child = spawn(command, args, {
    stdio: 'ignore',
    detached: true,
  })
  child.on('error', () => undefined)
  child.unref()
}

function serveFile(response, filePath) {
  response.statusCode = 200
  response.setHeader('Content-Type', contentType(filePath))
  const stream = createReadStream(filePath)
  stream.on('error', error => {
    if (!response.headersSent) {
      response.statusCode = 500
      response.end('Failed to read file')
    } else {
      response.destroy(error)
    }
  })
  stream.pipe(response)
}

function createPreviewMiddlewarePlugin(nbtPath, defaultPackRoot) {
  return {
    name: 'minecraft-builder-preview-middleware',
    configureServer(server) {
      server.middlewares.use('/__minecraft_builder__/build.nbt', (_request, response) => {
        serveFile(response, nbtPath)
      })

      server.middlewares.use('/__minecraft_builder__/default-pack/', async (request, response) => {
        try {
          const requestUrl = new URL(request.url ?? '/', 'http://localhost')
          const relativePath = decodeURIComponent(requestUrl.pathname.replace(/^\/+/, ''))
          const filePath = path.resolve(defaultPackRoot, relativePath)
          const allowedRoot = `${defaultPackRoot}${path.sep}`
          if (filePath !== defaultPackRoot && !filePath.startsWith(allowedRoot)) {
            response.statusCode = 403
            response.end('Forbidden')
            return
          }
          await fs.access(filePath)
          serveFile(response, filePath)
        } catch {
          response.statusCode = 404
          response.end('Not found')
        }
      })
    },
  }
}

async function main() {
  const options = parseArgs(process.argv.slice(2))
  if (options.help) {
    console.log(usage())
    return
  }
  if (!options.nbt) {
    throw new Error(`Missing --nbt path.\n${usage()}`)
  }

  const nbtPath = path.resolve(options.nbt)
  await fs.access(nbtPath)
  const lodestoneRoot = await resolveLodestoneRoot()
  const defaultPackRoot = path.join(lodestoneRoot, 'assets', 'default-pack')

  const server = await createServer({
    root: viewerRoot,
    appType: 'spa',
    clearScreen: false,
    plugins: [createPreviewMiddlewarePlugin(nbtPath, defaultPackRoot)],
    server: {
      host: options.host,
      port: options.port,
      strictPort: false,
      open: false,
      fs: {
        strict: false,
      },
    },
  })

  await server.listen()
  const local = server.resolvedUrls?.local?.[0] ?? `http://${options.host}:${options.port}/`
  const url = new URL(local)
  url.searchParams.set('nbt', '/__minecraft_builder__/build.nbt')
  url.searchParams.set('name', path.basename(nbtPath))
  if (options.lighting !== 'day') {
    url.searchParams.set('lighting', options.lighting)
  }

  console.log(`Minecraft build preview: ${url.toString()}`)
  if (options.open) {
    await openUrl(url.toString())
  }

  let closing = false
  const close = async () => {
    if (closing) return
    closing = true
    await server.close()
    process.exit(0)
  }
  process.on('SIGINT', close)
  process.on('SIGTERM', close)
}

main().catch(err => {
  console.error(`preview: ${err.message}`)
  process.exitCode = 1
})
