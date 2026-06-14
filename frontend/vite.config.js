import path from 'path'
import { defineConfig } from 'vite'
import tailwindcss from '@tailwindcss/vite'
import react from '@vitejs/plugin-react'


export default defineConfig({
  root: __dirname,
  plugins: [
    tailwindcss(),
    react(),
  ],
  build: {
    outDir: 'dist',
    rollupOptions: {
      input: path.resolve(__dirname, 'index.html'),
    },
  },
  resolve:{
    alias:{
      '@': path.resolve(__dirname, './src'),
    }
  }
})
