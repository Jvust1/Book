import { cp, mkdir, readFile } from 'node:fs/promises'
import { createRequire } from 'node:module'
import { dirname, join } from 'node:path'
import { fileURLToPath } from 'node:url'

// Fixed npm source only. Do not copy user PDFs or private local directories.
const require = createRequire(import.meta.url)
const source = dirname(require.resolve('pdfjs-dist/package.json'))
const packageInfo = JSON.parse(await readFile(join(source, 'package.json'), 'utf8'))
if (packageInfo.version !== '6.3.289') throw new Error('Review the PDF.js asset pin before updating')
const target = fileURLToPath(new URL('../public/pdfjs/', import.meta.url))
await mkdir(target, { recursive: true })
for (const directory of ['cmaps', 'standard_fonts', 'wasm', 'iccs']) {
  // Includes each upstream directory's license notices.
  await cp(join(source, directory), join(target, directory), { recursive: true })
}
await cp(join(source, 'LICENSE'), join(target, 'LICENSE'))
console.log(`Prepared local PDF.js ${packageInfo.version} rendering resources`)
