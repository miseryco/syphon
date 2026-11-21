import { readFileSync } from 'node:fs'
import { basename, dirname } from 'node:path'
import { defineConfig, loadEnv } from 'vite'

const shared = new URL('./shared/', import.meta.url)

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), 'VITE_')
  return {
    appType: 'mpa',
    base: env.VITE_BASE_PATH || '/syphon/',
    plugins: [{
      name: 'syphon-shared-html',
      transformIndexHtml: {
        order: 'pre',
        handler(html, { filename }) {
          const pageLink = `href="%BASE_URL%${basename(dirname(filename))}/"`
          return html.replace(/<!-- include ([\w-]+) -->/g, (_, name) => {
            const partial = readFileSync(new URL(name + '.html', shared), 'utf8')
            return name === 'footer'
              ? partial.replace(pageLink, `${pageLink} aria-current="page"`)
              : partial
          })
        },
      },
      handleHotUpdate({ file, server }) {
        if (file.includes('/shared/') && file.endsWith('.html')) {
          server.ws.send({ type: 'full-reload' })
          return []
        }
      },
    }],
    build: { rollupOptions: { input: ['index.html', 'booklet/index.html', 'download/index.html', 'support/index.html', 'privacy/index.html'] } },
  }
})
