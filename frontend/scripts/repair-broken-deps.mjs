import { mkdir, writeFile } from 'node:fs/promises'
import { existsSync } from 'node:fs'
import { join } from 'node:path'
import { fileURLToPath } from 'node:url'

const frontendDir = fileURLToPath(new URL('..', import.meta.url))
const estreeWalkerDir = join(frontendDir, 'node_modules', 'estree-walker')
const esmDir = join(estreeWalkerDir, 'dist', 'esm')
const umdDir = join(estreeWalkerDir, 'dist', 'umd')
const esmFile = join(esmDir, 'estree-walker.js')
const umdFile = join(umdDir, 'estree-walker.js')

const esmContent = `class WalkerBase {
  constructor() {
    this.should_skip = false
    this.should_remove = false
    this.replacement = null
    this.context = {
      skip: () => (this.should_skip = true),
      remove: () => (this.should_remove = true),
      replace: (node) => (this.replacement = node),
    }
  }

  replace(parent, prop, index, node) {
    if (!parent) return
    if (index !== null && index !== undefined) {
      parent[prop][index] = node
      return
    }
    parent[prop] = node
  }

  remove(parent, prop, index) {
    if (!parent) return
    if (index !== null && index !== undefined) {
      parent[prop].splice(index, 1)
      return
    }
    delete parent[prop]
  }
}

class SyncWalker extends WalkerBase {
  constructor(enter, leave) {
    super()
    this.enter = enter
    this.leave = leave
  }

  visit(node, parent, prop, index) {
    if (!node) return node

    if (this.enter) {
      const previousSkip = this.should_skip
      const previousRemove = this.should_remove
      const previousReplacement = this.replacement
      this.should_skip = false
      this.should_remove = false
      this.replacement = null
      this.enter.call(this.context, node, parent, prop, index)

      if (this.replacement) {
        node = this.replacement
        this.replace(parent, prop, index, node)
      }

      if (this.should_remove) {
        this.remove(parent, prop, index)
      }

      const skipped = this.should_skip
      const removed = this.should_remove
      this.should_skip = previousSkip
      this.should_remove = previousRemove
      this.replacement = previousReplacement
      if (skipped) return node
      if (removed) return null
    }

    for (const key in node) {
      const value = node[key]
      if (!value || typeof value !== 'object') continue

      if (Array.isArray(value)) {
        for (let offset = 0; offset < value.length; offset += 1) {
          const child = value[offset]
          if (child && typeof child.type === 'string') {
            const result = this.visit(child, node, key, offset)
            if (!result) {
              offset -= 1
            }
          }
        }
        continue
      }

      if (typeof value.type === 'string') {
        this.visit(value, node, key, null)
      }
    }

    if (this.leave) {
      const previousReplacement = this.replacement
      const previousRemove = this.should_remove
      this.replacement = null
      this.should_remove = false

      this.leave.call(this.context, node, parent, prop, index)

      if (this.replacement) {
        node = this.replacement
        this.replace(parent, prop, index, node)
      }

      if (this.should_remove) {
        this.remove(parent, prop, index)
      }

      const removed = this.should_remove
      this.replacement = previousReplacement
      this.should_remove = previousRemove
      if (removed) return null
    }

    return node
  }
}

class AsyncWalker extends WalkerBase {
  constructor(enter, leave) {
    super()
    this.enter = enter
    this.leave = leave
  }

  async visit(node, parent, prop, index) {
    if (!node) return node

    if (this.enter) {
      const previousSkip = this.should_skip
      const previousRemove = this.should_remove
      const previousReplacement = this.replacement
      this.should_skip = false
      this.should_remove = false
      this.replacement = null
      await this.enter.call(this.context, node, parent, prop, index)

      if (this.replacement) {
        node = this.replacement
        this.replace(parent, prop, index, node)
      }

      if (this.should_remove) {
        this.remove(parent, prop, index)
      }

      const skipped = this.should_skip
      const removed = this.should_remove
      this.should_skip = previousSkip
      this.should_remove = previousRemove
      this.replacement = previousReplacement
      if (skipped) return node
      if (removed) return null
    }

    for (const key in node) {
      const value = node[key]
      if (!value || typeof value !== 'object') continue

      if (Array.isArray(value)) {
        for (let offset = 0; offset < value.length; offset += 1) {
          const child = value[offset]
          if (child && typeof child.type === 'string') {
            const result = await this.visit(child, node, key, offset)
            if (!result) {
              offset -= 1
            }
          }
        }
        continue
      }

      if (typeof value.type === 'string') {
        await this.visit(value, node, key, null)
      }
    }

    if (this.leave) {
      const previousReplacement = this.replacement
      const previousRemove = this.should_remove
      this.replacement = null
      this.should_remove = false

      await this.leave.call(this.context, node, parent, prop, index)

      if (this.replacement) {
        node = this.replacement
        this.replace(parent, prop, index, node)
      }

      if (this.should_remove) {
        this.remove(parent, prop, index)
      }

      const removed = this.should_remove
      this.replacement = previousReplacement
      this.should_remove = previousRemove
      if (removed) return null
    }

    return node
  }
}

export function walk(ast, { enter, leave } = {}) {
  const walker = new SyncWalker(enter, leave)
  return walker.visit(ast, null)
}

export async function asyncWalk(ast, { enter, leave } = {}) {
  const walker = new AsyncWalker(enter, leave)
  return walker.visit(ast, null)
}
`

const umdContent = `'use strict'

${esmContent.replace(/export async function asyncWalk/g, 'async function asyncWalk').replace(/export function walk/g, 'function walk')}

module.exports = {
  walk,
  asyncWalk,
}
`

async function ensureEstreeWalkerDist() {
  if (!existsSync(estreeWalkerDir)) {
    return
  }

  await mkdir(esmDir, { recursive: true })
  await mkdir(umdDir, { recursive: true })
  await writeFile(esmFile, esmContent, 'utf8')
  await writeFile(umdFile, umdContent, 'utf8')
}

await ensureEstreeWalkerDist()
