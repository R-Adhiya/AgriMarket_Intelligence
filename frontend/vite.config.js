import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'
import { fileURLToPath } from 'url'

const __dirname = path.dirname(fileURLToPath(import.meta.url))
// Resolve the real (non-symlinked) path to prevent Vite/Rollup from
// deriving a relative path that traverses into OneDrive on Windows.
import { realpathSync } from 'fs'
const projectRoot = realpathSync(__dirname)

export default defineConfig({
  root: projectRoot,
  plugins: [react()],
  server: {
    port: 5173,
  },
  build: {
    outDir: path.join(projectRoot, 'dist'),
  },
})
